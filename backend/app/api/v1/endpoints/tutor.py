from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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


@router.post("/stream", summary="Progressive streaming tutor chat via Server-Sent Events (SSE)")
async def stream_tutor(req: TutorRequest):
    """
    Streams progressive token chunks using text/event-stream format.
    Events: 'start', 'content' (with chunk), and 'complete'.
    """
    try:
        return StreamingResponse(
            tutor_service.stream_interaction(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming service error: {str(e)}")
