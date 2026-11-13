"""Owner-controlled project registry and build-run ledger.

This module records build intent and outcomes only. It never executes shell
commands, starts workers, deploys software, or grants execution permissions.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from .db import execute, fetch_all, fetch_one, get_connection

router = APIRouter(prefix="/api/factory", tags=["build-factory"])

PROJECT_STATUSES = {"active", "paused", "archived"}
RUN_STATUSES = {"queued", "running", "succeeded", "failed", "cancelled"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_owner(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("BUDDY_OWNER_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="BUDDY_OWNER_TOKEN must be configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="owner bearer token required")
    supplied = authorization[len("Bearer "):]
    if not __import__("hmac").compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="invalid owner token")


def init_build_factory_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS factory_projects (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      repository TEXT NOT NULL UNIQUE,
      description TEXT NOT NULL DEFAULT '',
      stack TEXT NOT NULL DEFAULT '',
      build_command TEXT NOT NULL DEFAULT '',
      test_command TEXT NOT NULL DEFAULT '',
      default_branch TEXT NOT NULL DEFAULT 'main',
      status TEXT NOT NULL DEFAULT 'active',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS factory_runs (
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL,
      source_commit TEXT NOT NULL DEFAULT '',
      environment TEXT NOT NULL DEFAULT 'local',
      status TEXT NOT NULL DEFAULT 'queued',
      summary TEXT NOT NULL DEFAULT '',
      test_report TEXT NOT NULL DEFAULT '',
      artifact_ref TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL,
      started_at TEXT,
      finished_at TEXT,
      FOREIGN KEY(project_id) REFERENCES factory_projects(id)
    );
    CREATE INDEX IF NOT EXISTS idx_factory_runs_project_created
      ON factory_runs(project_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_factory_runs_status_created
      ON factory_runs(status, created_at);
    """
    with get_connection() as connection:
        connection.executescript(schema)


def _project_dict(row: Any) -> dict[str, Any]:
    return dict(row)


def _run_dict(row: Any) -> dict[str, Any]:
    return dict(row)


@router.post("/projects", dependencies=[Depends(_require_owner)])
def register_project(payload: dict[str, Any]) -> dict[str, Any]:
    name = payload.get("name")
    repository = payload.get("repository")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise HTTPException(status_code=400, detail="name is required (max 120 characters)")
    if not isinstance(repository, str) or "/" not in repository or len(repository) > 200:
        raise HTTPException(status_code=400, detail="repository must be in owner/repository form")
    status = payload.get("status", "active")
    if status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail="invalid project status")
    project_id = str(uuid.uuid4())
    now = _now()
    try:
        execute(
            """INSERT INTO factory_projects
            (id,name,repository,description,stack,build_command,test_command,default_branch,status,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                project_id, name.strip(), repository.strip(),
                str(payload.get("description", ""))[:2000],
                str(payload.get("stack", ""))[:500],
                str(payload.get("build_command", ""))[:500],
                str(payload.get("test_command", ""))[:500],
                str(payload.get("default_branch", "main"))[:100],
                status, now, now,
            ),
        )
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="repository is already registered") from exc
        raise
    return _project_dict(fetch_one("SELECT * FROM factory_projects WHERE id = ?", (project_id,)))


@router.get("/projects", dependencies=[Depends(_require_owner)])
def list_projects(status: str | None = None) -> list[dict[str, Any]]:
    if status and status not in PROJECT_STATUSES:
        raise HTTPException(status_code=400, detail="invalid project status")
    if status:
        rows = fetch_all("SELECT * FROM factory_projects WHERE status = ? ORDER BY created_at", (status,))
    else:
        rows = fetch_all("SELECT * FROM factory_projects ORDER BY created_at")
    return [_project_dict(row) for row in rows]


@router.post("/runs", dependencies=[Depends(_require_owner)])
def create_build_run(payload: dict[str, Any]) -> dict[str, Any]:
    project_id = payload.get("project_id")
    if not isinstance(project_id, str) or not fetch_one(
        "SELECT id FROM factory_projects WHERE id = ? AND status = 'active'", (project_id,)
    ):
        raise HTTPException(status_code=404, detail="active project not found")
    source_commit = payload.get("source_commit", "")
    if not isinstance(source_commit, str) or len(source_commit) > 80:
        raise HTTPException(status_code=400, detail="source_commit must be a string up to 80 characters")
    environment = payload.get("environment", "local")
    if environment not in {"local", "ci", "cloud"}:
        raise HTTPException(status_code=400, detail="environment must be local, ci, or cloud")
    run_id = str(uuid.uuid4())
    now = _now()
    execute(
        """INSERT INTO factory_runs
        (id,project_id,source_commit,environment,status,created_at)
        VALUES (?,?,?,?, 'queued', ?)""",
        (run_id, project_id, source_commit, environment, now),
    )
    return _run_dict(fetch_one("SELECT * FROM factory_runs WHERE id = ?", (run_id,)))


@router.get("/runs", dependencies=[Depends(_require_owner)])
def list_build_runs(project_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 200))
    if project_id:
        rows = fetch_all(
            "SELECT * FROM factory_runs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        )
    else:
        rows = fetch_all("SELECT * FROM factory_runs ORDER BY created_at DESC LIMIT ?", (limit,))
    return [_run_dict(row) for row in rows]


@router.post("/runs/{run_id}/start", dependencies=[Depends(_require_owner)])
def start_build_run(run_id: str) -> dict[str, Any]:
    run = fetch_one("SELECT * FROM factory_runs WHERE id = ?", (run_id,))
    if not run:
        raise HTTPException(status_code=404, detail="build run not found")
    if run["status"] != "queued":
        raise HTTPException(status_code=409, detail="only queued runs can be started")
    now = _now()
    execute("UPDATE factory_runs SET status = 'running', started_at = ? WHERE id = ?", (now, run_id))
    return _run_dict(fetch_one("SELECT * FROM factory_runs WHERE id = ?", (run_id,)))


@router.post("/runs/{run_id}/finish", dependencies=[Depends(_require_owner)])
def finish_build_run(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    run = fetch_one("SELECT * FROM factory_runs WHERE id = ?", (run_id,))
    if not run:
        raise HTTPException(status_code=404, detail="build run not found")
    if run["status"] != "running":
        raise HTTPException(status_code=409, detail="only running builds can be finished")
    status = payload.get("status")
    if status not in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(status_code=400, detail="status must be succeeded, failed, or cancelled")
    execute(
        """UPDATE factory_runs
        SET status = ?, summary = ?, test_report = ?, artifact_ref = ?, finished_at = ?
        WHERE id = ?""",
        (
            status,
            str(payload.get("summary", ""))[:4000],
            str(payload.get("test_report", ""))[:12000],
            str(payload.get("artifact_ref", ""))[:1000],
            _now(),
            run_id,
        ),
    )
    return _run_dict(fetch_one("SELECT * FROM factory_runs WHERE id = ?", (run_id,)))
