# Buddy Skill Factory v1 — Controlled Architecture and Bridge

Status: architecture contract plus a **local VS Code proposal/evaluation bridge**. The bridge is a controlled developer integration, not a production Skill Factory service. Agents can prepare candidate changes through VS Code AI assistants; the local bridge captures proposal metadata and supports fixed, digest-pinned Docker checks. Candidates remain quarantined.

Scope: Buddy Agency ecosystem (Buddy Desktop Dashboard, Buddy Computer Forge, BuddyBot, AutoGenius and BattleMind when their source workspaces are verified and connected).

Operating mode: **controlled autonomy**. Agents may propose, generate and test candidates. Only the Owner or an explicitly delegated human approver may promote, publish, distribute or grant capabilities.

## Implemented entry points

- [VS Code toolchain and multimodal contract](VSCODE-TOOLCHAIN-AND-MULTIMODAL.md)
- [VS Code bridge implementation and operating instructions](VSCODE-BRIDGE-IMPLEMENTATION.md)
- Local CLI: `python -m repo_maintainer.skill_factory propose` and `evaluate`
- VS Code Tasks: **Buddy Skill Factory: propose current diff** and **Buddy Skill Factory: evaluate in isolated Docker**
- Tests: `tests/test_skill_factory_bridge.py`

The bridge captures repository/base/head identity, changed paths and a SHA-256 digest. It refuses untracked files that would otherwise be omitted. Evaluation supports only fixed allowlisted checks inside a digest-pinned Docker image, with network disabled, read-only source, no secrets and resource limits. Passing checks create an `awaiting_owner_approval` report—not an approval.

## Goals

1. Discover capability gaps from approved project issues, test failures and repeated workflows.
2. Generate versioned skill packages with explicit inputs, outputs, dependencies and permissions.
3. Test candidates in disposable, resource-limited sandboxes with no ambient credentials or production network access.
4. Evaluate quality, safety, reproducibility and regression risk before promotion.
5. Maintain a provenance-aware registry with immutable versions and rollback.
6. Distribute approved versions to authorized agents through project-specific allowlists.
7. Preserve each project's existing governance, approval gates and execution restrictions.

## Non-goals

- No self-granting permissions, secrets access, production writes, deployment, merging, billing or unrestricted shell/computer control.
- No automatic publication or installation into production agents.
- No assumed AutoGenius or BattleMind repository access.
- No replacement of existing project-specific security controls.

## Logical architecture

`Skill Factory API` → `Discovery Queue` → `Builder / Package Compiler` → `Quarantine Registry` → `Sandbox Runner` → `Evaluator` → `Human Approval Gateway` → `Approved Registry` → `Distribution Broker` → `Agent Runtime`.

Supporting services: policy engine, provenance ledger, artifact store, dependency inventory, audit log, metrics and revocation service.

### Components

| Component | Responsibility | Trust boundary |
|---|---|---|
| Discovery | Convert approved work signals into a skill proposal | Read-only inputs; no execution |
| Builder | Produce manifest, instructions, code and tests | Untrusted candidate output |
| Quarantine registry | Store immutable candidate artifacts | No agent runtime can load candidates |
| Sandbox runner | Execute tests in disposable isolation | No host mounts, secrets or production credentials |
| Evaluator | Score tests, safety, reproducibility and scope | Cannot approve or publish |
| Approval gateway | Record owner decision and permitted target | Human authorization required |
| Approved registry | Store signed immutable versions | Write only through promotion service |
| Distribution broker | Deliver approved version to allowlisted agents | Deny by default; scoped project policy |
| Revocation service | Disable compromised or superseded versions | Immediate deny at runtime |

## Skill lifecycle

`proposed → drafted → quarantined → testing → evaluated → awaiting_owner_approval → approved → distributed → deprecated/revoked`.

A failed test transitions to `rejected` or `needs_revision`. Any material change creates a new version and restarts evaluation. No state transition may skip owner approval for promotion or distribution.

## Cross-project integration

- **Buddy Computer Forge:** host the control-plane proposal and sandbox orchestration interfaces; do not couple skill execution to computer-control privileges.
- **Buddy Desktop Dashboard:** display skill proposals, test evidence, approval requests and distribution status. It must not gain shell execution.
- **BuddyBot:** consume approved, compatible skill packages through a read-only registry client.
- **AutoGenius / BattleMind:** adapters remain disabled until their actual repositories/workspaces and contracts are verified.
- **Buddy Agency Core:** canonical policy, owner approvals, audit and skill catalog.

## Remaining phases

1. **P1 — Registry:** immutable versions, provenance, signatures and revocation metadata.
2. **P2 — Quarantine builder:** deterministic package assembly and static validation.
3. **P3 — Stronger sandbox:** independently reviewed microVM or equivalent isolation for hostile code.
4. **P4 — Evaluator:** expanded tests, policy checks, reproducibility and regression scoring.
5. **P5 — Approval and distribution:** authenticated owner decision, project allowlists, signed artifacts and rollback.
6. **P6 — Observability:** usage, failures, drift, cost where measurable and periodic recertification.

The local Docker runner is not a sufficient boundary for hostile code. The registry API, authenticated approval service, stronger sandbox and distribution broker remain unimplemented. No runtime activation, merge, deployment or skill release is claimed.
