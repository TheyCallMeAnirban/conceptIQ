"""
MongoDB Seed Script for ConceptIQ Universal Curriculum.
Populates:
- Subjects (CS, Math, Physics)
- Topics (C_PROGRAMMING, CALCULUS, CLASSICAL_MECHANICS)
- Concepts & DAG Prerequisites
- Misconceptions Catalog
- Diagnostic Questions
- Demonstration Learners (learner_gate_01, learner_gate_02)
- Zero pre-flooded ConceptMastery (Lazy initialization pattern)
"""

import logging
from pymongo.database import Database
from backend.app.core.mongo import db as default_mongo_db, init_indexes
from backend.app.domain.dag import ConceptDAGValidator
from backend.app.seed.c_curriculum_data import (
    SUBJECTS,
    TOPICS,
    CONCEPTS,
    PREREQUISITES,
    MISCONCEPTIONS,
    QUESTIONS,
)

logger = logging.getLogger(__name__)


def seed_mongo(mongo_db: Database = None):
    target_db = mongo_db if mongo_db is not None else default_mongo_db

    # 1. Validate DAG topological order and subject boundaries
    concept_ids = [c["id"] for c in CONCEPTS]
    edges = [(p[0], p[1]) for p in PREREQUISITES]
    topic_to_subject = {t["id"]: t["subject_id"] for t in TOPICS}
    concept_to_subject = {c["id"]: topic_to_subject.get(c.get("topic_id")) for c in CONCEPTS}
    sorted_concept_ids = ConceptDAGValidator.validate_and_sort(
        concept_ids, edges, concept_subject_map=concept_to_subject
    )
    logger.info(f"[Mongo Seed] Universal Curriculum DAG validated. Count: {len(sorted_concept_ids)}")

    # 2. Seed Subjects
    for s in SUBJECTS:
        target_db.subjects.update_one(
            {"id": s["id"]},
            {"$set": {
                "id": s["id"],
                "name": s["name"],
                "description": s["description"],
            }},
            upsert=True,
        )

    # 3. Seed Topics
    for t in TOPICS:
        target_db.topics.update_one(
            {"id": t["id"]},
            {"$set": {
                "id": t["id"],
                "subject_id": t["subject_id"],
                "name": t["name"],
                "description": t["description"],
            }},
            upsert=True,
        )

    # 4. Seed Concepts
    for c in CONCEPTS:
        target_db.concepts.update_one(
            {"id": c["id"]},
            {"$set": {
                "id": c["id"],
                "topic_id": c.get("topic_id", "C_PROGRAMMING"),
                "name": c["name"],
                "description": c["description"],
                "difficulty_base": c.get("difficulty_base", 0.5),
                "depth_level": c.get("depth_level", 1),
                "default_p_init": c["default_p_init"],
                "default_p_transit": c["default_p_transit"],
                "default_p_guess": c["default_p_guess"],
                "default_p_slip": c["default_p_slip"],
            }},
            upsert=True,
        )

    # 5. Seed Prerequisites
    for p in PREREQUISITES:
        target_db.concept_prerequisites.update_one(
            {"concept_id": p[0], "prerequisite_id": p[1]},
            {"$set": {
                "concept_id": p[0],
                "prerequisite_id": p[1],
            }},
            upsert=True,
        )

    # 6. Seed Misconceptions
    for m in MISCONCEPTIONS:
        target_db.misconceptions.update_one(
            {"id": m["id"]},
            {"$set": {
                "id": m["id"],
                "concept_id": m["concept_id"],
                "name": m["name"],
                "description": m["description"],
                "remediation_hint": m["remediation_hint"],
                "source": m.get("source", "CURATED"),
                "validation_status": m.get("validation_status", "CONFIRMED"),
                "confidence": m.get("confidence", 1.0),
                "evidence_count": m.get("evidence_count", 1),
            }},
            upsert=True,
        )

    # 7. Seed Questions
    for q in QUESTIONS:
        target_db.questions.update_one(
            {"id": q["id"]},
            {"$set": {
                "id": q["id"],
                "concept_id": q["concept_id"],
                "title": q["title"],
                "problem_text": q["problem_text"],
                "code_snippet": q.get("code_snippet"),
                "question_type": q.get("question_type", "MCQ"),
                "options": q.get("options"),
                "correct_answer": q["correct_answer"],
                "canonical_explanation": q.get("canonical_explanation", ""),
                "difficulty": q["difficulty"],
                "discrimination": q.get("discrimination", 1.0),
                "secondary_concept_ids": q.get("secondary_concept_ids", []),
                "known_misconceptions": q.get("known_misconceptions", []),
            }},
            upsert=True,
        )

    # 8. Seed Demo Learners
    learners = [
        {"id": "learner_gate_01", "name": "Arjun Sharma", "email": "arjun@conceptiq.internal"},
        {"id": "learner_gate_02", "name": "Priya Nair", "email": "priya@conceptiq.internal"},
    ]
    for l in learners:
        target_db.learners.update_one(
            {"id": l["id"]},
            {"$set": l},
            upsert=True,
        )

    logger.info(
        f"[Mongo Seed] Completed: {len(SUBJECTS)} subjects, {len(TOPICS)} topics, "
        f"{len(CONCEPTS)} concepts, {len(QUESTIONS)} questions."
    )


if __name__ == "__main__":
    init_indexes()
    seed_mongo()
    print("MongoDB successfully seeded.")
