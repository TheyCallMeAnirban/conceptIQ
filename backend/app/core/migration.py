import logging
from sqlalchemy import Engine
from backend.app.core.database import Base

logger = logging.getLogger(__name__)


def run_schema_upgrade(engine: Engine) -> None:
    """
    Explicit, idempotent SQLite schema migration.
    Inspects existing tables and adds missing columns safely,
    preserving all existing records and relationships.
    """
    # 1. Create any missing new tables (subjects, topics, etc.)
    Base.metadata.create_all(bind=engine)

    # 2. Check and migrate altered tables
    with engine.begin() as conn:
        cursor = conn.connection.cursor()

        # Helper to get existing column names for a table
        def get_columns(table_name: str) -> list[str]:
            cursor.execute(f"PRAGMA table_info({table_name});")
            return [row[1] for row in cursor.fetchall()]

        # A. Migrate 'concepts' table
        concept_cols = get_columns("concepts")
        if concept_cols:
            if "topic_id" not in concept_cols:
                cursor.execute("ALTER TABLE concepts ADD COLUMN topic_id VARCHAR(64) REFERENCES topics(id);")
                logger.info("[Migration] Added column 'topic_id' to 'concepts'.")

        # B. Migrate 'misconceptions' table
        misc_cols = get_columns("misconceptions")
        if misc_cols:
            if "source" not in misc_cols:
                cursor.execute("ALTER TABLE misconceptions ADD COLUMN source VARCHAR(32) DEFAULT 'CURATED';")
            if "confidence" not in misc_cols:
                cursor.execute("ALTER TABLE misconceptions ADD COLUMN confidence FLOAT DEFAULT 1.0;")
            if "validation_status" not in misc_cols:
                cursor.execute("ALTER TABLE misconceptions ADD COLUMN validation_status VARCHAR(32) DEFAULT 'CONFIRMED';")
            if "evidence_count" not in misc_cols:
                cursor.execute("ALTER TABLE misconceptions ADD COLUMN evidence_count INTEGER DEFAULT 1;")
            if "created_at" not in misc_cols:
                cursor.execute("ALTER TABLE misconceptions ADD COLUMN created_at DATETIME;")
            logger.info("[Migration] Upgraded 'misconceptions' schema with validation status and confidence.")

        # C. Migrate 'concept_masteries' table
        mastery_cols = get_columns("concept_masteries")
        if mastery_cols:
            if "assessment_state" not in mastery_cols:
                cursor.execute("ALTER TABLE concept_masteries ADD COLUMN assessment_state VARCHAR(32) DEFAULT 'UNASSESSED';")
            if "formal_attempt_count" not in mastery_cols:
                cursor.execute("ALTER TABLE concept_masteries ADD COLUMN formal_attempt_count INTEGER DEFAULT 0;")
            if "last_assessed_at" not in mastery_cols:
                cursor.execute("ALTER TABLE concept_masteries ADD COLUMN last_assessed_at DATETIME;")
            logger.info("[Migration] Upgraded 'concept_masteries' schema with lazy assessment state.")

        # D. Migrate 'questions' table (ensure secondary_concept_ids exists)
        q_cols = get_columns("questions")
        if q_cols and "secondary_concept_ids" not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN secondary_concept_ids JSON DEFAULT '[]';")

        cursor.close()

