# Shared contracts index

Canonical detailed contracts live in skills/computer-software-programmer/references/contracts.md. Seven shared envelopes:

1. agent_profile — stable agent ID, role, wing, mandate and provider mode.
2. meeting_event — event ID, meeting ID, event type, UTC timestamp and schema version.
3. evidence_item — claim, source locator, capture time, content hash and reviewer state.
4. cost_event — wing, operation, provider, token counts, currency, amount and timestamp.
5. artifact_record — artifact ID, path, lifecycle level, owner and evidence references.
6. approval_decision — subject, decision, approver, rationale and timestamp.
7. gt_event — media-derived timestamped observation with provenance, confidence and human-review state.

Payloads are versioned, timestamps are UTC ISO-8601, IDs are stable strings, and sensitive content is minimized. Unknown fields must not be treated as verified facts.
