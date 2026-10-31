from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.core.database import get_db
from backend.app.models import Learner, ConceptMastery, Concept
from backend.app.domain.scheduler import LeitnerScheduler
from pydantic import BaseModel

router = APIRouter()


class ConceptMasteryDTO(BaseModel):
    concept_id: str
    concept_name: str
    p_mastery: float
    leitner_box: int
    consecutive_correct: int
    last_reviewed_at: Any
    next_review_due: Any
    is_due_for_review: bool
    urgency_hours: float


@router.get("", summary="List learners")
def list_learners(db: Session = Depends(get_db)):
    learners = db.query(Learner).all()
    return [{"id": l.id, "name": l.name, "created_at": l.created_at} for l in learners]


@router.get("/{learner_id}/mastery", response_model=List[ConceptMasteryDTO], summary="Get learner concept mastery graph data")
def get_learner_mastery(learner_id: str, db: Session = Depends(get_db)):
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    masteries = db.query(ConceptMastery).filter(ConceptMastery.learner_id == learner_id).all()
    concepts = {c.id: c for c in db.query(Concept).all()}

    output = []
    for m in masteries:
        c = concepts.get(m.concept_id)
        is_due, urgency = LeitnerScheduler.evaluate_urgency(m.next_review_due)
        output.append(
            ConceptMasteryDTO(
                concept_id=m.concept_id,
                concept_name=c.name if c else m.concept_id,
                p_mastery=m.p_mastery,
                leitner_box=m.leitner_box,
                consecutive_correct=m.consecutive_correct or 0,
                last_reviewed_at=m.last_reviewed_at,
                next_review_due=m.next_review_due,
                is_due_for_review=is_due,
                urgency_hours=urgency,
            )
        )
    return output


@router.get("/{learner_id}/due-reviews", summary="Get concepts currently due for Leitner revision")
def get_due_reviews(learner_id: str, db: Session = Depends(get_db)):
    all_masteries = get_learner_mastery(learner_id, db)
    return [m for m in all_masteries if m.is_due_for_review]

