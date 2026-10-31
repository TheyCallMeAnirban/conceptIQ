"""
ConceptIQ Interactive Backend CLI Test Tool
Allows testing any answer and voice reasoning transcript against the backend.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.database import SessionLocal
from backend.app.models import AssessmentSession, Learner, Question
from backend.app.domain.schemas.session import AttemptSubmission
from backend.app.services.learning_loop import LearningLoopService


def run_demo(question_id: str = "Q_ARITH_01", student_answer: str = "Option A", reasoning: str = None):
    db = SessionLocal()
    try:
        learner = db.query(Learner).first()
        if not learner:
            print("No learner found. Run 'python -m backend.app.seed.seed_db' first.")
            return

        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            print(f"Question {question_id} not found.")
            return

        # Start a fresh test session
        session = AssessmentSession(
            learner_id=learner.id,
            current_question_id=question.id,
            status="ACTIVE",
        )
        db.add(session)
        db.commit()

        default_reasoning = (
            "Um, so ptr holds address 0x3000, and we add 2 to it. "
            "Because adding integers adds 1 byte each time, the address becomes 0x3002."
        )
        transcript = reasoning or default_reasoning

        print("=" * 70)
        print(f"ConceptIQ Diagnostic Runner — Session [{session.id[:8]}]")
        print(f"Learner: {learner.name} ({learner.id})")
        print("=" * 70)
        print(f"Question:  [{question.id}] {question.title}")
        print(f"Problem:   {question.problem_text}")
        if question.code_snippet:
            print(f"Snippet:\n{question.code_snippet}")
        print(f"Expected:  {question.correct_answer}")
        print("-" * 70)
        print(f"Submitted: {student_answer}")
        print(f"Dictation: \"{transcript}\"")
        print("=" * 70)

        submission = AttemptSubmission(
            learner_id=learner.id,
            session_id=session.id,
            question_id=question.id,
            student_answer=student_answer,
            reasoning_transcript=transcript,
        )

        service = LearningLoopService(db)
        result = service.process_attempt(submission)

        print("\n[1] DETERMINISTIC ANSWER EVALUATION")
        print(f" • Correctness:           {result.is_correct} (Determined by backend evaluator)")

        print("\n[2] DIAGNOSTIC ENGINE (REASONING & MISCONCEPTIONS)")
        print(f" • Quality:               {result.diagnosis.reasoning_quality.value}")
        print(f" • Misconceptions:        {result.diagnosis.detected_misconceptions or 'None detected'}")
        print(f" • Evidence:              {result.diagnosis.reasoning_evidence}")
        print(f" • Remediation Hint:      {result.diagnosis.recommended_intervention}")
        print(f" • Diagnostic Provider:   {result.diagnosis.diagnosis_provider}")

        print("\n[3] DETERMINISTIC BKT KNOWLEDGE TRACING")
        print(f" • Prior Mastery P(L):    {result.bkt_update['prior']:.4f}")
        print(f" • Posterior Mastery:     {result.bkt_update['posterior']:.4f}")
        print(f" • Delta:                 {result.bkt_update['delta']:+.4f}")
        print(f" • Parameters:            Slip={result.bkt_update['p_slip']}, Guess={result.bkt_update['p_guess']}, Transit={result.bkt_update['p_transit']}")

        print("\n[4] LEITNER SPACED-REPETITION SCHEDULER")
        print(f" • Box Transition:        Box {result.leitner_update['previous_box']} -> Box {result.leitner_update['new_box']}")
        print(f" • Consecutive Correct:   {result.leitner_update['consecutive_correct']}")
        print(f" • Next Review Due:       {result.leitner_update['next_review_due']}")

        print("\n[5] ADAPTIVE QUESTION SELECTION & RATIONALE")
        rec = result.next_question
        if rec:
            print(f" • Next Question:         [{rec.question_id}] {rec.title}")
            print(f" • Target Concept:        {rec.target_concept_name} ({rec.target_concept_id})")
            print(f" • Difficulty Level:      {rec.difficulty}")
            print(f" • Selection Reason:      {rec.rationale.selection_reason}")
            print(f" • Prerequisite Status:   {rec.rationale.prerequisite_status}")
            print(f" • Transparent Rationale: {rec.rationale.rationale_details}")
        else:
            print(" • Session Complete: All frontier questions addressed.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    q_id = sys.argv[1] if len(sys.argv) > 1 else "Q_ARITH_01"
    ans = sys.argv[2] if len(sys.argv) > 2 else "Option A"
    reason = sys.argv[3] if len(sys.argv) > 3 else None
    run_demo(q_id, ans, reason)
