#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
echo "Buddy AI Boardroom V1 setup — non-destructive"
for f in README.md INDEX.md boardroom.html player.html skill.js calibrate.js pm/artifacts.json skills/registry.json; do [[ -f "$f" ]] || { echo "Missing required file: $f"; exit 1; }; done
mkdir -p data poster-output
if [[ ! -f .env ]]; then cp .env.example .env; echo "Created local .env from template; add secrets locally only."; else echo ".env exists; left unchanged."; fi
node skill.js verify
echo "Setup checks passed. No server started and no remote settings changed."
