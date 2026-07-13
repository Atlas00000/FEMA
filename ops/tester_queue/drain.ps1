# AER-P5-01 - Drain tester queue FIFO, one job at a time, max N per night
# Usage:
#   powershell -File ops\tester_queue\drain.ps1
#   powershell -File ops\tester_queue\drain.ps1 -Max 3 -DryRun
#   powershell -File ops\tester_queue\drain.ps1 -Max 1 -SkipPostrun
#
# Does NOT promote. Does NOT touch Terminal A.

param(
    [int]$Max = 3,
    [switch]$DryRun,
    [switch]$SkipPostrun,
    [int]$TimeoutMinutes = 180,
    [string]$RepoRoot = "",
    [string]$QueuePath = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
if (-not $QueuePath) {
    $QueuePath = Join-Path $PSScriptRoot "queue.json"
}
if ($Max -lt 1 -or $Max -gt 3) {
    throw "AER-P5-01: Max must be 1..3 (EL7 wave cap)"
}

$launch = Join-Path $PSScriptRoot "launch.ps1"
$ran = 0
$results = New-Object System.Collections.Generic.List[object]

Write-Host "=== AER-P5 drain Max=$Max DryRun=$DryRun ==="

while ($ran -lt $Max) {
    $q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
    $next = @($q.jobs | Where-Object { $_.status -eq "queued" } | Sort-Object enqueued) | Select-Object -First 1
    if (-not $next) {
        Write-Host "queue empty after $ran job(s)"
        break
    }
    Write-Host "drain[$ran] $($next.id) preset=$($next.preset)"
    if ($DryRun) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $launch -JobId $next.id -DryRun -RepoRoot $RepoRoot -QueuePath $QueuePath
        $results.Add([ordered]@{ id = $next.id; preset = $next.preset; dry_run = $true; ok = $true }) | Out-Null
        # Do not consume queue on DryRun
        break
    }
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $launch, "-JobId", $next.id, "-RepoRoot", $RepoRoot, "-QueuePath", $QueuePath, "-TimeoutMinutes", "$TimeoutMinutes")
    if ($SkipPostrun) { $args += "-SkipPostrun" }
    & powershell @args
    $ok = ($LASTEXITCODE -eq 0)
    $results.Add([ordered]@{ id = $next.id; preset = $next.preset; dry_run = $false; ok = $ok; exit = $LASTEXITCODE }) | Out-Null
    $ran++
    if (-not $ok) {
        Write-Host "drain stop: launch failed exit=$LASTEXITCODE"
        break
    }
}

$live = Join-Path $RepoRoot "AI\data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
$resultArr = @()
foreach ($r in $results) {
    $resultArr += [PSCustomObject]$r
}
$art = [ordered]@{
    schema    = "fema_aer_p5_drain_v0"
    ran_utc   = (Get-Date).ToUniversalTime().ToString("o")
    aer_phase = "AER-P5-01"
    max       = [int]$Max
    ran       = [int]$ran
    dry_run   = [bool]$DryRun.IsPresent
    results   = $resultArr
    note      = "No auto-promote. Human reviews scorecard / checklist."
}
($art | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $live "drain_latest.json") -Encoding utf8
Write-Host "wrote AI/data/live/drain_latest.json ran=$ran"
Write-Host "=== drain done ==="
exit 0
