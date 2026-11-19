import argparse
import json
from pathlib import Path
from .engine import RepositoryMaintainer
from .policy import MaintainerPolicy

def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled-autonomy repository inspection")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--repository", required=True, help="owner/name, must be allowlisted")
    parser.add_argument("--base", default="main")
    args = parser.parse_args()
    policy = MaintainerPolicy(allowed_repositories=frozenset({args.repository}))
    maintainer = RepositoryMaintainer(Path(args.root), args.repository, policy)
    print(json.dumps({"inspection": maintainer.inspect(), "proposal": maintainer.propose(args.base).to_dict()}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
