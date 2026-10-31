from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    sessions,
    learners,
    concepts,
    questions,
    analytics,
    tutor,
)

api_router = APIRouter()

api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions (Adaptive Learning Loop)"])
api_router.include_router(learners.router, prefix="/learners", tags=["Learners (Mastery & Profiles)"])
api_router.include_router(concepts.router, prefix="/concepts", tags=["Concepts (Syllabus & DAG)"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions (Bank)"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics (Teacher Dashboard)"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["Universal AI Tutor Engine"])


