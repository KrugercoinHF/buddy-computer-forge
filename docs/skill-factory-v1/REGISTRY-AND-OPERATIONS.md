# Skill Registry and Operations

## Registry records

The registry stores immutable package metadata and content-addressed artifacts. Minimum record types:

- Skill identity and version.
- Artifact digest and signature.
- Source provenance and dependency inventory.
- Requested capabilities and effective approved capabilities.
- Validation and sandbox evidence.
- Independent review record.
- Owner approval bound to digest and targets.
- Distribution/install inventory.
- Runtime health and usage metrics.
- Deprecation, revocation and rollback events.

Candidate, approved and revoked records are separate states. Candidate packages are never discoverable by production agent runtimes.

## Suggested service interfaces

These are proposed contracts; no endpoints are implemented by this documentation change.

| Interface | Purpose | Authorization |
|---|---|---|
| POST /skill-proposals | Submit capability gap | Agent identity; proposal only |
| POST /skill-candidates | Upload candidate to quarantine | Builder identity; digest required |
| POST /skill-tests | Request isolated evaluation | Scheduler identity; quotas enforced |
| GET /skill-evaluations/{id} | Read evidence | Project read permission |
| POST /skill-approvals | Record owner decision | Owner approval gateway only |
| POST /skill-distributions | Distribute approved digest | Owner-authorized broker |
| POST /skill-revocations | Revoke a version | Owner/security authority |
| GET /skills | List approved compatible skills | Agent/project allowlist |

All writes require idempotency keys, audit correlation IDs, schema validation and explicit actor identity. Approval endpoints must reject service-agent identities.

## Audit events

Record append-only events: proposal.created, candidate.uploaded, validation.completed, sandbox.started, sandbox.completed, evaluation.completed, approval.requested, approval.granted, approval.denied, version.promoted, distribution.completed, distribution.failed, version.revoked and rollback.completed.

Events include actor, project, skill/version, artifact digest, timestamp, correlation ID, decision and evidence references. Never include raw credentials, secret values or sensitive user content.

## Quality metrics

- Proposal-to-accepted ratio.
- Candidate build reproducibility.
- Test pass rate and escaped defect rate.
- Policy violation and sandbox-denial rates.
- Mean time from proposal to reviewed decision.
- Skill invocation success and regression rate.
- Revocation propagation time.
- Resource consumption and cost where measurable.

Metrics must not incentivize unsafe permission expansion or automatic approval.

## Operational ownership

- Owner: final authority for promotion, distribution and consequential changes.
- Skill Architect: contract and architecture proposals.
- Builder: candidate generation only.
- Sandbox Operator: isolated execution only.
- Evaluator: evidence and recommendation only.
- Independent Reviewer: security, scope and test review.
- Registry Maintainer: immutable storage and metadata integrity.
- Distribution Broker: approved artifact delivery only.

No role may combine builder, evaluator and approver authority into one autonomous identity.
