"""VS Code → Buddy Skill Factory proposal and isolated-evaluation bridge.

Candidate code is never executed on the host. Evaluation uses a digest-pinned
Docker image, read-only source mount, no network, no secrets and fixed commands.
This is a constrained container boundary, not a claim of microVM-grade isolation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ALLOWED_CHECKS: dict[str, tuple[str, ...]] = {
    "pytest": ("python", "-m", "pytest", "-q"),
    "ruff": ("ruff", "check", "."),
}
IMAGE_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
MAX_LOG_BYTES = 64_000


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_proposal(root: Path, repository: str, base: str) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("workspace must be an existing directory")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be owner/name")
    head = git(root, "rev-parse", "HEAD")
    base_sha = git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    untracked = [line for line in status.splitlines() if line.startswith("??")]
    if untracked:
        raise ValueError("untracked files must be reviewed and git-added before proposal capture")
    patch = subprocess.run(
        ["git", "diff", "--binary", "--no-ext-diff", base, "--"],
        cwd=root, capture_output=True, check=True,
    ).stdout
    if not patch:
        raise ValueError("no candidate diff found against the selected base")
    digest = sha256(patch)
    changed = git(root, "diff", "--name-only", base, "--").splitlines()
    proposal_id = f"skill-proposal-{digest[:16]}"
    return {
        "schema_version": "buddy.skill-proposal/v1",
        "proposal_id": proposal_id,
        "repository": repository,
        "base_ref": base,
        "base_sha": base_sha,
        "head_sha": head,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "patch_sha256": digest,
        "patch_bytes": len(patch),
        "changed_files": changed,
        "worktree_dirty": bool(status),
        "requested_capabilities": [],
        "requested_targets": [],
        "state": "quarantined",
        "requires_owner_approval": True,
        "release_allowed": False,
    }


def validate_image(image: str) -> None:
    if not IMAGE_RE.fullmatch(image):
        raise ValueError("sandbox image must be pinned by full sha256 digest (image@sha256:<64 hex>)")


def run_isolated_check(root: Path, image: str, check_name: str, timeout: int = 600) -> dict:
    validate_image(image)
    if check_name not in ALLOWED_CHECKS:
        raise PermissionError(f"check is not allowlisted: {check_name}")
    source = root.resolve()
    if not source.is_dir():
        raise ValueError("workspace must be an existing directory")
    command = [
        "docker", "run", "--rm",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--pids-limit=128",
        "--memory=1g",
        "--cpus=2",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=64m",
        "--env=HOME=/tmp",
        "--env=PYTHONDONTWRITEBYTECODE=1",
        "--env=PYTEST_ADDOPTS=-p no:cacheprovider",
        "--mount", f"type=bind,src={source},dst=/workspace,readonly",
        "--workdir=/workspace",
        "--user=65532:65532",
        image,
        *ALLOWED_CHECKS[check_name],
    ]
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(
            command, cwd=source, text=True, capture_output=True,
            timeout=timeout, check=False, env={"PATH": "/usr/bin:/bin"},
        )
        return {
            "check": check_name, "command": list(ALLOWED_CHECKS[check_name]),
            "exit_code": result.returncode, "passed": result.returncode == 0,
            "stdout": result.stdout[-MAX_LOG_BYTES:], "stderr": result.stderr[-MAX_LOG_BYTES:],
            "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
            "sandbox_image": image, "network": "disabled",
            "source_mount": "read-only", "secrets_provided": False,
        }
    except FileNotFoundError as exc:
        raise RuntimeError("Docker CLI is unavailable; no check was run") from exc
    except subprocess.TimeoutExpired as exc:
        def tail(value):
            if value is None:
                return ""
            return value.decode(errors="replace") if isinstance(value, bytes) else value
        return {
            "check": check_name, "command": list(ALLOWED_CHECKS[check_name]),
            "exit_code": None, "passed": False, "timed_out": True,
            "stdout": tail(exc.stdout)[-MAX_LOG_BYTES:],
            "stderr": tail(exc.stderr)[-MAX_LOG_BYTES:],
            "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
            "sandbox_image": image, "network": "disabled",
            "source_mount": "read-only", "secrets_provided": False,
        }


def write_report(report: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{report['proposal_id']}-evaluation.json"
    md_path = out_dir / f"{report['proposal_id']}-approval-request.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    checks = report["checks"]
    heading = "Owner Approval Request" if report["evaluation_passed"] else "Evaluation Report — Changes Required"
    lines = [
        f"# Buddy Skill Factory — {heading}", "",
        f"- Proposal: `{report['proposal_id']}`",
        f"- Repository: `{report['repository']}`",
        f"- Patch SHA-256: `{report['patch_sha256']}`",
        f"- Base: `{report['base_ref']} ({report['base_sha']})`",
        f"- Candidate HEAD: `{report['head_sha']}`",
        f"- Evaluation: **{report['state']}**",
        "- Requested capabilities: none",
        "- Requested distribution targets: none", "",
        "## Evaluation checks", "",
    ]
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {status} — {check['check']} (exit: {check['exit_code']})")
    lines += [
        "", "## Owner decision", "",
        "This report is evidence for review, not approval. The candidate remains quarantined.",
        "Approval must identify this exact patch digest, requested capabilities and target agents.",
        "Any patch, permission or target change requires a new evaluation and approval.",
        "No merge, deployment, publication or distribution was performed.", "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def evaluate(root: Path, repository: str, base: str, image: str,
             check_names: Sequence[str], out_dir: Path) -> dict:
    proposal = build_proposal(root, repository, base)
    checks = [run_isolated_check(root, image, name) for name in check_names]
    passed = bool(checks) and all(item["passed"] for item in checks)
    report = dict(proposal)
    report.update({
        "state": "awaiting_owner_approval" if passed else "needs_revision",
        "checks": checks,
        "evaluation_passed": passed,
        "recommendation": "request_owner_review" if passed else "revise_candidate",
        "release_allowed": False,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    })
    json_path, md_path = write_report(report, out_dir)
    report["report_files"] = [str(json_path), str(md_path)]
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Buddy Skill Factory VS Code bridge")
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("propose", "evaluate"):
        cmd = sub.add_parser(action)
        cmd.add_argument("--workspace", default=".")
        cmd.add_argument("--repository", required=True)
        cmd.add_argument("--base", default="buddy-agency-integration")
        cmd.add_argument("--out", default=".buddy/skill-factory")
        if action == "evaluate":
            cmd.add_argument("--sandbox-image", required=True)
            cmd.add_argument("--checks", nargs="+", choices=sorted(ALLOWED_CHECKS), default=["pytest"])
    args = parser.parse_args(argv)
    root = Path(args.workspace)
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    try:
        if args.action == "propose":
            proposal = build_proposal(root, args.repository, args.base)
            out.mkdir(parents=True, exist_ok=True)
            path = out / f"{proposal['proposal_id']}.json"
            path.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"proposal": proposal["proposal_id"], "patch_sha256": proposal["patch_sha256"],
                              "state": proposal["state"], "file": str(path)}, indent=2))
            return 0
        report = evaluate(root, args.repository, args.base, args.sandbox_image, args.checks, out)
        print(json.dumps(report, indent=2))
        return 0 if report["evaluation_passed"] else 2
    except (ValueError, PermissionError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"skill-factory: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
