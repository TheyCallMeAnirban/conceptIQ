import logging
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.models import (
    Learner,
    Concept,
    Question,
    Misconception,
    ConceptMastery,
    AssessmentSession,
    QuestionAttempt,
)
from backend.app.domain.bkt import BKTEngine
from backend.app.domain.evaluator import AnswerEvaluator
from backend.app.domain.scheduler import LeitnerScheduler
from backend.app.domain.schemas.diagnosis import DiagnosticInput
from backend.app.domain.schemas.session import AttemptSubmission, AttemptResult
from backend.app.services.llm_diagnostician import LLMDiagnostician
from backend.app.services.question_selector import QuestionSelector

logger = logging.getLogger(__name__)


class LearningLoopService:
    """
    Orchestrates the complete ConceptIQ adaptive learning cycle:
    Student reasoning -> Diagnosis -> BKT update (binary) -> Leitner update -> Next question selection.
    Guarantees strict single-transaction atomicity.
    """

    def __init__(self, db: Session, diagnostician: Optional[LLMDiagnostician] = None):
        self.db = db
        self.diagnostician = diagnostician or LLMDiagnostician()
        self.selector = QuestionSelector(db)

    def process_attempt(self, submission: AttemptSubmission) -> AttemptResult:
        """
        Executes one full turn in the adaptive learning loop atomically.
        """
        eval_time = datetime.now(timezone.utc)

        # 1. Validate Session, Learner, and Question
        session = (
            self.db.query(AssessmentSession)
            .filter(
                AssessmentSession.id == submission.session_id,
                AssessmentSession.learner_id == submission.learner_id,
            )
            .first()
        )
        if not session:
            raise ValueError(f"Active session {submission.session_id} not found for learner {submission.learner_id}")

        question = self.db.query(Question).filter(Question.id == submission.question_id).first()
        if not question:
            raise ValueError(f"Question {submission.question_id} not found")

        concept = self.db.query(Concept).filter(Concept.id == question.concept_id).first()
        if not concept:
            raise ValueError(f"Concept {question.concept_id} not found")

        # 2. Duplicate Submission Check (Prevent double BKT transitions or duplicate attempts)
        existing_attempt = (
            self.db.query(QuestionAttempt)
            .filter(
                QuestionAttempt.session_id == session.id,
                QuestionAttempt.question_id == question.id,
            )
            .first()
        )
        if existing_attempt:
            raise ValueError(f"Question {question.id} has already been attempted in session {session.id}.")

        # 3. Deterministic Backend Answer Evaluation (Sole authority for correctness)
        backend_is_correct = AnswerEvaluator.evaluate(
            expected=question.correct_answer,
            submitted=submission.student_answer,
            question_type=question.question_type,
        )

        # 4. Query known misconceptions catalog for this question
        known_misc_records = (
            self.db.query(Misconception)
            .filter(Misconception.id.in_(question.known_misconceptions or []))
            .all()
        )
        misc_payload = [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "remediation_hint": m.remediation_hint,
            }
            for m in known_misc_records
        ]

        # 5. LLM Diagnostic Analysis (Reasoning, Misconceptions, Interventions)
        diag_input = DiagnosticInput(
            question_statement=f"{question.title}\n{question.problem_text}\nCode:\n{question.code_snippet or ''}",
            expected_answer=question.correct_answer,
            student_answer=submission.student_answer,
            is_correct=backend_is_correct,
            reasoning_transcript=submission.reasoning_transcript,
            primary_concept=concept.id,
            secondary_concepts=question.secondary_concept_ids or [],
            known_misconceptions=misc_payload,
        )
        diagnosis = self.diagnostician.diagnose(diag_input)

        # Enforce Backend Correctness Invariant (Override LLM if it disagreed)
        if diagnosis.is_correct != backend_is_correct:
            logger.warning(
                f"LLM diagnosis evaluated is_correct={diagnosis.is_correct}, "
                f"which contradicts backend authority ({backend_is_correct}). Backend evaluation enforced."
            )
            diagnosis.is_correct = backend_is_correct

        # 6. Standard BKT Mastery Update (Strictly backend binary observation)
        mastery_record = (
            self.db.query(ConceptMastery)
            .filter(
                ConceptMastery.learner_id == submission.learner_id,
                ConceptMastery.concept_id == concept.id,
            )
            .first()
        )
        if not mastery_record:
            # Initialize lazily on first formal assessment interaction
            mastery_record = ConceptMastery(
                learner_id=submission.learner_id,
                concept_id=concept.id,
                p_mastery=concept.default_p_init,
                p_transit=concept.default_p_transit,
                p_guess=concept.default_p_guess,
                p_slip=concept.default_p_slip,
                leitner_box=1,
                assessment_state="IN_PROGRESS",
                formal_attempt_count=0,
            )
            self.db.add(mastery_record)
            self.db.flush()

        prior_p = mastery_record.p_mastery
        bkt_res = BKTEngine.update(
            prior=prior_p,
            is_correct=backend_is_correct,
            p_transit=mastery_record.p_transit,
            p_guess=mastery_record.p_guess,
            p_slip=mastery_record.p_slip,
        )

        # 7. Leitner Spaced-Repetition Update (Strictly backend binary observation)
        leitner_res = LeitnerScheduler.calculate_update(
            concept_id=concept.id,
            current_box=mastery_record.leitner_box,
            is_correct=backend_is_correct,
            current_consecutive_correct=mastery_record.consecutive_correct or 0,
            now=eval_time,
        )

        # 8. Apply State Mutations & Progress Assessment State
        mastery_record.p_mastery = bkt_res.posterior
        mastery_record.leitner_box = leitner_res.new_box
        mastery_record.consecutive_correct = leitner_res.consecutive_correct
        mastery_record.last_reviewed_at = leitner_res.last_reviewed_at
        mastery_record.next_review_due = leitner_res.next_review_due
        
        # Advance assessment state (UNASSESSED -> IN_PROGRESS -> ASSESSED)
        mastery_record.formal_attempt_count = (mastery_record.formal_attempt_count or 0) + 1
        mastery_record.last_assessed_at = eval_time
        mastery_record.assessment_state = "ASSESSED" if mastery_record.formal_attempt_count >= 2 else "IN_PROGRESS"
        mastery_record.last_reviewed_at = leitner_res.last_reviewed_at
        mastery_record.next_review_due = leitner_res.next_review_due

        new_sequence = (session.attempt_count or 0) + 1
        session.attempt_count = new_sequence

        # Create attempt record with full audit trail
        attempt = QuestionAttempt(
            session_id=session.id,
            learner_id=submission.learner_id,
            question_id=question.id,
            concept_id=concept.id,
            sequence_number=new_sequence,
            student_answer=submission.student_answer,
            reasoning_transcript=submission.reasoning_transcript,
            is_correct=backend_is_correct,
            reasoning_quality=diagnosis.reasoning_quality.value,
            detected_misconceptions=diagnosis.detected_misconceptions,
            evidence=diagnosis.reasoning_evidence,
            recommended_intervention=diagnosis.recommended_intervention,
            diagnosis_provider=diagnosis.diagnosis_provider,
            p_mastery_prior=bkt_res.prior,
            p_mastery_posterior=bkt_res.posterior,
            p_transit_used=bkt_res.p_transit,
            p_guess_used=bkt_res.p_guess,
            p_slip_used=bkt_res.p_slip,
            created_at=eval_time,
        )
        self.db.add(attempt)

        # 7. Adaptive Next Question Selection
        # Collect all questions attempted in this session to prevent repetition
        attempted_qids = [
            a.question_id
            for a in self.db.query(QuestionAttempt.question_id)
            .filter(QuestionAttempt.session_id == session.id)
            .all()
        ]
        attempted_qids.append(question.id)

        first_detected_misc = (
            diagnosis.detected_misconceptions[0] if diagnosis.detected_misconceptions else None
        )
        next_question_rec = self.selector.select_next_question(
            learner_id=submission.learner_id,
            session_attempted_qids=attempted_qids,
            recent_misconception_id=first_detected_misc,
            now=eval_time,
        )

        if next_question_rec:
            session.current_question_id = next_question_rec.question_id
        else:
            session.status = "COMPLETED"
            session.completed_at = eval_time
            session.current_question_id = None

        # 8. Commit Single Atomic Transaction
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to commit learning loop attempt transaction: {e}")
            raise

        return AttemptResult(
            session_id=session.id,
            attempt_id=attempt.id,
            sequence_number=new_sequence,
            is_correct=diagnosis.is_correct,
            diagnosis=diagnosis,
            bkt_update={
                "prior": bkt_res.prior,
                "posterior": bkt_res.posterior,
                "delta": bkt_res.delta,
                "p_transit": bkt_res.p_transit,
                "p_guess": bkt_res.p_guess,
                "p_slip": bkt_res.p_slip,
            },
            leitner_update={
                "previous_box": leitner_res.previous_box,
                "new_box": leitner_res.new_box,
                "consecutive_correct": leitner_res.consecutive_correct,
                "next_review_due": leitner_res.next_review_due.isoformat(),
            },
            next_question=next_question_rec,
            session_status=session.status,
        )
