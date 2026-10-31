from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Any
import uuid

from backend.app.core.database import get_db
from backend.app.core.mongo_repo import MongoRepository
from backend.app.domain.schemas.session import AttemptSubmission, AttemptResult
from backend.app.domain.schemas.selection import QuestionRecommendation
from backend.app.services.learning_loop import LearningLoopService
from backend.app.services.question_selector import QuestionSelector
from pydantic import BaseModel, Field

router = APIRouter()


class StartSessionRequest(BaseModel):
    learner_id: str
    target_subject: Optional[str] = "C_POINTERS_ARRAYS"
    force_new: Optional[bool] = False


class StartSessionResponse(BaseModel):
    session_id: str
    learner_id: str
    status: str
    current_question: Optional[QuestionRecommendation] = None


@router.post("/start", response_model=StartSessionResponse, summary="Start or resume an assessment session")
def start_session(payload: StartSessionRequest, db: Any = Depends(get_db)):
    # Support MongoRepository as well as legacy SQLAlchemy session
    is_mongo = isinstance(db, MongoRepository)
    if is_mongo:
        learner = db.get_learner(payload.learner_id)
        if not learner:
            raise HTTPException(status_code=404, detail=f"Learner {payload.learner_id} not found")

        active_session = None if payload.force_new else db.get_active_session(payload.learner_id)
        selector = QuestionSelector(db)

        if active_session:
            rec = None
            if active_session.current_question_id:
                rec = selector.select_next_question(
                    learner_id=payload.learner_id,
                    session_attempted_qids=db.get_session_attempted_qids(active_session.id),
                )
            return StartSessionResponse(
                session_id=active_session.id,
                learner_id=active_session.learner_id,
                status=active_session.status,
                current_question=rec,
            )

        # Create brand new session
        first_q_rec = selector.select_next_question(
            learner_id=payload.learner_id,
            session_attempted_qids=[],
        )
        if not first_q_rec:
            raise HTTPException(status_code=500, detail="No eligible questions found in curriculum bank")

        new_session_id = str(uuid.uuid4())
        new_session = db.save_session({
            "id": new_session_id,
            "learner_id": payload.learner_id,
            "current_question_id": first_q_rec.question_id,
            "status": "ACTIVE",
            "attempt_count": 0,
        })

        return StartSessionResponse(
            session_id=new_session.id,
            learner_id=new_session.learner_id,
            status=new_session.status,
            current_question=first_q_rec,
        )

    # Legacy SQLAlchemy fallback
    from backend.app.models import AssessmentSession, Learner, Question
    learner = db.query(Learner).filter(Learner.id == payload.learner_id).first()
    if not learner:
        raise HTTPException(status_code=404, detail=f"Learner {payload.learner_id} not found")

    active_session = None if payload.force_new else (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.learner_id == payload.learner_id,
            AssessmentSession.status == "ACTIVE",
        )
        .first()
    )

    selector = QuestionSelector(db)

    if active_session:
        rec = None
        if active_session.current_question_id:
            rec = selector.select_next_question(
                learner_id=payload.learner_id,
                session_attempted_qids=[],
            )
        return StartSessionResponse(
            session_id=active_session.id,
            learner_id=active_session.learner_id,
            status=active_session.status,
            current_question=rec,
        )

    first_q_rec = selector.select_next_question(
        learner_id=payload.learner_id,
        session_attempted_qids=[],
    )
    if not first_q_rec:
        raise HTTPException(status_code=500, detail="No eligible questions found in curriculum bank")

    new_session = AssessmentSession(
        learner_id=payload.learner_id,
        current_question_id=first_q_rec.question_id,
        status="ACTIVE",
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return StartSessionResponse(
        session_id=new_session.id,
        learner_id=new_session.learner_id,
        status=new_session.status,
        current_question=first_q_rec,
    )


@router.post("/submit", response_model=AttemptResult, summary="Submit student answer and voice reasoning transcript")
def submit_attempt(submission: AttemptSubmission, db: Any = Depends(get_db)):
    service = LearningLoopService(db)
    try:
        return service.process_attempt(submission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error processing attempt: {str(e)}")

