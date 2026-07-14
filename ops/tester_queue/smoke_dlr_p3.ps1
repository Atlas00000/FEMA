# DLR-P3-02 - Smoke: 1x Lane A + 1x Lane B on scorecard (no Tester launch, no promote)
# Usage:
#   powershell -File ops\tester_queue\smoke_dlr_p3.ps1
#
# Injects two finished queue jobs + lightweight run metrics, runs scorecard + decisions,
# asserts both lanes visible. Does NOT touch Terminal A. Does NOT call launch/drain.

param(
    [string]$RepoRoot = "",
    [switch]$KeepArtifacts
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

$tq = $PSScriptRoot
$ai = Join-Path $RepoRoot "AI"
$live = Join-Path $ai "data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$presetA = "Candidate_DLR_P3_A"
$presetB = "Challenger_P1BASE_p3smoke_01"
$utcNow = (Get-Date).ToUniversalTime()
$finished = $utcNow.ToString("o")
$enqueued = $utcNow.AddMinutes(-5).ToString("o")

# Isolated queue (never overwrite live queue.json)
$smokeQ = Join-Path $live "dlr_p3_smoke_queue.json"
$q = [ordered]@{
    schema = "fema_tester_queue_v1"
    updated = (Get-Date -Format "yyyy-MM-dd")
    max_concurrent = 1
    jobs = @(
        [ordered]@{
            id = "job_p3_a_$stamp"
            preset = $presetA
            symbol = "EURUSD"
            window = "2026.01.01-2026.07.31"
            notes = "DLR-P3-02 smoke Lane A"
            status = "finished"
            enqueued = $enqueued
            started = $enqueued
            finished = $finished
            run_id = "20260101_${presetA}_p3smoke"
            lane = "A"
            parent = "PRODUCTION"
            role = "candidate"
            profile_id = "prof_$presetA"
            subsystem = "adx"
            dd_balance_pct = 19.5
        },
        [ordered]@{
            id = "job_p3_b_$stamp"
            preset = $presetB
            symbol = "EURUSD"
            window = "2026.01.01-2026.07.31"
            notes = "DLR-P3-02 smoke Lane B"
            status = "finished"
            enqueued = $enqueued
            started = $enqueued
            finished = $finished
            run_id = "20260101_${presetB}_p3smoke"
            lane = "B"
            parent = "P1-BASELINE"
            role = "challenger"
            profile_id = "prof_$presetB"
            subsystem = "adx"
            dd_balance_pct = 17.5
        }
    )
    note = "DLR-P3-02 smoke queue - not the live tester queue"
}
($q | ConvertTo-Json -Depth 8) | Set-Content $smokeQ -Encoding utf8

# Lightweight metrics dirs so scorecard picks both up
foreach ($pair in @(
    @{ preset = $presetA; pf = 1.41; dd = 19.5; net = 100; n = 50; role = "candidate" },
    @{ preset = $presetB; pf = 1.38; dd = 17.5; net = 90; n = 48; role = "candidate" }
)) {
    $runId = "20260101_$($pair.preset)_p3smoke"
    $dir = Join-Path $ai "kb\runs\$runId"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $mj = [ordered]@{
        schema = "fema_run_v1"
        run_id = $runId
        preset = $pair.preset
        role = $pair.role
        registered_at = $finished
        metrics = @{
            profit_factor = $pair.pf
            net = $pair.net
            n = $pair.n
        }
        notes = "DLR-P3-02 smoke synthetic - NOT a production run"
        status = "recorded"
    }
    ($mj | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $dir "metrics.json") -Encoding utf8
    "DLR-P3-02 smoke" | Set-Content (Join-Path $dir "SOURCE.txt") -Encoding utf8
}

Write-Host "=== DLR-P3-02 smoke 1xA + 1xB ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tq "scorecard.ps1") `
    -RepoRoot $RepoRoot -QueuePath $smokeQ -LookbackHours 48 | Out-Null

$scPath = Join-Path $live "discovery_scorecard_latest.json"
$sc = Get-Content -Raw $scPath | ConvertFrom-Json
$cands = @($sc.candidates)
$lanes = @($cands | ForEach-Object { $_.lane } | Select-Object -Unique)
$hasA = @($cands | Where-Object { $_.lane -eq "A" -and $_.preset -eq $presetA }).Count -ge 1
$hasB = @($cands | Where-Object { $_.lane -eq "B" -and $_.preset -eq $presetB }).Count -ge 1
if (-not $hasA) { throw "DLR-P3-02: scorecard missing Lane A row for $presetA" }
if (-not $hasB) { throw "DLR-P3-02: scorecard missing Lane B row for $presetB" }

# Log G1 via decision (Reject / Alternate) - no Promote
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tq "decision.ps1") `
    -Preset $presetA -PF 1.41 -DD 19.5 -Decision Reject -FailureReason dd_breach `
    -Signer "dlr_p3_smoke" -Lane A -Parent PRODUCTION -Role candidate -Subsystem adx `
    -RunId "20260101_${presetA}_p3smoke" -RepoRoot $RepoRoot -QueuePath $smokeQ | Out-Null

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tq "decision.ps1") `
    -Preset $presetB -PF 1.38 -DD 17.5 -Decision Alternate -FailureReason dd_breach `
    -Signer "dlr_p3_smoke" -Lane B -Parent P1-BASELINE -Role challenger -Subsystem adx `
    -RunId "20260101_${presetB}_p3smoke" -RepoRoot $RepoRoot -QueuePath $smokeQ | Out-Null

$dec = Get-Content -Raw (Join-Path $live "promote_decision_latest.json") | ConvertFrom-Json
if ($dec.decision -eq "Promote") { throw "DLR-P3-02: unexpected Promote" }

# Policy advisor
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tq "el7_policy.ps1") -RepoRoot $RepoRoot | Out-Null
$pol = Get-Content -Raw (Join-Path $live "dlr_el7_policy_latest.json") | ConvertFrom-Json

$report = [ordered]@{
    schema = "fema_dlr_p3_smoke_v0"
    ran_utc = $finished
    preset_a = $presetA
    preset_b = $presetB
    scorecard_has_a = $hasA
    scorecard_has_b = $hasB
    lanes_seen = $lanes
    g1_logged = $true
    promote = $false
    policy_recommend_b = [bool]$pol.recommend_b
    note = "NO AUTO-PROMOTE. Synthetic metrics for scorecard compare only."
}
$reportPath = Join-Path $live "dlr_p3_smoke_latest.json"
($report | ConvertTo-Json -Depth 5) | Set-Content $reportPath -Encoding utf8

Write-Host "scorecard lanes: $($lanes -join ',')"
Write-Host "G1 logged via decision (Reject A / Alternate B) - no promote"
Write-Host "wrote $reportPath"
Write-Host "DLR-P3-02 SMOKE_OK"

if (-not $KeepArtifacts) {
    # Leave synthetic runs + smoke queue for audit
}
