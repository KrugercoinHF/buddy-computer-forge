# AI Boardroom Simulator V1 — canonical contract

Repository: KrugercoinHF/buddy-computer-forge  
Branch: feat/ai-boardroom-simulator-v1  
Status: declarative architecture plus local validation tools. File presence is not runtime evidence.

## Authority and safety
The existing Python service in boardroom_app.py is the application foundation. boardroom.html is a static entry surface. Agent output remains simulation unless a provider adapter is separately implemented, configured and verified. Nothing here authorizes autonomous execution, deployment, external messaging or computer control.

## Contracts
- wings/*.json: declarative functional-wing metadata; dev is the meta-wing.
- pm/artifacts.json: lifecycle ledger. Promotion requires owner evidence; CI alone cannot promote.
- skills/registry.json: declared inventory, not a dynamic runtime loader.
- skill.js: local CLI for score, verify, determinism, registry and poster prompt.
- skills/terminal: read-only command surface; no arbitrary shell execution.
- calibrate.js: ten-repeat local determinism harness; writes its report only when invoked.
- ingest.js: scaffold only; checks local media tools and prints a proposed pipeline plan.
- evidence.yml: pull-request validation; it does not promote or deploy.
- gh-gate.sh: plan-only by default; settings change only with --apply and confirmation.
- nano.py: optional Gemini image bridge; requires a local key and explicit invocation.

## Lifecycle
SPEC → SCAFFOLDED → RUNNING → MAINTAINED. No skipping. Every promotion is owner-approved and backed by command output, exit code and artifact hash. A checked-in source file is not evidence that it ran.

## Local commands
    node skill.js score
    node skill.js verify
    node skill.js determinism
    node skill.js registry
    node skill.js poster
    node calibrate.js
    node skills/terminal/scripts/terminal-cli.js help
    python nano.py --help
    node ingest.js --help

Copy .env.example to .env and provide keys only locally. Never commit .env, API keys, media, generated outputs or local databases.
