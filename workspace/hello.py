$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $env:BUDDY_NODE_ID) { throw "BUDDY_NODE_ID is required" }
if (-not $env:BUDDY_NODE_TOKEN) { throw "BUDDY_NODE_TOKEN is required" }
if (-not $env:BUDDY_SERVER) { $env:BUDDY_SERVER = 'http://127.0.0.1:8741' }

. .\.venv\Scripts\Activate.ps1
python -m worker.agent --workspace .\workspace
