from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.domain.schemas.diagnosis import DiagnosticOutput
from backend.app.domain.schemas.selection import QuestionRecommendation


class AttemptSubmission(BaseModel):
    learner_id: str
    session_id: str
    question_id: str
    student_answer: str
    reasoning_transcript: str

    model_config = ConfigDict(extra="forbid")


class AttemptResult(BaseModel):
    session_id: str
    attempt_id: str
    sequence_number: int
    is_correct: bool
    diagnosis: DiagnosticOutput
    bkt_update: dict  # { prior, posterior, delta, p_transit, p_guess, p_slip }
    leitner_update: dict  # { previous_box, new_box, next_review_due }
    next_question: Optional[QuestionRecommendation] = None
    session_status: str

    model_config = ConfigDict(extra="forbid")

