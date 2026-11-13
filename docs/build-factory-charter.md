# Buddy Build Factory — Architecture Charter

Status: Approved direction; implementation not yet complete
Owner: Buddy ecosystem owner
Home repository: KrugercoinHF/buddy-computer-forge
Date: 2026-11-13

## Mission

Establish one owner-controlled, platform-independent build system for every Buddy project. Lovable and other hosted builders may be optional interfaces, but no project may depend on them to retain source code, continue development, test, or deploy.

## Operating principles

1. Git repositories are the source of truth. Every meaningful change is committed and recoverable.
2. Each product retains its own repository and release lifecycle. The factory orchestrates projects; it does not indiscriminately merge them.
3. Local execution is the primary development path. Cloud environments are optional alternatives, not single points of failure.
4. Every build produces a recorded result: commit, environment, commands, test results, artifacts, and known limitations.
5. Work is checkpointed at meaningful milestones so interruptions do not erase progress.
6. AI providers are adapters behind a replaceable interface. No provider is assumed connected until credentials, permissions, and a successful test are verified.
7. Secrets stay server-side or in an appropriate local secret store; never commit keys or expose them in browser code.
8. Code execution, deployment, destructive changes, and external side effects require explicit owner approval until the relevant controls are independently tested.
9. Failed builds preserve logs and the last known-good revision. Recovery must be repeatable.
10. Contributions, decisions, authorship preferences, and project provenance are recorded with timestamps and revision references. These records are operational evidence, not a guarantee of legal ownership.

## Shared architecture

- Command centre: project registry, missions, approvals, status, and build history.
- Orchestration API: creates runs, dispatches bounded tasks, records state, and supports retries.
- Build workers: isolated local or remote workers with scoped credentials and workspace boundaries.
- Provider adapters: common interface for optional AI models; per-provider connection and cost status.
- Template catalogue: reusable web, desktop, API, and automation project starters.
- Quality gates: lint, type checks, unit/integration tests, dependency and security checks.
- Artifact store: versioned build outputs and logs, linked to source commits.
- Project memory: decisions, requirements, checkpoints, and contribution/provenance records.

## Initial platform choices

- Existing control-plane foundation: Buddy Computer Forge (FastAPI, SQLite, owner authentication, worker registration, task queue, mission planning, approval-gated execution semantics).
- Existing desktop-shell candidate: Buddy Desktop OS (React, TypeScript, Vite, Electron, Express).
- GitHub: source control, review, version history, and backup.
- Local machine: primary build and test runtime.
- Docker or equivalent isolation: introduce where available and security-reviewed; do not assume it is already configured.
- GitHub Actions: optional CI runner for repeatable checks; local checks must remain possible.

## Project coverage

The factory is intended to support, without merging their repositories:

- Buddy Computer Forge and Buddy Desktop OS
- AutoGenius
- Buddy Racing Group
- Buddy AI Boardroom
- Offline Content Bank
- Skill Forge and future Buddy projects

Each project must register its repository, owner, purpose, stack, required secrets (names only, never values), build/test commands, deployment target, risk level, and approval policy.

## Delivery sequence

### Phase 0 — Baseline and inventory
- Inspect repository trees, branches, recent commits, dependency manifests, test commands, and existing security controls.
- Identify overlap and integration boundaries. Do not merge repositories during the audit.
- Record a baseline and preserve current working states.

### Phase 1 — Shared build contract
- Define a project manifest and standard run lifecycle: queued, running, tests, approval-required, succeeded, failed, cancelled.
- Define structured logs, checkpoints, artifact metadata, retry policy, and failure recovery.
- Add a reusable project template and a minimal local developer workflow.

### Phase 2 — Build orchestration
- Extend the existing control plane only after baseline tests pass.
- Add project registration, build-run records, worker capabilities, and bounded workspace execution.
- Keep execution disabled by default; require explicit approvals for risky actions.

### Phase 3 — Quality and recovery
- Add automated tests, lint/type checks, dependency scanning, secret scanning, and build reproducibility checks.
- Store logs and artifact checksums against the source commit.
- Test interruption, retry, rollback, and worker disconnection scenarios.

### Phase 4 — Provider and product integrations
- Add provider adapters one at a time with explicit user-supplied credentials and connection tests.
- Integrate product repositories through manifests and scoped workers.
- Add deployment adapters only after staging and rollback procedures are verified.

### Phase 5 — Operations
- Publish a dashboard showing project health, current runs, failures, approvals, costs where available, and latest known-good builds.
- Establish regular backups and recovery drills.
- Keep Lovable optional; never make it the only way to edit, build, or deploy.

## Definition of done

A project is onboarded only when its source remains available independently, its build can run from documented commands, tests produce recorded results, failures are recoverable, secrets are protected, and external actions follow its approval policy.

## Current limitations and cautions

This charter records the approved direction; it does not mean the factory is implemented or production-ready. The existing Buddy Computer Forge README documents a FastAPI/SQLite control plane and says container execution is disabled by default. The Buddy Desktop OS README describes starter automation components; their security and operational readiness must be audited before use. No provider connections, deployments, repository merges, or autonomous execution are authorized by this document.

## First implementation task

Complete a read-only technical baseline of Buddy Computer Forge and Buddy Desktop OS, then propose a minimal-diff integration plan with test evidence. Preserve existing project histories and avoid destructive changes.