from datetime import datetime, timedelta, timezone
from backend.app.domain.scheduler import LeitnerScheduler


def test_leitner_box_advancement_on_correct():
    """Correct answer should advance box from 1 up to max 5."""
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    
    # Box 1 -> 2
    r1 = LeitnerScheduler.calculate_update("C1", current_box=1, is_correct=True, now=now)
    assert r1.previous_box == 1
    assert r1.new_box == 2
    assert r1.consecutive_correct == 1
    assert r1.next_review_due == now + timedelta(hours=72)

    # Box 4 -> 5
    r2 = LeitnerScheduler.calculate_update("C1", current_box=4, is_correct=True, current_consecutive_correct=3, now=now)
    assert r2.previous_box == 4
    assert r2.new_box == 5
    assert r2.consecutive_correct == 4
    assert r2.next_review_due == now + timedelta(hours=720)

    # Box 5 stays at 5 (capped)
    r3 = LeitnerScheduler.calculate_update("C1", current_box=5, is_correct=True, current_consecutive_correct=4, now=now)
    assert r3.new_box == 5
    assert r3.consecutive_correct == 5


def test_leitner_reset_on_incorrect():
    """Incorrect answer resets box to Box 1 and zeros consecutive correct counter."""
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    res = LeitnerScheduler.calculate_update("C1", current_box=4, is_correct=False, current_consecutive_correct=3, now=now)
    
    assert res.previous_box == 4
    assert res.new_box == 1
    assert res.consecutive_correct == 0
    assert res.next_review_due == now + timedelta(hours=24)


def test_leitner_urgency_evaluation():
    """Verify overdue, future, and never-reviewed item urgencies."""
    now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)

    # Never reviewed
    is_due, urgency = LeitnerScheduler.evaluate_urgency(None, now=now)
    assert is_due is True
    assert urgency == 100.0

    # Overdue by 5 hours
    due_past = now - timedelta(hours=5)
    is_due, urgency = LeitnerScheduler.evaluate_urgency(due_past, now=now)
    assert is_due is True
    assert urgency == 5.0

    # Due in future (10 hours ahead)
    due_future = now + timedelta(hours=10)
    is_due, urgency = LeitnerScheduler.evaluate_urgency(due_future, now=now)
    assert is_due is False
    assert urgency == -10.0

