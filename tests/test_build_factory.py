from fastapi.testclient import TestClient

from buddy import db, main
from buddy.main import app


def setup_factory(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "factory-test.db")
    monkeypatch.setattr(main, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setenv("BUDDY_OWNER_TOKEN", "test-owner-token")


def headers():
    return {"Authorization": "Bearer test-owner-token"}


def test_factory_requires_owner_token(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/factory/projects")
        assert response.status_code == 401


def test_project_registration_and_build_run_lifecycle(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        project_response = client.post(
            "/api/factory/projects",
            headers=headers(),
            json={"name": "Buddy Computer Forge", "repository": "KrugercoinHF/buddy-computer-forge"},
        )
        assert project_response.status_code == 200
        project = project_response.json()
        assert project["status"] == "active"

        run_response = client.post(
            "/api/factory/runs",
            headers=headers(),
            json={"project_id": project["id"], "source_commit": "abc123", "environment": "local"},
        )
        assert run_response.status_code == 200
        run = run_response.json()
        assert run["status"] == "queued"

        start_response = client.post(f"/api/factory/runs/{run['id']}/start", headers=headers())
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "running"

        finish_response = client.post(
            f"/api/factory/runs/{run['id']}/finish",
            headers=headers(),
            json={"status": "succeeded", "summary": "Ledger lifecycle test", "test_report": "passed"},
        )
        assert finish_response.status_code == 200
        assert finish_response.json()["status"] == "succeeded"
        assert finish_response.json()["source_commit"] == "abc123"

        listed = client.get("/api/factory/runs", headers=headers())
        assert listed.status_code == 200
        assert len(listed.json()) == 1


def test_duplicate_repository_is_rejected(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    payload = {"name": "Project", "repository": "KrugercoinHF/buddy-computer-forge"}
    with TestClient(app) as client:
        first = client.post("/api/factory/projects", headers=headers(), json=payload)
        second = client.post("/api/factory/projects", headers=headers(), json=payload)
        assert first.status_code == 200
        assert second.status_code == 409


def test_invalid_build_environment_is_rejected(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        project = client.post(
            "/api/factory/projects", headers=headers(),
            json={"name": "Project", "repository": "owner/project"},
        ).json()
        response = client.post(
            "/api/factory/runs", headers=headers(),
            json={"project_id": project["id"], "environment": "production-shell"},
        )
        assert response.status_code == 400
