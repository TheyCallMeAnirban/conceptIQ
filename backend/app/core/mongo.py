from typing import Generator
import pymongo
from pymongo.database import Database
from backend.app.core.config import settings

client = pymongo.MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB_NAME]


def get_mongo_db() -> Generator[Database, None, None]:
    """FastAPI dependency for MongoDB database connection."""
    yield db


def init_indexes():
    """Ensure essential indexes for fast queries and uniqueness constraints."""
    # Subjects
    db.subjects.create_index("id", unique=True)
    # Topics
    db.topics.create_index("id", unique=True)
    db.topics.create_index("subject_id")
    # Concepts
    db.concepts.create_index("id", unique=True)
    db.concepts.create_index("topic_id")
    # Concept Prerequisites
    db.concept_prerequisites.create_index([("concept_id", 1), ("prerequisite_id", 1)], unique=True)
    # Questions
    db.questions.create_index("id", unique=True)
    db.questions.create_index("concept_id")
    # Misconceptions
    db.misconceptions.create_index("id", unique=True)
    db.misconceptions.create_index("concept_id")
    # Learners
    db.learners.create_index("id", unique=True)
    # Concept Mastery: unique learner + concept pair
    db.concept_mastery.create_index([("learner_id", 1), ("concept_id", 1)], unique=True)
    # Sessions
    db.assessment_sessions.create_index("id", unique=True)
    db.assessment_sessions.create_index("learner_id")
    # Attempts
    db.question_attempts.create_index("id", unique=True)
    db.question_attempts.create_index([("session_id", 1), ("question_id", 1)], unique=True)
    db.question_attempts.create_index("learner_id")

