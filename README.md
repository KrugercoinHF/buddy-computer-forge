# Buddy Computer Forge

Buddy Computer Forge is the local control plane for a bounded compute fabric. It provides:

- FastAPI backend with SQLite persistence
- Owner token auth and node-scoped credentials
- Worker heartbeat registration and telemetry
- Queued tasks and claim/lease/retry flow
- Mission planning with ordered tasks
- Approval-gated container execution semantics
- Bounded workspace reads for local worker execution
- Minimal dashboard for overview and task insight

## Local quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
export BUDDY_OWNER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn buddy.main:app --host 127.0.0.1 --port 8741
```

Open:

- http://127.0.0.1:8741/
- http://127.0.0.1:8741/docs

## Windows quick start

```powershell
Set-ExecutionPolicy -Scope Process Bypass
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[test]'
$env:BUDDY_OWNER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
uvicorn buddy.main:app --host 127.0.0.1 --port 8741
```

## Worker quick start

Generate a worker credential in the dashboard or API and start the node worker:

```bash
export BUDDY_NODE_ID='worker-node-id'
export BUDDY_NODE_TOKEN='one-time-node-token'
export BUDDY_SERVER='http://127.0.0.1:8741'
python -m worker.agent --workspace ./workspace
```

## Tests

```bash
pytest
```

## Security notes

- Bind to localhost only unless you intentionally want remote network exposure.
- Keep owner token in a secret manager.
- Container execution is disabled by default.
- Worker file reads are confined to the workspace root.


## AI Boardroom Simulator V1

The isolated Boardroom simulator is available on port 8750:

    export BOARDROOM_OWNER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    uvicorn boardroom_app:app --host 127.0.0.1 --port 8750

Open http://127.0.0.1:8750/. The simulator includes 100 agent profiles, meeting sessions, simulated contributions, advisory voting, minutes and owner-gated proposal decisions. V1 does not connect external AI models or execute actions. See docs/ai-boardroom-simulator-v1.md for architecture and safety boundaries.


## Buddy Computer Programming Agent

The drop-in skill definition is at skills/computer-software-programmer/SKILL.md.
It includes deterministic generation checks, JSONL trace-to-bundle scaffolding,
bundle integrity verification and refusal/governance rules. See
docs/multimodal-system-integration-v1.md for the shared image/audio/video/text
integration boundary. The skill and multimodal design are specifications and
local tools; they do not register themselves in a runtime or enable model,
media-capture or computer-execution access.

Run the skill utility tests with:

    node --test tests/skill-tools.test.js
