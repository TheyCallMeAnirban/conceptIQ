from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.app.core.database import SessionLocal, engine, Base
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
from backend.app.domain.dag import ConceptDAGValidator
from backend.app.seed.c_curriculum_data import (
    SUBJECTS,
    TOPICS,
    CONCEPTS,
    PREREQUISITES,
    MISCONCEPTIONS,
    QUESTIONS,
)


def seed_database(db: Session = None) -> None:
    """
    Idempotent seeding function for the Universal Academic Curriculum.
    Applies explicit SQLite schema upgrades first, validates multi-subject DAG integrity,
    and upserts subjects, topics, concepts, prerequisites, misconceptions, questions,
    and demo learners without eager mastery flooding.
    """
    close_at_end = False
    if db is None:
        # Run explicit schema upgrade on engine
        run_schema_upgrade(engine)
        db = SessionLocal()
        close_at_end = True

    try:
        # 1. Validate DAG before writing anything
        concept_ids = [c["id"] for c in CONCEPTS]
        edges = [(p[0], p[1]) for p in PREREQUISITES]
        
        # Build concept -> subject mapping for cross-subject boundary validation
        topic_to_subject = {t["id"]: t["subject_id"] for t in TOPICS}
        concept_to_subject = {c["id"]: topic_to_subject.get(c.get("topic_id")) for c in CONCEPTS}
        
        topological_order = ConceptDAGValidator.validate_and_sort(
            concept_ids, edges, concept_subject_map=concept_to_subject
        )
        print(f"[Seed] Universal Curriculum DAG validated successfully. Topological order: {len(topological_order)} concepts.")

        # 2. Seed Subjects
        for s_data in SUBJECTS:
            existing_s = db.query(Subject).filter(Subject.id == s_data["id"]).first()
            if not existing_s:
                subj = Subject(
                    id=s_data["id"],
                    name=s_data["name"],
                    description=s_data["description"],
                )
                db.add(subj)
            else:
                existing_s.name = s_data["name"]
                existing_s.description = s_data["description"]
        db.commit()

        # 3. Seed Topics
        for t_data in TOPICS:
            existing_t = db.query(Topic).filter(Topic.id == t_data["id"]).first()
            if not existing_t:
                topic = Topic(
                    id=t_data["id"],
                    subject_id=t_data["subject_id"],
                    name=t_data["name"],
                    description=t_data["description"],
                )
                db.add(topic)
            else:
                existing_t.subject_id = t_data["subject_id"]
                existing_t.name = t_data["name"]
                existing_t.description = t_data["description"]
        db.commit()

        # 4. Seed Concepts
        for c_data in CONCEPTS:
            existing_c = db.query(Concept).filter(Concept.id == c_data["id"]).first()
            if not existing_c:
                concept = Concept(
                    id=c_data["id"],
                    topic_id=c_data.get("topic_id"),
                    name=c_data["name"],
                    description=c_data["description"],
                    default_p_init=c_data["default_p_init"],
                    default_p_transit=c_data["default_p_transit"],
                    default_p_guess=c_data["default_p_guess"],
                    default_p_slip=c_data["default_p_slip"],
                )
                db.add(concept)
            else:
                existing_c.topic_id = c_data.get("topic_id")
                existing_c.name = c_data["name"]
                existing_c.description = c_data["description"]
                existing_c.default_p_init = c_data["default_p_init"]
                existing_c.default_p_transit = c_data["default_p_transit"]
                existing_c.default_p_guess = c_data["default_p_guess"]
                existing_c.default_p_slip = c_data["default_p_slip"]
        db.commit()

        # 5. Seed Prerequisites (Idempotent)
        for concept_id, prereq_id in PREREQUISITES:
            existing_p = (
                db.query(ConceptPrerequisite)
                .filter(
                    ConceptPrerequisite.concept_id == concept_id,
                    ConceptPrerequisite.prerequisite_id == prereq_id,
                )
                .first()
            )
            if not existing_p:
                edge = ConceptPrerequisite(
                    concept_id=concept_id,
                    prerequisite_id=prereq_id,
                )
                db.add(edge)
        db.commit()

        # 6. Seed Misconceptions
        for m_data in MISCONCEPTIONS:
            existing_m = db.query(Misconception).filter(Misconception.id == m_data["id"]).first()
            if not existing_m:
                misc = Misconception(
                    id=m_data["id"],
                    concept_id=m_data["concept_id"],
                    name=m_data["name"],
                    description=m_data["description"],
                    remediation_hint=m_data["remediation_hint"],
                    source=m_data.get("source", "CURATED"),
                    validation_status=m_data.get("validation_status", "CONFIRMED"),
                    confidence=m_data.get("confidence", 1.0),
                    evidence_count=1,
                )
                db.add(misc)
            else:
                existing_m.name = m_data["name"]
                existing_m.description = m_data["description"]
                existing_m.remediation_hint = m_data["remediation_hint"]
                existing_m.source = m_data.get("source", "CURATED")
                existing_m.validation_status = m_data.get("validation_status", "CONFIRMED")
                existing_m.confidence = m_data.get("confidence", 1.0)
        db.commit()

        # 7. Seed Questions
        for q_data in QUESTIONS:
            existing_q = db.query(Question).filter(Question.id == q_data["id"]).first()
            if not existing_q:
                q = Question(
                    id=q_data["id"],
                    concept_id=q_data["concept_id"],
                    title=q_data["title"],
                    problem_text=q_data["problem_text"],
                    code_snippet=q_data.get("code_snippet"),
                    question_type=q_data.get("question_type", "MCQ"),
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    canonical_explanation=q_data["canonical_explanation"],
                    difficulty=q_data["difficulty"],
                    secondary_concept_ids=q_data.get("secondary_concept_ids", []),
                    known_misconceptions=q_data.get("known_misconceptions", []),
                )
                db.add(q)
            else:
                existing_q.title = q_data["title"]
                existing_q.problem_text = q_data["problem_text"]
                existing_q.code_snippet = q_data.get("code_snippet")
                existing_q.options = q_data.get("options")
                existing_q.correct_answer = q_data["correct_answer"]
                existing_q.canonical_explanation = q_data["canonical_explanation"]
                existing_q.difficulty = q_data["difficulty"]
                existing_q.secondary_concept_ids = q_data.get("secondary_concept_ids", [])
                existing_q.known_misconceptions = q_data.get("known_misconceptions", [])
        db.commit()

        # 8. Seed Demo Learners (WITHOUT globally initializing mastery for all concepts)
        demo_learners = [
            {"id": "learner_gate_01", "name": "Rahul Sharma"},
            {"id": "learner_gate_02", "name": "Priya Verma"},
        ]
        for l_data in demo_learners:
            learner = db.query(Learner).filter(Learner.id == l_data["id"]).first()
            if not learner:
                learner = Learner(id=l_data["id"], name=l_data["name"])
                db.add(learner)
        db.commit()

        print(
            f"[Seed] Seeding complete: {len(SUBJECTS)} subjects, {len(TOPICS)} topics, "
            f"{len(CONCEPTS)} concepts, {len(QUESTIONS)} questions."
        )

    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    seed_database()
