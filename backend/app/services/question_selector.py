from typing import List, Optional, Dict, Set, Union, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pymongo.database import Database

from backend.app.models import (
    Concept,
    ConceptPrerequisite,
    Question,
    ConceptMastery,
    QuestionAttempt,
)
from backend.app.core.mongo_repo import MongoRepository, MongoEntity
from backend.app.domain.dag import ConceptDAGValidator
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

    Compatible with both SQLite Session and MongoDB Database/MongoRepository.
    """

    PREREQUISITE_MASTERY_THRESHOLD = 0.50
    MASTERY_CEILING_FOR_LEARNING = 0.85

    def __init__(self, db: Union[Session, Database, MongoRepository]):
        if isinstance(db, MongoRepository):
            self.repo = db
            self.is_mongo = True
        elif isinstance(db, Database):
            self.repo = MongoRepository(db)
            self.is_mongo = True
        else:
            self.db = db
            self.is_mongo = False

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
        if self.is_mongo:
            concepts_list = self.repo.get_all_concepts()
            all_concepts = {c.id: c for c in concepts_list}
            all_edges = self.repo.get_all_prerequisites()
        else:
            all_concepts = {c.id: c for c in self.db.query(Concept).all()}
            all_edges = [(cp.concept_id, cp.prerequisite_id) for cp in self.db.query(ConceptPrerequisite).all()]
        prereq_map = ConceptDAGValidator.get_prerequisites_map(all_edges)

        # 2. Load learner mastery and Leitner states
        if self.is_mongo:
            masteries = {m.concept_id: m for m in self.repo.get_learner_masteries(learner_id)}
        else:
            masteries = {
                m.concept_id: m
                for m in self.db.query(ConceptMastery).filter(ConceptMastery.learner_id == learner_id).all()
            }

        # Helper to get mastery probability
        def get_mastery(cid: str) -> float:
            m = masteries.get(cid)
            return m.p_mastery if m else all_concepts[cid].default_p_init

        # 3. Strategy 1: Check for Prerequisite Remediation
        for concept_id, concept in all_concepts.items():
            curr_mastery = get_mastery(concept_id)
            prereqs = prereq_map.get(concept_id, set())

            for pid in prereqs:
                p_mastery = get_mastery(pid)
                if p_mastery < self.PREREQUISITE_MASTERY_THRESHOLD:
                    if self.is_mongo:
                        has_attempted_child = self.repo.has_attempted_concept(learner_id, concept_id)
                    else:
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
                            return self._build_recommendation(candidate, rationale)

        # 4. Strategy 2: Spaced Repetition Due Review
        for cid, m in masteries.items():
            if m.next_review_due:
                due_time = m.next_review_due
                if due_time.tzinfo is None:
                    due_time = due_time.replace(tzinfo=timezone.utc)
                if due_time <= eval_time:
                    candidate = self._pick_question_for_concept(
                        cid, target_diff=0.5, excluded_qids=attempted_qids
                    )
                    if candidate:
                        rationale = SelectionRationale(
                            question_id=candidate.id,
                            target_concept_id=cid,
                            target_concept_name=all_concepts[cid].name,
                            current_mastery=round(m.p_mastery, 4),
                            prerequisite_status="Prerequisites previously validated during initial mastery.",
                            selection_reason="SPACED_REPETITION_DUE",
                            recommended_difficulty=0.5,
                            rationale_details=f"Concept is due for Leitner Box {m.leitner_box} spaced-repetition review.",
                        )
                        return self._build_recommendation(candidate, rationale)

        # 5. Strategy 3: Frontier Advancement
        # Find active frontier concepts whose prerequisites are all satisfied (>= 0.50)
        # and whose own mastery is below ceiling (< 0.85).
        frontier_concepts = []
        for cid, concept in all_concepts.items():
            m_score = get_mastery(cid)
            if m_score >= self.MASTERY_CEILING_FOR_LEARNING:
                continue

            prereqs = prereq_map.get(cid, set())
            prereqs_met = all(get_mastery(p) >= self.PREREQUISITE_MASTERY_THRESHOLD for p in prereqs)
            if prereqs_met:
                frontier_concepts.append((cid, m_score, prereqs))

        if not frontier_concepts:
            # All available concepts mastered
            return None

        # Pick the frontier concept with lowest mastery to advance next
        frontier_concepts.sort(key=lambda x: x[1])
        target_cid, target_mastery, target_prereqs = frontier_concepts[0]
        target_concept = all_concepts[target_cid]

        # Difficulty calibration based on target mastery
        if target_mastery < 0.35:
            target_diff = 0.3
            reason = "CONCEPT_CALIBRATION_EASY"
        elif target_mastery < 0.70:
            target_diff = 0.5
            reason = "CONCEPT_PROGRESSION_MEDIUM"
        else:
            target_diff = 0.75
            reason = "CONCEPT_MASTERY_CHALLENGE"

        candidate = self._pick_question_for_concept(
            target_cid, target_diff=target_diff, excluded_qids=attempted_qids
        )
        if candidate:
            prereq_names = [all_concepts[p].name for p in target_prereqs]
            prereq_text = (
                f"Prerequisites satisfied: {', '.join(prereq_names)}."
                if prereq_names
                else "Prerequisites satisfied: None (Root concept)."
            )

            rationale = SelectionRationale(
                question_id=candidate.id,
                target_concept_id=target_cid,
                target_concept_name=target_concept.name,
                current_mastery=round(target_mastery, 4),
                prerequisite_status=prereq_text,
                selection_reason=reason,
                recommended_difficulty=target_diff,
                rationale_details=f"Advancing along learning frontier. Current mastery is {target_mastery:.2f}. Selected item matching target difficulty {target_diff:.2f}.",
            )
            return self._build_recommendation(candidate, rationale)

        return None

    def _pick_question_for_concept(
        self, concept_id: str, target_diff: float, excluded_qids: Set[str]
    ) -> Optional[Any]:
        """
        Finds the unattempted question in concept_id closest to target_diff.
        """
        if self.is_mongo:
            available = [
                q for q in self.repo.get_questions_by_concept(concept_id)
                if q.id not in excluded_qids
            ]
        else:
            available = (
                self.db.query(Question)
                .filter(
                    Question.concept_id == concept_id,
                    ~Question.id.in_(excluded_qids) if excluded_qids else True,
                )
                .all()
            )
        if not available:
            return None

        # Sort by distance from target difficulty
        available.sort(key=lambda q: abs(q.difficulty - target_diff))
        return available[0]

    def _build_recommendation(
        self, question: Any, rationale: SelectionRationale
    ) -> QuestionRecommendation:
        return QuestionRecommendation(
            question_id=question.id,
            title=question.title,
            problem_text=question.problem_text,
            code_snippet=question.code_snippet,
            question_type=question.question_type,
            options=question.options,
            difficulty=question.difficulty,
            target_concept_id=rationale.target_concept_id,
            target_concept_name=rationale.target_concept_name,
            rationale=rationale,
        )
