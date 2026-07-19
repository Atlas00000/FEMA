# After Terminal B Strategy Tester finishes — sync, ingest, register, optional G1 check.
# Usage:
#   powershell -File ops\tester_queue\postrun.ps1 -Preset Candidate_X1 -DD 19.0
#   powershell -File ops\tester_queue\postrun.ps1 -Preset Candidate_X1 -JobId job_20260713_003000

param(
    [Parameter(Mandatory = $true)][string]$Preset,
    [string]$JobId = "",
    [double]$DD = 0.0,
    [string]$WindowFrom = "2026.01.01",
    [string]$WindowTo = "2026.07.31",
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

Write-Host "=== AER postrun preset=$Preset ==="

& powershell -File (Join-Path $RepoRoot "ops\sync\sync.ps1") -Source tester -RepoRoot $RepoRoot
Push-Location (Join-Path $RepoRoot "AI")
try {
    python -m fema_ops ingest --source tester
    $baskets = Join-Path $RepoRoot "AI\data\live\latest_baskets.csv"
    $meta = Join-Path $RepoRoot "ops\incoming\tester\EURUSD_20260707_run.meta.txt"
    $regArgs = @(
        "-m", "fema_ops", "register",
        "--baskets", $baskets,
        "--preset", $Preset,
        "--role", "candidate",
        "--from", $WindowFrom,
        "--to", $WindowTo,
        "--notes", "AER postrun $(Get-Date -Format 'yyyy-MM-dd')"
    )
    if (Test-Path $meta) {
        $regArgs += @("--meta", $meta)
    }
    python @regArgs
    # ASI-P3: TEP shadow on newly registered run (no live skip)
    $latestRun = Get-ChildItem (Join-Path $RepoRoot "AI\kb\runs") -Directory |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($latestRun) {
        Write-Host "asi-shadow run_id=$($latestRun.Name)"
        python -m fema_ops asi-shadow --run-id $latestRun.Name
    }
    python -m fema_ops gate-polish
    if ($DD -gt 0) {
        $metricsPath = Get-ChildItem (Join-Path $RepoRoot "AI\kb\runs") -Directory |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1 |
            ForEach-Object { Join-Path $_.FullName "metrics.json" }
        if ($metricsPath -and (Test-Path $metricsPath)) {
            $m = Get-Content $metricsPath -Raw | ConvertFrom-Json
            $pf = $m.metrics.profit_factor
            Write-Host "gate-check pf=$pf dd=$DD"
            python -m fema_ops gate-check --pf $pf --dd $DD --from $WindowFrom --to $WindowTo
        }
    } else {
        Write-Host "Tip: re-run with -DD <max_dd_balance_pct> from MT5 report for G1 check"
    }
} finally {
    Pop-Location
}

if (Test-Path $QueuePath) {
    $q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
    $updated = $false
    foreach ($j in $q.jobs) {
        $match = ($JobId -ne "" -and $j.id -eq $JobId) -or
                 ($JobId -eq "" -and $j.preset -eq $Preset -and $j.status -eq "queued")
        if ($match) {
            $j.status = "finished"
            $j.finished = (Get-Date).ToUniversalTime().ToString("o")
            $updated = $true
            if ($JobId -eq "") { Write-Host "marked finished: $($j.id)" }
            break
        }
    }
    if ($updated) {
        $q.updated = (Get-Date -Format "yyyy-MM-dd")
        ($q | ConvertTo-Json -Depth 6) | Set-Content -Path $QueuePath -Encoding utf8
    }
}

Write-Host "=== postrun done ==="
