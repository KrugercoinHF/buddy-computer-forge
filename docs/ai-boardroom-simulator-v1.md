# Buddy AI Boardroom Simulator V1

**Date:** 2026-11-14  
**Status:** Interactive local application with P0 safety preflight and SHA-256 minutes verification — isolated feature branch  
**Repository:** \`KrugercoinHF/buddy-computer-forge\`  
**Branch:** \`feat/ai-boardroom-simulator-v1\`

## Product scope

A local-first, hybrid futuristic/corporate boardroom simulator with a directory of 100 specialist agents. Users can convene a meeting with 5–100 participants, run a deterministic simulated debate, inspect each contribution, review an advisory vote, read minutes, and review proposed follow-up actions.

## Architecture

- **Presentation:** \`boardroom.html\` — responsive, browser-based command centre (the previously separate dashboard has been promoted to the served entry page).
- **Application/API:** \`boardroom_app.py\` — FastAPI service, agent directory, meeting lifecycle, simulation engine and owner approval endpoint.
- **Persistence:** SQLite at \`data/boardroom.sqlite3\` by default; override with \`BOARDROOM_DB_PATH\`.
- **Agent catalogue:** 10 executive profiles plus 90 specialist profiles across nine committees.
- **Meeting lifecycle:** scheduled → completed; outputs include contributions, advisory vote, minutes, a canonical SHA-256 digest, P0 safety-gate evidence and proposals.
- **Governance:** proposal decisions require \`BOARDROOM_OWNER_TOKEN\`. Approval records a decision only; execution remains disabled. Every meeting passes the hard P0 preflight before simulation.
- **Integration boundary:** this is an isolated module in the existing Forge foundation. It does not modify Build Factory routes, Buddy Desktop OS, App Genesis, BuddyBot or other repositories. Future integrations must use explicit APIs and least-privilege credentials.

## Run locally

From the repository root:

\`\`\`bash
python -m pip install -e '.[test]'
export BOARDROOM_OWNER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn boardroom_app:app --host 127.0.0.1 --port 8750
\`\`\`

Open \`http://127.0.0.1:8750/\`. API docs are at \`http://127.0.0.1:8750/docs\`.

Windows PowerShell:

\`\`\`powershell
$env:BOARDROOM_OWNER_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m uvicorn boardroom_app:app --host 127.0.0.1 --port 8750
\`\`\`

## API

- \`GET /api/health\` — health and capability flags.
- \`GET /api/agents?limit=100\` — list the 100-agent directory.
- \`POST /api/meetings\` — create a meeting.
- \`GET /api/meetings\` — list recent meetings.
- \`GET /api/meetings/{id}\` — retrieve a meeting.\n- \`GET /api/meetings/{id}/verify\` — recompute and verify the meeting-minutes SHA-256 digest.
- \`POST /api/meetings/{id}/run\` — run the deterministic simulation.
- \`POST /api/meetings/{id}/proposals/{proposal_id}/decision\` — owner-authenticated approve/reject decision.

## Important capability boundary

V1 is a **simulator**, not a live multi-model AI system. Agent contributions are deterministic sample reasoning and clearly marked \`provider=simulation\`. No OpenAI, Anthropic, Gemini or other model provider is connected. No autonomous tool use, repository mutation, deployment, computer control, external messaging or task execution is available from the Boardroom. An owner approval changes the proposal record only and leaves \`execution=not_executed\`.

## Next phases (not implemented)

1. Add model-provider adapters with explicit per-provider configuration and spend limits.
2. Add structured evidence objects and source citations to agent claims.
3. Add durable event/audit records and meeting version history.
4. Add committee-level deliberation and configurable voting/quorum policies.
5. Add a narrow, authenticated Build Factory handoff that creates a proposed task, still requiring a separate owner approval before execution.
6. Add a read-only integration with Buddy Knowledge Core, then other Buddy projects through versioned contracts.

## Test

\`\`\`bash
pytest -q tests/test_boardroom.py
\`\`\`
