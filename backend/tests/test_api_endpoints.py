import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["docs"] == "/docs"


def test_list_concepts_endpoint():
    res = client.get("/api/v1/concepts")
    assert res.status_code == 200
    concepts = res.json()
    assert len(concepts) >= 9
    assert any(c["id"] == "POINTER_ARITHMETIC" for c in concepts)


def test_list_learners_endpoint():
    res = client.get("/api/v1/learners")
    assert res.status_code == 200
    learners = res.json()
    assert len(learners) >= 1
    assert any(l["id"] == "learner_gate_01" for l in learners)


def test_start_and_submit_session_via_rest_api():
    # 1. Start or resume session
    start_res = client.post("/api/v1/sessions/start", json={"learner_id": "learner_gate_01"})
    assert start_res.status_code == 200
    session_data = start_res.json()
    assert "session_id" in session_data
    session_id = session_data["session_id"]

    # 2. Submit attempt via REST API
    submit_res = client.post(
        "/api/v1/sessions/submit",
        json={
            "learner_id": "learner_gate_01",
            "session_id": session_id,
            "question_id": "Q_DATA_01",
            "student_answer": "Option B",
            "reasoning_transcript": "sizeof int is 4, &x is pointer 8 bytes, so 4 8.",
        },
    )
    # Could be 200 or 400 if already attempted
    assert submit_res.status_code in [200, 400]
    if submit_res.status_code == 200:
        result_data = submit_res.json()
        assert result_data["is_correct"] is True
        assert "bkt_update" in result_data
        assert "next_question" in result_data


def test_analytics_misconceptions_endpoint():
    res = client.get("/api/v1/analytics/misconceptions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

