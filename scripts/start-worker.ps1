$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e '.[test]'

if (-not $env:BUDDY_OWNER_TOKEN) {
  $env:BUDDY_OWNER_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
}

Write-Host "Buddy API starting on http://127.0.0.1:8741"
Write-Host "Owner token: $env:BUDDY_OWNER_TOKEN"
uvicorn buddy.main:app --host 127.0.0.1 --port 8741
