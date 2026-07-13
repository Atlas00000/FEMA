# AER-P3-01 / P3-02 — Terminal B Discovery sync + ingest (no auto register/G1)
# Run after overnight Tester, or on schedule for morning catch-up.
# Full candidate scoring still needs: postrun.ps1 -Preset <id> -DD <pct>
#   powershell -File ops\scheduler\scheduled_tester.ps1

param([string]$RepoRoot = "")

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")
if (-not $RepoRoot) { $RepoRoot = Get-FemaRepoRoot }

$logDir = Join-Path $RepoRoot "AI\data\live\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("scheduled_tester_{0}.log" -f (Get-Date -Format "yyyyMMdd"))

function Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $logFile -Value $line -Encoding utf8
    Write-Host $line
}

Log "start tester scheduler"
$code = Invoke-FemaSync -RepoRoot $RepoRoot -Source tester
if ($code -ne 0) {
    if ($code -eq 2) {
        Write-SyncFailHeartbeat -RepoRoot $RepoRoot -Source tester -Note "no tester Agent CSV (no Discovery run yet)"
        Log 'sync: no tester CSV (exit 2) - heartbeat written'
    } else {
        Log "sync failed exit=$code"
    }
    Write-SchedulerArtifact -RepoRoot $RepoRoot -Job "scheduled_tester" -ExitCode $code -Message "sync+ingest skipped"
    exit $code
}

# sync.ps1 already calls ingest; confirm latest_source is tester
$srcFile = Join-Path $RepoRoot "AI\data\live\latest_source.txt"
$srcHint = ""
if (Test-Path $srcFile) {
    $srcHint = (Get-Content $srcFile -Raw).Split("`n") | Where-Object { $_ -match "^source=" } | Select-Object -First 1
}

Log "tester sync+ingest ok $srcHint"
Write-SchedulerArtifact -RepoRoot $RepoRoot -Job "scheduled_tester" -ExitCode 0 -Message "sync+ingest ok" -Extra @{
    latest_source = $srcHint
    note          = 'Run postrun.ps1 with -Preset and -DD after manual Tester for G1'
}
exit 0
