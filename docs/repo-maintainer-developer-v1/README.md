# Autonomous Repository Maintainer and Developer v1

Status: controlled prototype; read-only inspection and proposal generation only.

## Mission

Operate as the Buddy Agency Dev meta-wing: maintain approved repositories, turn verified issues and CI failures into scoped work plans, propose code changes, run approved tests, and prepare draft pull requests. It is not an unrestricted coding agent.

## Agent roles

- A-architect: translate owner goals into contracts and technical plans.
- A-implementer: produce candidate patches in an isolated feature branch or worktree.
- A-reviewer: independently inspect diffs, permissions and architecture.
- A-tester: run allowlisted tests in a disposable sandbox.
- A-docs: update docs and changelogs with provenance.
- A-release: prepare release notes and a release proposal; cannot publish.

## Runtime lanes

specification, build, review, test, release-proposal. Each lane emits a versioned artifact, actor identity, source refs, evidence and correlation ID. The implementer cannot approve its own work. Reviewer and tester are separate identities. Release is proposal-only.

## Implemented in this first slice

- Local Git inspection: branch, HEAD, tracked files and dirty-worktree detection.
- Read-only quality-gate findings for README, tests and GitHub Actions CI.
- Deterministic proposal IDs and structured work proposals.
- Repository and base-branch allowlists.
- Capability flags defaulting to deny for branch creation, file writes, PR creation, merge, deployment and network tests.
- Human approval record bound to a proposal digest and explicit scope.
- Adapter contracts for GitHub, coding agents and approval gateways.
- Unit tests for inspection, policy denial and dirty-worktree detection.

## Not implemented or enabled

No autonomous patch generation, GitHub write adapter, remote issue or CI polling, sandbox runner, background scheduler, automatic commits, merges, deployments or secrets access. These are separate phases and require independent security review and explicit owner approval.

## Quick start

From the repository root:

    python -m repo_maintainer.cli --repository KrugercoinHF/buddy-computer-forge .
    pytest tests/test_repo_maintainer.py

The CLI only inspects and prints a proposal. It does not write files or call GitHub.

## Planned integration

- Buddy Agency Core / BuddyEco: canonical identity, policy, approvals, audit and budgets.
- AutoGenius: task orchestration, leases, retries and result ownership.
- Buddy Computer Forge: isolated worker and sandbox execution after security validation.
- GitHub: read issues, PRs, commits and CI; propose branch and PR actions behind approval.
- Buddy Knowledge Core: retrieve approved repository docs, design records and provenance.

## Acceptance target for next phase

A single repo run should produce a reproducible report containing repository identity, base and head SHA, open issue and PR references, failing CI evidence, prioritized work proposals, test plan, risk classification and owner approval requirements. No merge or deployment is in scope.
