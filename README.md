# Buddy Computer Forge

Buddy Computer Forge is the local control plane for a bounded compute fabric. It provides a FastAPI backend, SQLite persistence, owner-token authentication, worker telemetry, queued tasks, mission planning, approval-gated execution semantics and bounded workspace reads.

## Local quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
export BUDDY_OWNER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn buddy.main:app --host 127.0.0.1 --port 8741
```

Open http://127.0.0.1:8741/ and http://127.0.0.1:8741/docs.

## Unified Buddy Router — live command deck

Run the local menu-driven routing demo from the repository root:

```bash
python -m buddy_router.demo_server
```

Open http://127.0.0.1:8760/. The interface discovers specialist profiles, accepts a task, supports automatic or manual profile selection, shows the real router's policy decision and displays a six-step trace. It binds to localhost only and requires no additional dependencies. See [buddy_router/README.md](buddy_router/README.md).

The demo is advisory-only: no AI provider calls, external actions, task persistence or computer execution. Computer Forge remains disabled for execution.

## AI Boardroom Simulator V1

Run the existing Boardroom API on localhost port 8750:

```bash
export BOARDROOM_OWNER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn boardroom_app:app --host 127.0.0.1 --port 8750
```

The existing Python service contains 100 agent profiles, meetings, simulated contributions, advisory voting, minutes and owner-gated proposal decisions. It does not connect external AI providers or execute actions.

The new static entry surface is boardroom.html; the read-only replay inspector is player.html. Read INDEX.md for the canonical architecture and safety contract.

## Boardroom developer tools

```bash
node skill.js score
node skill.js verify
node skill.js determinism
node skill.js registry
node calibrate.js
node skills/terminal/scripts/terminal-cli.js help
node ingest.js --help
python nano.py --help
```

The score command measures file presence only. Calibration runs a deterministic local fixture, not a provider benchmark. Media ingest is a scaffold. nano.py is an optional explicitly invoked Gemini image bridge.

## Tests

```bash
pytest
node --test tests/*.test.js
node scripts/validate-dev-config.js
```

## Security boundaries

- Bind services to localhost unless remote exposure is deliberately reviewed.
- Keep credentials in local environment variables or a secret manager; never commit .env.
- Container execution is disabled by default.
- Boardroom decisions record intent only; no automatic execution or deployment.
- Functional wings and skill registry are declarative.
- Lifecycle promotion requires owner evidence; CI success alone does not promote.
- gh-gate.sh is plan-only by default and must not be run with --apply without an explicit owner decision.

See docs/ai-boardroom-simulator-v1.md, INDEX.md and docs/multimodal-system-integration-v1.md.
