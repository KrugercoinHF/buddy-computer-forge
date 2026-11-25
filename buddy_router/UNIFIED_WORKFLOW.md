# Buddy Agency Unified Workflow Demo

Run from the repository root with Python 3.11+:

```sh
python -m buddy_router.unified_demo
```

Open http://127.0.0.1:8761/.

To record owner decisions, set a private token before starting:
```sh
export BUDDY_OWNER_APPROVAL_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m buddy_router.unified_demo
```

Workflow: Buddy Router → deterministic specialist adapter → five-role simulated Boardroom review → owner approval gateway. Computer-operation requests create a pending approval record. Approve/reject requires the configured token and records intent only.

API: GET /api/health, GET /api/profiles, POST /api/route, POST /api/workflow, GET /api/approvals, POST /api/approvals/{approval_id}/decision.

Safety: loopback only; no live providers, external actions, task persistence or computer execution. Specialist and Boardroom outputs are simulations, not real model reasoning or a connection to the separate 100-agent Boardroom service. Approval records are process-memory only and disappear on restart. Approval never enables execution. Do not expose this demo to a network or use production credentials.

Test: `python -m unittest buddy_router.tests.test_unified_workflow -v`
