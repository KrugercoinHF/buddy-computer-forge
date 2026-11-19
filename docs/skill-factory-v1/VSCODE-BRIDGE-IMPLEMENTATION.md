# VS Code → Skill Factory Bridge — Implementation v1

Status: controlled local integration slice. Candidate generation and proposal capture are implemented; isolated check execution is implemented through a caller-supplied, digest-pinned Docker test image. The Skill Factory API, remote registry, hardened microVM runner, and production distribution broker are not implemented.

## Developer workflow

1. Open the repository in VS Code and use Copilot or Codex to prepare changes on a dedicated feature branch.
2. Review the Git diff. Stage every intended new file; the bridge refuses to silently omit untracked files.
3. Run **Buddy Skill Factory: propose current diff** from VS Code Tasks. This writes a proposal JSON under `.buddy/skill-factory/` with repository/base/head identity, changed paths, patch SHA-256, quarantine state, and approval requirement.
4. Build or obtain an audited test-runner image separately. The image must already contain the required test tools and dependencies; evaluation never installs dependencies or downloads packages.
5. Run **Buddy Skill Factory: evaluate in isolated Docker**. Supply the exact image digest. The bridge invokes only fixed allowlisted commands. Source is mounted read-only; container networking is disabled; no secrets or host credentials are passed; resource limits and a timeout apply.
6. Review the JSON evaluation report and Markdown approval request. A passing evaluation changes the report state to `awaiting_owner_approval`, not `approved`.
7. The Owner reviews the exact patch digest, changed files, checks, requested capabilities and target agents. Any change requires a fresh proposal and evaluation.

## Current check allowlist

- `pytest` → `python -m pytest -q`
- `ruff` → `ruff check .`

The bridge does not accept free-form shell commands, model-generated command strings, arbitrary image tags, network-enabled checks, or caller-supplied environment variables. A digest-pinned image must be supplied. Its contents and provenance must be independently audited before use.

## Trust boundaries and limitations

- VS Code AI extensions are proposal authors, not trusted executors or approvers.
- The bridge records a patch digest and refuses to omit untracked files.
- Docker is configured with no network, read-only root and source mount, dropped Linux capabilities, no-new-privileges, process/memory/CPU limits and a disposable container.
- **A Docker container is not a sufficient boundary for hostile code.** This first runner is a constrained developer check environment, not a hardened multi-tenant sandbox or microVM. Do not use it for malicious/unknown code until the runner is replaced by independently reviewed stronger isolation.
- No credentials, secrets, Docker socket or approval token are mounted in the candidate container.
- Reports are local evidence. They are not signed attestations and are not submitted to a remote approval service.
- The bridge does not create branches, commit, push, open/merge PRs, deploy, publish, install skills or grant permissions.
- There is no CI workflow that executes candidate code with privileged tokens. A future remote runner must use a separately reviewed workflow with minimal permissions and an explicit untrusted-code threat model.

## Manual Owner approval record

The Markdown report is a request, not an approval. The Owner's decision must be recorded outside the candidate process and bind to:
- repository and immutable base/head commit identities;
- patch SHA-256 and exact changed paths;
- evaluation report and runner image digest;
- approved capabilities and target agents;
- decision timestamp, approver identity and expiry.

A changed digest, capability set or target list invalidates the decision. Release remains prohibited until a separate owner-controlled promotion and distribution service exists.
