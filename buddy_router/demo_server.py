"""Local, dependency-free HTTP demo for the advisory Buddy Router."""
from __future__ import annotations

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .engine import DISABLED, REGISTRY, route

ROOT = Path(__file__).resolve().parent
MAX_BODY_BYTES = 16_384


def discover_profiles() -> list[dict[str, Any]]:
    """Return the public, read-only specialist directory."""
    return [
        {
            "profile_id": profile_id,
            "intents": list(spec["intents"]),
            "risk_level": spec["risk"],
            "capabilities": list(spec["capabilities"]),
            "enabled_for_advisory_routing": True,
            "execution_enabled": False,
            "disabled_for_execution": profile_id in DISABLED,
        }
        for profile_id, spec in REGISTRY.items()
    ]


def process_request(payload: Any) -> dict[str, Any]:
    """Run one deterministic route and return an explainable trace."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    task = payload.get("task")
    intent = payload.get("intent")
    requested_profile = payload.get("requested_profile")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty string.")
    if len(task) > 2_000:
        raise ValueError("task must be 2,000 characters or fewer.")
    if not isinstance(intent, str) or not intent.strip():
        raise ValueError("intent must be a non-empty string.")

    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id.strip():
        trace_id = "route-" + uuid.uuid4().hex[:12]

    decision = route({
        "trace_id": trace_id,
        "intent": intent,
        "requested_profile": requested_profile,
    })
    selected_id = decision["profile_id"]
    selected_spec = REGISTRY.get(selected_id) if selected_id else None

    trace = [
        {
            "step": 1,
            "name": "Request received",
            "status": "complete",
            "detail": "Task accepted by the local demo API; no external service was called.",
        },
        {
            "step": 2,
            "name": "Specialist directory inspected",
            "status": "complete",
            "detail": f"{len(REGISTRY)} registered profiles are available for advisory routing.",
        },
    ]

    if requested_profile is None:
        trace.append({
            "step": 3,
            "name": "Profile selection",
            "status": "complete" if selected_id else "blocked",
            "detail": (
                f"Automatic selection chose {selected_id} for intent '{intent}'."
                if selected_id else "No registered specialist supports this intent."
            ),
        })
    elif isinstance(requested_profile, str) and requested_profile in REGISTRY:
        trace.append({
            "step": 3,
            "name": "Requested profile validated",
            "status": "complete",
            "detail": f"'{requested_profile}' exists in the specialist directory.",
        })
    else:
        trace.append({
            "step": 3,
            "name": "Requested profile validated",
            "status": "blocked",
            "detail": "The requested value is not a valid registered profile identifier.",
        })

    compatible = bool(selected_spec and intent in selected_spec["intents"])
    trace.append({
        "step": 4,
        "name": "Intent compatibility",
        "status": "complete" if compatible else "blocked",
        "detail": (
            f"{selected_id} supports '{intent}'."
            if compatible else decision["reason"]
        ),
    })

    is_disabled = bool(selected_id in DISABLED) if selected_id else False
    trace.append({
        "step": 5,
        "name": "Safety and permission policy",
        "status": "approval_required" if is_disabled else (
            "blocked" if decision["policy"] == "deny" else "complete"
        ),
        "detail": decision["reason"],
    })
    trace.append({
        "step": 6,
        "name": "Final routing decision",
        "status": decision["policy"],
        "detail": (
            f"Selected {selected_id}; execution remains disabled."
            if selected_id else "No specialist was selected; request denied."
        ),
    })

    return {
        "trace_id": trace_id,
        "task": task,
        "intent": intent,
        "requested_profile": requested_profile,
        "decision": decision,
        "trace": trace,
        "safety": {
            "mode": "local_advisory_demo",
            "provider_calls_enabled": False,
            "computer_execution_enabled": False,
            "external_actions_enabled": False,
        },
    }


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "BuddyRouterDemo/1.0"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: Any) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path == "/":
            page = (ROOT / "demo.html").read_bytes()
            self._send(200, page, "text/html; charset=utf-8")
        elif self.path == "/api/health":
            self._json(200, {
                "status": "ok",
                "mode": "local_advisory_demo",
                "execution_enabled": False,
            })
        elif self.path == "/api/profiles":
            self._json(200, {"profiles": discover_profiles()})
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/api/route":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json(400, {"error": "invalid_content_length"})
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._json(413, {"error": "request_body_size_invalid"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = process_request(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._json(400, {"error": "invalid_request", "detail": str(exc)})
            return
        self._json(200, result)

    def log_message(self, format: str, *args: Any) -> None:
        # Keep the demo's terminal output concise and free of submitted task text.
        print("[Buddy Router Demo] " + (format % args))


def main() -> None:
    port = int(os.getenv("BUDDY_ROUTER_DEMO_PORT", "8760"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    print(f"Buddy Router Demo listening on http://127.0.0.1:{port}")
    print("Local-only • advisory routing • provider calls and execution disabled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Buddy Router Demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
