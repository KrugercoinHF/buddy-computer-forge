# Buddy Skill Factory v1 — Architecture Proposal

Status: **architecture-only proposal; not runtime-enabled**  
Scope: Buddy Agency ecosystem (Buddy Desktop Dashboard, Buddy Computer Forge, BuddyBot, AutoGenius and BattleMind when their source workspaces are verified and connected).  
Operating mode: **controlled autonomy**. Agents may propose, generate and test skills in isolated sandboxes. Only the Owner or an explicitly delegated human approver may promote, publish, distribute or grant capabilities.

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

## Delivery phases

1. **P0 — Contracts and threat model:** manifest, lifecycle, permissions, audit events and approval policy.
2. **P1 — Registry:** immutable versions, provenance, signatures and revocation metadata.
3. **P2 — Quarantine builder:** deterministic package assembly and static validation; no execution.
4. **P3 — Sandbox runner:** disposable isolation, resource quotas, network deny-by-default and evidence capture.
5. **P4 — Evaluator:** tests, policy checks, reproducibility and regression scoring.
6. **P5 — Approval and distribution:** explicit owner decision, project allowlists, signed artifacts and rollback.
7. **P6 — Observability:** usage, failures, drift, cost where measurable and periodic recertification.

Each phase requires a separate reviewed implementation PR. Security-boundary phases require explicit owner approval before implementation or activation.
