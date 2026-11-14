# Buddy Agency Integration Plan V1

**Date:** 2026-11-14  
**Status:** Draft architecture contract; no runtime integrations enabled  
**Branch:** `feat/buddy-agency-integration-contract-v1`

## Objective

Connect the Buddy Agency projects through explicit, versioned contracts while keeping each project independently deployable and preserving owner control. This document is a target architecture and implementation plan, not a claim that the ecosystem is already integrated or production-ready.

## System map

- **Owner / final authority:** approves sensitive access, policy changes, releases and production-affecting actions.
- **AI Boardroom:** governance and decision-support layer; proposals, debate, recorded decisions and release recommendations. It does not bypass owner gates.
- **AutoGenius:** central orchestration coordinator. Routes work to approved capabilities; it is not an unrestricted execution authority.
- **BuddyBot:** personal companion interface and offline-agent concept. Receives only explicitly granted context and capabilities.
- **Buddy Knowledge Core:** evidence-backed knowledge and retrieval layer. Stores provenance and distinguishes verified facts, user-provided claims and generated proposals.
- **Buddy Computer Forge:** bounded local-compute control plane. Authentication, scoped workers, approval-gated tasks and audit records remain mandatory.
- **Buddy Desktop OS:** desktop/workstation interface. Any computer-control capability remains disabled unless explicitly enabled through a separate owner-approved security review.
- **Buddy Programming Agent:** software construction skill-set with deterministic checks, tests, bundle verification and refusal rules.
- **BattleMind:** separate AI champion platform; integration is through a narrow API/event contract, not shared unrestricted execution.
- **Multimodal Gateway:** future boundary for text, images, audio, video and screen-derived evidence. Provider calls, capture and uploads require explicit consent and are not enabled by this document.

## Integration principles

1. Each project retains its own repository, runtime, release process and secrets.
2. Integrations use authenticated, least-privilege APIs and versioned schemas.
3. No shared database writes across project boundaries; use documented APIs or event envelopes.
4. Every consequential action records actor, capability, target, approval reference, timestamp, result and correlation ID.
5. Treat model output and retrieved content as untrusted input; validate before use.
6. Fail closed when identity, policy, approval, provenance or required evidence is missing.
7. No agent may approve its own privileged action or promote its own artifact lifecycle status.
8. No automatic deployment, external messaging, remote computer control or production execution is enabled by this plan.

## Initial shared contracts

### 1. Identity and capability

A caller presents a short-lived credential bound to a project, actor and explicit capability set. A capability is scoped to a resource and action; possession of a general agent identity does not imply permission to execute commands, read arbitrary files, access secrets or release software.

### 2. Work request

A work request carries:
- `request_id` and `correlation_id`
- `source_project` and `target_project`
- `requested_capability`
- `task_summary` and bounded input references
- `risk_class`
- `approval_ref` when required
- `created_at` and expiry

The receiver validates schema, caller identity, capability, expiry and policy before accepting work.

### 3. Event envelope

Events carry:
- `event_id`, `event_type`, `schema_version`
- `occurred_at`, `actor`, `source_project`
- `correlation_id`, `subject_ref`
- `payload`, `evidence_refs`
- `previous_hash` and `event_hash` when hash chaining is implemented

Events are append-only at the source. Consumers are idempotent and must tolerate duplicates and out-of-order delivery.

### 4. Approval record

An approval record binds the approver to the exact action, target, scope, risk summary and expiry. Any material change to the action invalidates the approval. Approval is not inferred from silence, a general conversation acknowledgement or a prior approval for another action.

### 5. Artifact lifecycle

Use the existing ordered lifecycle:
- **SPEC:** requirements and acceptance criteria documented.
- **SCAFFOLDED:** implementation exists and builder-run evidence is recorded.
- **RUNNING:** owner independently runs and verifies the artifact with command, exit code, output and SHA-256.
- **MAINTAINED:** at least seven days of production monitoring without open regressions, with owner and CTO approval.

CI success is evidence, but does not by itself establish owner verification or production readiness.

## Repository integration map

| Project | Repository | Integration role | Current boundary |
|---|---|---|---|
| Buddy Computer Forge | `KrugercoinHF/buddy-computer-forge` | Local compute control plane and audit | This branch contains the integration contract only |
| Buddy Desktop OS | `KrugercoinHF/buddy-desktop-dashboard` | Desktop/workstation UI | Separate repository; no changes made |
| BuddyBot | `KrugercoinHF/BuddyBot` | Companion interface | Separate repository; no changes made |
| BattleMind | Existing project repository | AI champion platform | Separate project; integration deferred until its current repository state is inspected |
| AutoGenius | Existing project work | Orchestration | No runtime connection created |
| Buddy Knowledge Core | Existing project work | Evidence and retrieval | No data migration or shared store created |
| AI Boardroom | Forge Boardroom work | Governance and decision support | Existing draft work remains isolated |

## Delivery sequence

### Phase 0 — Baseline and contracts
- Inspect current default-branch state for every participating repository.
- Keep integration work on isolated branches.
- Agree on identity, capability, work-request, event and approval schemas.
- Add schema validation and contract tests before wiring services.

### Phase 1 — Read-only integration
- Add health/status endpoints and authenticated read-only project discovery.
- Establish correlation IDs and provenance metadata.
- Demonstrate a Boardroom proposal that references evidence without executing actions.

### Phase 2 — Gated task routing
- Route a low-risk, non-executing task through AutoGenius to one approved project.
- Require explicit capability checks and approval references for sensitive tasks.
- Record request, decision and result events.

### Phase 3 — Knowledge and multimodal evidence
- Connect Knowledge Core through read-only retrieval first.
- Add multimodal ingestion only with explicit user consent, source provenance and retention rules.
- Keep model/provider credentials isolated per service.

### Phase 4 — Controlled operations
- Consider bounded Forge/desktop operations only after threat modelling, authentication review, sandbox validation, audit verification and explicit owner approval.
- Keep deployment and production release as separate approval decisions.

## Acceptance criteria for the first integrated milestone

- Every project can be identified by stable project ID and declared API/schema version.
- Invalid identity, missing capability, expired approval and malformed requests are rejected.
- A request can be traced end-to-end with one correlation ID.
- Events preserve provenance and are safe to replay idempotently.
- No component can silently elevate permissions.
- Tests prove the above; a demo shows read-only routing only.
- No computer execution, deployment or production write is enabled.

## Immediate next actions

1. Inspect and document the current main-branch state of Buddy Desktop OS, BuddyBot, BattleMind, AutoGenius and Knowledge Core.
2. Add machine-readable JSON Schemas for the work request, event envelope and approval record.
3. Add contract tests and a read-only integration demo.
4. Review the resulting diff and CI evidence before proposing any runtime connection.

---

# Visual design brief: Buddy Agency ecosystem

Create a landscape 16:9 architecture infographic titled **BUDDY AGENCY — THE COMPLETE OPERATING ECOSYSTEM**. Use a premium, legible command-centre blueprint style: deep navy and graphite panels, white typography, cyan/teal/amber accents, precise connectors, clear hierarchy and generous spacing.

Show the owner at the top as final authority; below that, the AI Boardroom governance layer; then parallel business wings and the Dev meta-wing. Explicitly label the Dev wing as infrastructure that builds the system other wings run on, not as another business function. Show the six Dev roles (architect, implementer, reviewer, tester, docs, release) and five lanes (SPEC, BUILD, REVIEW, TEST, RELEASE).

Below them show the shared spine: cognition/HUDs, time/Chronicle, business ledger, governance P0–P10, construction/skills and PM lifecycle. Then show foundation services: AutoGenius, BuddyBot, Buddy Knowledge Core, Buddy Computer Forge, Buddy Desktop OS, Buddy Programming Agent and Multimodal Gateway. Add evidence and verification: hashes, event ledger, manifests, replay frames, verified bundles and CI/test evidence.

On the right show the operating loop: PLAN → BUILD → REVIEW → TEST → OWNER APPROVAL → RELEASE → MONITOR → LEARN. Include the artifact maturity sequence SPEC → SCAFFOLDED → RUNNING → MAINTAINED, with evidence required at each promotion. Add career capabilities: systems architecture, AI orchestration, DevOps/CI, AI governance and safety, multimodal integration, evidence-led delivery.

**Truthfulness:** depict this as a target architecture and phased operating model, not a claim that all services are live, connected or deployed. Do not invent dashboards, integrations, test results or production status.