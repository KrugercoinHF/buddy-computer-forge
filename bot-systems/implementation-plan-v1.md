# Implementation plan — increment 2

1. **Registry validator:** schema validation, unique IDs, profile capability consistency.
2. **Pure routing core:** intent matching with deterministic precedence and explicit unavailable capability.
3. **Policy layer:** risk classification and deny/approval-required decisions; execution intentionally absent.
4. **Menu adapter:** filtered menu generation from registry and actor policy; direct-call policy equivalence.
5. **Trace model:** structured decision records with redaction and stable task IDs.
6. **Fixture-driven tests:** allow/deny, unknown profile, capability missing, disabled profile, expiry/replay design checks, malformed requests.
7. **UI prototype:** display routes, risk, availability and reason; never pretend a menu action executed.

Release gate: all unit tests, security-focused tests, independent review and owner approval before any provider or execution adapter.
