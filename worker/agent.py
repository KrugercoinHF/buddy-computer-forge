"""Node worker for Buddy Computer Forge.

The worker only executes explicitly supported, bounded task types. It never
executes arbitrary shell or Python submitted by a server task.
"""
import argparse
import json
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


def save_credentials(path: Path, server: str, node_id: str, node_token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"server": server, "node_id": node_id, "node_token": node_token}, indent=2),
        encoding="utf-8",
    )
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_credentials(path: Path) -> tuple[str, str, str]:
    if not path.exists():
        raise SystemExit(
            "No node credentials found. Run with --enroll and an owner-issued enrollment code."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    server = data.get("server") or os.getenv("BUDDY_SERVER", "http://127.0.0.1:8741")
    node_id = data.get("node_id") or os.getenv("BUDDY_NODE_ID")
    node_token = data.get("node_token") or os.getenv("BUDDY_NODE_TOKEN")
    if not node_id or not node_token:
        raise SystemExit("Stored credentials are incomplete")
    return server.rstrip("/"), node_id, node_token


def enroll(server: str, enrollment_code: str, credential_path: Path) -> None:
    response = requests.post(
        f"{server.rstrip('/')}/api/nodes/enroll",
        json={"enrollment_code": enrollment_code, "hostname": platform.node()},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    save_credentials(credential_path, server, data["node_id"], data["node_token"])
    print(f"Enrolled node {data['node_id']}. Credentials saved to {credential_path}.")


def run(workspace: Path, credential_path: Path) -> None:
    server, node_id, node_token = load_credentials(credential_path)
    workspace.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"X-Buddy-Node": node_id, "X-Buddy-Node-Token": node_token})

    heartbeat = {
        "node_id": node_id,
        "node_token": node_token,
        "name": node_id,
        "hostname": platform.node(),
        "telemetry": {"system": platform.system()},
    }
    request(session, "POST", f"{server}/api/nodes/heartbeat", json=heartbeat)

    while True:
        claim = request(session, "POST", f"{server}/api/tasks/claim", json={})
        if not claim.get("claimed"):
            time.sleep(3)
            continue
        task = claim["task"]
        task_type = task.get("task_type")
        payload = task.get("payload") or {}
        if isinstance(payload, str):
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
        request(
            session,
            "POST",
            f"{server}/api/tasks/result",
            json={
                "node_id": node_id,
                "node_token": node_token,
                "task_id": task["id"],
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            },
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="./workspace")
    parser.add_argument("--credential-file", default=".buddy-node.json")
    parser.add_argument("--enroll", action="store_true", help="Redeem an owner-issued enrollment code")
    parser.add_argument("--enrollment-code", default=os.getenv("BUDDY_ENROLLMENT_CODE", ""))
    args = parser.parse_args()

    server = os.getenv("BUDDY_SERVER", "http://127.0.0.1:8741").rstrip("/")
    credential_path = Path(args.credential_file).resolve()

    if args.enroll:
        if not args.enrollment_code:
            raise SystemExit("An enrollment code is required: use --enrollment-code or BUDDY_ENROLLMENT_CODE")
        enroll(server, args.enrollment_code, credential_path)
    else:
        run(Path(args.workspace).resolve(), credential_path)
