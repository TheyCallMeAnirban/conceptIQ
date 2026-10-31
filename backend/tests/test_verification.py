import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import Base
from backend.app.models import (
    Concept,
    Question,
    Learner,
    ConceptMastery,
    AssessmentSession,
    QuestionAttempt,
)
from backend.app.domain.bkt import BKTEngine, BKTParameters


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_bkt_parameter_validation_direct_args():
    """Verify bounds enforcement on direct arguments to BKTEngine.update."""
    with pytest.raises(ValueError, match="prior must be between"):
        BKTEngine.update(prior=1.5, is_correct=True)

    with pytest.raises(ValueError, match="prior must be between"):
        BKTEngine.update(prior=-0.1, is_correct=True)

    with pytest.raises(ValueError, match="p_transit must be between"):
        BKTEngine.update(prior=0.5, is_correct=True, p_transit=1.2)


def test_bkt_learning_transition_applied_once():
    """
    Verify transition P(T) is applied strictly once.
    P(L)=0.4, S=0.1, G=0.2, T=0.0 (Zero transition case):
      P(L | obs=1) = (0.4 * 0.9) / (0.4 * 0.9 + 0.6 * 0.2) = 0.36 / 0.48 = 0.75
      With T=0.0, posterior must equal 0.75 exactly.
    With T=0.10:
      P(L_t+1) = 0.75 + (1 - 0.75) * 0.10 = 0.75 + 0.025 = 0.7750
    """
    res_no_t = BKTEngine.update(prior=0.4, is_correct=True, p_slip=0.1, p_guess=0.2, p_transit=0.0)
    assert res_no_t.posterior == 0.7500

    res_with_t = BKTEngine.update(prior=0.4, is_correct=True, p_slip=0.1, p_guess=0.2, p_transit=0.10)
    assert res_with_t.posterior == 0.7750


def test_bkt_boundary_stability():
    """Test near-zero and near-one priors remain strictly within [0, 1]."""
    for prior in [0.0, 0.0001, 0.5, 0.9999, 1.0]:
        for obs in [True, False]:
            res = BKTEngine.update(prior=prior, is_correct=obs)
            assert 0.0 <= res.posterior <= 1.0


def test_question_primary_and_secondary_concepts(test_db):
    """Test questions can store and query primary and secondary concepts."""
    c1 = Concept(id="C1", name="Concept 1")
    c2 = Concept(id="C2", name="Concept 2")
    c3 = Concept(id="C3", name="Concept 3")
    test_db.add_all([c1, c2, c3])
    test_db.commit()

    q = Question(
        id="Q1",
        concept_id="C1",
        title="Multi-concept Question",
        problem_text="Test question",
        correct_answer="A",
        canonical_explanation="Explanation",
        difficulty=0.5,
        secondary_concept_ids=["C2", "C3"],
    )
    test_db.add(q)
    test_db.commit()

    retrieved = test_db.query(Question).filter(Question.id == "Q1").first()
    assert retrieved.concept_id == "C1"
    assert retrieved.secondary_concept_ids == ["C2", "C3"]


def test_sqlite_foreign_key_enforcement(test_db):
    """Verify that foreign key violations raise IntegrityError."""
    # Attempt to create an AssessmentSession for non-existent learner
    invalid_session = AssessmentSession(learner_id="NON_EXISTENT_LEARNER")
    test_db.add(invalid_session)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_single_transaction_atomicity_and_rollback(test_db):
    """
    Verify attempt persistence, mastery updates, diagnostic records,
    and session state changes succeed atomically or roll back completely.
    """
    # Setup prerequisite data
    learner = Learner(id="L_ATOMIC", name="Atomic Learner")
    concept = Concept(id="C_ATOMIC", name="Atomic Concept")
    question = Question(
        id="Q_ATOMIC",
        concept_id="C_ATOMIC",
        title="Atomic Q",
        problem_text="Atomic question",
        correct_answer="A",
        canonical_explanation="Explanation",
    )
    mastery = ConceptMastery(
        learner_id="L_ATOMIC",
        concept_id="C_ATOMIC",
        p_mastery=0.20,
        p_transit=0.15,
        p_guess=0.20,
        p_slip=0.10,
    )
    session = AssessmentSession(
        id="S_ATOMIC",
        learner_id="L_ATOMIC",
        current_question_id="Q_ATOMIC",
        status="ACTIVE",
        attempt_count=0,
    )
    test_db.add_all([learner, concept, question, mastery, session])
    test_db.commit()

    # Step 1: Successful atomic transaction (all 4 changes in 1 commit)
    attempt = QuestionAttempt(
        session_id="S_ATOMIC",
        learner_id="L_ATOMIC",
        question_id="Q_ATOMIC",
        concept_id="C_ATOMIC",
        sequence_number=1,
        student_answer="A",
        reasoning_transcript="Because A is correct",
        is_correct=True,
        reasoning_quality="SOUND",
        detected_misconceptions=[],
        p_mastery_prior=0.20,
        p_mastery_posterior=0.45,
        p_transit_used=0.15,
        p_guess_used=0.20,
        p_slip_used=0.10,
    )
    mastery.p_mastery = 0.45
    session.attempt_count = 1
    session.current_question_id = None
    session.status = "COMPLETED"

    test_db.add(attempt)
    test_db.commit()

    # Assert all state changes persisted
    saved_attempt = test_db.query(QuestionAttempt).filter(QuestionAttempt.session_id == "S_ATOMIC").first()
    assert saved_attempt is not None
    assert saved_attempt.p_mastery_posterior == 0.45
    assert test_db.query(ConceptMastery).filter(ConceptMastery.learner_id == "L_ATOMIC").first().p_mastery == 0.45
    assert test_db.query(AssessmentSession).filter(AssessmentSession.id == "S_ATOMIC").first().status == "COMPLETED"

    # Step 2: Rollback verification on failure
    # Simulate a second transaction that mutates session and mastery, then fails on an invalid attempt
    mastery.p_mastery = 0.99
    session.status = "ACTIVE"
    corrupt_attempt = QuestionAttempt(
        session_id="INVALID_SESSION_FK",  # Foreign key violation
        learner_id="L_ATOMIC",
        question_id="Q_ATOMIC",
        concept_id="C_ATOMIC",
        sequence_number=2,
        student_answer="B",
        reasoning_transcript="Corrupt",
        is_correct=False,
        p_mastery_prior=0.45,
        p_mastery_posterior=0.20,
        p_transit_used=0.15,
        p_guess_used=0.20,
        p_slip_used=0.10,
    )
    test_db.add(corrupt_attempt)
    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()

    # Verify state after rollback remains pristine
    refreshed_mastery = test_db.query(ConceptMastery).filter(ConceptMastery.learner_id == "L_ATOMIC").first()
    refreshed_session = test_db.query(AssessmentSession).filter(AssessmentSession.id == "S_ATOMIC").first()
    assert refreshed_mastery.p_mastery == 0.45  # NOT 0.99
    assert refreshed_session.status == "COMPLETED"  # NOT ACTIVE

