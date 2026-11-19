# Autonomous Repository Maintainer and Developer v2

Status: controlled automation foundation. Read-only inspection and CI are enabled; privileged automation remains disabled.

## Mission

Operate as the Buddy Agency Dev meta-wing: inspect approved repositories, turn verified issues and CI failures into scoped work plans, propose code changes, run approved tests, and prepare draft pull requests. It is not an unrestricted coding agent.

## Agent roles

- A-architect: translate owner goals into contracts and technical plans.
- A-implementer: produce candidate patches in an isolated feature branch or worktree.
- A-reviewer: independently inspect diffs, permissions and architecture.
- A-tester: run allowlisted tests in a disposable sandbox.
- A-docs: update docs and changelogs with provenance.
- A-release: prepare release notes and a release proposal; cannot publish.

## Implemented in this phase

- Read-only Git inspection and deterministic maintenance proposals.
- Gateway-verified approval evidence bound to the exact proposal digest and requested scope.
- No approval from a caller-supplied name; absent or invalid gateway evidence fails closed.
- External trusted policy file, explicit repository allowlist, expected GitHub origin verification and base-branch allowlist.
- CI workflow for pushes, pull requests and manual dispatch across branches.
- CI token permissions are read-only; no secrets or write-capable automation credentials are exposed.

## Local policy setup

Create a trusted JSON policy file outside the repository checkout, for example in a user-owned configuration directory:

    {
      "repositories": {
        "KrugercoinHF/buddy-computer-forge": {
          "origin": "https://github.com/KrugercoinHF/buddy-computer-forge.git",
          "allowed_base_branches": ["feat/buddy-skill-factory-architecture-v1"]
        }
      }
    }

Protect it from agent modification (on POSIX, use `chmod 600 trusted-policy.json`). Then run:

    python -m repo_maintainer.cli . \
      --repository KrugercoinHF/buddy-computer-forge \
      --policy-file /secure/path/trusted-policy.json \
      --base feat/buddy-skill-factory-architecture-v1

The CLI refuses policy files inside the checkout, writable-by-group/other files, unknown repositories, mismatched Git origins and unapproved base branches.

## Approval gateway contract

Production integration must provide an `ApprovalGateway` that verifies a signed owner-approval token and returns `VerifiedApproval` only after checking issuer, audience, signature, repository, proposal digest, exact scope, expiry, revocation and one-time token ID. The gateway must use a durable atomic replay store. No gateway is configured by default, so approval-dependent operations are denied.

## Automation status

The GitHub Actions workflow runs the Python test suite on branch pushes, pull requests and manual dispatch. It has read-only repository permissions. It does not write files, create commits or branches, open PRs, merge, deploy, or access secrets.

No background scheduler, autonomous patch generation, sandbox executor, GitHub write adapter, AutoGenius connection or BuddyEco approval service is activated in this phase. Those require separate integration and owner authorization.

## Integration direction

- Buddy Agency Core / BuddyEco: canonical identity, policy, approvals, audit and budgets.
- AutoGenius: task orchestration, leases, retries and result ownership.
- Buddy Computer Forge: isolated worker and sandbox execution after security validation.
- GitHub: read issues, PRs, commits and CI; propose write actions behind approval.
- Buddy Knowledge Core: approved docs and provenance.

## Next acceptance gate

Before any code-writing agent is enabled: deploy and independently test the approval gateway; configure trusted policy outside the checkout; provision an isolated disposable sandbox; add a read-only monitor; require independent review and test evidence; then obtain explicit owner approval for each capability expansion. Merge and deployment remain owner actions.
