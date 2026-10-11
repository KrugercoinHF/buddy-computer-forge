import json
import os
import platform
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from .auth import generate_token, hash_secret, verify_hash
from .config import CONTAINER_IMAGE, DEFAULT_OWNER_TOKEN, ENABLE_CONTAINERS, SERVER_HOST, SERVER_PORT, WORKSPACE_ROOT
from .db import execute, fetch_all, fetch_one, get_connection, init_db
from .workspace import list_workspace_files, parse_payload, read_workspace_file, write_workspace_note

app = FastAPI(title="Buddy Computer Forge", version="0.8.0")

ALLOWED_TASK_TYPES = {
    "collect_system_info",
    "read_workspace_file",
    "write_note",
    "container_python",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_owner_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("BUDDY_OWNER_TOKEN", DEFAULT_OWNER_TOKEN)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid Authorization header")
    if authorization.split(" ", 1)[1] != token:
        raise HTTPException(status_code=401, detail="invalid owner token")


def add_audit(event_type: str, message: str, node_id: str | None = None, task_id: str | None = None) -> None:
    execute(
        "INSERT INTO audit_events (id, event_type, node_id, task_id, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), event_type, node_id, task_id, message, now_utc()),
    )


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)


@app.get("/")
def dashboard() -> HTMLResponse:
    return HTMLResponse("<html><body><h1>Buddy Computer Forge</h1><p>Control plane running.</p></body></html>")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": "0.8.0"}


@app.get("/api/overview")
def overview(_: None = Depends(require_owner_token)) -> dict[str, Any]:
    return {"status": "ok"}


@app.post("/api/nodes/heartbeat")
def heartbeat(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "node_id": payload.get("node_id", "unknown")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
