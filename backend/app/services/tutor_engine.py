import os
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
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
    Supports real token-level progressive response streaming via SSE.
    """

    def __init__(self, diagnostician: Optional[LLMDiagnostician] = None):
        self.diagnostician = diagnostician or LLMDiagnostician()

    def _build_prompt(self, req: TutorRequest) -> str:
        system_instruction = (
            "You are ConceptIQ's Universal AI Tutor and Academic Intelligence System. "
            "You are a dedicated, world-class professor and tutor available on demand.\n\n"
            "CRITICAL PEDAGOGICAL RULES:\n"
            "1. Respond directly and naturally to the student. DO NOT dump internal metadata, learner IDs, "
            "JSON structures, system status codes, or database concept keys.\n"
            "2. Never dump an entire textbook chapter at once. Teach progressively and engagingly.\n"
            "3. Use intuitive analogies first (e.g. 'Think of a variable as a house and a pointer as the address on paper...').\n"
            "4. Provide formal definitions, clean code examples, and mathematical equations with LaTeX (e.g. \\(a^2+b^2=c^2\\) or \\[\\int u\\,dv = uv - \\int v\\,du\\]).\n"
            "5. Highlight common student pitfalls to avoid.\n"
            "6. Conclude with a quick conceptual reflection question to test active understanding."
        )

        user_query = f"Mode: {req.mode}\nStudent Question: {req.message}"
        if req.concept_id:
            user_query += f"\nSyllabus Topic Context: {req.concept_id}"
        return f"{system_instruction}\n\n{user_query}"

    async def stream_interaction(self, req: TutorRequest) -> AsyncGenerator[str, None]:
        """
        Streams response chunks progressively using SSE (text/event-stream).
        Emits 'start', 'content', and 'complete' events.
        """
        import uuid
        req_id = str(uuid.uuid4())

        # 1. Emit start event
        start_payload = {
            "type": "start",
            "request_id": req_id,
            "mode": req.mode,
            "concept_id": req.concept_id,
            "status": "THINKING",
        }
        yield f"data: {json.dumps(start_payload)}\n\n"

        prompt = self._build_prompt(req)

        # 2. Try Gemini Streaming API with high-quota fallback chain
        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            for model_name in [
                "gemini-flash-lite-latest",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-flash-latest",
            ]:
                try:
                    import urllib.request
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?key={settings.GEMINI_API_KEY}&alt=sse"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 1500,
                        },
                    }
                    req_obj = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )

                    with urllib.request.urlopen(req_obj, timeout=20) as resp:
                        for raw_line in resp:
                            line_str = raw_line.decode("utf-8").strip()
                            if not line_str or not line_str.startswith("data:"):
                                continue

                            data_content = line_str[5:].strip()
                            try:
                                chunk_json = json.loads(data_content)
                                candidates = chunk_json.get("candidates", [])
                                if candidates and "content" in candidates[0]:
                                    parts = candidates[0]["content"].get("parts", [])
                                    for part in parts:
                                        chunk_text = part.get("text", "")
                                        if chunk_text:
                                            chunk_payload = {
                                                "type": "content",
                                                "chunk": chunk_text,
                                            }
                                            yield f"data: {json.dumps(chunk_payload)}\n\n"
                            except Exception as parse_err:
                                logger.debug(f"Chunk parse note: {parse_err}")

                    # Successfully finished stream from this model
                    complete_payload = {
                        "type": "complete",
                        "provider": f"gemini ({model_name})",
                        "status": "IDLE",
                    }
                    yield f"data: {json.dumps(complete_payload)}\n\n"
                    return
                except Exception as model_err:
                    logger.warning(f"Streaming failed on {model_name}: {model_err}, attempting next model.")

        # 3. Fallback deterministic generator if API is unavailable or rate-limited
        fallback_paragraphs = [
            f"### Intuitive Overview ({req.mode})\n\n",
            f"Let's explore your question: *\"{req.message}\"*\n\n",
            "In foundational studies, understanding invariant rules always comes before procedural calculations.\n\n",
            "**Key Mechanism:**\n",
            "- Variables represent allocated state locations.\n",
            "- Operations act on state boundaries through well-defined invariants.\n\n",
            "Try putting this into practice in Practice Mode to test your active recall!\n",
        ]

        import asyncio
        for p in fallback_paragraphs:
            await asyncio.sleep(0.06)
            yield f"data: {json.dumps({'type': 'content', 'chunk': p})}\n\n"

        yield f"data: {json.dumps({'type': 'complete', 'provider': 'deterministic_fallback', 'status': 'IDLE'})}\n\n"

    def handle_interaction(self, req: TutorRequest) -> TutorResponse:
        """Non-streaming fallback method."""
        prompt = self._build_prompt(req)

        if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            for model_name in [
                "gemini-flash-lite-latest",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-flash-latest",
            ]:
                try:
                    import urllib.request
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 1024,
                        },
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
                            provider=f"gemini ({model_name})",
                        )
                except Exception as e:
                    logger.warning(f"Tutor call to {model_name} failed ({e}), checking next.")

        fallback_reply = (
            f"### Pedagogical Insight ({req.mode})\n\n"
            f"**Regarding your inquiry:** *\"{req.message}\"*\n\n"
            f"- **Core Principle:** Understanding fundamentals precedes mechanics.\n"
            f"- **Intuition:** Break the problem down into state variables and invariant rules.\n"
            f"- **Next Step:** Verify this concept in Practice Mode to test your active recall."
        )
        return TutorResponse(
            mode=req.mode,
            reply=fallback_reply,
            concept_id=req.concept_id,
            provider="deterministic_fallback",
        )
