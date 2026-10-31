import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import ConceptMastery, QuestionAttempt
from backend.app.seed.seed_db import seed_database
from backend.app.services.question_selector import QuestionSelector


@pytest.fixture
def seeded_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    seed_database(db=session)
    try:
        yield session
    finally:
        session.close()


def test_question_selector_initial_frontier(seeded_db):
    """Initial learner should be served root concept with calibration difficulty."""
    selector = QuestionSelector(seeded_db)
    rec = selector.select_next_question("learner_gate_01", session_attempted_qids=[])

    assert rec is not None
    assert rec.target_concept_id == "DATA_TYPES_MEM_REP"
    assert rec.rationale.selection_reason == "CONCEPT_CALIBRATION_EASY"
    assert rec.difficulty <= 0.45


def test_question_selector_prerequisite_remediation(seeded_db):
    """
    If learner attempts ARRAY_POINTER_DECAY but prerequisite DATA_TYPES_MEM_REP
    is weak (< 0.50), prerequisite remediation should be triggered.
    """
    # Simulate an attempt on child concept ARRAY_POINTER_DECAY
    attempt = QuestionAttempt(
        session_id="S_TEST",
        learner_id="learner_gate_01",
        question_id="Q_DECAY_01",
        concept_id="ARRAY_POINTER_DECAY",
        sequence_number=1,
        student_answer="A",
        reasoning_transcript="flawed reasoning",
        is_correct=False,
        p_mastery_prior=0.10,
        p_mastery_posterior=0.08,
        p_transit_used=0.10,
        p_guess_used=0.20,
        p_slip_used=0.15,
    )
    seeded_db.add(attempt)
    # Ensure prerequisite DATA_TYPES_MEM_REP is low (e.g. 0.20)
    prereq_mastery = (
        seeded_db.query(ConceptMastery)
        .filter(
            ConceptMastery.learner_id == "learner_gate_01",
            ConceptMastery.concept_id == "DATA_TYPES_MEM_REP",
        )
        .first()
    )
    if not prereq_mastery:
        prereq_mastery = ConceptMastery(
            learner_id="learner_gate_01",
            concept_id="DATA_TYPES_MEM_REP",
            p_mastery=0.20,
            p_transit=0.15,
            p_guess=0.20,
            p_slip=0.10,
        )
        seeded_db.add(prereq_mastery)
    else:
        prereq_mastery.p_mastery = 0.20
    seeded_db.commit()

    selector = QuestionSelector(seeded_db)
    rec = selector.select_next_question("learner_gate_01", session_attempted_qids=["Q_DECAY_01"])

    assert rec is not None
    assert rec.rationale.selection_reason == "PREREQUISITE_REMEDIATION"
    assert "Remediation triggered" in rec.rationale.prerequisite_status


def test_question_selector_difficulty_escalation(seeded_db):
    """When a concept has high mastery (> 0.70) and is not due for spaced repetition, selector escalates difficulty."""
    from datetime import datetime, timedelta, timezone
    future = datetime.now(timezone.utc) + timedelta(days=7)

    # Set all concepts' next_review_due into future so spaced repetition doesn't intercept
    for m in seeded_db.query(ConceptMastery).filter(ConceptMastery.learner_id == "learner_gate_01").all():
        m.next_review_due = future
    
    root_mastery = (
        seeded_db.query(ConceptMastery)
        .filter(
            ConceptMastery.learner_id == "learner_gate_01",
            ConceptMastery.concept_id == "DATA_TYPES_MEM_REP",
        )
        .first()
    )
    if not root_mastery:
        root_mastery = ConceptMastery(
            learner_id="learner_gate_01",
            concept_id="DATA_TYPES_MEM_REP",
            p_mastery=0.80,
            p_transit=0.15,
            p_guess=0.20,
            p_slip=0.10,
            next_review_due=future,
        )
        seeded_db.add(root_mastery)
    else:
        root_mastery.p_mastery = 0.80
        root_mastery.next_review_due = future
    seeded_db.commit()

    selector = QuestionSelector(seeded_db)
    rec = selector.select_next_question("learner_gate_01", session_attempted_qids=[])

    assert rec is not None
    assert rec.rationale.selection_reason in ["DIFFICULTY_ESCALATION_HARD", "CONCEPT_PROGRESSION_MEDIUM"]
    assert rec.rationale.recommended_difficulty >= 0.50


def test_question_selector_duplicate_avoidance(seeded_db):
    """Already attempted questions must not be repeated in the same session."""
    selector = QuestionSelector(seeded_db)
    
    first_rec = selector.select_next_question("learner_gate_01", session_attempted_qids=[])
    assert first_rec is not None

    second_rec = selector.select_next_question(
        "learner_gate_01", session_attempted_qids=[first_rec.question_id]
    )
    assert second_rec is not None
    assert second_rec.question_id != first_rec.question_id
