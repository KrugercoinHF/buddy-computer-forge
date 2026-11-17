# Buddy Computer Forge

Buddy Computer Forge is the local control plane for a bounded compute fabric. It provides:

- FastAPI backend with SQLite persistence
- Owner bearer-token authentication
- Owner-issued, one-time worker enrollment codes
- Node-scoped worker credentials with centralized authentication
- Node revocation and token rotation
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

## Owner-issued worker enrollment

1. Create a one-time enrollment invitation as the owner:

```bash
curl -X POST http://127.0.0.1:8741/api/nodes/enrollments \
  -H "Authorization: Bearer $BUDDY_OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"node_id":"worker-01","name":"Workshop PC","ttl_minutes":15}'
```

2. Copy the returned `enrollment_code` to the worker machine.

3. Redeem it once on the worker:

```bash
export BUDDY_SERVER='http://127.0.0.1:8741'
python -m worker.agent --enroll --enrollment-code 'ONE_TIME_CODE'
```

The worker saves its node ID and node token to `.buddy-node.json` with restrictive file permissions. The enrollment code cannot be reused.

4. Start the worker:

```bash
python -m worker.agent --workspace ./workspace
```

## Node administration

Rotate a worker token:

```bash
curl -X POST http://127.0.0.1:8741/api/nodes/worker-01/rotate-token \
  -H "Authorization: Bearer $BUDDY_OWNER_TOKEN"
```

Revoke a worker:

```bash
curl -X POST http://127.0.0.1:8741/api/nodes/worker-01/revoke \
  -H "Authorization: Bearer $BUDDY_OWNER_TOKEN"
```

Revoked workers cannot heartbeat, claim tasks, renew leases, or submit results.

## Tests

```bash
pytest
```

## Security notes

- Bind to localhost only unless you intentionally want remote network exposure.
- Use HTTPS for any non-loopback deployment; enrollment responses contain a permanent worker token.
- Keep the owner token in a secret manager.
- Worker tokens are stored only as SHA-256 hashes on the server.
- Enrollment codes are single-use and expire automatically.
- Container execution is disabled by default.
- Worker file reads are confined to the workspace root.
