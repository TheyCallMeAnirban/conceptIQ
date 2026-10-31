from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models import (
    Concept,
    ConceptPrerequisite,
    Misconception,
    Question,
    Learner,
    ConceptMastery,
)
from backend.app.domain.dag import ConceptDAGValidator
from backend.app.seed.c_curriculum_data import (
    CONCEPTS,
    PREREQUISITES,
    MISCONCEPTIONS,
    QUESTIONS,
)


def seed_database(db: Session = None) -> None:
    """
    Idempotent seeding function.
    Validates DAG integrity, then upserts concepts, prerequisites,
    misconceptions, questions, and default demo learners.
    """
    close_at_end = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_at_end = True

    # Ensure schema is up to date (lightweight migration for SQLite)
    try:
        with engine.begin() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(questions);")
            columns = [row[1] for row in cursor.fetchall()]
            if columns and "secondary_concept_ids" not in columns:
                cursor.execute("ALTER TABLE questions ADD COLUMN secondary_concept_ids JSON DEFAULT '[]';")
            cursor.close()
    except Exception:
        pass

    try:
        # 1. Validate DAG before writing anything to DB
        concept_ids = [c["id"] for c in CONCEPTS]
        edges = [(p[0], p[1]) for p in PREREQUISITES]
        topological_order = ConceptDAGValidator.validate_and_sort(concept_ids, edges)
        print(f"[Seed] Curriculum DAG validated successfully. Topological order: {len(topological_order)} concepts.")

        # 2. Seed Concepts (Upsert / Ignore existing)
        for c_data in CONCEPTS:
            existing = db.query(Concept).filter(Concept.id == c_data["id"]).first()
            if not existing:
                concept = Concept(
                    id=c_data["id"],
                    name=c_data["name"],
                    description=c_data["description"],
                    default_p_init=c_data["default_p_init"],
                    default_p_transit=c_data["default_p_transit"],
                    default_p_guess=c_data["default_p_guess"],
                    default_p_slip=c_data["default_p_slip"],
                )
                db.add(concept)
            else:
                existing.name = c_data["name"]
                existing.description = c_data["description"]
                existing.default_p_init = c_data["default_p_init"]
                existing.default_p_transit = c_data["default_p_transit"]
                existing.default_p_guess = c_data["default_p_guess"]
                existing.default_p_slip = c_data["default_p_slip"]
        db.commit()

        # 3. Seed Prerequisite Edges (Idempotent)
        for concept_id, prereq_id in PREREQUISITES:
            existing = (
                db.query(ConceptPrerequisite)
                .filter(
                    ConceptPrerequisite.concept_id == concept_id,
                    ConceptPrerequisite.prerequisite_id == prereq_id,
                )
                .first()
            )
            if not existing:
                edge = ConceptPrerequisite(
                    concept_id=concept_id,
                    prerequisite_id=prereq_id,
                )
                db.add(edge)
        db.commit()

        # 4. Seed Misconceptions
        for m_data in MISCONCEPTIONS:
            existing = db.query(Misconception).filter(Misconception.id == m_data["id"]).first()
            if not existing:
                misc = Misconception(
                    id=m_data["id"],
                    concept_id=m_data["concept_id"],
                    name=m_data["name"],
                    description=m_data["description"],
                    remediation_hint=m_data["remediation_hint"],
                )
                db.add(misc)
            else:
                existing.name = m_data["name"]
                existing.description = m_data["description"]
                existing.remediation_hint = m_data["remediation_hint"]
        db.commit()

        # 5. Seed Questions
        for q_data in QUESTIONS:
            existing = db.query(Question).filter(Question.id == q_data["id"]).first()
            if not existing:
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
                existing.title = q_data["title"]
                existing.problem_text = q_data["problem_text"]
                existing.code_snippet = q_data.get("code_snippet")
                existing.options = q_data.get("options")
                existing.correct_answer = q_data["correct_answer"]
                existing.canonical_explanation = q_data["canonical_explanation"]
                existing.difficulty = q_data["difficulty"]
                existing.secondary_concept_ids = q_data.get("secondary_concept_ids", [])
                existing.known_misconceptions = q_data.get("known_misconceptions", [])
        db.commit()

        # 6. Seed Demo Learners & Initial Masteries
        demo_learners = [
            {"id": "learner_gate_01", "name": "Rahul Sharma (GATE Aspirant)"},
            {"id": "learner_gate_02", "name": "Priya Verma (GATE Aspirant)"},
        ]
        for l_data in demo_learners:
            learner = db.query(Learner).filter(Learner.id == l_data["id"]).first()
            if not learner:
                learner = Learner(id=l_data["id"], name=l_data["name"])
                db.add(learner)
                db.flush()

            # Ensure all concepts have an initial ConceptMastery record
            for c_data in CONCEPTS:
                mastery = (
                    db.query(ConceptMastery)
                    .filter(
                        ConceptMastery.learner_id == learner.id,
                        ConceptMastery.concept_id == c_data["id"],
                    )
                    .first()
                )
                if not mastery:
                    mastery = ConceptMastery(
                        learner_id=learner.id,
                        concept_id=c_data["id"],
                        p_mastery=c_data["default_p_init"],
                        p_transit=c_data["default_p_transit"],
                        p_guess=c_data["default_p_guess"],
                        p_slip=c_data["default_p_slip"],
                        leitner_box=1,
                    )
                    db.add(mastery)
        db.commit()
        print(f"[Seed] Seeding complete: {len(CONCEPTS)} concepts, {len(PREREQUISITES)} prerequisites, {len(MISCONCEPTIONS)} misconceptions, {len(QUESTIONS)} questions.")

    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    seed_database()

