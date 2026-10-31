from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SelectionRationale(BaseModel):
    question_id: str
    target_concept_id: str
    target_concept_name: str
    current_mastery: float
    prerequisite_status: str
    selection_reason: str
    recommended_difficulty: float
    rationale_details: str

    model_config = ConfigDict(extra="forbid")


class QuestionRecommendation(BaseModel):
    question_id: str
    title: str
    problem_text: str
    code_snippet: Optional[str] = None
    question_type: str
    options: Optional[List[dict]] = None
    difficulty: float
    target_concept_id: str
    target_concept_name: str
    rationale: SelectionRationale

    model_config = ConfigDict(extra="forbid")

