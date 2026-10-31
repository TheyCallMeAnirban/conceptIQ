import logging
from typing import Optional, List, Union
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from pymongo.database import Database

from backend.app.models import (
    Learner,
    Concept,
    Question,
    Misconception,
    ConceptMastery,
    AssessmentSession,
    QuestionAttempt,
)
from backend.app.core.mongo_repo import MongoRepository, MongoEntity
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
    Compatible with both SQLite Session and MongoDB Database/MongoRepository.
    """

    def __init__(
        self,
        db: Union[Session, Database, MongoRepository],
        diagnostician: Optional[LLMDiagnostician] = None,
    ):
        if isinstance(db, MongoRepository):
            self.repo = db
            self.is_mongo = True
        elif isinstance(db, Database):
            self.repo = MongoRepository(db)
            self.is_mongo = True
        else:
            self.db = db
            self.is_mongo = False

        self.diagnostician = diagnostician or LLMDiagnostician()
        self.selector = QuestionSelector(self.repo if self.is_mongo else self.db)

    def process_attempt(self, submission: AttemptSubmission) -> AttemptResult:
        """
        Executes one full turn in the adaptive learning loop atomically.
        """
        eval_time = datetime.now(timezone.utc)

        # 1. Validate Session, Learner, and Question
        if self.is_mongo:
            session = self.repo.get_session(submission.session_id)
            if not session or session.learner_id != submission.learner_id:
                raise ValueError(f"Active session {submission.session_id} not found for learner {submission.learner_id}")
            question = self.repo.get_question(submission.question_id)
            if not question:
                raise ValueError(f"Question {submission.question_id} not found")
            concept = self.repo.get_concept(question.concept_id)
            if not concept:
                raise ValueError(f"Concept {question.concept_id} not found")
            existing_attempt = self.repo.get_attempt_by_session_and_question(session.id, question.id)
        else:
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
            existing_attempt = (
                self.db.query(QuestionAttempt)
                .filter(
                    QuestionAttempt.session_id == session.id,
                    QuestionAttempt.question_id == question.id,
                )
                .first()
            )

        # 2. Duplicate Submission Check (Prevent double BKT transitions or duplicate attempts)
        if existing_attempt:
            raise ValueError(f"Question {question.id} has already been attempted in session {session.id}.")

        # 3. Deterministic Backend Answer Evaluation (Sole authority for correctness)
        backend_is_correct = AnswerEvaluator.evaluate(
            expected=question.correct_answer,
            submitted=submission.student_answer,
            question_type=question.question_type,
        )

        # 4. Query known misconceptions catalog for this question
        known_misc_ids = question.known_misconceptions or []
        if self.is_mongo:
            known_misc_records = self.repo.get_misconceptions_by_ids(known_misc_ids)
        else:
            known_misc_records = (
                self.db.query(Misconception)
                .filter(Misconception.id.in_(known_misc_ids))
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
        if self.is_mongo:
            mastery_record = self.repo.get_mastery(submission.learner_id, concept.id)
            if not mastery_record:
                mastery_data = {
                    "learner_id": submission.learner_id,
                    "concept_id": concept.id,
                    "p_mastery": concept.default_p_init,
                    "p_transit": concept.default_p_transit,
                    "p_guess": concept.default_p_guess,
                    "p_slip": concept.default_p_slip,
                    "leitner_box": 1,
                    "consecutive_correct": 0,
                    "assessment_state": "IN_PROGRESS",
                    "formal_attempt_count": 0,
                }
                mastery_record = self.repo.save_mastery(mastery_data)
        else:
            mastery_record = (
                self.db.query(ConceptMastery)
                .filter(
                    ConceptMastery.learner_id == submission.learner_id,
                    ConceptMastery.concept_id == concept.id,
                )
                .first()
            )
            if not mastery_record:
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
            current_box=mastery_record.leitner_box or 1,
            is_correct=backend_is_correct,
            current_consecutive_correct=mastery_record.consecutive_correct or 0,
            now=eval_time,
        )

        # 8. Apply State Mutations & Progress Assessment State
        formal_count = (mastery_record.formal_attempt_count or 0) + 1
        new_assessment_state = "ASSESSED" if formal_count >= 2 else "IN_PROGRESS"

        if self.is_mongo:
            updated_mastery_dict = mastery_record.to_dict()
            updated_mastery_dict.update({
                "p_mastery": bkt_res.posterior,
                "leitner_box": leitner_res.new_box,
                "consecutive_correct": leitner_res.consecutive_correct,
                "last_reviewed_at": leitner_res.last_reviewed_at,
                "next_review_due": leitner_res.next_review_due,
                "formal_attempt_count": formal_count,
                "last_assessed_at": eval_time,
                "assessment_state": new_assessment_state,
            })
            self.repo.save_mastery(updated_mastery_dict)
        else:
            mastery_record.p_mastery = bkt_res.posterior
            mastery_record.leitner_box = leitner_res.new_box
            mastery_record.consecutive_correct = leitner_res.consecutive_correct
            mastery_record.last_reviewed_at = leitner_res.last_reviewed_at
            mastery_record.next_review_due = leitner_res.next_review_due
            mastery_record.formal_attempt_count = formal_count
            mastery_record.last_assessed_at = eval_time
            mastery_record.assessment_state = new_assessment_state

        new_sequence = (session.attempt_count or 0) + 1
        attempt_id = str(uuid.uuid4())

        attempt_dict = {
            "id": attempt_id,
            "session_id": session.id,
            "learner_id": submission.learner_id,
            "question_id": question.id,
            "concept_id": concept.id,
            "sequence_number": new_sequence,
            "student_answer": submission.student_answer,
            "reasoning_transcript": submission.reasoning_transcript,
            "is_correct": backend_is_correct,
            "reasoning_quality": diagnosis.reasoning_quality.value,
            "detected_misconceptions": diagnosis.detected_misconceptions,
            "evidence": diagnosis.reasoning_evidence,
            "recommended_intervention": diagnosis.recommended_intervention,
            "diagnosis_provider": diagnosis.diagnosis_provider,
            "p_mastery_prior": bkt_res.prior,
            "p_mastery_posterior": bkt_res.posterior,
            "p_transit_used": bkt_res.p_transit,
            "p_guess_used": bkt_res.p_guess,
            "p_slip_used": bkt_res.p_slip,
            "created_at": eval_time,
        }

        if self.is_mongo:
            self.repo.save_attempt(attempt_dict)
            attempted_qids = self.repo.get_session_attempted_qids(session.id)
            if question.id not in attempted_qids:
                attempted_qids.append(question.id)
        else:
            attempt = QuestionAttempt(**attempt_dict)
            self.db.add(attempt)
            attempted_qids = [
                a.question_id
                for a in self.db.query(QuestionAttempt.question_id)
                .filter(QuestionAttempt.session_id == session.id)
                .all()
            ]
            attempted_qids.append(question.id)

        # 9. Adaptive Next Question Selection
        first_detected_misc = (
            diagnosis.detected_misconceptions[0] if diagnosis.detected_misconceptions else None
        )
        next_question_rec = self.selector.select_next_question(
            learner_id=submission.learner_id,
            session_attempted_qids=attempted_qids,
            recent_misconception_id=first_detected_misc,
            now=eval_time,
        )

        session_status = "ACTIVE"
        if next_question_rec:
            next_qid = next_question_rec.question_id
        else:
            session_status = "COMPLETED"
            next_qid = None

        if self.is_mongo:
            session_dict = session.to_dict()
            session_dict.update({
                "attempt_count": new_sequence,
                "current_question_id": next_qid,
                "status": session_status,
                "completed_at": eval_time if session_status == "COMPLETED" else None,
            })
            self.repo.save_session(session_dict)
        else:
            session.attempt_count = new_sequence
            session.current_question_id = next_qid
            session.status = session_status
            if session_status == "COMPLETED":
                session.completed_at = eval_time
            self.db.commit()

        return AttemptResult(
            session_id=session.id,
            attempt_id=attempt_id,
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
            session_status=session_status,
        )
