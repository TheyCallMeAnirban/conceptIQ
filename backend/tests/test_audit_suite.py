import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models import (
    Concept,
    Question,
    Learner,
    ConceptMastery,
    AssessmentSession,
    QuestionAttempt,
)
from backend.app.seed.seed_db import seed_database
from backend.app.domain.bkt import BKTEngine
from backend.app.domain.evaluator import AnswerEvaluator
from backend.app.domain.scheduler import LeitnerScheduler
from backend.app.domain.schemas.diagnosis import DiagnosticInput, DiagnosticOutput, ReasoningQuality
from backend.app.domain.schemas.session import AttemptSubmission
from backend.app.services.llm_diagnostician import LLMDiagnostician
from backend.app.services.learning_loop import LearningLoopService
from backend.app.services.question_selector import QuestionSelector


@pytest.fixture
def audit_db():
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    seed_database(db=session)
    try:
        yield session
    finally:
        session.close()


# ============================================================================
# 1. CORRECTNESS AUTHORITY AUDIT TESTS
# ============================================================================

def test_backend_evaluator_mcq_normalizations():
    """Verify robust deterministic normalization of student MCQ answers."""
    assert AnswerEvaluator.evaluate("B", "B") is True
    assert AnswerEvaluator.evaluate("B", "Option B") is True
    assert AnswerEvaluator.evaluate("B", "(b)") is True
    assert AnswerEvaluator.evaluate("B", "b.") is True
    assert AnswerEvaluator.evaluate("B", "Choice C") is False
    assert AnswerEvaluator.evaluate("B", "") is False
    assert AnswerEvaluator.evaluate("B", None) is False


def test_backend_evaluator_nat_numerical_tolerances():
    """Verify NAT float tolerance and string fallbacks."""
    assert AnswerEvaluator.evaluate("1024", "1024", question_type="NAT") is True
    assert AnswerEvaluator.evaluate("1024.0", "1024", question_type="NAT") is True
    assert AnswerEvaluator.evaluate("1024.00005", "1024.0", question_type="NAT") is True
    assert AnswerEvaluator.evaluate("1024.5", "1024.0", question_type="NAT") is False
    assert AnswerEvaluator.evaluate("xyz", "xyz", question_type="NAT") is True
    assert AnswerEvaluator.evaluate("xyz", "abc", question_type="NAT") is False


def test_llm_cannot_override_backend_correctness_when_wrong(audit_db):
    """
    If the LLM hallucinates is_correct=True for an objectively wrong answer,
    the backend MUST override it to False, and BKT must decrease.
    """
    learner_id = "learner_gate_01"
    session = AssessmentSession(
        learner_id=learner_id,
        current_question_id="Q_DATA_01",  # Correct answer is B
        status="ACTIVE",
    )
    audit_db.add(session)
    audit_db.commit()

    # Mock diagnostician returning hallucinated is_correct=True for wrong answer 'A'
    mock_diag = MagicMock()
    mock_diag.diagnose.return_value = DiagnosticOutput(
        is_correct=True,  # Hallucinated!
        reasoning_quality=ReasoningQuality.FLAWED,
        detected_misconceptions=[],
        affected_concepts=["DATA_TYPES_MEM_REP"],
        reasoning_evidence="Hallucinated confirmation",
        explanation="LLM thought it was right",
        recommended_intervention="None",
        suggested_difficulty=0.5,
        diagnosis_provider="mock_llm",
    )

    loop_service = LearningLoopService(db=audit_db, diagnostician=mock_diag)
    submission = AttemptSubmission(
        learner_id=learner_id,
        session_id=session.id,
        question_id="Q_DATA_01",
        student_answer="Option A",  # Wrong! Expected is B
        reasoning_transcript="I think x and &x are both 4 bytes.",
    )

    result = loop_service.process_attempt(submission)

    # Invariant: Backend authority wins!
    assert result.is_correct is False
    assert result.diagnosis.is_correct is False
    assert result.bkt_update["delta"] < 0  # BKT decreased


def test_llm_cannot_override_backend_correctness_when_right(audit_db):
    """
    If the LLM falsely claims an answer is False when it is correct,
    the backend MUST enforce True, and BKT must increase.
    """
    learner_id = "learner_gate_01"
    session = AssessmentSession(
        learner_id=learner_id,
        current_question_id="Q_DATA_01",
        status="ACTIVE",
    )
    audit_db.add(session)
    audit_db.commit()

    # Mock diagnostician falsely claiming is_correct=False for correct answer 'B'
    mock_diag = MagicMock()
    mock_diag.diagnose.return_value = DiagnosticOutput(
        is_correct=False,  # False negative hallucination
        reasoning_quality=ReasoningQuality.SOUND,
        detected_misconceptions=[],
        affected_concepts=["DATA_TYPES_MEM_REP"],
        reasoning_evidence="Good reasoning",
        explanation="LLM mistakenly said false",
        recommended_intervention="None",
        suggested_difficulty=0.5,
        diagnosis_provider="mock_llm",
    )

    loop_service = LearningLoopService(db=audit_db, diagnostician=mock_diag)
    submission = AttemptSubmission(
        learner_id=learner_id,
        session_id=session.id,
        question_id="Q_DATA_01",
        student_answer="Option B",  # Correct!
        reasoning_transcript="sizeof x is 4 and address &x is 8 on 64-bit.",
    )

    result = loop_service.process_attempt(submission)

    # Invariant: Backend authority wins!
    assert result.is_correct is True
    assert result.diagnosis.is_correct is True
    assert result.bkt_update["delta"] > 0  # BKT increased


# ============================================================================
# 2. DIAGNOSTIC ENGINE FAILURE & RESILIENCE TESTS
# ============================================================================

@pytest.fixture
def base_input():
    return DiagnosticInput(
        question_statement="Pointer addition test",
        expected_answer="B",
        student_answer="A",
        is_correct=False,
        reasoning_transcript="ptr + 2 adds 1 byte per step.",
        primary_concept="POINTER_ARITHMETIC",
        known_misconceptions=[
            {
                "id": "BYTE_INCREMENT_FALLACY",
                "name": "Byte increment fallacy",
                "description": "Assumes ptr+1 adds 1 byte",
                "remediation_hint": "Scales by sizeof(*ptr)",
            }
        ],
    )


def test_diagnostician_missing_credentials(base_input):
    """Missing API key defaults to labeled deterministic fallback."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = None
    res = diag.diagnose(base_input)
    assert res.diagnosis_provider == "deterministic_fallback"
    assert res.is_correct == base_input.is_correct


def test_diagnostician_timeout_fallback(base_input):
    """Network timeout falls back to deterministic fallback."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = "fake_key"
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):
        res = diag.diagnose(base_input)
        assert res.diagnosis_provider == "deterministic_fallback"


def test_diagnostician_http_4xx_fallback(base_input):
    """HTTP 401/403 errors fall back gracefully."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = "fake_key"
    mock_resp = MagicMock(status_code=401)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_resp)
    with patch("httpx.Client.post", return_value=mock_resp):
        res = diag.diagnose(base_input)
        assert res.diagnosis_provider == "deterministic_fallback"


def test_diagnostician_http_5xx_fallback(base_input):
    """HTTP 500/503 errors fall back gracefully."""
    diag = LLMDiagnostician(provider="openai")
    diag.openai_api_key = "fake_key"
    mock_resp = MagicMock(status_code=503)
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Service Unavailable", request=MagicMock(), response=mock_resp)
    with patch("httpx.Client.post", return_value=mock_resp):
        res = diag.diagnose(base_input)
        assert res.diagnosis_provider == "deterministic_fallback"


def test_diagnostician_invalid_json_fallback(base_input):
    """Invalid / unparseable JSON falls back gracefully."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = "fake_key"
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "THIS IS NOT JSON {{{{"}]}}]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        res = diag.diagnose(base_input)
        assert res.diagnosis_provider == "deterministic_fallback"


def test_diagnostician_schema_violation_fallback(base_input):
    """JSON that violates Pydantic schema (e.g. difficulty = 99.0) falls back gracefully."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = "fake_key"
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {"parts": [{
                "text": '{"is_correct": false, "reasoning_quality": "SOUND", "suggested_difficulty": 99.0, "reasoning_evidence": "x", "explanation": "x", "recommended_intervention": "x"}'
            }]}
        }]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        res = diag.diagnose(base_input)
        assert res.diagnosis_provider == "deterministic_fallback"


def test_diagnostician_sanitizes_unknown_misconceptions(base_input):
    """Hallucinated misconception IDs not in the catalog must be purged."""
    diag = LLMDiagnostician(provider="gemini")
    diag.gemini_api_key = "fake_key"
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {
        "candidates": [{
            "content": {"parts": [{
                "text": '{"is_correct": false, "reasoning_quality": "FLAWED", "detected_misconceptions": ["HALLUCINATED_ID", "BYTE_INCREMENT_FALLACY"], "affected_concepts": ["POINTER_ARITHMETIC"], "reasoning_evidence": "quote", "explanation": "exp", "recommended_intervention": "hint", "suggested_difficulty": 0.5}'
            }]}
        }]
    }
    with patch("httpx.Client.post", return_value=mock_resp):
        res = diag.diagnose(base_input)
        assert "HALLUCINATED_ID" not in res.detected_misconceptions
        assert "BYTE_INCREMENT_FALLACY" in res.detected_misconceptions


# ============================================================================
# 3. BKT NUMERICAL VERIFICATION AUDIT
# ============================================================================

def test_bkt_independent_numerical_derivation():
    """
    Exact analytical verification:
    P(L) = 0.50, S = 0.12, G = 0.20, T = 0.12
    Observation: False (Incorrect)
    1. Posterior given obs=0:
       Num = 0.50 * 0.12 = 0.06
       Den = 0.06 + (1 - 0.50) * (1 - 0.20) = 0.06 + 0.40 = 0.46
       P(L | obs=0) = 0.06 / 0.46 = 3 / 23 = 0.13043478...
    2. Transition:
       P(L_t+1) = 0.13043478 + (1 - 0.13043478) * 0.12
                = 0.13043478 + 0.10434783 = 0.2347826...
       Rounded to 4 decimal places = 0.2348
    """
    res = BKTEngine.update(
        prior=0.50,
        is_correct=False,
        p_slip=0.12,
        p_guess=0.20,
        p_transit=0.12,
    )
    assert abs(res.posterior - 0.2348) < 1e-4
    assert abs(res.delta - (0.2348 - 0.50)) < 1e-4


def test_duplicate_submission_prevention(audit_db):
    """Submitting the same question twice in the same session must be rejected."""
    session = AssessmentSession(learner_id="learner_gate_01", current_question_id="Q_DATA_01")
    audit_db.add(session)
    audit_db.commit()

    sub = AttemptSubmission(
        learner_id="learner_gate_01",
        session_id=session.id,
        question_id="Q_DATA_01",
        student_answer="B",
        reasoning_transcript="x is 4 &x is 8",
    )
    loop = LearningLoopService(db=audit_db)
    res1 = loop.process_attempt(sub)
    assert res1.attempt_id is not None

    # Second attempt on identical question in same session must raise ValueError
    with pytest.raises(ValueError, match="already been attempted"):
        loop.process_attempt(sub)


# ============================================================================
# 4. LEITNER SCHEDULER EDGE CASES
# ============================================================================

def test_leitner_box_5_capped():
    """Box 5 stays at Box 5 on correct answer."""
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    res = LeitnerScheduler.calculate_update("C1", current_box=5, is_correct=True, now=now)
    assert res.previous_box == 5
    assert res.new_box == 5


def test_leitner_box_1_stays_box_1_on_incorrect():
    """Box 1 stays at Box 1 on incorrect answer."""
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    res = LeitnerScheduler.calculate_update("C1", current_box=1, is_correct=False, now=now)
    assert res.previous_box == 1
    assert res.new_box == 1
    assert res.consecutive_correct == 0


def test_leitner_timezone_safety():
    """Verify timezone safety for naive and aware datetimes."""
    now = datetime.now(timezone.utc)
    # Naive timestamp should not crash evaluate_urgency
    naive_due = datetime(2026, 10, 31, 10, 0)
    is_due, urgency = LeitnerScheduler.evaluate_urgency(naive_due, now=now)
    assert isinstance(is_due, bool)
    assert isinstance(urgency, float)


# ============================================================================
# 5. ADAPTIVE SELECTOR & PREREQUISITE AUDIT
# ============================================================================

def test_selector_never_selects_unmet_prerequisites_as_frontier(audit_db):
    """
    Concepts whose prerequisites have mastery < 0.50 must NOT be selected
    as learning-frontier concepts.
    """
    # Force DATA_TYPES_MEM_REP to low mastery (0.20)
    m = audit_db.query(ConceptMastery).filter(
        ConceptMastery.learner_id == "learner_gate_01",
        ConceptMastery.concept_id == "DATA_TYPES_MEM_REP"
    ).first()
    if not m:
        m = ConceptMastery(
            learner_id="learner_gate_01",
            concept_id="DATA_TYPES_MEM_REP",
            p_mastery=0.20,
            p_transit=0.15,
            p_guess=0.20,
            p_slip=0.10,
        )
        audit_db.add(m)
    else:
        m.p_mastery = 0.20
    audit_db.commit()

    selector = QuestionSelector(audit_db)
    rec = selector.select_next_question("learner_gate_01", session_attempted_qids=[])

    # Must target the unmastered root, not downstream concepts like MULTIDIMENSIONAL_ARRAYS
    assert rec.target_concept_id == "DATA_TYPES_MEM_REP"
    assert rec.target_concept_id != "MULTIDIMENSIONAL_ARRAYS"
