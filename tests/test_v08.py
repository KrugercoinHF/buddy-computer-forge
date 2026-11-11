from fastapi.testclient import TestClient

from buddy.main import app
from buddy.db import init_db


def test_health_is_public(monkeypatch, tmp_path):
    monkeypatch.setenv("BUDDY_DB_PATH", str(tmp_path / "test.db"))
    init_db()
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_owner_routes_require_configured_token(monkeypatch, tmp_path):
    monkeypatch.setenv("BUDDY_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("BUDDY_OWNER_TOKEN", raising=False)
    init_db()
    with TestClient(app) as client:
        response = client.get("/api/overview")
        assert response.status_code == 503


def test_workspace_path_rejects_traversal(tmp_path, monkeypatch):
    from buddy.config import WORKSPACE_ROOT
    from buddy.workspace import safe_workspace_path

    monkeypatch.setattr("buddy.workspace.WORKSPACE_ROOT", tmp_path)
    try:
        safe_workspace_path("../outside.txt")
        assert False, "expected path traversal to be rejected"
    except ValueError:
        pass
