import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import Concept, ConceptPrerequisite, Question, Misconception, Learner, ConceptMastery
from backend.app.seed.seed_db import seed_database


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_seed_database_idempotency(in_memory_db):
    """Running seed multiple times should not create duplicate entries or crash."""
    # First seed run
    seed_database(db=in_memory_db)
    
    concept_count_1 = in_memory_db.query(Concept).count()
    prereq_count_1 = in_memory_db.query(ConceptPrerequisite).count()
    q_count_1 = in_memory_db.query(Question).count()
    misc_count_1 = in_memory_db.query(Misconception).count()
    learner_count_1 = in_memory_db.query(Learner).count()
    mastery_count_1 = in_memory_db.query(ConceptMastery).count()

    assert concept_count_1 == 9
    assert prereq_count_1 == 12
    assert q_count_1 == 22
    assert misc_count_1 == 8
    assert learner_count_1 == 2
    assert mastery_count_1 == 18  # 2 learners * 9 concepts

    # Second seed run (must be completely idempotent)
    seed_database(db=in_memory_db)

    assert in_memory_db.query(Concept).count() == concept_count_1
    assert in_memory_db.query(ConceptPrerequisite).count() == prereq_count_1
    assert in_memory_db.query(Question).count() == q_count_1
    assert in_memory_db.query(Misconception).count() == misc_count_1
    assert in_memory_db.query(Learner).count() == learner_count_1
    assert in_memory_db.query(ConceptMastery).count() == mastery_count_1

