from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api.v1.router import api_router
from backend.app.seed.seed_db import seed_database

from backend.app.core.migration import run_schema_upgrade

# Create tables, apply schema migrations, and seed curriculum on startup
try:
    run_schema_upgrade(engine)
    seed_database()
except Exception as e:
    print(f"[Startup] DB migration/seeding completed or handled: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ConceptIQ — Adaptive GATE CSE Exam-Preparation Platform & Intelligent Tutor.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Enable CORS for local dev / frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_v1": settings.API_V1_STR,
    }

