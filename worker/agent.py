"""Node worker for Buddy Computer Forge.

The worker only executes the explicitly supported, bounded task types. It never
executes arbitrary shell or Python submitted by a server task.
"""
import argparse
import os
import platform
import time
import uuid
from pathlib import Path

import requests


def request(session, method, url, **kwargs):
    response = session.request(method, url, timeout=15, **kwargs)
    response.raise_for_status()
    return response.json() if response.content else {}


def run(workspace: Path) -> None:
    server = os.getenv("BUDDY_SERVER", "http://127.0.0.1:8741").rstrip("/")
    node_id = os.getenv("BUDDY_NODE_ID") or str(uuid.uuid4())
    node_token = os.getenv("BUDDY_NODE_TOKEN")
    owner_token = os.getenv("BUDDY_OWNER_TOKEN")
    if not node_token:
        raise SystemExit("BUDDY_NODE_TOKEN is required")
    workspace.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"X-Buddy-Node": node_id, "X-Buddy-Node-Token": node_token})

    heartbeat = {"node_id": node_id, "node_token": node_token, "name": node_id,
                 "hostname": platform.node(), "telemetry": {"system": platform.system()}}
    if owner_token:
        request(session, "POST", f"{server}/api/nodes/heartbeat",
                json=heartbeat, headers={"Authorization": f"Bearer {owner_token}"})
    else:
        request(session, "POST", f"{server}/api/nodes/heartbeat", json=heartbeat)

    while True:
        claim = request(session, "POST", f"{server}/api/tasks/claim",
                        json={"node_id": node_id, "node_token": node_token})
        if not claim.get("claimed"):
            time.sleep(3)
            continue
        task = claim["task"]
        task_type = task.get("task_type")
        payload = task.get("payload") or {}
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        stdout, stderr, exit_code = "", "", 0
        try:
            if task_type == "collect_system_info":
                stdout = f"system={platform.system()}\nrelease={platform.release()}\n"
            elif task_type == "read_workspace_file":
                rel = Path(payload.get("path", ""))
                target = (workspace / rel).resolve()
                if workspace.resolve() not in target.parents and target != workspace.resolve():
                    raise ValueError("path escapes worker workspace")
                if target.stat().st_size > 200_000:
                    raise ValueError("file exceeds read limit")
                stdout = target.read_text(encoding="utf-8")
            elif task_type == "write_note":
                rel = Path(payload.get("path", ""))
                target = (workspace / rel).resolve()
                if workspace.resolve() not in target.parents or target.suffix not in {".txt", ".md", ".json"}:
                    raise ValueError("invalid workspace note path")
                content = payload.get("content", "")
                if not isinstance(content, str) or len(content.encode("utf-8")) > 200_000:
                    raise ValueError("invalid note content")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                stdout = f"wrote {rel.as_posix()}"
            else:
                raise ValueError(f"unsupported worker task type: {task_type}")
        except Exception as exc:
            stderr, exit_code = str(exc), 1
        request(session, "POST", f"{server}/api/tasks/result",
                json={"node_id": node_id, "node_token": node_token, "task_id": task["id"],
                      "stdout": stdout, "stderr": stderr, "exit_code": exit_code})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="./workspace")
    args = parser.parse_args()
    run(Path(args.workspace).resolve())
