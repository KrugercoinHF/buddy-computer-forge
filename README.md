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
