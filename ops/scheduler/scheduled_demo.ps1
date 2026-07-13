# AER-P3-03 — Terminal A demo watch (never mixes tester CSVs)
# Schedule: every 15 min daytime, or run manually.
#   powershell -File ops\scheduler\scheduled_demo.ps1

param([string]$RepoRoot = "")

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")
if (-not $RepoRoot) { $RepoRoot = Get-FemaRepoRoot }

$logDir = Join-Path $RepoRoot "AI\data\live\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("scheduled_demo_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding utf8
    Write-Host $line
}

Log "start demo scheduler"
$code = Invoke-FemaSync -RepoRoot $RepoRoot -Source demo
if ($code -ne 0) {
    if ($code -eq 2) {
        Write-SyncFailHeartbeat -RepoRoot $RepoRoot -Source demo -Note "no demo CSV found (header-only or no baskets yet)"
        Log 'sync: no demo CSV (exit 2) - heartbeat written'
    } else {
        Log "sync failed exit=$code"
    }
    Write-SchedulerArtifact -RepoRoot $RepoRoot -Job "scheduled_demo" -ExitCode $code -Message "sync only"
    exit $code
}

Push-Location (Join-Path $RepoRoot "AI")
try {
    python -m fema_ops pipeline
    $pipeCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$msg = if ($pipeCode -eq 0) { "sync + pipeline ok" } else { "pipeline exit $pipeCode" }
Log $msg
Write-SchedulerArtifact -RepoRoot $RepoRoot -Job "scheduled_demo" -ExitCode $pipeCode -Message $msg
exit $pipeCode
