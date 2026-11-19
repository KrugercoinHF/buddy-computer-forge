import argparse
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from .engine import RepositoryMaintainer
from .policy import MaintainerPolicy


def normalize_github_remote(remote: str) -> str:
    """Normalize HTTPS, SSH URL, or SCP-style GitHub remotes to one canonical URL."""
    value = remote.strip()
    scp = re.fullmatch(r"(?:[^@/:]+@)?github\.com:([^/]+)/([^/]+?)(?:\.git)?", value)
    if scp:
        owner, name = scp.groups()
        return f"https://github.com/{owner}/{name}.git"
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "ssh"} or parsed.hostname != "github.com":
        raise PermissionError("origin must be a GitHub HTTPS or SSH remote")
    if parsed.username not in {None, "git"} or parsed.password or parsed.query or parsed.fragment:
        raise PermissionError("origin contains unsupported credentials or URL components")
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or not all(parts):
        raise PermissionError("origin must identify exactly one GitHub owner/repository")
    return f"https://github.com/{parts[0]}/{parts[1]}.git"


def verify_checkout_origin(root: Path, expected_origin: str) -> None:
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=root, text=True, capture_output=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise PermissionError("checkout has no configured origin remote")
    actual = normalize_github_remote(result.stdout)
    expected = normalize_github_remote(expected_origin)
    if actual != expected:
        raise PermissionError(f"checkout origin mismatch: expected {expected}, found {actual}")


def load_trusted_policy(policy_file: Path, root: Path, repository: str) -> tuple[MaintainerPolicy, str]:
    """Load policy only from a separate, non-writable-by-group/other config file."""
    raw_policy_file = policy_file.expanduser()
    if raw_policy_file.is_symlink():
        raise PermissionError("policy file must not be a symlink")
    policy_file = raw_policy_file.resolve(strict=True)
    root = root.resolve(strict=True)
    if not policy_file.is_file():
        raise PermissionError("policy file must be a regular file")
    try:
        policy_file.relative_to(root)
    except ValueError:
        pass
    else:
        raise PermissionError("trusted policy file must be outside the repository checkout")
    if os.name == "posix" and stat.S_IMODE(policy_file.stat().st_mode) & 0o022:
        raise PermissionError("policy file must not be group- or world-writable")

    config = json.loads(policy_file.read_text(encoding="utf-8"))
    entry = config.get("repositories", {}).get(repository)
    if not isinstance(entry, dict):
        raise PermissionError(f"repository is not in trusted policy: {repository}")
    origin = entry.get("origin")
    branches = entry.get("allowed_base_branches")
    if (
        not isinstance(origin, str)
        or not isinstance(branches, list)
        or not branches
        or not all(isinstance(branch, str) and branch.strip() for branch in branches)
    ):
        raise ValueError("repository policy requires origin and non-empty string allowed_base_branches")
    policy = MaintainerPolicy(
        allowed_repositories=frozenset({repository}),
        allowed_base_branches=frozenset(branches),
    )
    policy.validate_repository(repository)
    return policy, origin


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled-autonomy repository inspection")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--repository", required=True, help="owner/name, must exist in trusted policy")
    parser.add_argument("--policy-file", required=True, help="trusted JSON policy stored outside the checkout")
    parser.add_argument("--base", required=True, help="base branch, must be allowlisted")
    args = parser.parse_args()

    root = Path(args.root).resolve(strict=True)
    policy, expected_origin = load_trusted_policy(Path(args.policy_file), root, args.repository)
    verify_checkout_origin(root, expected_origin)
    maintainer = RepositoryMaintainer(root, args.repository, policy)
    print(json.dumps({
        "inspection": maintainer.inspect(),
        "proposal": maintainer.propose(args.base).to_dict(),
        "automation_mode": "read-only",
        "write_capabilities": "disabled",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
