import pytest
from pydantic import ValidationError
from backend.app.domain.schemas.diagnosis import (
    DiagnosticInput,
    DiagnosticOutput,
    ReasoningQuality,
)
from backend.app.services.llm_diagnostician import LLMDiagnostician


@pytest.fixture
def sample_misconceptions():
    return [
        {
            "id": "BYTE_INCREMENT_FALLACY",
            "name": "Assuming pointer addition increases raw address by 1 byte",
            "description": "Student assumes ptr + 1 simply adds 1 to the numeric memory address.",
            "remediation_hint": "In C, (ptr + 1) scales the memory address by sizeof(*ptr) bytes.",
        },
        {
            "id": "COMMUTATIVITY_OF_INDEXING_DISBELIEF",
            "name": "Believing i[a] is invalid syntax in C",
            "description": "Student assumes i[a] will throw a compiler error.",
            "remediation_hint": "Because a[i] == *(a + i) and addition is commutative, i[a] is valid.",
        },
    ]


def test_diagnostic_output_schema_extra_fields_forbidden():
    """Verify extra fields in DiagnosticOutput trigger validation error."""
    valid_data = {
        "is_correct": True,
        "reasoning_quality": "SOUND",
        "detected_misconceptions": [],
        "affected_concepts": ["POINTER_ARITHMETIC"],
        "reasoning_evidence": "Valid step",
        "explanation": "Correct",
        "recommended_intervention": "Proceed",
        "suggested_difficulty": 0.5,
        "diagnosis_provider": "deterministic_fallback",
    }
    # Should succeed
    out = DiagnosticOutput.model_validate(valid_data)
    assert out.is_correct is True

    # With extra field (must raise)
    invalid_data = {**valid_data, "arbitrary_bkt_score": 0.85}
    with pytest.raises(ValidationError):
        DiagnosticOutput.model_validate(invalid_data)


def test_deterministic_fallback_labeling(sample_misconceptions):
    """When LLM provider is unavailable or unset, provider must be 'deterministic_fallback'."""
    diagnostician = LLMDiagnostician(provider="fallback")
    inp = DiagnosticInput(
        question_statement="Address of arr[3]",
        expected_answer="B",
        student_answer="B",
        is_correct=True,
        reasoning_transcript="Um so arr 3 is base plus 3 times 4 bytes so it is 0x200C",
        primary_concept="ARRAYS_BASIC",
        known_misconceptions=sample_misconceptions,
    )
    result = diagnostician.diagnose(inp)
    assert result.diagnosis_provider == "deterministic_fallback"
    assert result.is_correct is True
    assert result.reasoning_quality == ReasoningQuality.SOUND


def test_contextual_misconception_detection(sample_misconceptions):
    """Detects BYTE_INCREMENT_FALLACY when student reasons address adds 1 byte."""
    diagnostician = LLMDiagnostician(provider="fallback")
    inp = DiagnosticInput(
        question_statement="Address produced by ptr + 2 on int* 0x3000",
        expected_answer="B",
        student_answer="A",  # Student chose 0x3002
        is_correct=False,
        reasoning_transcript="Like, uh, ptr is 0x3000, so adding 2 just adds 1 byte per step so it gives 0x3002.",
        primary_concept="POINTER_ARITHMETIC",
        known_misconceptions=sample_misconceptions,
    )
    result = diagnostician.diagnose(inp)
    assert result.is_correct is False
    assert "BYTE_INCREMENT_FALLACY" in result.detected_misconceptions
    assert result.reasoning_quality == ReasoningQuality.FLAWED
    assert "sizeof(*ptr)" in result.recommended_intervention


def test_insufficient_evidence_does_not_invent_misconception(sample_misconceptions):
    """Short or guess transcripts should not trigger false positive misconception classifications."""
    diagnostician = LLMDiagnostician(provider="fallback")
    inp = DiagnosticInput(
        question_statement="Address produced by ptr + 2",
        expected_answer="B",
        student_answer="C",
        is_correct=False,
        reasoning_transcript="idk I just guessed C",
        primary_concept="POINTER_ARITHMETIC",
        known_misconceptions=sample_misconceptions,
    )
    result = diagnostician.diagnose(inp)
    assert result.is_correct is False
    assert result.detected_misconceptions == []  # MUST NOT invent one
    assert result.reasoning_quality == ReasoningQuality.INSUFFICIENT_EVIDENCE


def test_wispr_flow_speech_artifacts_resilience(sample_misconceptions):
    """Handles filler words, stuttering, and informal spoken phrasing gracefully."""
    diagnostician = LLMDiagnostician(provider="fallback")
    inp = DiagnosticInput(
        question_statement="What is 2[arr]?",
        expected_answer="C",
        student_answer="Option C",
        is_correct=True,
        reasoning_transcript="Uh, wait... so you know how a of i is star a plus i? Well, commutativity means two plus arr is same thing so 300.",
        primary_concept="POINTER_ARRAY_RELATION",
        known_misconceptions=sample_misconceptions,
    )
    result = diagnostician.diagnose(inp)
    assert result.is_correct is True
    assert result.reasoning_quality == ReasoningQuality.SOUND
    assert result.detected_misconceptions == []

