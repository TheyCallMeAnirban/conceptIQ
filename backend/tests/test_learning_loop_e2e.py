import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import (
    AssessmentSession,
    QuestionAttempt,
    ConceptMastery,
    Learner,
)
from backend.app.seed.seed_db import seed_database
from backend.app.domain.schemas.session import AttemptSubmission
from backend.app.services.learning_loop import LearningLoopService


@pytest.fixture
def clean_db():
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


def test_complete_learning_loop_misconception_flow(clean_db):
    """
    Demonstrates the full end-to-end adaptive flow:
    Student reasoning -> Diagnosis -> BKT update (binary) -> Leitner update -> Adaptive question selection -> Selection rationale.
    """
    learner_id = "learner_gate_01"
    
    # 1. Create active assessment session starting on Q_ARITH_01 (Pointer addition)
    session = AssessmentSession(
        learner_id=learner_id,
        current_question_id="Q_ARITH_01",
        status="ACTIVE",
    )
    clean_db.add(session)
    clean_db.commit()

    # Pre-attempt state inspection - set realistic prior above P(T) to observe mastery drop
    initial_mastery = (
        clean_db.query(ConceptMastery)
        .filter(
            ConceptMastery.learner_id == learner_id,
            ConceptMastery.concept_id == "POINTER_ARITHMETIC",
        )
        .first()
    )
    if not initial_mastery:
        initial_mastery = ConceptMastery(
            learner_id=learner_id,
            concept_id="POINTER_ARITHMETIC",
            p_mastery=0.50,
            p_transit=0.12,
            p_guess=0.20,
            p_slip=0.12,
            assessment_state="UNASSESSED",
        )
        clean_db.add(initial_mastery)
    else:
        initial_mastery.p_mastery = 0.50
    clean_db.commit()
    prior_p = 0.50

    # 2. Student dictates flawed reasoning (Wispr Flow style with speech artifacts)
    # Question Q_ARITH_01 expects B (0x3008), student chooses A (0x3002) exhibiting BYTE_INCREMENT_FALLACY
    submission = AttemptSubmission(
        learner_id=learner_id,
        session_id=session.id,
        question_id="Q_ARITH_01",
        student_answer="Option A",
        reasoning_transcript="Um, so ptr holds address 0x3000, and we add 2 to it. Because adding integers adds 1 byte each time, the address becomes 0x3002.",
    )

    loop_service = LearningLoopService(db=clean_db)
    result = loop_service.process_attempt(submission)

    # 3. Assert Diagnosis
    assert result.is_correct is False
    assert "BYTE_INCREMENT_FALLACY" in result.diagnosis.detected_misconceptions
    assert "sizeof" in result.diagnosis.recommended_intervention.lower() or "byte" in result.diagnosis.recommended_intervention.lower()
    assert result.diagnosis.diagnosis_provider in ["gemini", "deterministic_fallback"]

    # 4. Assert BKT Mastery Update (Strictly binary, no arbitrary weights)
    assert result.bkt_update["prior"] == prior_p
    assert result.bkt_update["posterior"] < prior_p
    assert result.bkt_update["delta"] < 0
    # Audit log check in DB
    saved_attempt = clean_db.query(QuestionAttempt).filter(QuestionAttempt.id == result.attempt_id).first()
    assert saved_attempt is not None
    assert saved_attempt.p_mastery_prior == prior_p
    assert saved_attempt.p_mastery_posterior == result.bkt_update["posterior"]

    # 5. Assert Leitner Spaced Repetition Update
    assert result.leitner_update["new_box"] == 1
    assert result.leitner_update["consecutive_correct"] == 0

    # 6. Assert Adaptive Next Question Selection & Transparent Rationale
    assert result.next_question is not None
    assert result.next_question.question_id != "Q_ARITH_01"  # No repetition
    assert result.next_question.rationale.selection_reason in [
        "PREREQUISITE_REMEDIATION",
        "CONCEPT_CALIBRATION_EASY",
        "SPACED_REPETITION_DUE",
    ]
    assert len(result.next_question.rationale.prerequisite_status) > 0
    assert len(result.next_question.rationale.rationale_details) > 0

    # 7. Assert Session State Persistence
    updated_session = clean_db.query(AssessmentSession).filter(AssessmentSession.id == session.id).first()
    assert updated_session.attempt_count == 1
    assert updated_session.current_question_id == result.next_question.question_id
    assert updated_session.status == "ACTIVE"


def test_complete_learning_loop_sound_reasoning_flow(clean_db):
    """
    Demonstrates the positive learning path:
    Student provides correct answer and sound reasoning -> Mastery increases -> Leitner advances.
    """
    learner_id = "learner_gate_02"
    session = AssessmentSession(
        learner_id=learner_id,
        current_question_id="Q_DATA_01",
        status="ACTIVE",
    )
    clean_db.add(session)
    clean_db.commit()

    prior_rec = (
        clean_db.query(ConceptMastery)
        .filter(
            ConceptMastery.learner_id == learner_id,
            ConceptMastery.concept_id == "DATA_TYPES_MEM_REP",
        )
        .first()
    )
    if not prior_rec:
        prior_rec = ConceptMastery(
            learner_id=learner_id,
            concept_id="DATA_TYPES_MEM_REP",
            p_mastery=0.25,
            p_transit=0.15,
            p_guess=0.20,
            p_slip=0.10,
            assessment_state="UNASSESSED",
        )
        clean_db.add(prior_rec)
        clean_db.commit()
    prior_mastery = prior_rec.p_mastery

    submission = AttemptSubmission(
        learner_id=learner_id,
        session_id=session.id,
        question_id="Q_DATA_01",
        student_answer="B",
        reasoning_transcript="sizeof x evaluates to 4 bytes for int, and &x is a pointer so on 64-bit architecture it evaluates to 8 bytes, so 4 8.",
    )

    loop_service = LearningLoopService(db=clean_db)
    result = loop_service.process_attempt(submission)

    assert result.is_correct is True
    assert result.diagnosis.detected_misconceptions == []
    assert result.bkt_update["posterior"] > prior_mastery
    assert result.bkt_update["delta"] > 0
    assert result.leitner_update["new_box"] == 2
    assert result.leitner_update["consecutive_correct"] == 1
