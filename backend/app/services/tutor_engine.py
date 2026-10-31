import os
import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.services.llm_diagnostician import LLMDiagnostician

logger = logging.getLogger(__name__)


class TutorRequest(BaseModel):
    learner_id: str
    message: str
    mode: str = "DOUBT"  # DOUBT, EXPLAIN, TEACH, ANALYZE
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    concept_id: Optional[str] = None


class TutorResponse(BaseModel):
    mode: str
    reply: str
    concept_id: Optional[str] = None
    pedagogical_breakdown: Optional[Dict[str, str]] = None
    provider: str = "gemini"


class UniversalTutorService:
    """
    Universal AI Tutor Engine for ConceptIQ.
    Handles DOUBT, EXPLAIN, TEACH, and ANALYZE requests.
    INVARIANT: Casual doubt queries and pedagogical explanations
    do NOT mutate BKT mastery states.
    """

    def __init__(self, diagnostician: Optional[LLMDiagnostician] = None):
        self.diagnostician = diagnostician or LLMDiagnostician()

    def handle_interaction(self, req: TutorRequest) -> TutorResponse:
        system_instruction = (
            "You are ConceptIQ's Universal AI Tutor and Academic Intelligence System. "
            "Your tone is sharp, encouraging, highly rigorous, and pedagogically transparent. "
            "You teach and answer doubts across Computer Science, Mathematics, Physics, and beyond.\n"
            "Format your answer with clear markdown headings, concise intuitive analogies, formal definitions, "
            "concrete code or mathematical equations where applicable, and common student pitfalls to avoid.\n"
            "Never hallucinate facts. Be direct and avoid empty fluff."
        )

        user_prompt = f"Mode: {req.mode}\nLearner: {req.learner_id}\nQuery: {req.message}\n"
        if req.concept_id:
            user_prompt += f"Target Concept: {req.concept_id}\n"

        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            try:
                import urllib.request
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{user_prompt}"}]}
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1024,
                    }
                }
                req_obj = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req_obj, timeout=12) as response:
                    raw_res = json.loads(response.read().decode("utf-8"))
                    text = raw_res["candidates"][0]["content"]["parts"][0]["text"]
                    return TutorResponse(
                        mode=req.mode,
                        reply=text,
                        concept_id=req.concept_id,
                        provider="gemini",
                    )
            except Exception as e:
                logger.warning(f"Tutor Gemini call failed ({e}), falling back to deterministic explanation.")

        # Fallback explanation
        fallback_reply = (
            f"### ConceptIQ Pedagogical Insight ({req.mode})\n\n"
            f"**Regarding your inquiry:** *\"{req.message}\"*\n\n"
            f"- **Core Principle:** In {req.subject_id or 'academic foundations'}, understanding fundamentals precedes mechanics.\n"
            f"- **Intuition:** Break the problem down into state variables and invariant rules.\n"
            f"- **Next Step:** Verify this concept in Practice Mode to test your active recall."
        )
        return TutorResponse(
            mode=req.mode,
            reply=fallback_reply,
            concept_id=req.concept_id,
            provider="deterministic_fallback",
        )

