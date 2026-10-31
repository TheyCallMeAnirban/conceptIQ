from fastapi import APIRouter, HTTPException
from backend.app.services.tutor_engine import (
    UniversalTutorService,
    TutorRequest,
    TutorResponse,
)

router = APIRouter()
tutor_service = UniversalTutorService()


@router.post("/query", response_model=TutorResponse, summary="Universal Tutor chat, doubt resolution, and concept explanations")
def query_tutor(req: TutorRequest):
    try:
        return tutor_service.handle_interaction(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tutor service error: {str(e)}")

