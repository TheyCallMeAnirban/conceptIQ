from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.models import Concept, ConceptPrerequisite
from pydantic import BaseModel

router = APIRouter()


class ConceptDetailDTO(BaseModel):
    id: str
    name: str
    description: str
    prerequisites: List[str]
    default_p_init: float


@router.get("", response_model=List[ConceptDetailDTO], summary="List all syllabus concepts and prerequisite DAG edges")
def list_concepts(db: Session = Depends(get_db)):
    concepts = db.query(Concept).all()
    prereqs = db.query(ConceptPrerequisite).all()

    prereq_map = {}
    for p in prereqs:
        prereq_map.setdefault(p.concept_id, []).append(p.prerequisite_id)

    return [
        ConceptDetailDTO(
            id=c.id,
            name=c.name,
            description=c.description or "",
            prerequisites=prereq_map.get(c.id, []),
            default_p_init=c.default_p_init,
        )
        for c in concepts
    ]

