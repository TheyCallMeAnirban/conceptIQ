import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.core.migration import run_schema_upgrade
from backend.app.models import (
    Subject,
    Topic,
    Concept,
    ConceptPrerequisite,
    Misconception,
    Question,
    Learner,
    ConceptMastery,
)
from backend.app.domain.dag import ConceptDAGValidator, DAGValidationError
from backend.app.seed.seed_db import seed_database


@pytest.fixture
def clean_db():
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    run_schema_upgrade(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    seed_database(db=session)
    try:
        yield session
    finally:
        session.close()


def test_subject_and_topic_creation(clean_db):
    """Verify Subject and Topic creation with explicit ownership."""
    bio = Subject(id="BIO", name="Biology", description="Study of life")
    clean_db.add(bio)
    clean_db.commit()

    genetics = Topic(id="GENETICS", subject_id="BIO", name="Genetics & Heredity")
    clean_db.add(genetics)
    clean_db.commit()

    retrieved = clean_db.query(Topic).filter(Topic.id == "GENETICS").first()
    assert retrieved is not None
    assert retrieved.subject.name == "Biology"
    assert retrieved.subject_id == "BIO"


def test_concept_ownership_hierarchy(clean_db):
    """Verify Concept belongs to exactly one Topic, and Topic belongs to one Subject."""
    dna_concept = Concept(
        id="DNA_REPLICATION",
        topic_id="GENETICS",
        name="DNA Replication Mechanics",
        default_p_init=0.20,
    )
    # First ensure GENETICS topic exists
    bio = Subject(id="BIO_2", name="Biology 2")
    clean_db.add(bio)
    clean_db.commit()

    gen = Topic(id="GENETICS", subject_id="BIO_2", name="Genetics")
    clean_db.add(gen)
    clean_db.add(dna_concept)
    clean_db.commit()

    c = clean_db.query(Concept).filter(Concept.id == "DNA_REPLICATION").first()
    assert c.topic.name == "Genetics"
    assert c.topic.subject.name == "Biology 2"


def test_multi_subject_curriculum_coexistence(clean_db):
    """Verify CS, Mathematics, and Physics concepts coexist cleanly."""
    cs_concept = clean_db.query(Concept).filter(Concept.id == "POINTER_ARITHMETIC").first()
    math_concept = clean_db.query(Concept).filter(Concept.id == "INTEGRATION_BY_PARTS").first()
    phys_concept = clean_db.query(Concept).filter(Concept.id == "NEWTON_FIRST_LAW").first()

    assert cs_concept is not None
    assert cs_concept.topic.subject_id == "CS"

    assert math_concept is not None
    assert math_concept.topic.subject_id == "MATH"

    assert phys_concept is not None
    assert phys_concept.topic.subject_id == "PHYSICS"


def test_lazy_mastery_initialization(clean_db):
    """
    Learner should NOT have mastery records globally created for every concept.
    Mastery records are created on-demand.
    """
    new_learner = Learner(id="L_LAZY_01", name="Arjun")
    clean_db.add(new_learner)
    clean_db.commit()

    # Pre-condition: Arjun has 0 mastery rows
    mastery_count = clean_db.query(ConceptMastery).filter(ConceptMastery.learner_id == "L_LAZY_01").count()
    assert mastery_count == 0

    # Arjun studies Calculus
    calc_mastery = ConceptMastery(
        learner_id="L_LAZY_01",
        concept_id="INTEGRATION_BY_PARTS",
        p_mastery=0.15,
        p_transit=0.12,
        p_guess=0.20,
        p_slip=0.12,
        assessment_state="UNASSESSED",
    )
    clean_db.add(calc_mastery)
    clean_db.commit()

    # Arjun has exactly 1 mastery row, not flooded with CS or Physics
    assert clean_db.query(ConceptMastery).filter(ConceptMastery.learner_id == "L_LAZY_01").count() == 1


def test_unassessed_vs_assessed_mastery_state(clean_db):
    """
    Distinguish between UNASSESSED (no formal evidence),
    IN_PROGRESS, and ASSESSED. Unassessed must not be treated as zero knowledge.
    """
    learner = Learner(id="L_STATES_01", name="Meera")
    clean_db.add(learner)
    clean_db.commit()

    # 1. Unassessed concept (e.g. initial prior exists in BKT, but assessment_state is UNASSESSED)
    m1 = ConceptMastery(
        learner_id="L_STATES_01",
        concept_id="NEWTON_FIRST_LAW",
        p_mastery=0.30,  # Prior P(L_0), NOT measured 0.0 or verified 0.30
        p_transit=0.15,
        p_guess=0.20,
        p_slip=0.10,
        assessment_state="UNASSESSED",
        formal_attempt_count=0,
    )
    clean_db.add(m1)
    clean_db.commit()

    assert m1.assessment_state == "UNASSESSED"
    assert m1.formal_attempt_count == 0

    # 2. Transition to IN_PROGRESS on first assessment
    m1.assessment_state = "IN_PROGRESS"
    m1.formal_attempt_count = 1
    clean_db.commit()

    # 3. Transition to ASSESSED after multiple calibrated assessments
    m1.assessment_state = "ASSESSED"
    m1.formal_attempt_count = 3
    clean_db.commit()

    refreshed = clean_db.query(ConceptMastery).filter(ConceptMastery.id == m1.id).first()
    assert refreshed.assessment_state == "ASSESSED"
    assert refreshed.formal_attempt_count == 3


def test_independent_learner_mastery_across_subjects(clean_db):
    """
    A single learner profile must support high mastery in Calculus,
    weak mastery in C, and unassessed status in Physics.
    """
    learner_id = "L_MULTI_SUBJ"
    learner = Learner(id=learner_id, name="Vikram")
    clean_db.add(learner)

    # High Calculus mastery
    m_calc = ConceptMastery(
        learner_id=learner_id,
        concept_id="INTEGRATION_BY_PARTS",
        p_mastery=0.88,
        p_transit=0.12,
        p_guess=0.20,
        p_slip=0.12,
        assessment_state="ASSESSED",
        formal_attempt_count=4,
    )
    # Weak C mastery
    m_c = ConceptMastery(
        learner_id=learner_id,
        concept_id="POINTER_ARITHMETIC",
        p_mastery=0.22,
        p_transit=0.12,
        p_guess=0.20,
        p_slip=0.12,
        assessment_state="IN_PROGRESS",
        formal_attempt_count=1,
    )
    # Unassessed Physics
    m_phys = ConceptMastery(
        learner_id=learner_id,
        concept_id="NEWTON_FIRST_LAW",
        p_mastery=0.30,
        p_transit=0.15,
        p_guess=0.20,
        p_slip=0.10,
        assessment_state="UNASSESSED",
        formal_attempt_count=0,
    )
    clean_db.add_all([m_calc, m_c, m_phys])
    clean_db.commit()

    masteries = {m.concept_id: m for m in clean_db.query(ConceptMastery).filter(ConceptMastery.learner_id == learner_id).all()}
    assert masteries["INTEGRATION_BY_PARTS"].p_mastery == 0.88
    assert masteries["INTEGRATION_BY_PARTS"].assessment_state == "ASSESSED"

    assert masteries["POINTER_ARITHMETIC"].p_mastery == 0.22
    assert masteries["POINTER_ARITHMETIC"].assessment_state == "IN_PROGRESS"

    assert masteries["NEWTON_FIRST_LAW"].assessment_state == "UNASSESSED"


def test_dag_rejects_illegal_cross_subject_prerequisite():
    """
    Ensure concepts from unrelated subjects cannot accidentally become
    prerequisites without explicit authorization.
    """
    concepts = ["POINTER_ARITHMETIC", "NEWTON_FIRST_LAW"]
    concept_to_subject = {
        "POINTER_ARITHMETIC": "CS",
        "NEWTON_FIRST_LAW": "PHYSICS",
    }
    # Illegal edge: Physics depending on C Pointer Arithmetic
    illegal_edges = [("NEWTON_FIRST_LAW", "POINTER_ARITHMETIC")]

    with pytest.raises(DAGValidationError, match="Illegal cross-subject prerequisite"):
        ConceptDAGValidator.validate_and_sort(
            concepts, illegal_edges, concept_subject_map=concept_to_subject
        )


def test_dynamic_misconception_candidate_registration(clean_db):
    """
    Verify dynamic misconceptions can be registered with CANDIDATE status,
    confidence score, and source='LLM_DISCOVERED'.
    """
    candidate_misc = Misconception(
        id="DYNAMIC_LIMIT_SQUEEZE_CONFUSION",
        concept_id="CALCULUS_LIMITS",
        name="Assuming squeeze theorem applies without bounding inequalities",
        description="Student assumed limit is 0 without establishing upper and lower bounds.",
        remediation_hint="Verify that g(x) <= f(x) <= h(x) before applying the squeeze theorem.",
        source="LLM_DISCOVERED",
        confidence=0.82,
        validation_status="CANDIDATE",
        evidence_count=1,
    )
    clean_db.add(candidate_misc)
    clean_db.commit()

    saved = clean_db.query(Misconception).filter(Misconception.id == "DYNAMIC_LIMIT_SQUEEZE_CONFUSION").first()
    assert saved is not None
    assert saved.source == "LLM_DISCOVERED"
    assert saved.validation_status == "CANDIDATE"
    assert saved.confidence == 0.82
    assert saved.concept_id == "CALCULUS_LIMITS"


def test_existing_c_curriculum_preservation(clean_db):
    """Ensure all 9 original C concepts and 22 questions remain intact."""
    c_concepts = clean_db.query(Concept).filter(Concept.topic_id == "C_PROGRAMMING").all()
    assert len(c_concepts) == 9

    c_questions = [
        q for q in clean_db.query(Question).all()
        if q.concept_id in [c.id for c in c_concepts]
    ]
    assert len(c_questions) == 22
