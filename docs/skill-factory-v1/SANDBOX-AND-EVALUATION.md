# Sandbox, Evaluation and Security Gates

## Threat model

Treat generated instructions, source code, dependencies, model output, test fixtures and tool responses as untrusted. A skill may be malformed, malicious, prompt-injected, resource-exhausting, exfiltrating or designed to escape its intended scope.

## Sandbox requirements

A future implementation must provide:

- Disposable per-run isolation; destroy the environment after completion.
- Non-root execution, syscall/container hardening and restricted process tree.
- No host Docker socket, host home directory, browser profile, SSH agent or credential mounts.
- No production secrets, owner tokens, worker tokens or connected-app credentials.
- Network disabled by default; deny DNS and outbound traffic unless a reviewed test fixture explicitly needs an allowlisted endpoint.
- Read-only base image and explicit temporary workspace.
- CPU, memory, process, wall-clock, storage and output-size quotas.
- Immutable test inputs and captured stdout/stderr with secret redaction.
- Artifact digest before and after testing; no mutation of source repositories.
- Separate identity for builder, runner, evaluator and approver.
- Runner cannot access approval or registry-promotion credentials.

A container alone is not a sufficient security boundary for hostile code. Select an isolation technology appropriate to the deployment threat model (for example, microVM or hardened sandbox runtime) and validate escape resistance before executing untrusted skills.

## Evaluation gates

Every candidate must pass:

1. Manifest schema and policy validation.
2. Static analysis, dependency/license inventory and known-vulnerability checks.
3. Unit and contract tests with deterministic fixtures.
4. Negative tests for unauthorized filesystem, network, process and tool access.
5. Reproducibility check using a clean environment and pinned dependencies.
6. Resource-limit and timeout tests.
7. Prompt-injection and untrusted-input handling tests where the skill consumes language or documents.
8. Regression suite for the target project.
9. Provenance and artifact-integrity verification.
10. Independent review of diff, permissions, dependencies, tests and evidence.

A pass is evidence for review, not permission to publish.

## Promotion gate

The evaluator produces a signed report containing artifact digest, test commands, exit codes, test totals, policy findings, dependency inventory, resource use and evaluator version. The Owner sees the exact version, requested permissions, target agents and rollback plan.

Only an explicit owner approval may authorize promotion. Approval is bound to the exact artifact digest, version, permissions and distribution targets. Any change invalidates the approval.

## Distribution controls

- Default deny; per-project and per-agent allowlists.
- Verify signature and digest at install and load time.
- Install immutable versions; no floating `latest`.
- Capability tokens are short-lived, scoped and revocable.
- No skill may modify the registry, policy engine or approval gateway.
- Canary only in a non-production test cohort after owner approval.
- Monitor invocation, error rate, resource consumption and policy denials.
- Emergency revocation blocks future loads and invalidates active grants where technically possible.

## Rollback

Distribution broker returns agents to the last approved compatible version. Registry retains revoked metadata and audit history. Never rewrite published artifacts or delete audit evidence. Rollback does not undo external side effects; skills with side effects require explicit compensating-action plans before approval.

## Explicitly prohibited

No self-approval, permission escalation, unrestricted shell/computer control, production write access, secret extraction, deployment, merge, spending or policy bypass.
