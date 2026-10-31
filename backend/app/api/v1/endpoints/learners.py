from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from backend.app.core.database import get_db
from backend.app.models import Learner, ConceptMastery, Concept, Topic, Subject
from backend.app.domain.scheduler import LeitnerScheduler
from pydantic import BaseModel

router = APIRouter()


class ConceptMasteryDTO(BaseModel):
    concept_id: str
    concept_name: str
    topic_id: Optional[str] = None
    subject_id: Optional[str] = None
    p_mastery: float
    leitner_box: int
    consecutive_correct: int
    last_reviewed_at: Any
    next_review_due: Any
    is_due_for_review: bool
    urgency_hours: float
    assessment_state: str = "UNASSESSED"  # UNASSESSED, IN_PROGRESS, ASSESSED
    formal_attempt_count: int = 0
    last_assessed_at: Any = None


@router.get("", summary="List learners")
def list_learners(db: Session = Depends(get_db)):
    learners = db.query(Learner).all()
    return [{"id": l.id, "name": l.name, "created_at": l.created_at} for l in learners]


@router.get("/{learner_id}/mastery", response_model=List[ConceptMasteryDTO], summary="Get learner concept mastery graph data")
def get_learner_mastery(learner_id: str, subject_id: Optional[str] = None, db: Session = Depends(get_db)):
    learner = db.query(Learner).filter(Learner.id == learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    masteries = db.query(ConceptMastery).filter(ConceptMastery.learner_id == learner_id).all()
    concepts = {c.id: c for c in db.query(Concept).all()}
    topics = {t.id: t for t in db.query(Topic).all()}

    output = []
    for m in masteries:
        c = concepts.get(m.concept_id)
        topic = topics.get(c.topic_id) if c and c.topic_id else None
        c_subj_id = topic.subject_id if topic else None

        # Filter by subject if requested
        if subject_id and c_subj_id != subject_id:
            continue

        is_due, urgency = LeitnerScheduler.evaluate_urgency(m.next_review_due)
        output.append(
            ConceptMasteryDTO(
                concept_id=m.concept_id,
                concept_name=c.name if c else m.concept_id,
                topic_id=c.topic_id if c else None,
                subject_id=c_subj_id,
                p_mastery=m.p_mastery,
                leitner_box=m.leitner_box,
                consecutive_correct=m.consecutive_correct or 0,
                last_reviewed_at=m.last_reviewed_at,
                next_review_due=m.next_review_due,
                is_due_for_review=is_due,
                urgency_hours=urgency,
                assessment_state=m.assessment_state or "UNASSESSED",
                formal_attempt_count=m.formal_attempt_count or 0,
                last_assessed_at=m.last_assessed_at,
            )
        )
    return output


@router.get("/{learner_id}/due-reviews", summary="Get concepts currently due for Leitner revision")
def get_due_reviews(learner_id: str, db: Session = Depends(get_db)):
    all_masteries = get_learner_mastery(learner_id, db)
    return [m for m in all_masteries if m.is_due_for_review]

