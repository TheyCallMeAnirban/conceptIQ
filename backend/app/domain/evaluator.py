import re
from typing import Optional


class AnswerEvaluator:
    """
    Deterministic answer evaluation engine.
    Sole authority for correctness in ConceptIQ.
    LLM diagnosis cannot override or determine whether an answer is correct.
    """

    @staticmethod
    def evaluate(expected: str, submitted: str, question_type: str = "MCQ") -> bool:
        if submitted is None or expected is None:
            return False

        norm_exp = expected.strip().upper()
        norm_sub = submitted.strip().upper()

        if question_type == "MCQ":
            # Extract standalone option letter (e.g., "Option B", "(B)", "B.", "Choice B" -> "B")
            exp_match = re.search(r"\b([A-D])\b", norm_exp)
            sub_match = re.search(r"\b([A-D])\b", norm_sub)

            clean_exp = exp_match.group(1) if exp_match else norm_exp
            clean_sub = sub_match.group(1) if sub_match else norm_sub

            return clean_exp == clean_sub

        elif question_type == "NAT":  # Numerical Answer Type
            try:
                # Support exact or within float tolerance
                exp_val = float(norm_exp)
                sub_val = float(norm_sub)
                return abs(exp_val - sub_val) < 1e-4
            except ValueError:
                return norm_exp == norm_sub

        # Default string equality fallback
        return norm_exp == norm_sub

