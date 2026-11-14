# Dev meta-wing, skill registry and artifact lifecycle

**Status:** Additive declarative foundation; runtime integrations are not enabled.
**Safety posture:** Existing Boardroom, Forge API, worker and Desktop code are unchanged.

## Architecture decision

The Dev wing is infrastructure (a meta-wing), not a business function. It reports to the CTO and has six construction roles: architect, implementer, reviewer, tester, docs and release. Its HUD lanes describe construction work: spec, build, review, test and release.

Three additive contracts are introduced:

- `wings/dev.json`: meta-wing configuration and an explicitly disabled daily-cycle schedule.
- `skills/registry.json`: versioned, declarative skill inventory. This file does not load skills into a runtime or propagate permissions by itself.
- `pm/artifacts.json`: owner-governed lifecycle records. Chronicle's `dev.event` stream is the intended source of truth; the current file is a seed projection, not a live event-sourced service.

## Lifecycle and evidence

Levels are ordered: SPEC → SCAFFOLDED → RUNNING → MAINTAINED.

- SPEC: specification is complete; no owner-accepted execution evidence has been recorded.
- SCAFFOLDED: artifact exists and the builder supplies a successful run output and exit code.
- RUNNING: owner supplies their own successful run output, exact command, exit code and artifact SHA-256.
- MAINTAINED: production monitoring demonstrates at least seven days without open regressions; owner and CTO approve.

Automated CI results are recorded as observations. They do not silently promote an artifact. An agent cannot promote its own work or claim a run it did not observe. A missing output, non-zero exit code or missing hash blocks promotion.

The initial PM records intentionally remain SPEC because owner-local run evidence has not been supplied. Existing successful CI observations are retained as observations rather than misrepresented as owner verification.

## Release safety

P10-release is an alias for the P10 release gate, not a new independent gate. P0 board approval is required for any production-affecting release. A-release prepares a release request and supporting evidence; it cannot approve, merge, deploy or enable computer execution.

A future release agenda item should be a separate typed request, for example:

```json
{
  "type": "release",
  "artifact": "computer-software-programmer-skill",
  "from": "SCAFFOLDED",
  "to": "RUNNING",
  "evidence_ref": "owner-run-evidence-id"
}
```

This is a proposal contract only. The existing Boardroom meeting API and dashboard are not modified in this increment.

## Daily cycle

The 08:00 cycle in `wings/dev.json` is disabled by default. It is a schedule declaration only: no cron job, background worker, notification or external messaging integration is installed.

## Deliberately deferred

- Runtime skill loader and automatic refusal-rule inheritance.
- Chronicle event writer and replayable PM projection.
- Release-request agenda UI/API.
- Daily scheduler and chat integration.
- Any deployment or computer execution.

These are separate future increments requiring contracts, tests and owner approval. This patch does not alter `boardroom_app.py`, `boardroom_dashboard.html`, `calibrate.js`, existing Forge routes, worker execution or production configuration.
