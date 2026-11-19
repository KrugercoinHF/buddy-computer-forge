# Security and autonomy boundaries

## Default-deny capabilities

| Capability | Default | Gate |
|---|---|---|
| Read repository metadata and files | allowlisted read-only | Repository allowlist |
| Create branch | deny | Explicit owner approval and policy enablement |
| Write candidate files | deny | Isolated worktree and explicit scoped approval |
| Run tests | deny | Exact command allowlist and disposable sandbox |
| Network access from tests | deny | Endpoint allowlist and separate approval |
| Open draft PR | deny | Diff digest and explicit approval |
| Request review | deny | Owner-approved workflow |
| Merge | deny | Human owner action only |
| Deploy, release or publish | deny | Human owner action only |
| Read secrets | prohibited | Never granted to coding agents |

## Separation of duties

The implementer cannot evaluate or approve its own patch. The reviewer cannot modify the candidate. The tester cannot promote artifacts. The approval gateway must authenticate a human owner or delegated approver and bind the decision to the exact diff digest, repository, branch, permissions and expiry.

## Safe execution requirements for future phases

- Disposable sandbox or microVM, non-root, resource, time and output quotas.
- No host mounts, Docker socket, SSH agent, browser profile or ambient credentials.
- Network deny-by-default; dependency installs use a controlled mirror or cache.
- No arbitrary shell supplied by model output. Test commands must match exact allowlisted argument arrays.
- Candidate patch is applied only to an isolated worktree; never overwrite dirty user changes.
- Capture test command, exit code, logs, dependency inventory and artifact digest.
- Redact secrets from logs and never send secrets to model providers.
- Signed audit events; idempotency and correlation IDs for all writes.

## Stop conditions

Stop and request owner review for dirty worktrees, protected-branch changes, migrations, auth or security changes, dependency or license risks, secret exposure, unexplained test failures, broad deletions, generated binary changes, or any request to merge, deploy, spend money or expand permissions.
