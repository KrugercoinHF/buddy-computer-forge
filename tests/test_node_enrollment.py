import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from buddy import db, main
from buddy.main import app


def setup_security(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "security-test.db")
    monkeypatch.setattr(main, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setenv("BUDDY_OWNER_TOKEN", "test-owner-token")


def owner_headers():
    return {"Authorization": "Bearer test-owner-token"}


def node_headers(node_id, node_token):
    return {"X-Buddy-Node": node_id, "X-Buddy-Node-Token": node_token}


def create_enrollment(client, node_id="worker-01"):
    response = client.post(
        "/api/nodes/enrollments",
        headers=owner_headers(),
        json={"node_id": node_id, "name": "Test Worker", "ttl_minutes": 15},
    )
    assert response.status_code == 200
    return response.json()


def redeem_enrollment(client, enrollment_code):
    response = client.post(
        "/api/nodes/enroll",
        json={"enrollment_code": enrollment_code, "hostname": "test-host"},
    )
    assert response.status_code == 200
    return response.json()


def test_owner_can_issue_and_worker_can_redeem_enrollment(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        assert enrollment["node_id"] == "worker-01"
        assert enrollment["enrollment_code"]

        redeemed = redeem_enrollment(client, enrollment["enrollment_code"])
        assert redeemed["node_id"] == "worker-01"
        assert redeemed["node_token"]

        heartbeat = client.post(
            "/api/nodes/heartbeat",
            headers=node_headers(redeemed["node_id"], redeemed["node_token"]),
            json={"telemetry": {"cpu": 1}},
        )
        assert heartbeat.status_code == 200
        assert heartbeat.json()["status"] == "online"

        claim = client.post(
            "/api/tasks/claim",
            headers=node_headers(redeemed["node_id"], redeemed["node_token"]),
            json={},
        )
        assert claim.status_code == 200
        assert claim.json()["claimed"] is False


def test_enrollment_code_cannot_be_reused(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        first = redeem_enrollment(client, enrollment["enrollment_code"])
        assert first["node_id"] == "worker-01"

        reuse = client.post(
            "/api/nodes/enroll",
            json={"enrollment_code": enrollment["enrollment_code"]},
        )
        assert reuse.status_code == 410


def test_expired_enrollment_cannot_be_redeemed(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        db.execute(
            "UPDATE node_enrollments SET expires_at = ? WHERE id = ?",
            (past, enrollment["enrollment_id"]),
        )
        response = client.post(
            "/api/nodes/enroll",
            json={"enrollment_code": enrollment["enrollment_code"]},
        )
        assert response.status_code == 410


def test_missing_owner_token_cannot_issue_enrollment(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    monkeypatch.delenv("BUDDY_OWNER_TOKEN")
    with TestClient(app) as client:
        response = client.post(
            "/api/nodes/enrollments",
            json={"node_id": "worker-01", "name": "Test Worker"},
        )
        assert response.status_code == 503


def test_revoked_node_cannot_authenticate(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        redeemed = redeem_enrollment(client, enrollment["enrollment_code"])
        headers = node_headers(redeemed["node_id"], redeemed["node_token"])

        revoke = client.post(
            f"/api/nodes/{redeemed['node_id']}/revoke",
            headers=owner_headers(),
        )
        assert revoke.status_code == 200

        heartbeat = client.post("/api/nodes/heartbeat", headers=headers, json={})
        assert heartbeat.status_code == 401
        assert heartbeat.json()["detail"] == "node has been revoked"

        claim = client.post("/api/tasks/claim", headers=headers, json={})
        assert claim.status_code == 401

        result = client.post(
            "/api/tasks/result",
            headers=headers,
            json={"task_id": "missing", "exit_code": 0},
        )
        assert result.status_code == 401


def test_token_rotation_invalidates_previous_token(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        redeemed = redeem_enrollment(client, enrollment["enrollment_code"])
        old_headers = node_headers(redeemed["node_id"], redeemed["node_token"])

        rotated = client.post(
            f"/api/nodes/{redeemed['node_id']}/rotate-token",
            headers=owner_headers(),
        )
        assert rotated.status_code == 200
        new_token = rotated.json()["node_token"]
        assert new_token != redeemed["node_token"]

        old_heartbeat = client.post("/api/nodes/heartbeat", headers=old_headers, json={})
        assert old_heartbeat.status_code == 401

        new_headers = node_headers(redeemed["node_id"], new_token)
        new_heartbeat = client.post("/api/nodes/heartbeat", headers=new_headers, json={})
        assert new_heartbeat.status_code == 200


def test_invalid_node_token_is_rejected(monkeypatch, tmp_path):
    setup_security(monkeypatch, tmp_path)
    with TestClient(app) as client:
        enrollment = create_enrollment(client)
        redeemed = redeem_enrollment(client, enrollment["enrollment_code"])
        response = client.post(
            "/api/nodes/heartbeat",
            headers=node_headers(redeemed["node_id"], "invalid-token"),
            json={},
        )
        assert response.status_code == 401
