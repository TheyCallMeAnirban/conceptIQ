from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from backend.app.core.database import get_db
from backend.app.models import QuestionAttempt, Misconception, Concept
from pydantic import BaseModel

router = APIRouter()


class MisconceptionStatDTO(BaseModel):
    misconception_id: str
    misconception_name: str
    concept_id: str
    concept_name: str
    occurrence_count: int
    remediation_hint: str


@router.get("/misconceptions", response_model=List[MisconceptionStatDTO], summary="Teacher Dashboard: Class-wide misconception frequency")
def get_misconception_analytics(db: Session = Depends(get_db)):
    attempts = db.query(QuestionAttempt).all()
    misc_catalog = {m.id: m for m in db.query(Misconception).all()}
    concepts = {c.id: c for c in db.query(Concept).all()}

    counts: Dict[str, int] = {}
    for a in attempts:
        for m_id in (a.detected_misconceptions or []):
            counts[m_id] = counts.get(m_id, 0) + 1

    result = []
    for m_id, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        m = misc_catalog.get(m_id)
        if m:
            c = concepts.get(m.concept_id)
            result.append(
                MisconceptionStatDTO(
                    misconception_id=m.id,
                    misconception_name=m.name,
                    concept_id=m.concept_id,
                    concept_name=c.name if c else m.concept_id,
                    occurrence_count=count,
                    remediation_hint=m.remediation_hint,
                )
            )

    return result

