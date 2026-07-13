# AER-P5-03 - Morning Discovery scorecard (PF/DD vs PRODUCTION + G1)
# Usage:
#   powershell -File ops\tester_queue\scorecard.ps1
#
# Read-only. Does NOT promote.

param(
    [int]$LookbackHours = 36,
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

$ai = Join-Path $RepoRoot "AI"
$gates = Get-Content -Raw (Join-Path $ai "kb\gate_rules.json") | ConvertFrom-Json
$benchPf = [double]$gates.production_benchmark.profit_factor
$benchDd = [double]$gates.production_benchmark.max_dd_balance_pct
$cutoff = (Get-Date).ToUniversalTime().AddHours(-$LookbackHours)

$q = Get-Content -Raw $QueuePath | ConvertFrom-Json
$jobs = @($q.jobs | Where-Object {
    $_.finished -and ([datetime]$_.finished -ge $cutoff) -and ($_.status -in @("finished", "failed"))
})

$runsDir = Join-Path $ai "kb\runs"
$jobPresets = @($jobs | ForEach-Object { $_.preset } | Select-Object -Unique)
$runRows = @()
if (Test-Path $runsDir) {
    Get-ChildItem $runsDir -Directory | ForEach-Object {
        $mj = Join-Path $_.FullName "metrics.json"
        if (-not (Test-Path $mj)) { return }
        $m = Get-Content -Raw $mj | ConvertFrom-Json
        if ($m.role -ne "candidate") { return }
        $reg = $null
        try { $reg = [datetime]$m.registered_at } catch { return }
        if ($reg -lt $cutoff) { return }
        # Prefer Discovery wave presets (Candidate_*) or anything finished in queue lookback
        $isWave = ($m.preset -like "Candidate_*") -or ($jobPresets -contains $m.preset)
        if (-not $isWave) { return }
        $pf = [double]$m.metrics.profit_factor
        $dd = 0.0
        $jobDd = @($jobs | Where-Object { $_.preset -eq $m.preset -and $_.dd_balance_pct }) | Select-Object -First 1
        if ($jobDd) { $dd = [double]$jobDd.dd_balance_pct }
        $g1Pf = ($pf -ge $benchPf)
        $g1Pass = $g1Pf -and ($dd -gt 0) -and ($dd -le $benchDd)
        $decision = if ($dd -le 0) { "need_dd" } elseif ($g1Pass) { "g1_pass_review" } elseif (-not $g1Pf) { "reject_pf" } else { "reject_dd" }
        $runRows += [ordered]@{
            run_id = $m.run_id
            preset = $m.preset
            pf = $pf
            net = $m.metrics.net
            n = $m.metrics.n
            dd = $dd
            g1_pass = $g1Pass
            decision = $decision
            registered_at = $m.registered_at
        }
    }
}

$live = Join-Path $ai "data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
$jsonPath = Join-Path $live "discovery_scorecard_latest.json"
$mdPath = Join-Path $live "discovery_scorecard_latest.md"

$payload = @{
    schema = "fema_aer_p5_scorecard_v0"
    ran_utc = (Get-Date).ToUniversalTime().ToString("o")
    lookback_hours = $LookbackHours
    production = @{ pf = $benchPf; max_dd_balance_pct = $benchDd; run_id = $gates.production_benchmark.run_id }
    jobs_finished = @($jobs | ForEach-Object { [ordered]@{ id = $_.id; preset = $_.preset; status = $_.status; dd = $_.dd_balance_pct; finished = $_.finished } })
    candidates = $runRows
    note = "NO AUTO-PROMOTE. Use AI/templates/promotion_checklist.md. Keep PRODUCTION unless human signs."
}
($payload | ConvertTo-Json -Depth 8) | Set-Content $jsonPath -Encoding utf8

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Discovery scorecard (AER-P5-03)") | Out-Null
$md.Add("") | Out-Null
$md.Add("Generated: $($payload.ran_utc)") | Out-Null
$md.Add("") | Out-Null
$md.Add("**PRODUCTION bench:** PF >= **$benchPf** and max DD bal <= **$benchDd%**") | Out-Null
$md.Add("") | Out-Null
$md.Add("**NO AUTO-PROMOTE** - human checklist only.") | Out-Null
$md.Add("") | Out-Null
$md.Add("| preset | run_id | PF | net | n | DD% | G1 | decision |") | Out-Null
$md.Add("| --- | --- | ---: | ---: | ---: | ---: | --- | --- |") | Out-Null
foreach ($r in $runRows) {
    $md.Add("| $($r.preset) | $($r.run_id) | $($r.pf) | $($r.net) | $($r.n) | $($r.dd) | $(if ($r.g1_pass) { 'PASS' } else { 'FAIL' }) | $($r.decision) |") | Out-Null
}
if ($runRows.Count -eq 0) {
    $md.Add("| _(none in lookback)_ | | | | | | | |") | Out-Null
}
$md.Add("") | Out-Null
$md.Add("Queue finished (lookback): $($jobs.Count)") | Out-Null
($md -join "`r`n") + "`r`n" | Set-Content $mdPath -Encoding utf8

Write-Host "wrote $jsonPath"
Write-Host "wrote $mdPath"
Write-Host "candidates=$($runRows.Count) jobs=$($jobs.Count) (no promote)"
