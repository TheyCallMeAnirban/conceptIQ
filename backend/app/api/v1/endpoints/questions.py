from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any

from backend.app.core.database import get_db
from backend.app.core.mongo_repo import MongoRepository
from pydantic import BaseModel

router = APIRouter()


class QuestionDTO(BaseModel):
    id: str
    concept_id: str
    title: str
    problem_text: str
    code_snippet: Optional[str] = None
    question_type: str
    options: Optional[List[Any]] = None
    difficulty: float
    secondary_concept_ids: List[str] = []
    known_misconceptions: List[str] = []


@router.get("", response_model=List[QuestionDTO], summary="List questions in question bank")
def list_questions(concept_id: Optional[str] = None, db: Any = Depends(get_db)):
    if isinstance(db, MongoRepository):
        questions = db.get_all_questions(concept_id)
        return [
            QuestionDTO(
                id=item.id,
                concept_id=item.concept_id,
                title=item.title,
                problem_text=item.problem_text,
                code_snippet=item.code_snippet,
                question_type=item.question_type,
                options=item.options,
                difficulty=item.difficulty,
                secondary_concept_ids=item.secondary_concept_ids or [],
                known_misconceptions=item.known_misconceptions or [],
            )
            for item in questions
        ]

    from backend.app.models import Question
    q = db.query(Question)
    if concept_id:
        q = q.filter(Question.concept_id == concept_id)
    questions = q.all()

    return [
        QuestionDTO(
            id=item.id,
            concept_id=item.concept_id,
            title=item.title,
            problem_text=item.problem_text,
            code_snippet=item.code_snippet,
            question_type=item.question_type,
            options=item.options,
            difficulty=item.difficulty,
            secondary_concept_ids=item.secondary_concept_ids or [],
            known_misconceptions=item.known_misconceptions or [],
        )
        for item in questions
    ]


@router.get("/{question_id}", response_model=QuestionDTO, summary="Get question by ID")
def get_question(question_id: str, db: Any = Depends(get_db)):
    if isinstance(db, MongoRepository):
        q = db.get_question(question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        return QuestionDTO(
            id=q.id,
            concept_id=q.concept_id,
            title=q.title,
            problem_text=q.problem_text,
            code_snippet=q.code_snippet,
            question_type=q.question_type,
            options=q.options,
            difficulty=q.difficulty,
            secondary_concept_ids=q.secondary_concept_ids or [],
            known_misconceptions=q.known_misconceptions or [],
        )

    from backend.app.models import Question
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionDTO(
        id=q.id,
        concept_id=q.concept_id,
        title=q.title,
        problem_text=q.problem_text,
        code_snippet=q.code_snippet,
        question_type=q.question_type,
        options=q.options,
        difficulty=q.difficulty,
        secondary_concept_ids=q.secondary_concept_ids or [],
        known_misconceptions=q.known_misconceptions or [],
    )
