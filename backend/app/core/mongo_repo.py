"""
MongoDB Database Adapter for ConceptIQ.
Provides an object-mapped or dictionary-compatible access layer
so services and endpoints can interact with MongoDB cleanly with minimal diff.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pymongo.database import Database
from backend.app.core.mongo import db as mongo_default_db


class MongoEntity:
    """Lightweight wrapper so doc['field'] can also be accessed via doc.field."""
    def __init__(self, data: Dict[str, Any]):
        self.__dict__["_data"] = data or {}

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                return MongoEntity(val)
            return val
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def to_dict(self) -> Dict[str, Any]:
        return self._data


class MongoRepository:
    """
    Unified MongoDB Repository providing clean query and persistence helpers
    for Subjects, Topics, Concepts, Questions, Misconceptions, Learners,
    ConceptMastery, Sessions, and QuestionAttempts.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db: Database = db if db is not None else mongo_default_db

    # ------------------ Subjects & Topics ------------------
    def get_subjects(self) -> List[MongoEntity]:
        docs = list(self.db.subjects.find({}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def get_topics(self, subject_id: Optional[str] = None) -> List[MongoEntity]:
        query = {"subject_id": subject_id} if subject_id else {}
        docs = list(self.db.topics.find(query, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    # ------------------ Concepts ------------------
    def get_all_concepts(self, topic_id: Optional[str] = None) -> List[MongoEntity]:
        query = {"topic_id": topic_id} if topic_id else {}
        docs = list(self.db.concepts.find(query, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def get_concept(self, concept_id: str) -> Optional[MongoEntity]:
        doc = self.db.concepts.find_one({"id": concept_id}, {"_id": 0})
        return MongoEntity(doc) if doc else None

    def get_all_prerequisites(self) -> List[tuple]:
        docs = list(self.db.concept_prerequisites.find({}, {"_id": 0}))
        return [(d["concept_id"], d["prerequisite_id"]) for d in docs]

    # ------------------ Misconceptions ------------------
    def get_misconception(self, misc_id: str) -> Optional[MongoEntity]:
        doc = self.db.misconceptions.find_one({"id": misc_id}, {"_id": 0})
        return MongoEntity(doc) if doc else None

    def get_misconceptions_by_ids(self, ids: List[str]) -> List[MongoEntity]:
        if not ids:
            return []
        docs = list(self.db.misconceptions.find({"id": {"$in": ids}}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def get_all_misconceptions(self) -> List[MongoEntity]:
        docs = list(self.db.misconceptions.find({}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def save_misconception(self, data: Dict[str, Any]) -> MongoEntity:
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        self.db.misconceptions.update_one({"id": data["id"]}, {"$set": data}, upsert=True)
        return MongoEntity(data)

    # ------------------ Questions ------------------
    def get_question(self, question_id: str) -> Optional[MongoEntity]:
        doc = self.db.questions.find_one({"id": question_id}, {"_id": 0})
        return MongoEntity(doc) if doc else None

    def get_questions_by_concept(self, concept_id: str) -> List[MongoEntity]:
        docs = list(self.db.questions.find({"concept_id": concept_id}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def get_all_questions(self, concept_id: Optional[str] = None) -> List[MongoEntity]:
        query = {"concept_id": concept_id} if concept_id else {}
        docs = list(self.db.questions.find(query, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    # ------------------ Learners ------------------
    def get_learner(self, learner_id: str) -> Optional[MongoEntity]:
        doc = self.db.learners.find_one({"id": learner_id}, {"_id": 0})
        return MongoEntity(doc) if doc else None

    def get_all_learners(self) -> List[MongoEntity]:
        docs = list(self.db.learners.find({}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    # ------------------ Concept Mastery (Lazy Initialized) ------------------
    def get_mastery(self, learner_id: str, concept_id: str) -> Optional[MongoEntity]:
        doc = self.db.concept_mastery.find_one(
            {"learner_id": learner_id, "concept_id": concept_id}, {"_id": 0}
        )
        return MongoEntity(doc) if doc else None

    def get_learner_masteries(self, learner_id: str) -> List[MongoEntity]:
        docs = list(self.db.concept_mastery.find({"learner_id": learner_id}, {"_id": 0}))
        return [MongoEntity(d) for d in docs]

    def save_mastery(self, mastery_data: Dict[str, Any]) -> MongoEntity:
        self.db.concept_mastery.update_one(
            {"learner_id": mastery_data["learner_id"], "concept_id": mastery_data["concept_id"]},
            {"$set": mastery_data},
            upsert=True,
        )
        return MongoEntity(mastery_data)

    # ------------------ Assessment Sessions ------------------
    def get_session(self, session_id: str) -> Optional[MongoEntity]:
        doc = self.db.assessment_sessions.find_one({"id": session_id}, {"_id": 0})
        return MongoEntity(doc) if doc else None

    def get_active_session(self, learner_id: str) -> Optional[MongoEntity]:
        doc = self.db.assessment_sessions.find_one(
            {"learner_id": learner_id, "status": "ACTIVE"}, {"_id": 0}
        )
        return MongoEntity(doc) if doc else None

    def save_session(self, session_data: Dict[str, Any]) -> MongoEntity:
        if "id" not in session_data:
            session_data["id"] = str(uuid.uuid4())
        self.db.assessment_sessions.update_one(
            {"id": session_data["id"]},
            {"$set": session_data},
            upsert=True,
        )
        return MongoEntity(session_data)

    # ------------------ Question Attempts ------------------
    def get_attempt_by_session_and_question(self, session_id: str, question_id: str) -> Optional[MongoEntity]:
        doc = self.db.question_attempts.find_one(
            {"session_id": session_id, "question_id": question_id}, {"_id": 0}
        )
        return MongoEntity(doc) if doc else None

    def get_session_attempted_qids(self, session_id: str) -> List[str]:
        cursor = self.db.question_attempts.find({"session_id": session_id}, {"question_id": 1, "_id": 0})
        return [doc["question_id"] for doc in cursor]

    def has_attempted_concept(self, learner_id: str, concept_id: str) -> bool:
        return self.db.question_attempts.find_one(
            {"learner_id": learner_id, "concept_id": concept_id}, {"_id": 1}
        ) is not None

    def save_attempt(self, attempt_data: Dict[str, Any]) -> MongoEntity:
        if "id" not in attempt_data:
            attempt_data["id"] = str(uuid.uuid4())
        self.db.question_attempts.update_one(
            {"id": attempt_data["id"]},
            {"$set": attempt_data},
            upsert=True,
        )
        return MongoEntity(attempt_data)

    def get_attempts_for_learner(self, learner_id: str) -> List[MongoEntity]:
        docs = list(self.db.question_attempts.find({"learner_id": learner_id}, {"_id": 0}).sort("created_at", 1))
        return [MongoEntity(d) for d in docs]

