# Router Contract V1

This is a contract for the next implementation slice; it is not runtime code.

## Request
`task_id`, `trace_id`, `actor`, `intent`, `payload_ref`, `requested_profile` (optional), `risk_hint` (optional), `context_scope`, `created_at`.

## Decision
`trace_id`, `profile_id`, `agent_id`, `capability_ids`, `risk_level`, `policy` (allow/deny/approval_required), `reason`, `missing_capabilities`, `approval_digest` (when applicable).

## Routing sequence
1. Validate request and actor.
2. Resolve intent; reject ambiguous high-risk requests for clarification.
3. Select requested or best matching profile from enabled registry.
4. Confirm declared capabilities and adapter health; unavailable must remain unavailable.
5. Apply actor, scope, risk and permission policy.
6. If consequential, generate action digest and request explicit owner approval; no execution in this slice.
7. Produce recommendation or bounded draft, record provenance.
8. Return decision/result and audit trace.

## Policy invariants
- Registry/menu visibility never confers authorization.
- Provider credentials are not read or exposed by the router.
- No shell, computer, network, account, communication, financial or deployment actions.
- No implicit provider invocation; mock fixtures only for tests.
- Direct tool paths must enforce the same policy as menu paths.
