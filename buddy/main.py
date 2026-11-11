import json
import os
import platform
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

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


def get_node_from_headers(x_buddy_node: str | None = Header(default=None), node_token: str | None = Header(default=None)) -> tuple[str, str]:
    if not x_buddy_node:
        raise HTTPException(status_code=401, detail="missing X-Buddy-Node header")
    if not node_token:
        raise HTTPException(status_code=401, detail="missing X-Buddy-Node-Token header")
    return x_buddy_node, node_token


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


@app.on_event("startup")
def startup_event() -> None:
    init_db()
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    if not WORKSPACE_ROOT.joinpath("hello.py").exists():
        (WORKSPACE_ROOT / "hello.py").write_text("print('hello from Buddy workspace')\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("test_hello.py").exists():
        (WORKSPACE_ROOT / "test_hello.py").write_text("def test_hello():\n    assert 'hello' in 'hello from Buddy workspace'\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("README.md").exists():
        (WORKSPACE_ROOT / "README.md").write_text("# Buddy workspace\n\nStarter workspace for local experimentation.\n", encoding="utf-8")
    if not WORKSPACE_ROOT.joinpath("mission-brief.json").exists():
        (WORKSPACE_ROOT / "mission-brief.json").write_text(json.dumps({"mission": "demo", "status": "ready"}, indent=2), encoding="utf-8")


@app.get("/")
def dashboard() -> HTMLResponse:
    rows = fetch_all("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10")
    mission_rows = fetch_all("SELECT * FROM missions ORDER BY created_at DESC LIMIT 10")
    node_rows = fetch_all("SELECT * FROM nodes ORDER BY created_at DESC LIMIT 10")
    html = """
    <html>
      <head>
        <title>Buddy Computer Forge</title>
        <style>
          body { font-family: sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }
          h1, h2 { margin-top: 0; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
          .card { background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 12px; padding: 1rem; }
          table { width: 100%; border-collapse: collapse; }
          th, td { text-align: left; border-bottom: 1px solid #334155; padding: 0.5rem; }
          code { background: #111827; padding: 0.2rem 0.4rem; border-radius: 6px; }
          a { color: #7dd3fc; }
        </style>
      </head>
      <body>
        <h1>Buddy Computer Forge</h1>
        <div class="grid">
          <div class="card"><h2>Overview</h2><p>Tasks: {tasks}</p><p>Missions: {missions}</p><p>Nodes: {nodes}</p></div>
          <div class="card"><h2>Host</h2><p>API: http://127.0.0.1:8741</p><p>Owner token loaded: {owner_loaded}</p></div>
          <div class="card"><h2>Features</h2><p>Bounded workspace reads</p><p>Mission plans</p><p>Approval gating</p></div>
        </div>
        <div class="card"><h2>Recent tasks</h2><table><thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Node</th></tr></thead><tbody>{tasks_row}</tbody></table></div>
        <div class="card"><h2>Recent missions</h2><table><thead><tr><th>ID</th><th>Name</th><th>Status</th></tr></thead><tbody>{missions_row}</tbody></table></div>
      </body>
    </html>
    """.format(
        tasks=len(fetch_all("SELECT 1 FROM tasks")),
        missions=len(fetch_all("SELECT 1 FROM missions")),
        nodes=len(fetch_all("SELECT 1 FROM nodes")),
        owner_loaded="yes" if os.getenv("BUDDY_OWNER_TOKEN") else "default",
        tasks_row="".join(f"<tr><td><code>{row['id'][:8]}</code></td><td>{row['task_type']}</td><td>{row['status']}</td><td>{row['claimed_by'] or '-'}</td></tr>" for row in rows),
        missions_row="".join(f"<tr><td><code>{row['id'][:8]}</code></td><td>{row['name']}</td><td>{row['status']}</td></tr>" for row in mission_rows),
    )
    return HTMLResponse(content=html)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "version": "0.8.0",
        "features": {
            "owner_auth": True,
            "node_credentials": True,
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


@app.post("/api/nodes/heartbeat")
def node_heartbeat(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
    node_id = payload.get("node_id")
    node_token = payload.get("node_token")
    if not node_id or not node_token:
        raise HTTPException(status_code=400, detail="node_id and node_token are required")
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if node is None:
        if authorization and authorization.startswith("Bearer "):
            legacy = authorization.split(" ", 1)[1]
            if legacy != os.getenv("BUDDY_OWNER_TOKEN", DEFAULT_OWNER_TOKEN):
                raise HTTPException(status_code=401, detail="invalid owner token")
        else:
            raise HTTPException(status_code=401, detail="node not enrolled")
        token_hash = hash_secret(node_token)
        execute(
            "INSERT INTO nodes (id, name, hostname, token_hash, node_type, telemetry, last_seen, created_at, revoked, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'online')",
            (
                node_id,
                payload.get("name", node_id),
                payload.get("hostname", platform.node()),
                token_hash,
                payload.get("node_type", "worker"),
                json.dumps(payload.get("telemetry", {})),
                now_utc(),
                now_utc(),
            ),
        )
        add_audit("node_registered", f"node {node_id} registered", node_id=node_id)
    else:
        if verify_hash(node_token, node.get("token_hash")) is False:
            raise HTTPException(status_code=401, detail="invalid node token")
        execute(
            "UPDATE nodes SET hostname = ?, telemetry = ?, last_seen = ?, status = 'online' WHERE id = ?",
            (payload.get("hostname", node["hostname"]), json.dumps(payload.get("telemetry", {})), now_utc(), node_id),
        )
        add_audit("node_heartbeat", f"node {node_id} heartbeat", node_id=node_id)
    return {"ok": True, "node_id": node_id, "status": "online"}


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
            (task_id, mission_id, task_type, json.dumps(item.get("payload") or {}), now_utc(),),
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
def claim_task(payload: dict[str, Any], x_buddy_node: str | None = Header(default=None), x_buddy_node_token: str | None = Header(default=None)) -> dict[str, Any]:
    node_id = x_buddy_node or payload.get("node_id")
    node_token = x_buddy_node_token or payload.get("node_token")
    if not node_id or not node_token:
        raise HTTPException(status_code=400, detail="node_id and node_token required")
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    if not verify_hash(node_token, node["token_hash"]):
        raise HTTPException(status_code=401, detail="invalid node token")

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
        (node_id, lease_until, task["id"]),
    )
    add_audit("task_claimed", f"task {task['id']} claimed by {node_id}", node_id=node_id, task_id=task['id'])
    return {"claimed": True, "task": dict(task), "lease_until": lease_until}


@app.post("/api/tasks/{task_id}/lease")
def renew_lease(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    node_id = payload.get("node_id")
    node_token = payload.get("node_token")
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if not node or not verify_hash(node_token, node["token_hash"]):
        raise HTTPException(status_code=401, detail="invalid node")
    if task["claimed_by"] != node_id:
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
def submit_task_result(payload: dict[str, Any]) -> dict[str, Any]:
    node_id = payload.get("node_id")
    node_token = payload.get("node_token")
    task_id = payload.get("task_id")
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id required")
    node = fetch_one("SELECT * FROM nodes WHERE id = ?", (node_id,))
    if not node or not verify_hash(node_token, node["token_hash"]):
        raise HTTPException(status_code=401, detail="invalid node credential")
    task = fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    if task["claimed_by"] != node_id:
        raise HTTPException(status_code=403, detail="task is not claimed by this node")

    stdout = payload.get("stdout") or ""
    stderr = payload.get("stderr") or ""
    exit_code = int(payload.get("exit_code", 0))
    status = "completed" if exit_code == 0 else "failed"
    execute(
        "UPDATE tasks SET status = ?, stdout = ?, stderr = ?, exit_code = ?, claimed_by = NULL, lease_until = NULL WHERE id = ?",
        (status, stdout, stderr, exit_code, task_id),
    )
    add_audit("task_completed", f"task {task_id} finished", node_id=node_id, task_id=task_id)
    return {"ok": True, "task_id": task_id, "exit_code": exit_code, "status": status}


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
