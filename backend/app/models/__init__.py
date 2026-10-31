import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime, Enum, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String(64), primary_key=True)  # e.g., 'POINTER_ARITHMETIC'
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), default="C_POINTERS_ARRAYS")
    
    # Default BKT parameters for this concept
    default_p_init = Column(Float, default=0.20)      # P(L_0)
    default_p_transit = Column(Float, default=0.15)   # P(T)
    default_p_guess = Column(Float, default=0.20)     # P(G)
    default_p_slip = Column(Float, default=0.10)      # P(S)

    # Relationships
    prerequisites = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    dependents = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.prerequisite_id",
        back_populates="prerequisite",
        cascade="all, delete-orphan"
    )
    questions = relationship("Question", back_populates="concept")
    masteries = relationship("ConceptMastery", back_populates="concept")


class ConceptPrerequisite(Base):
    __tablename__ = "concept_prerequisites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    prerequisite_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)

    concept = relationship("Concept", foreign_keys=[concept_id], back_populates="prerequisites")
    prerequisite = relationship("Concept", foreign_keys=[prerequisite_id], back_populates="dependents")


class Misconception(Base):
    __tablename__ = "misconceptions"

    id = Column(String(64), primary_key=True)  # e.g., 'CONFUSING_ARRAY_NAME_WITH_POINTER_VARIABLE'
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    remediation_hint = Column(Text, nullable=False)


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(64), primary_key=True)  # e.g., 'Q_PTR_ARITH_01'
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    problem_text = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    question_type = Column(String(32), default="MCQ")  # MCQ, NAT, MSQ
    options = Column(JSON, nullable=True)              # list of { "id": "A", "text": "..." }
    correct_answer = Column(String(128), nullable=False)
    canonical_explanation = Column(Text, nullable=False)
    difficulty = Column(Float, nullable=False, default=0.5)  # 0.1 (easy) to 1.0 (hard)
    secondary_concept_ids = Column(JSON, default=list)       # list of secondary concept IDs
    known_misconceptions = Column(JSON, default=list)        # list of Misconception IDs

    concept = relationship("Concept", back_populates="questions")


class Learner(Base):
    __tablename__ = "learners"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    masteries = relationship("ConceptMastery", back_populates="learner", cascade="all, delete-orphan")
    sessions = relationship("AssessmentSession", back_populates="learner", cascade="all, delete-orphan")


class ConceptMastery(Base):
    __tablename__ = "concept_masteries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    learner_id = Column(String(64), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)

    # Standard BKT state
    p_mastery = Column(Float, nullable=False)  # Current P(L_t)
    p_transit = Column(Float, nullable=False)  # Configured P(T)
    p_guess = Column(Float, nullable=False)    # Configured P(G)
    p_slip = Column(Float, nullable=False)     # Configured P(S)

    # Spaced Repetition (Simple Leitner Box 1..5)
    leitner_box = Column(Integer, default=1)
    consecutive_correct = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_due = Column(DateTime, nullable=True)

    learner = relationship("Learner", back_populates="masteries")
    concept = relationship("Concept", back_populates="masteries")


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    learner_id = Column(String(64), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    current_question_id = Column(String(64), ForeignKey("questions.id"), nullable=True)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, COMPLETED, ABANDONED
    attempt_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    learner = relationship("Learner", back_populates="sessions")
    current_question = relationship("Question")
    attempts = relationship("QuestionAttempt", back_populates="session", cascade="all, delete-orphan", order_by="QuestionAttempt.sequence_number")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    learner_id = Column(String(64), ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(64), ForeignKey("questions.id"), nullable=False)
    concept_id = Column(String(64), ForeignKey("concepts.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)

    # Student submission
    student_answer = Column(String(255), nullable=False)
    reasoning_transcript = Column(Text, nullable=False)  # Wispr Flow text

    # Evaluation
    is_correct = Column(Boolean, nullable=False)

    # Diagnostic Signal (LLM evaluation, strictly separated from BKT)
    reasoning_quality = Column(String(32), nullable=True)      # e.g., SOUND, PARTIALLY_CORRECT, FLAWED, GUESS
    detected_misconceptions = Column(JSON, default=list)       # list of misconception IDs
    evidence = Column(Text, nullable=True)
    recommended_intervention = Column(Text, nullable=True)
    diagnosis_provider = Column(String(32), default="deterministic_fallback") # 'llm' or 'deterministic_fallback'

    # Deterministic BKT Audit Record (Strict adherence to requirement C)
    p_mastery_prior = Column(Float, nullable=False)
    p_mastery_posterior = Column(Float, nullable=False)
    p_transit_used = Column(Float, nullable=False)
    p_guess_used = Column(Float, nullable=False)
    p_slip_used = Column(Float, nullable=False)

    created_at = Column(DateTime, default=utc_now)

    session = relationship("AssessmentSession", back_populates="attempts")
    question = relationship("Question")
    concept = relationship("Concept")

