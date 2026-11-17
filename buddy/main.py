import json
import os
import platform
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .auth import generate_token, hash_secret, verify_hash
from .config import CONTAINER_IMAGE, ENABLE_CONTAINERS, SERVER_HOST, SERVER_PORT, WORKSPACE_ROOT
from .db import execute, fetch_all, fetch_one, get_connection, init_db
from .workspace import list_workspace_files, parse_payload, read_workspace_file, write_workspace_note
from .build_factory import init_build_factory_db, router as build_factory_router


ALLOWED_TASK_TYPES = {
    "collect_system_info",
    "read_workspace_file",
    "write_note",
    "container_python",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_owner_token(authorization: str | None = Header(default=None)) -> None:
    token = os.getenv("BUDDY_OWNER_TOKEN", "")
    if not token:
        raise HTTPException(status_code=503, detail="BUDDY_OWNER_TOKEN must be configured")
    if not authorization:
        raise HTTPException(status_code=401, detail="missing Authorization header")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="invalid bearer format")
    provided = authorization[len(prefix):]
    if not __import__("hmac").compare_digest(provided, token):
        raise HTTPException(status_code=401, detail="invalid owner token")


def authenticate_node(
    x_buddy_node: str | None = Header(default=None),
    x_buddy_node_token: str | None = Header(default=None),
    payload: dict[str, Any] | None = None,
) -> sqlite3.Row:
    payload = payload or {}
    node_id = x_buddy_node or payload.get("node_id")
    node_token = x_buddy_node_token or payload.get("node_token")
    if not node_id or not node_token:
        raise HTTPException(status_code=401, detail="node credentials required")
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if node is None:
        raise HTTPException(status_code=401, detail="invalid node credentials")
    if node["revoked"]:
        raise HTTPException(status_code=401, detail="node has been revoked")
    if not verify_hash(node_token, node["token_hash"]):
        raise HTTPException(status_code=401, detail="invalid node credentials")
    return node


def add_audit(event_type: str, message: str, node_id: str | None = None, task_id: str | None = None) -> None:
    execute(
        "INSERT INTO audit_events (id, event_type, node_id, task_id, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), event_type, node_id, task_id, message, now_utc()),
    )


def get_system_info() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "memory_total_gb": round(mem.total / (1024 ** 3), 2),
        "memory_available_gb": round(mem.available / (1024 ** 3), 2),
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "workspace_root": str(WORKSPACE_ROOT),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_build_factory_db()
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    if not WORKSPACE_ROOT.joinpath("hello.py").exists():
        (WORKSPACE_ROOT / "hello.py").write_text("print('hello from Buddy workspace')\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("test_hello.py").exists():
        (WORKSPACE_ROOT / "test_hello.py").write_text("def test_hello():\n    assert 'hello' in 'hello from Buddy workspace'\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("README.md").exists():
        (WORKSPACE_ROOT / "README.md").write_text("# Buddy workspace\n\nStarter workspace for local experimentation.\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("mission-brief.json").exists():
        (WORKSPACE_ROOT / "mission-brief.json").write_text(json.dumps({"mission": "demo", "status": "ready"}, indent=2), encoding="utf-8")

    yield


app = FastAPI(title="Buddy Computer Forge", version="0.9.0", lifespan=lifespan)
app.include_router(build_factory_router)


@app.get("/")
def dashboard() -> HTMLResponse:
    rows = fetch_all("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10")
    mission_rows = fetch_all("SELECT * FROM missions ORDER BY created_at DESC LIMIT 10")
    node_rows = fetch_all("SELECT * FROM nodes ORDER BY created_at DESC LIMIT 10")
    html = """
    <html>
      <head><title>Buddy Computer Forge</title></head>
      <body>
        <h1>Buddy Computer Forge</h1>
        <p>Tasks: {tasks} | Missions: {missions} | Nodes: {nodes}</p>
        <p>Owner token loaded: {owner_loaded}</p>
      </body>
    </html>
    """.format(
        tasks=len(fetch_all("SELECT 1 FROM tasks")),
        missions=len(fetch_all("SELECT 1 FROM missions")),
        nodes=len(fetch_all("SELECT 1 FROM nodes")),
        owner_loaded="yes" if os.getenv("BUDDY_OWNER_TOKEN") else "no",
    )
    return HTMLResponse(content=html)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "0.9.0",
        "features": {
            "owner_auth": True,
            "owner_issued_node_enrollment": True,
            "node_credentials": True,
            "node_revocation": True,
            "workspace_reads": True,
            "mission_planning": True,
            "approval_gating": True,
            "container_execution": ENABLE_CONTAINERS,
        },
    }


@app.get("/api/overview")
def overview(_: None = Depends(require_owner_token)) -> dict[str, Any]:
    node_count = len(fetch_all("SELECT 1 FROM nodes WHERE revoked = 0"))
    mission_count = len(fetch_all("SELECT 1 FROM missions"))
    task_count = len(fetch_all("SELECT 1 FROM tasks"))
    queued_count = len(fetch_all("SELECT 1 FROM tasks WHERE status = 'queued'"))
    running_count = len(fetch_all("SELECT 1 FROM tasks WHERE status = 'running'"))
    return {
        "nodes": node_count,
        "missions": mission_count,
        "tasks": task_count,
        "queued": queued_count,
        "running": running_count,
        "host": get_system_info(),
    }


@app.get("/api/nodes")
def list_nodes(_: None = Depends(require_owner_token)) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM nodes ORDER BY created_at DESC")
    return [dict(row) for row in rows]


@app.post("/api/nodes/enrollments")
def create_node_enrollment(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    node_id = payload.get("node_id")
    name = payload.get("name") or node_id
    node_type = payload.get("node_type", "worker")
    ttl_minutes = payload.get("ttl_minutes", 15)

    if not isinstance(node_id, str) or not node_id.strip() or len(node_id) > 100:
        raise HTTPException(status_code=400, detail="node_id is required (max 100 characters)")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise HTTPException(status_code=400, detail="name is required (max 120 characters)")
    if not isinstance(node_type, str) or not node_type.strip() or len(node_type) > 50:
        raise HTTPException(status_code=400, detail="node_type is required (max 50 characters)")
    if not isinstance(ttl_minutes, int) or ttl_minutes < 1 or ttl_minutes > 60:
        raise HTTPException(status_code=400, detail="ttl_minutes must be between 1 and 60")

    if fetch_one("SELECT id FROM nodes WHERE id = ?", (node_id,)):
        raise HTTPException(status_code=409, detail="node_id is already enrolled")
    if fetch_one(
        "SELECT id FROM node_enrollments WHERE proposed_node_id = ? AND status = 'pending'",
        (node_id,),
    ):
        raise HTTPException(status_code=409, detail="a pending enrollment already exists for this node_id")

    enrollment_id = str(uuid.uuid4())
    enrollment_code = generate_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
    execute(
        """INSERT INTO node_enrollments
        (id,enrollment_code_hash,proposed_node_id,name,node_type,status,expires_at,created_by,created_at)
        VALUES (?,?,?,?,?,'pending',?, 'owner', ?)""",
        (enrollment_id, hash_secret(enrollment_code), node_id, name.strip(), node_type.strip(), expires_at, now_utc()),
    )
    add_audit("enrollment_created", f"enrollment created for {node_id}", node_id=node_id)
    return {
        "enrollment_id": enrollment_id,
        "node_id": node_id,
        "enrollment_code": enrollment_code,
        "expires_at": expires_at,
    }


@app.post("/api/nodes/enroll")
def redeem_node_enrollment(payload: dict[str, Any]) -> dict[str, Any]:
    enrollment_code = payload.get("enrollment_code")
    hostname = payload.get("hostname") or platform.node()
    if not isinstance(enrollment_code, str) or not enrollment_code.strip():
        raise HTTPException(status_code=400, detail="enrollment_code is required")

    enrollment = fetch_one(
        "SELECT * FROM node_enrollments WHERE enrollment_code_hash = ?",
        (hash_secret(enrollment_code),),
    )
    expired = False
    if enrollment:
        expired = datetime.fromisoformat(enrollment["expires_at"]) <= datetime.now(timezone.utc)
    if enrollment is None or enrollment["status"] != "pending" or expired:
        raise HTTPException(status_code=410, detail="enrollment code is invalid, expired, or already redeemed")

    node_id = enrollment["proposed_node_id"]
    if fetch_one("SELECT id FROM nodes WHERE id = ?", (node_id,)):
        raise HTTPException(status_code=409, detail="node_id is already enrolled")

    node_token = generate_token()
    now = now_utc()
    execute(
        """INSERT INTO nodes
        (id,name,hostname,token_hash,node_type,telemetry,last_seen,created_at,revoked,status)
        VALUES (?,?,?,?,?,?,?, ?, 0, 'online')""",
        (node_id, enrollment["name"], hostname, hash_secret(node_token), enrollment["node_type"], "{}", now, now),
    )
    execute(
        """UPDATE node_enrollments
        SET status = 'redeemed', redeemed_at = ?, redeemed_by_node_id = ?
        WHERE id = ?""",
        (now, node_id, enrollment["id"]),
    )
    add_audit("enrollment_redeemed", f"node {node_id} enrolled", node_id=node_id)
    return {
        "node_id": node_id,
        "node_token": node_token,
        "token_type": "bearer",
        "expires_at": None,
    }


@app.post("/api/nodes/heartbeat")
def node_heartbeat(
    payload: dict[str, Any],
    x_buddy_node: str | None = Header(default=None),
    x_buddy_node_token: str | None = Header(default=None),
) -> dict[str, Any]:
    node = authenticate_node(x_buddy_node, x_buddy_node_token, payload)
    execute(
        "UPDATE nodes SET hostname = ?, telemetry = ?, last_seen = ?, status = 'online' WHERE id = ?",
        (payload.get("hostname", node["hostname"]), json.dumps(payload.get("telemetry", {})), now_utc(), node["id"]),
    )
    add_audit("node_heartbeat", f"node {node['id']} heartbeat", node_id=node["id"])
    return {"ok": True, "node_id": node["id"], "status": "online"}


@app.post("/api/missions")
def create_mission(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    mission_id = str(uuid.uuid4())
    name = payload.get("name") or "mission"
    description = payload.get("description") or ""
    execute(
        "INSERT INTO missions (id, name, description, status, created_at) VALUES (?, ?, ?, 'queued', ?)",
        (mission_id, name, description, now_utc()),
    )
    add_audit("mission_created", f"mission {name} created", task_id=mission_id)
    return {"id": mission_id, "name": name, "status": "queued"}


@app.get("/api/missions")
def list_missions(_: None = Depends(require_owner_token)) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM missions ORDER BY created_at DESC")
    return [dict(row) for row in rows]


@app.post("/api/missions/{mission_id}/plan")
def plan_mission(mission_id: str, payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    rows = payload.get("tasks")
    if not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="tasks must be a list")
    if len(rows) > 20:
        raise HTTPException(status_code=400, detail="maximum 20 tasks per mission")
    mission = fetch_one("SELECT * FROM missions WHERE id = ?", (mission_id,))
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")
    created = []
    for item in rows:
        task_type = item.get("type")
        if task_type not in ALLOWED_TASK_TYPES:
            raise HTTPException(status_code=400, detail=f"unsupported task type: {task_type}")
        task_id = str(uuid.uuid4())
        execute(
            "INSERT INTO tasks (id, mission_id, task_type, payload, status, created_at, approved) VALUES (?, ?, ?, ?, 'queued', ?, 1)",
            (task_id, mission_id, task_type, json.dumps(item.get("payload") or {}), now_utc()),
        )
        if task_type == "container_python":
            execute("UPDATE tasks SET approved = 0 WHERE id = ?", (task_id,))
        created.append({"id": task_id, "type": task_type})
    execute("UPDATE missions SET status = 'planned' WHERE id = ?", (mission_id,))
    return {"mission_id": mission_id, "created": created}


@app.post("/api/tasks")
def create_task(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    task_type = payload.get("type")
    if task_type not in ALLOWED_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"unsupported task type: {task_type}")
    task_id = str(uuid.uuid4())
    approved = 1 if task_type != "container_python" else 0
    execute(
        "INSERT INTO tasks (id, mission_id, task_type, payload, status, created_at, approved, submitted_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            task_id,
            payload.get("mission_id"),
            task_type,
            json.dumps(payload.get("payload") or {}),
            "pending_approval" if task_type == "container_python" else "queued",
            now_utc(),
            approved,
            payload.get("submitted_code") or "",
        ),
    )
    if task_type == "container_python":
        add_audit("task_pending_approval", f"task {task_id} awaiting approval", task_id=task_id)
    return {"id": task_id, "status": "pending_approval" if task_type == "container_python" else "queued"}


@app.get("/api/tasks")
def list_tasks(_: None = Depends(require_owner_token)) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM tasks ORDER BY created_at DESC")
    return [dict(row) for row in rows]


@app.post("/api/tasks/claim")
def claim_task(
    payload: dict[str, Any],
    x_buddy_node: str | None = Header(default=None),
    x_buddy_node_token: str | None = Header(default=None),
) -> dict[str, Any]:
    node = authenticate_node(x_buddy_node, x_buddy_node_token, payload)
    task = fetch_one(
        "SELECT * FROM tasks WHERE status IN ('queued', 'pending_approval') AND (approved = 1 OR approved IS NULL) ORDER BY created_at ASC LIMIT 1"
    )
    if task is None:
        return {"claimed": False, "reason": "no task available"}
    if task["task_type"] == "container_python" and task["approved"] != 1:
        return {"claimed": False, "reason": "container task is pending approval"}

    lease_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    execute(
        "UPDATE tasks SET status = 'running', claimed_by = ?, lease_until = ? WHERE id = ?",
        (node["id"], lease_until, task["id"]),
    )
    add_audit("task_claimed", f"task {task['id']} claimed by {node['id']}", node_id=node["id"], task_id=task["id"])
    return {"claimed": True, "task": dict(task), "lease_until": lease_until}


@app.post("/api/tasks/{task_id}/lease")
def renew_lease(
    task_id: str,
    payload: dict[str, Any],
    x_buddy_node: str | None = Header(default=None),
    x_buddy_node_token: str | None = Header(default=None),
) -> dict[str, Any]:
    node = authenticate_node(x_buddy_node, x_buddy_node_token, payload)
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if task["claimed_by"] != node["id"]:
        raise HTTPException(status_code=403, detail="task is not claimed by this node")
    lease_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    execute("UPDATE tasks SET lease_until = ? WHERE id = ?", (lease_until, task_id))
    return {"ok": True, "lease_until": lease_until}


@app.post("/api/tasks/{task_id}/retry")
def retry_task(task_id: str, _: None = Depends(require_owner_token)) -> dict[str, Any]:
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    execute("UPDATE tasks SET status = 'queued', claimed_by = NULL, lease_until = NULL, stderr = NULL, stdout = NULL, exit_code = NULL WHERE id = ?", (task_id,))
    return {"ok": True, "status": "queued"}


@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: str, _: None = Depends(require_owner_token)) -> dict[str, Any]:
    execute("UPDATE tasks SET status = 'cancelled', claimed_by = NULL, lease_until = NULL WHERE id = ?", (task_id,))
    add_audit("task_cancelled", f"task {task_id} cancelled", task_id=task_id)
    return {"ok": True, "status": "cancelled"}


@app.post("/api/tasks/result")
def submit_task_result(
    payload: dict[str, Any],
    x_buddy_node: str | None = Header(default=None),
    x_buddy_node_token: str | None = Header(default=None),
) -> dict[str, Any]:
    node = authenticate_node(x_buddy_node, x_buddy_node_token, payload)
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id required")
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if task["claimed_by"] != node["id"]:
        raise HTTPException(status_code=403, detail="task is not claimed by this node")

    stdout = payload.get("stdout") or ""
    stderr = payload.get("stderr") or ""
    exit_code = int(payload.get("exit_code", 0))
    status = "completed" if exit_code == 0 else "failed"
    execute(
        "UPDATE tasks SET status = ?, stdout = ?, stderr = ?, exit_code = ?, claimed_by = NULL, lease_until = NULL WHERE id = ?",
        (status, stdout, stderr, exit_code, task_id),
    )
    add_audit("task_completed", f"task {task_id} finished", node_id=node["id"], task_id=task_id)
    return {"ok": True, "task_id": task_id, "exit_code": exit_code, "status": status}


@app.post("/api/nodes/{node_id}/rotate-token")
def rotate_node_token(node_id: str, _: None = Depends(require_owner_token)) -> dict[str, Any]:
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    node_token = generate_token()
    execute("UPDATE nodes SET token_hash = ? WHERE id = ?", (hash_secret(node_token), node_id))
    add_audit("node_token_rotated", f"node {node_id} token rotated", node_id=node_id)
    return {"node_id": node_id, "node_token": node_token, "token_type": "bearer"}


@app.post("/api/nodes/{node_id}/revoke")
def revoke_node(node_id: str, _: None = Depends(require_owner_token)) -> dict[str, Any]:
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    execute("UPDATE nodes SET revoked = 1, status = 'offline' WHERE id = ?", (node_id,))
    add_audit("node_revoked", f"node {node_id} revoked", node_id=node_id)
    return {"ok": True, "node_id": node_id, "status": "revoked"}


@app.post("/api/approvals/{approval_id}/decision")
def approval_decision(approval_id: str, payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    approval = fetch_one("SELECT * FROM approvals WHERE id = ?", (approval_id,))
    if approval is None:
        task = fetch_one("SELECT * FROM tasks WHERE id = ?", (approval_id,))
        if task is None:
            raise HTTPException(status_code=404, detail="approval not found")
        approval = fetch_one("SELECT * FROM approvals WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task["id"],))
    if approval is None:
        raise HTTPException(status_code=404, detail="approval not found")
    decision = payload.get("decision")
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (approval["task_id"],))
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    approved_value = 1 if decision == "approve" else 0
    execute("UPDATE tasks SET approved = ?, status = ? WHERE id = ?", (approved_value, "queued" if decision == "approve" else "rejected", task["id"]))
    execute(
        "INSERT INTO approvals (id, task_id, decision, actor, note, created_at, submitted_code) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), task["id"], decision, "owner", payload.get("note", ""), now_utc(), task["submitted_code"] or ""),
    )
    add_audit("approval_decision", f"task {task['id']} {decision}d", task_id=task["id"])
    return {"ok": True, "task_id": task["id"], "decision": decision}


@app.get("/api/audit")
def audit(_: None = Depends(require_owner_token)) -> list[dict[str, Any]]:
    rows = fetch_all("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 100")
    return [dict(row) for row in rows]


@app.get("/api/capabilities")
def capabilities(_: None = Depends(require_owner_token)) -> dict[str, Any]:
    return {
        "allowed_tasks": sorted(ALLOWED_TASK_TYPES),
        "container_execution_enabled": ENABLE_CONTAINERS,
        "container_image": CONTAINER_IMAGE,
        "workspace_files": list_workspace_files(),
    }


@app.post("/api/workspace/read")
def workspace_read(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    path = payload.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    content = read_workspace_file(path)
    return {"path": path, "content": content}


@app.post("/api/workspace/write")
def workspace_write(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    rel_path = payload.get("path")
    content = payload.get("content")
    if not rel_path or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="path and content required")
    try:
        saved = write_workspace_note(rel_path, content)
        return {"ok": True, "path": saved}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/tasks/execute")
def execute_task(payload: dict[str, Any], _: None = Depends(require_owner_token)) -> dict[str, Any]:
    task_type = payload.get("type")
    if task_type == "collect_system_info":
        return {"ok": True, "result": get_system_info()}
    if task_type == "read_workspace_file":
        path = parse_payload(payload.get("payload"))
        rel_path = path.get("path")
        if not rel_path:
            raise HTTPException(status_code=400, detail="payload.path is required")
        return {"ok": True, "result": read_workspace_file(rel_path)}
    if task_type == "write_note":
        path_obj = parse_payload(payload.get("payload"))
        rel_path = path_obj.get("path")
        content = path_obj.get("content")
        if not rel_path or not isinstance(content, str):
            raise HTTPException(status_code=400, detail="payload.path and payload.content are required")
        return {"ok": True, "result": write_workspace_note(rel_path, content)}
    if task_type == "container_python":
        if not ENABLE_CONTAINERS:
            raise HTTPException(status_code=403, detail="container execution is disabled")
        return {"ok": True, "result": {"mode": "container_python", "image": CONTAINER_IMAGE, "status": "ready"}}
    raise HTTPException(status_code=400, detail=f"unsupported task type: {task_type}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
