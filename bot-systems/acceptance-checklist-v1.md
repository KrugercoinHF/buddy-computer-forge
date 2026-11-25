# Unified Bot Systems — Acceptance Checklist

- [ ] Recover original Menusbot and Jarvis specs from accessible conversation history
- [ ] Inventory repos, code, branches, PRs and existing contracts; avoid duplicate implementations
- [ ] Define validated profile, skill, menu, task, approval and audit schemas
- [ ] Implement registry validation and deterministic routing tests
- [ ] Implement risk/permission middleware; prove menu and direct-call paths are equivalent
- [ ] Add unavailable-provider and unavailable-capability handling
- [ ] Add approval digest, expiry, actor, idempotency and replay tests
- [ ] Add traceable task feedback/evaluation loop
- [ ] Integrate UI with capability discovery and menu navigation
- [ ] Verify tests and CI on actual commit SHA before claiming success
- [ ] Owner review required before provider calls, computer operations, external effects or deployment
