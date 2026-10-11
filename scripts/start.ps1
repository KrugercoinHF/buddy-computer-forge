import argparse
import json
import os
import time
from typing import Any

import requests


DEFAULT_SERVER = os.getenv("BUDDY_SERVER", "http://127.0.0.1:8741")


def main() -> None:
    parser = argparse.ArgumentParser(description="Buddy node worker")
    parser.add_argument("--workspace", default="./workspace")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    args = parser.parse_args()

    node_id = os.getenv("BUDDY_NODE_ID")
    node_token = os.getenv("BUDDY_NODE_TOKEN")
    if not node_id or not node_token:
        raise SystemExit("BUDDY_NODE_ID and BUDDY_NODE_TOKEN must be set")

    telemetry = {"workspace": args.workspace, "status": "online"}
    headers = {"Content-Type": "application/json"}
    payload = {"node_id": node_id, "node_token": node_token, "hostname": os.uname().nodename if hasattr(os, "uname") else "worker", "telemetry": telemetry}

    for _ in range(3):
        try:
            response = requests.post(f"{args.server}/api/nodes/heartbeat", json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException:
            time.sleep(1)

    while True:
        try:
            claim_response = requests.post(
                f"{args.server}/api/tasks/claim",
                json={"node_id": node_id, "node_token": node_token},
                headers={"X-Buddy-Node": node_id, "X-Buddy-Node-Token": node_token},
                timeout=10,
            )
            if claim_response.status_code == 200:
                body = claim_response.json()
                if body.get("claimed"):
                    task = body.get("task", {})
                    task_id = task.get("id")
                    task_type = task.get("task_type")
                    payload_obj = json.loads(task.get("payload") or "{}")
                    if task_type == "collect_system_info":
                        result = {"node_id": node_id, "status": "ok", "payload": payload_obj}
                    elif task_type == "read_workspace_file":
                        path = payload_obj.get("path", "README.md")
                        with open(os.path.join(args.workspace, path), "r", encoding="utf-8") as handle:
                            result = {"path": path, "content": handle.read()}
                    else:
                        result = {"status": "not_implemented", "task_type": task_type}
                    result_response = requests.post(
                        f"{args.server}/api/tasks/result",
                        json={
                            "node_id": node_id,
                            "node_token": node_token,
                            "task_id": task_id,
                            "stdout": json.dumps(result),
                            "stderr": "",
                            "exit_code": 0,
                        },
                        timeout=10,
                    )
                    if result_response.status_code >= 400:
                        print(result_response.text)
        except requests.RequestException as exc:
            print(f"worker poll failed: {exc}")
        time.sleep(2)


if __name__ == "__main__":
    main()
