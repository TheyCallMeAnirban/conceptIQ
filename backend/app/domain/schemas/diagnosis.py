from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ReasoningQuality(str, Enum):
    SOUND = "SOUND"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    FLAWED = "FLAWED"
    GUESS = "GUESS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DiagnosticInput(BaseModel):
    question_statement: str
    expected_answer: str
    student_answer: str
    is_correct: bool = Field(description="Deterministic backend evaluation of answer correctness.")
    reasoning_transcript: str
    primary_concept: str
    secondary_concepts: List[str] = Field(default_factory=list)
    known_misconceptions: List[dict] = Field(default_factory=list)  # list of {id, name, description, remediation_hint}

    model_config = ConfigDict(extra="forbid")


class DiagnosticOutput(BaseModel):
    is_correct: bool = Field(description="Whether the student's answer is mathematically and conceptually correct.")
    reasoning_quality: ReasoningQuality = Field(description="Assessed quality of the student's reasoning.")
    detected_misconceptions: List[str] = Field(
        default_factory=list,
        description="IDs of confirmed misconceptions. Must only include known catalog IDs if clear evidence exists, else empty.",
    )
    affected_concepts: List[str] = Field(
        default_factory=list,
        description="Concept IDs directly impacted by the student's error or demonstration.",
    )
    reasoning_evidence: str = Field(
        description="Direct quote or specific synthesis of student statements supporting the diagnosis.",
    )
    explanation: str = Field(
        description="Clear, concise pedagogical explanation of why the reasoning is sound or where it derailed.",
    )
    recommended_intervention: str = Field(
        description="Actionable instruction or remediation hint for the student.",
    )
    suggested_difficulty: float = Field(
        ge=0.1,
        le=1.0,
        description="Suggested difficulty level (0.1 - 1.0) for the next assessment item.",
    )
    diagnosis_provider: str = Field(
        description="The provider that produced this diagnosis: 'gemini', 'openai', or 'deterministic_fallback'.",
    )

    model_config = ConfigDict(extra="forbid")

