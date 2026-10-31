from typing import List, Optional, Dict, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models import (
    Concept,
    ConceptPrerequisite,
    Question,
    ConceptMastery,
    QuestionAttempt,
)
from backend.app.domain.dag import ConceptDAGValidator
from backend.app.domain.scheduler import LeitnerScheduler
from backend.app.domain.schemas.selection import (
    SelectionRationale,
    QuestionRecommendation,
)


class QuestionSelector:
    """
    Adaptive Decision Engine.
    Deterministically selects the next question based on:
    - Current BKT mastery probability
    - Prerequisite DAG readiness
    - Misconception remediation signals
    - Leitner review urgency
    - Question difficulty calibration
    - Session attempt history (duplicate avoidance)
    """

    PREREQUISITE_MASTERY_THRESHOLD = 0.50
    MASTERY_CEILING_FOR_LEARNING = 0.85

    def __init__(self, db: Session):
        self.db = db

    def select_next_question(
        self,
        learner_id: str,
        session_attempted_qids: Optional[List[str]] = None,
        recent_misconception_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Optional[QuestionRecommendation]:
        """
        Determines the optimal next question and generates a transparent,
        deterministic selection rationale.
        """
        eval_time = now or datetime.now(timezone.utc)
        attempted_qids: Set[str] = set(session_attempted_qids or [])

        # 1. Load curriculum DAG and prerequisites
        all_concepts = {c.id: c for c in self.db.query(Concept).all()}
        all_edges = [(cp.concept_id, cp.prerequisite_id) for cp in self.db.query(ConceptPrerequisite).all()]
        prereq_map = ConceptDAGValidator.get_prerequisites_map(all_edges)

        # 2. Load learner mastery and Leitner states
        masteries: Dict[str, ConceptMastery] = {
            m.concept_id: m
            for m in self.db.query(ConceptMastery).filter(ConceptMastery.learner_id == learner_id).all()
        }

        # Helper to get mastery probability
        def get_mastery(cid: str) -> float:
            m = masteries.get(cid)
            return m.p_mastery if m else all_concepts[cid].default_p_init

        # 3. Strategy 1: Check for Prerequisite Remediation
        # If learner is struggling on a concept (mastery < 0.40) or triggered a misconception,
        # verify if any prerequisite is below threshold.
        for concept_id, concept in all_concepts.items():
            curr_mastery = get_mastery(concept_id)
            prereqs = prereq_map.get(concept_id, set())

            for pid in prereqs:
                p_mastery = get_mastery(pid)
                if p_mastery < self.PREREQUISITE_MASTERY_THRESHOLD:
                    # Found an unmastered prerequisite! Check if learner has attempted child concept
                    has_attempted_child = (
                        self.db.query(QuestionAttempt)
                        .filter(
                            QuestionAttempt.learner_id == learner_id,
                            QuestionAttempt.concept_id == concept_id,
                        )
                        .first()
                        is not None
                    )
                    if has_attempted_child or recent_misconception_id:
                        # Remediate the prerequisite first
                        candidate = self._pick_question_for_concept(
                            pid, target_diff=0.35, excluded_qids=attempted_qids
                        )
                        if candidate:
                            rationale = SelectionRationale(
                                question_id=candidate.id,
                                target_concept_id=pid,
                                target_concept_name=all_concepts[pid].name,
                                current_mastery=round(p_mastery, 4),
                                prerequisite_status=f"Remediation triggered: Dependent concept '{concept.name}' failed because prerequisite '{all_concepts[pid].name}' mastery is only {p_mastery:.2f} (< {self.PREREQUISITE_MASTERY_THRESHOLD:.2f}).",
                                selection_reason="PREREQUISITE_REMEDIATION",
                                recommended_difficulty=0.35,
                                rationale_details=f"Routing student backward in the concept DAG to remediate foundational prerequisite '{all_concepts[pid].name}' before re-attempting '{concept.name}'.",
                            )
                            return self._build_recommendation(candidate, all_concepts[pid], rationale)

        # 4. Strategy 2: Spaced Repetition Due (Leitner Review)
        due_concepts = []
        for cid, m in masteries.items():
            is_due, urgency = LeitnerScheduler.evaluate_urgency(m.next_review_due, now=eval_time)
            if is_due and m.p_mastery >= self.PREREQUISITE_MASTERY_THRESHOLD:
                due_concepts.append((urgency, cid, m))

        due_concepts.sort(key=lambda x: x[0], reverse=True)  # most urgent first
        for urgency, cid, m in due_concepts:
            # Pick a review question not yet attempted in this session
            candidate = self._pick_question_for_concept(
                cid, target_diff=min(0.7, m.p_mastery), excluded_qids=attempted_qids
            )
            if candidate:
                rationale = SelectionRationale(
                    question_id=candidate.id,
                    target_concept_id=cid,
                    target_concept_name=all_concepts[cid].name,
                    current_mastery=round(m.p_mastery, 4),
                    prerequisite_status="Prerequisites verified.",
                    selection_reason="SPACED_REPETITION_DUE",
                    recommended_difficulty=round(min(0.7, m.p_mastery), 2),
                    rationale_details=f"Concept '{all_concepts[cid].name}' is due for spaced review in Leitner Box {m.leitner_box} (urgency score: {urgency:.1f}h).",
                )
                return self._build_recommendation(candidate, all_concepts[cid], rationale)

        # 5. Strategy 3: Frontier Adaptive Progression
        # Find concepts whose prerequisites are satisfied (>= 0.50), but concept itself < 0.85
        topological_order = ConceptDAGValidator.validate_and_sort(
            list(all_concepts.keys()), all_edges
        )

        for cid in topological_order:
            curr_mastery = get_mastery(cid)
            prereqs = prereq_map.get(cid, set())

            # Check if all prerequisites are satisfied
            prereqs_satisfied = True
            for pid in prereqs:
                if get_mastery(pid) < self.PREREQUISITE_MASTERY_THRESHOLD:
                    prereqs_satisfied = False
                    break

            if prereqs_satisfied and curr_mastery < self.MASTERY_CEILING_FOR_LEARNING:
                # Calibrate target difficulty based on current mastery
                if curr_mastery < 0.40:
                    target_diff = 0.30
                    reason = "CONCEPT_CALIBRATION_EASY"
                elif curr_mastery < 0.70:
                    target_diff = 0.50
                    reason = "CONCEPT_PROGRESSION_MEDIUM"
                else:
                    target_diff = 0.75
                    reason = "DIFFICULTY_ESCALATION_HARD"

                candidate = self._pick_question_for_concept(
                    cid, target_diff=target_diff, excluded_qids=attempted_qids
                )
                if candidate:
                    prereq_names = [all_concepts[p].name for p in prereqs] or ["None (Root concept)"]
                    rationale = SelectionRationale(
                        question_id=candidate.id,
                        target_concept_id=cid,
                        target_concept_name=all_concepts[cid].name,
                        current_mastery=round(curr_mastery, 4),
                        prerequisite_status=f"Prerequisites satisfied: {', '.join(prereq_names)}.",
                        selection_reason=reason,
                        recommended_difficulty=target_diff,
                        rationale_details=f"Advancing along learning frontier. Current mastery is {curr_mastery:.2f}. Selected item matching target difficulty {target_diff:.2f}.",
                    )
                    return self._build_recommendation(candidate, all_concepts[cid], rationale)

        # 6. Fallback: If all unattempted questions in learning frontier are exhausted,
        # find any unattempted question across the entire bank
        fallback_q = (
            self.db.query(Question)
            .filter(~Question.id.in_(attempted_qids) if attempted_qids else True)
            .order_by(Question.difficulty.asc())
            .first()
        )
        if fallback_q:
            cid = fallback_q.concept_id
            curr_mastery = get_mastery(cid)
            rationale = SelectionRationale(
                question_id=fallback_q.id,
                target_concept_id=cid,
                target_concept_name=all_concepts[cid].name,
                current_mastery=round(curr_mastery, 4),
                prerequisite_status="Curriculum breadth selection.",
                selection_reason="CURRICULUM_EXPANSION",
                recommended_difficulty=fallback_q.difficulty,
                rationale_details=f"Selected unattempted question {fallback_q.id} to expand curriculum coverage.",
            )
            return self._build_recommendation(fallback_q, all_concepts[cid], rationale)

        return None

    def _pick_question_for_concept(
        self,
        concept_id: str,
        target_diff: float,
        excluded_qids: Set[str],
    ) -> Optional[Question]:
        """
        Picks the question for a given concept closest to target_diff,
        excluding already-attempted questions.
        """
        query = self.db.query(Question).filter(Question.concept_id == concept_id)
        if excluded_qids:
            query = query.filter(~Question.id.in_(excluded_qids))

        candidates = query.all()
        if not candidates:
            return None

        # Pick the candidate minimizing |difficulty - target_diff|
        return min(candidates, key=lambda q: abs(q.difficulty - target_diff))

    def _build_recommendation(
        self,
        question: Question,
        concept: Concept,
        rationale: SelectionRationale,
    ) -> QuestionRecommendation:
        return QuestionRecommendation(
            question_id=question.id,
            title=question.title,
            problem_text=question.problem_text,
            code_snippet=question.code_snippet,
            question_type=question.question_type,
            options=question.options,
            difficulty=question.difficulty,
            target_concept_id=concept.id,
            target_concept_name=concept.name,
            rationale=rationale,
        )

