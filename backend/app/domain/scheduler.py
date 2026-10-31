from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class LeitnerScheduleResult:
    concept_id: str
    previous_box: int
    new_box: int
    consecutive_correct: int
    last_reviewed_at: datetime
    next_review_due: datetime
    is_due: bool
    urgency: float  # higher means more urgent (positive = overdue)


class LeitnerScheduler:
    """
    Standard Leitner Spaced-Repetition Scheduler (Boxes 1..5).
    Maintains revision intervals independent of BKT mastery probability.
    """

    # Box review intervals in hours (scaled cleanly for both testing and production)
    # Box 1: 1 day (24h)
    # Box 2: 3 days (72h)
    # Box 3: 7 days (168h)
    # Box 4: 14 days (336h)
    # Box 5: 30 days (720h)
    BOX_INTERVALS_HOURS: Dict[int, int] = {
        1: 24,
        2: 72,
        3: 168,
        4: 336,
        5: 720,
    }

    @classmethod
    def calculate_update(
        cls,
        concept_id: str,
        current_box: int,
        is_correct: bool,
        current_consecutive_correct: int = 0,
        now: Optional[datetime] = None,
    ) -> LeitnerScheduleResult:
        """
        Updates the Leitner box and schedules the next review date.
        - Correct answer: advances box up to 5, increments consecutive count.
        - Incorrect answer: resets box to 1 (remediation), resets consecutive count to 0.
        """
        eval_time = now or datetime.now(timezone.utc)
        safe_box = max(1, min(5, current_box))

        if is_correct:
            new_box = min(5, safe_box + 1)
            consecutive = current_consecutive_correct + 1
        else:
            new_box = 1  # Standard Leitner resets to Box 1 for immediate relearning
            consecutive = 0

        interval_hours = cls.BOX_INTERVALS_HOURS.get(new_box, 24)
        next_due = eval_time + timedelta(hours=interval_hours)

        return LeitnerScheduleResult(
            concept_id=concept_id,
            previous_box=safe_box,
            new_box=new_box,
            consecutive_correct=consecutive,
            last_reviewed_at=eval_time,
            next_review_due=next_due,
            is_due=False,
            urgency=0.0,
        )

    @classmethod
    def evaluate_urgency(
        cls,
        next_review_due: Optional[datetime],
        now: Optional[datetime] = None,
    ) -> tuple[bool, float]:
        """
        Evaluates whether a concept is currently due for review and computes urgency.
        Urgency > 0 indicates overdue hours.
        If never reviewed (next_review_due is None), it is considered due with high baseline urgency.
        """
        eval_time = now or datetime.now(timezone.utc)
        if next_review_due is None:
            return True, 100.0  # High priority for initial review

        # Ensure timezone-aware comparison
        if next_review_due.tzinfo is None:
            next_review_due = next_review_due.replace(tzinfo=timezone.utc)

        diff_seconds = (eval_time - next_review_due).total_seconds()
        diff_hours = diff_seconds / 3600.0

        is_due = diff_hours >= 0.0
        urgency = max(0.0, diff_hours) if is_due else -abs(diff_hours)
        return is_due, round(urgency, 2)

