# Initial Static Baseline — Buddy Build Factory

Date: 2026-11-13
Scope: Read-only source inspection of the current default-branch files in Buddy Computer Forge and Buddy Desktop OS.
Execution status: No application was launched; no tests were run in a runtime. Findings below are static observations, not a penetration test.

## Executive decision

Use Buddy Computer Forge as the initial control-plane foundation. Treat Buddy Desktop OS as a candidate user interface only after security remediation. Do not connect the desktop automation endpoints to the central factory or expose this service to a network yet.

## Repository observations

### Buddy Computer Forge

- Python package requires Python >=3.11.
- FastAPI and SQLite are the current backend foundation.
- The README documents owner-token authentication, node-scoped credentials, worker heartbeat/telemetry, queued tasks, retries, mission planning, and approval-gated container execution semantics.
- The README says container execution is disabled by default and recommends localhost binding.
- The visible test file currently covers health, missing owner-token behavior, and workspace path traversal. This is a small baseline, not proof of complete security or functional coverage.
- The visible application code defines owner-token validation and workspace path controls. These are useful foundations to preserve.

### Buddy Desktop OS

- The package uses React, TypeScript, Vite, Electron, Express, Playwright, WebSocket, and RobotJS.
- The dev UI script binds Vite to 0.0.0.0, which exposes the development server on network interfaces unless the environment/firewall restricts it.
- Express enables permissive CORS and exposes task creation, task approval, task execution, filesystem listing, browser, and desktop automation routes in the inspected server file.
- The inspected task approval route changes a task to approved without authenticating the caller.
- The inspected task execution route runs command/browser/filesystem operations without applying the approval classifier first.
- The imported approval helper is applied to mouse and keyboard endpoints, but that does not secure the other routes.
- The Electron preload exposes a runCommand bridge; the main process executes the supplied command through a shell. This is a high-risk capability and needs a strict, narrow, owner-authorized command policy before use.
- The inspected server keeps tasks in an in-memory Map, so those task records do not survive a server restart.
- Electron enables contextIsolation and disables nodeIntegration, which are positive defaults, but sandbox is explicitly false in the inspected window configuration. Review whether it can be enabled safely.

## Priority blockers before integration

1. Add authentication and authorization to every state-changing and sensitive API route; do not rely on UI visibility.
2. Enforce approval server-side for every high/medium-risk action, including command execution, browser actions, file access/writes, and desktop control.
3. Remove arbitrary shell-command execution from the general-purpose API and Electron bridge; replace it with an allowlisted task catalogue and isolated worker.
4. Replace wildcard CORS with an explicit trusted-origin policy; bind development services to localhost by default.
5. Add request validation, rate limits, audit events, bounded execution time/output, and safe error handling.
6. Persist task lifecycle state and approval evidence in a durable store.
7. Review Electron sandboxing, navigation restrictions, IPC argument validation, and preload exposure.
8. Add tests for unauthenticated access, approval bypass, command injection, path traversal, worker isolation, restart recovery, and permission boundaries.

## Recommended integration boundary

- Buddy Computer Forge owns project registry, missions, workers, task state, audit history, and approval policy.
- Buddy Desktop OS is a client interface. It must call authenticated control-plane APIs; it must not independently execute unrestricted commands.
- Product repositories remain separate and are onboarded through project manifests.
- AI provider integrations are optional adapters and cannot bypass project permissions or approval gates.

## Next safe engineering increment

Create a feature branch and implement the project manifest plus build-run record model in Buddy Computer Forge, with tests first. Keep worker execution disabled during this increment. In parallel, prepare a separate hardening branch for Buddy Desktop OS; do not deploy or merge it until the blockers above have tests demonstrating the fixes.

## Verification boundary

This report is based on the inspected README, pyproject.toml, one test module, FastAPI application source, and selected Electron/Express source files. No runtime, dependency audit, secret scan, complete repository scan, or external security assessment has been performed.