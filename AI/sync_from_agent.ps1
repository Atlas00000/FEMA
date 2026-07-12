# INF-EXPORT — sync newest FEMA_AI CSVs into AI/data/live/
# From Experts/FEMA:
#   .\AI\sync_from_agent.ps1
#   .\AI\sync_from_agent.ps1 -Magic 20260707

param(
    [string]$Magic = "",
    [string]$FromDir = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "FEMA.mq5"))) {
    # Script lives in AI/; parent is repo root Experts/FEMA
    $Root = Split-Path -Parent $PSScriptRoot
}

Set-Location $Root

$pyArgs = @("AI/sync_from_agent.py")
if ($Magic -ne "") {
    $pyArgs += @("--magic", $Magic)
}
if ($FromDir -ne "") {
    $pyArgs += @("--from-dir", $FromDir)
}

python @pyArgs
exit $LASTEXITCODE
