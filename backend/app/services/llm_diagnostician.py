import json
import re
import logging
from typing import Optional, Dict, Any, List
import httpx

from backend.app.core.config import settings
from backend.app.domain.schemas.diagnosis import (
    DiagnosticInput,
    DiagnosticOutput,
    ReasoningQuality,
)

logger = logging.getLogger(__name__)


class LLMDiagnostician:
    """
    Diagnostic Engine responsible for evaluating student reasoning,
    detecting misconceptions, and recommending pedagogical interventions.
    Strictly isolated from BKT quantitative calculations and correctness evaluation.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        timeout: float = 8.0,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.timeout = timeout
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY

    def diagnose(self, input_data: DiagnosticInput) -> DiagnosticOutput:
        """
        Main entrypoint. Attempts LLM diagnosis; gracefully degrades to
        deterministic fallback on any error, timeout, HTTP failure, or schema violation.
        """
        # 1. Attempt configured LLM provider if API key exists
        if self.provider == "gemini" and self.gemini_api_key:
            try:
                result = self._call_gemini(input_data)
                return self._sanitize_diagnosis(result, input_data)
            except Exception as e:
                logger.warning(f"Gemini diagnosis failed: {e}. Falling back to deterministic.")
        elif self.provider == "openai" and self.openai_api_key:
            try:
                result = self._call_openai(input_data)
                return self._sanitize_diagnosis(result, input_data)
            except Exception as e:
                logger.warning(f"OpenAI diagnosis failed: {e}. Falling back to deterministic.")

        # 2. Deterministic Fallback
        return self._deterministic_fallback(input_data)

    def _sanitize_diagnosis(self, diag: DiagnosticOutput, inp: DiagnosticInput) -> DiagnosticOutput:
        """
        Sanitizes LLM output:
        1. Guarantees backend correctness authority: diag.is_correct MUST match inp.is_correct.
        2. Discards any hallucinated misconception IDs not in the catalog.
        """
        valid_misc_ids = {m["id"] for m in inp.known_misconceptions}
        sanitized_misconceptions = [m for m in diag.detected_misconceptions if m in valid_misc_ids]

        # Force backend correctness authority
        return DiagnosticOutput(
            is_correct=inp.is_correct,
            reasoning_quality=diag.reasoning_quality,
            detected_misconceptions=sanitized_misconceptions,
            affected_concepts=diag.affected_concepts or [inp.primary_concept],
            reasoning_evidence=diag.reasoning_evidence,
            explanation=diag.explanation,
            recommended_intervention=diag.recommended_intervention,
            suggested_difficulty=diag.suggested_difficulty,
            diagnosis_provider=diag.diagnosis_provider,
        )

    def _build_prompt(self, inp: DiagnosticInput) -> str:
        misconceptions_text = "\n".join(
            [f"- ID: {m['id']}\n  Name: {m['name']}\n  Description: {m['description']}\n  Remediation: {m['remediation_hint']}"
             for m in inp.known_misconceptions]
        ) or "None cataloged."

        return f"""You are the Diagnostic Engine for ConceptIQ, an intelligent tutor for GATE CSE aspirants in C Programming (Arrays & Pointers).
Your task is to analyze the student's reasoning, evaluate its conceptual validity, classify known misconceptions, and recommend pedagogical interventions.

NOTE ON CORRECTNESS:
The backend has already evaluated whether the answer is mathematically and computationally correct.
Backend Evaluation: is_correct = {inp.is_correct}
You must NOT dispute or alter this correctness determination. Your role is purely diagnostic.

STUDENT REASONING CONTEXT:
The student's reasoning was captured via voice dictation (Wispr Flow). It may contain speech artifacts, filler words ('um', 'uh', 'like'), informal phrasing, self-corrections, or spoken operators (e.g. 'star p' for *p, 'arr of i' for arr[i]). Focus on their conceptual thinking, not diction.

INPUT DATA:
- Question: {inp.question_statement}
- Expected Answer: {inp.expected_answer}
- Student's Answer: {inp.student_answer}
- Evaluated Correctness: {inp.is_correct}
- Student's Dictated Reasoning: "{inp.reasoning_transcript}"
- Primary Concept: {inp.primary_concept}
- Secondary Concepts: {', '.join(inp.secondary_concepts) if inp.secondary_concepts else 'None'}

KNOWN MISCONCEPTION CATALOG (Only choose from these IDs):
{misconceptions_text}

INSTRUCTIONS:
1. is_correct must be set to {str(inp.is_correct).lower()}.
2. Evaluate reasoning quality: 'SOUND', 'PARTIALLY_CORRECT', 'FLAWED', 'GUESS', or 'INSUFFICIENT_EVIDENCE'.
3. Misconception Detection:
   - Only detect a misconception if there is clear, unambiguous evidence in the student's reasoning.
   - Do NOT match solely on superficial keyword presence.
   - You MUST only output IDs from the KNOWN MISCONCEPTION CATALOG above. Never invent new IDs.
   - If student guessed, was silent, or gave minimal explanation without exposing the misconception structure, return empty list [] for detected_misconceptions.
4. Affected Concepts: List concept IDs impacted.
5. Provide evidence: Quote or specifically reference student's statements.
6. Provide concise explanation and recommended intervention.
7. Suggested difficulty: Between 0.1 and 1.0.
8. Output MUST be strict valid JSON adhering to the required schema with no Markdown codeblocks and no extra fields.

JSON Schema format:
{{
  "is_correct": {str(inp.is_correct).lower()},
  "reasoning_quality": "SOUND" | "PARTIALLY_CORRECT" | "FLAWED" | "GUESS" | "INSUFFICIENT_EVIDENCE",
  "detected_misconceptions": ["ID"],
  "affected_concepts": ["CONCEPT_ID"],
  "reasoning_evidence": "string",
  "explanation": "string",
  "recommended_intervention": "string",
  "suggested_difficulty": float between 0.1 and 1.0,
  "diagnosis_provider": "{self.provider}"
}}
"""

    def _clean_json_response(self, raw_text: str) -> str:
        """Strip markdown fences if present."""
        clean = raw_text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return clean.strip()

    def _call_gemini(self, inp: DiagnosticInput) -> DiagnosticOutput:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = self._build_prompt(inp)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = self._clean_json_response(raw_text)
            parsed = json.loads(cleaned)
            parsed["diagnosis_provider"] = "gemini"
            parsed["is_correct"] = inp.is_correct
            return DiagnosticOutput.model_validate(parsed)

    def _call_openai(self, inp: DiagnosticInput) -> DiagnosticOutput:
        url = "https://api.openai.com/v1/chat/completions"
        prompt = self._build_prompt(inp)

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a strict diagnostic evaluator returning JSON only."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            cleaned = self._clean_json_response(raw_text)
            parsed = json.loads(cleaned)
            parsed["diagnosis_provider"] = "openai"
            parsed["is_correct"] = inp.is_correct
            return DiagnosticOutput.model_validate(parsed)

    def _deterministic_fallback(self, inp: DiagnosticInput) -> DiagnosticOutput:
        """
        Deterministic, robust fallback when LLM is unavailable or unconfigured.
        Strictly respects backend is_correct authority.
        Labels provider explicitly as 'deterministic_fallback'.
        """
        is_correct = inp.is_correct
        transcript = inp.reasoning_transcript.strip().lower()
        word_count = len(transcript.split())

        detected_misconceptions = []
        affected_concepts = [inp.primary_concept]

        # Contextual misconception heuristics for fallback
        if not is_correct:
            for misc in inp.known_misconceptions:
                m_id = misc.get("id")
                if m_id == "BYTE_INCREMENT_FALLACY":
                    if ("1 byte" in transcript or "adds 1" in transcript or "add one" in transcript) and "sizeof" not in transcript:
                        detected_misconceptions.append(m_id)
                elif m_id == "ARRAY_NAME_IS_POINTER_VARIABLE":
                    if ("pointer variable" in transcript or "can increment arr" in transcript or "reassign" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "SIZEOF_ARRAY_EQUALS_POINTER_SIZE":
                    if ("sizeof gives 8" in transcript or "sizeof pointer" in transcript or "always 8 bytes" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "PRECEDENCE_DEREF_AND_POSTINCREMENT":
                    if ("increments the value" in transcript or "bracket around" in transcript or "dereferences first" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "COMMUTATIVITY_OF_INDEXING_DISBELIEF":
                    if ("syntax error" in transcript or "invalid syntax" in transcript or "brackets backwards" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "DOUBLE_POINTER_EQUALS_2D_ARRAY":
                    if ("2d array is double pointer" in transcript or "same as int**" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "CONFUSING_ARRAY_OF_POINTERS_WITH_POINTER_TO_ARRAY":
                    if ("pointer array" in transcript and "array of pointers" in transcript):
                        detected_misconceptions.append(m_id)
                elif m_id == "OUT_OF_BOUNDS_COMPILER_ERROR_BELIEF":
                    if ("compiler error" in transcript or "compile error" in transcript or "out of bounds exception" in transcript):
                        detected_misconceptions.append(m_id)

        # Quality evaluation
        is_guess = any(kw in transcript for kw in ["guess", "guessed", "idk", "no idea", "i don't know", "not sure"])
        if word_count < 5 or is_guess:
            reasoning_quality = ReasoningQuality.INSUFFICIENT_EVIDENCE
            reasoning_evidence = f"Student provided minimal or speculative reasoning: '{inp.reasoning_transcript}'"
            explanation = "Insufficient substantive explanation provided to verify underlying conceptual model."
            recommended_intervention = "Encourage the student to articulate why this choice was selected using Wispr Flow."
            suggested_diff = 0.3 if is_correct else 0.2
        elif is_correct:
            reasoning_quality = ReasoningQuality.SOUND
            reasoning_evidence = f"Student provided supporting explanation: '{inp.reasoning_transcript[:120]}...'"
            explanation = "Answer is correct and consistent with expected C memory semantics."
            recommended_intervention = "Reinforce mastery with an advanced or combination problem."
            suggested_diff = 0.6
        else:
            if detected_misconceptions:
                reasoning_quality = ReasoningQuality.FLAWED
                m_details = next((m for m in inp.known_misconceptions if m["id"] == detected_misconceptions[0]), None)
                reasoning_evidence = f"Student exhibited misconception {detected_misconceptions[0]} in explanation: '{inp.reasoning_transcript[:120]}...'"
                explanation = m_details["description"] if m_details else "Identified conceptual misconception in memory/pointer interpretation."
                recommended_intervention = m_details["remediation_hint"] if m_details else "Review prerequisite concepts."
                suggested_diff = 0.3
            else:
                reasoning_quality = ReasoningQuality.FLAWED
                reasoning_evidence = f"Student provided incorrect explanation: '{inp.reasoning_transcript[:120]}...'"
                explanation = "Answer is incorrect. Reasoning does not clearly manifest a cataloged misconception, but deviates from standard C evaluation."
                recommended_intervention = f"Review the canonical definition for concept {inp.primary_concept}."
                suggested_diff = 0.35

        return DiagnosticOutput(
            is_correct=is_correct,
            reasoning_quality=reasoning_quality,
            detected_misconceptions=detected_misconceptions,
            affected_concepts=affected_concepts,
            reasoning_evidence=reasoning_evidence,
            explanation=explanation,
            recommended_intervention=recommended_intervention,
            suggested_difficulty=suggested_diff,
            diagnosis_provider="deterministic_fallback",
        )
