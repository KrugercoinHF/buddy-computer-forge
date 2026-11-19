# Skill Package Contract v1

This is a proposed data contract, not an executable permission grant.

## Required manifest fields

| Field | Type | Rule |
|---|---|---|
| skill_id | stable string | Namespaced, immutable identity |
| name | string | Human-readable title |
| version | SemVer | Immutable release version |
| description | string | Capability and limitations |
| owner_project | string | Verified project identifier |
| author | string | Agent or human provenance identity |
| created_at | ISO-8601 UTC | Creation timestamp |
| source_refs | list | Approved issue/commit/document references |
| inputs | list | Typed, validated input contract |
| outputs | list | Typed output contract |
| dependencies | list | Exact versions and integrity digests |
| permissions_requested | list | Declarative least-privilege request |
| network_policy | object | Default deny; explicit destinations only |
| resource_limits | object | CPU, memory, time, storage and output caps |
| tests | list | Reproducible test entrypoints and expected results |
| compatibility | object | Runtime and API compatibility |
| provenance | object | Source commit, builder version and artifact digest |
| approval | object | Required approval state and approver record |

## Permission vocabulary

Allowed declarations are descriptive capabilities, not direct grants:

- `read:project-artifacts`
- `read:approved-knowledge`
- `write:quarantine-artifact`
- `network:allowlisted-endpoint` (requires explicit policy)
- `invoke:approved-tool` (requires tool-specific authorization)

Never accept wildcard permissions such as `*`, unrestricted filesystem access, arbitrary shell, credential-store access, production database access, or permission escalation. A skill cannot approve its own requested permissions.

## Versioning

- Patch: documentation or backward-compatible bug fix.
- Minor: backward-compatible capability addition.
- Major: breaking inputs, outputs, dependencies or policy contract.
- Published versions are immutable. Corrections create a new version.
- Revocation is a separate registry state and must be enforced by distribution clients.

## Integrity and provenance

Every artifact receives a cryptographic digest. The registry records the source revision, builder identity/version, dependency digests, test evidence, evaluator version, approval identity and distribution targets. Signatures are verified before installation. Secrets must never be stored in manifests, logs or artifacts.

## Example (illustrative only)

```yaml
apiVersion: buddy.agency/v1
kind: Skill
metadata:
  skill_id: buddy.example.document-summarizer
  name: Document Summarizer
  version: 0.1.0
spec:
  owner_project: buddy-agency
  inputs:
    - name: document_ref
      type: approved_artifact_reference
  outputs:
    - name: summary
      type: markdown
  permissions_requested:
    - read:project-artifacts
  network_policy:
    default: deny
    allow: []
  resource_limits:
    wall_time_seconds: 30
    memory_mb: 256
    storage_mb: 32
  tests:
    - id: summarize-fixture
      command: "REQUIRES_APPROVED_SANDBOX_RUNNER"
  approval:
    required: true
    state: awaiting_owner_approval
```

The example is documentation only; the placeholder command must not be executed.
