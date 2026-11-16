from fastapi.testclient import TestClient

from buddy import db, main
from buddy.main import app


def setup_factory(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "factory-test.db")
    monkeypatch.setattr(main, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setenv("BUDDY_OWNER_TOKEN", "test-owner-token")


def headers():
    return {"Authorization": "Bearer test-owner-token"}


def register_project(client, name="Project", repository="owner/project", status="active"):
    response = client.post(
        "/api/factory/projects",
        headers=headers(),
        json={"name": name, "repository": repository, "status": status},
    )
    assert response.status_code == 200
    return response.json()


def create_run(client, project_id, environment="local"):
    response = client.post(
        "/api/factory/runs",
        headers=headers(),
        json={"project_id": project_id, "source_commit": "abc123", "environment": environment},
    )
    assert response.status_code == 200
    return response.json()


def test_factory_requires_owner_token(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/factory/projects")
        assert response.status_code == 401


def test_project_registration_and_build_run_lifecycle(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        project = register_project(
            client,
            name="Buddy Computer Forge",
            repository="KrugercoinHF/buddy-computer-forge",
        )
        assert project["status"] == "active"

        run = create_run(client, project["id"])
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
        project = register_project(client)
        response = client.post(
            "/api/factory/runs", headers=headers(),
            json={"project_id": project["id"], "environment": "production-shell"},
        )
        assert response.status_code == 400


def test_inactive_project_cannot_create_run(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        for status in ("paused", "archived"):
            project = register_project(
                client,
                name=f"Inactive {status}",
                repository=f"owner/{status}",
                status=status,
            )
            response = client.post(
                "/api/factory/runs",
                headers=headers(),
                json={"project_id": project["id"]},
            )
            assert response.status_code == 409
            assert response.json()["detail"] == "project must be active to create a build run"


def test_unknown_project_cannot_create_run(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.post(
            "/api/factory/runs",
            headers=headers(),
            json={"project_id": "does-not-exist"},
        )
        assert response.status_code == 404


def test_only_queued_runs_can_start(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        project = register_project(client)
        run = create_run(client, project["id"])

        first_start = client.post(f"/api/factory/runs/{run['id']}/start", headers=headers())
        assert first_start.status_code == 200

        second_start = client.post(f"/api/factory/runs/{run['id']}/start", headers=headers())
        assert second_start.status_code == 409
        assert second_start.json()["detail"] == "only queued runs can be started"


def test_only_running_runs_can_finish(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        project = register_project(client)
        run = create_run(client, project["id"])

        early_finish = client.post(
            f"/api/factory/runs/{run['id']}/finish",
            headers=headers(),
            json={"status": "succeeded"},
        )
        assert early_finish.status_code == 409
        assert early_finish.json()["detail"] == "only running builds can be finished"

        client.post(f"/api/factory/runs/{run['id']}/start", headers=headers())
        finish = client.post(
            f"/api/factory/runs/{run['id']}/finish",
            headers=headers(),
            json={"status": "failed", "summary": "expected failure"},
        )
        assert finish.status_code == 200
        assert finish.json()["status"] == "failed"


def test_project_status_filter_and_run_limit(monkeypatch, tmp_path):
    setup_factory(monkeypatch, tmp_path)
    with TestClient(app) as client:
        active_project = register_project(client, name="Active", repository="owner/active")
        paused_project = register_project(
            client, name="Paused", repository="owner/paused", status="paused"
        )

        for _ in range(3):
            create_run(client, active_project["id"])

        active_only = client.get("/api/factory/projects?status=active", headers=headers())
        assert active_only.status_code == 200
        assert [item["id"] for item in active_only.json()] == [active_project["id"]]

        paused_only = client.get("/api/factory/projects?status=paused", headers=headers())
        assert paused_only.status_code == 200
        assert [item["id"] for item in paused_only.json()] == [paused_project["id"]]

        limited_runs = client.get("/api/factory/runs?limit=2", headers=headers())
        assert limited_runs.status_code == 200
        assert len(limited_runs.json()) == 2
