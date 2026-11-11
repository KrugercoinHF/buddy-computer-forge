import json
from pathlib import Path
from typing import Any

from .config import WORKSPACE_ROOT

ALLOWED_EXTENSIONS = {".py", ".md", ".txt", ".json"}
MAX_READ_BYTES = 200_000


def safe_workspace_path(rel_path: str) -> Path:
    if not isinstance(rel_path, str) or not rel_path.strip():
        raise ValueError("path is required")
    root = WORKSPACE_ROOT.resolve()
    candidate = (root / rel_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("path escapes workspace")
    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("file extension is not allowed")
    return candidate


def list_workspace_files() -> list[str]:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    return sorted(str(p.relative_to(WORKSPACE_ROOT)) for p in WORKSPACE_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS)


def read_workspace_file(rel_path: str) -> str:
    path = safe_workspace_path(rel_path)
    if not path.is_file():
        raise FileNotFoundError(rel_path)
    if path.stat().st_size > MAX_READ_BYTES:
        raise ValueError("file exceeds maximum read size")
    return path.read_text(encoding="utf-8")


def write_workspace_note(rel_path: str, content: str) -> str:
    path = safe_workspace_path(rel_path)
    if path.suffix.lower() not in {".md", ".txt", ".json"}:
        raise ValueError("notes may only be .md, .txt, or .json")
    if len(content.encode("utf-8")) > MAX_READ_BYTES:
        raise ValueError("content exceeds maximum size")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path.relative_to(WORKSPACE_ROOT))


def parse_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}
