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

    assert concept_count_1 == 13      # 9 C + 2 Math + 2 Physics
    assert prereq_count_1 == 14       # 12 C + 1 Math + 1 Physics
    assert q_count_1 == 24            # 22 C + 1 Math + 1 Physics
    assert misc_count_1 == 10         # 8 C + 1 Math + 1 Physics
    assert learner_count_1 == 2
    assert mastery_count_1 == 0       # Lazy initialization: 0 pre-flooded masteries

    # Second seed run (must be completely idempotent)
    seed_database(db=in_memory_db)

    assert in_memory_db.query(Concept).count() == concept_count_1
    assert in_memory_db.query(ConceptPrerequisite).count() == prereq_count_1
    assert in_memory_db.query(Question).count() == q_count_1
    assert in_memory_db.query(Misconception).count() == misc_count_1
    assert in_memory_db.query(Learner).count() == learner_count_1
    assert in_memory_db.query(ConceptMastery).count() == mastery_count_1

