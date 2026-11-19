# Security and autonomy boundaries

## Default-deny capabilities

| Capability | Default | Gate |
|---|---|---|
| Read repository metadata and files | allowlisted read-only | Trusted repository policy and verified origin |
| Create branch | deny | Explicit owner approval and policy enablement |
| Write candidate files | deny | Isolated worktree and explicit scoped approval |
| Run tests | CI-only read-only | CI workflow; no write token or secrets |
| Network access from tests | deny | Endpoint allowlist and separate approval |
| Open draft PR | deny | Diff digest and explicit approval |
| Request review | deny | Owner-approved workflow |
| Merge | deny | Human owner action only |
| Deploy, release or publish | deny | Human owner action only |
| Read secrets | prohibited to coding agents | Never granted to coding agents |

## Approval authenticity

- A caller-supplied name is not proof of identity and must never create an approval.
- Approval records require a configured `ApprovalGateway` implementation.
- The gateway must verify a cryptographic signature issued by the trusted owner-approval service.
- The signed claims must bind repository, proposal digest, exact approved capability scope, issuer/audience, expiry and a unique token ID.
- The gateway must atomically reject replayed token IDs and reject revoked or expired approvals.
- The maintainer records the gateway-verified subject, token ID, verifier, expiry and proposal digest.
- No built-in fake gateway, local self-approval or agent-controlled signing key is provided.

The protocol in this repository defines the trust boundary; production use requires a separately deployed gateway and durable replay store. Until that service is configured, approval-dependent operations fail closed.

## Repository identity

- The CLI requires a trusted JSON policy file outside the checkout.
- The policy file must not be a symlink or group/world-writable on POSIX systems.
- The repository name must be explicitly present in the policy.
- The checkout's configured `origin` must normalize to the exact trusted GitHub owner/repository URL.
- The requested base branch must be in that repository's explicit branch allowlist.
- The repository name supplied on the command line is never used to construct its own allowlist.

The local policy file is an administrative trust anchor. Store it in a user-owned configuration directory and protect it from modification by build agents.

## Workflow boundary

- CI has `contents: read` only and no secrets.
- CI runs tests; it does not commit, create branches, open PRs, merge or deploy.
- Workflow triggers include pushes, pull requests and manual dispatch on all branches.
- Do not add `pull_request_target`, write permissions, self-hosted runners or privileged secrets to this workflow.
- Any future privileged job must use a separate job and explicit owner approval; it must not share credentials with coding or test agents.

## Separation of duties

The implementer cannot evaluate or approve its own patch. The reviewer cannot modify the candidate. The tester cannot promote artifacts. Release is proposal-only.

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
