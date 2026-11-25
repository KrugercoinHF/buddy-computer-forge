# Buddy Router — local command deck

Run from the repository root with Python 3.11 or newer:

```sh
python -m buddy_router.demo_server
```

Open http://127.0.0.1:8760/ in your browser. The service binds to loopback only. Set `BUDDY_ROUTER_DEMO_PORT` to change the local port.

The command deck calls the real deterministic `buddy_router.engine.route` function. It provides:
- A live read-only specialist directory at `/api/profiles`.
- A task form with automatic or manually requested specialist selection.
- A routing decision with risk, policy, capabilities and execution state.
- A six-step trace for request intake, profile discovery, selection, compatibility, policy and outcome.

API routes: `GET /api/health`, `GET /api/profiles`, `POST /api/route`.

Run the tests from the repository root:

```sh
python -m unittest discover -s buddy_router/tests -v
```

**Safety contract:** local-only, deterministic and advisory. No provider calls, external actions or computer execution. Computer Forge remains disabled for execution. The demo does not persist submitted tasks.
