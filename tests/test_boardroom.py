import pytest
from fastapi.testclient import TestClient

import boardroom_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BOARDROOM_DB_PATH", str(tmp_path / "boardroom.sqlite3"))
    monkeypatch.setenv("BOARDROOM_OWNER_TOKEN", "test-owner-token")
    with TestClient(boardroom_app.app) as test_client:
        yield test_client


def test_health_and_full_agent_directory(client):
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["agent_directory_size"] == 100
    assert health["external_models_connected"] is False
    agents = client.get("/api/agents").json()
    assert agents["total"] == 100
    assert len(agents["agents"]) == 100
    assert agents["agents"][0]["short_name"] == "CEO"


def test_meeting_simulation_creates_minutes_and_gated_proposals(client):
    created = client.post("/api/meetings", json={
        "topic": "Assess controlled beta readiness",
        "context": "Keep execution disabled and require owner approval.",
        "participant_count": 20,
    })
    assert created.status_code == 200
    meeting_id = created.json()["id"]
    result = client.post(f"/api/meetings/{meeting_id}/run")
    assert result.status_code == 200
    meeting = result.json()
    assert meeting["status"] == "completed"
    assert len(meeting["contributions"]) == 20
    assert meeting["minutes"]["key_themes"]
    assert len(meeting["proposals"]) == 3
    assert all(p["status"] == "pending_owner_approval" for p in meeting["proposals"])
    assert all(p["execution"] == "not_executed" for p in meeting["proposals"])


def test_owner_decision_is_required_and_never_executes(client):
    created = client.post("/api/meetings", json={"topic": "Review deployment readiness", "participant_count": 5}).json()
    meeting = client.post(f"/api/meetings/{created['id']}/run").json()
    proposal = meeting["proposals"][0]
    endpoint = f"/api/meetings/{created['id']}/proposals/{proposal['id']}/decision"
    payload = {"decision": "approve", "note": "Approved for planning only."}
    assert client.post(endpoint, json=payload).status_code == 401
    response = client.post(endpoint, json=payload, headers={"Authorization": "Bearer test-owner-token"})
    assert response.status_code == 200
    assert response.json()["proposal"]["status"] == "owner_approved"
    assert response.json()["proposal"]["execution"] == "not_executed"
    assert "No task" in response.json()["message"]


def test_invalid_agent_selection_is_rejected(client):
    response = client.post("/api/meetings", json={"topic": "Test invalid agent", "agent_ids": ["AG-999"]})
    assert response.status_code == 422
