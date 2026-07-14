# DLR-P3-01 - EL7 dual-lane policy advisor (read-only recommendation)
# Usage:
#   powershell -File ops\tester_queue\el7_policy.ps1
#   powershell -File ops\tester_queue\el7_policy.ps1 -LookbackDays 14
#
# Does NOT enqueue. Does NOT promote. Prints plan + writes dlr_el7_policy_latest.json.
# Human may then: el7_enqueue.ps1 (Lane A) and/or enqueue_lane_b.ps1 when recommend_b=true.

param(
    [int]$LookbackDays = 21,
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

. (Join-Path $PSScriptRoot "lib_roster.ps1")

$ai = Join-Path $RepoRoot "AI"
$policyPath = Join-Path $ai "kb\dlr_policy.json"
if (-not (Test-Path $policyPath)) {
    throw "DLR-P3: missing $policyPath"
}
$policy = Get-Content -Raw $policyPath | ConvertFrom-Json
$nEscalate = [int]$policy.escalate_b_after_a_fails
if ($nEscalate -lt 1) { $nEscalate = 2 }
$maxB = [int]$policy.max_lane_b_per_cycle
if ($maxB -lt 1) { $maxB = 1 }
if ($maxB -gt 2) { $maxB = 2 }

$cutoff = (Get-Date).ToUniversalTime().AddDays(-$LookbackDays)
$aFails = New-Object System.Collections.Generic.List[object]

# 1) Recent decision packets under kb/decisions (Lane A candidates)
$decDir = Join-Path $ai "kb\decisions"
if (Test-Path $decDir) {
    Get-ChildItem $decDir -Filter "*.md" | Sort-Object LastWriteTime -Descending | ForEach-Object {
        if ($_.LastWriteTime.ToUniversalTime() -lt $cutoff) { return }
        $name = $_.BaseName
        if ($name -notmatch "_(Reject|Alternate)$") { return }
        $kind = $Matches[1].ToLowerInvariant()
        if ($name -notmatch "Candidate_") { return }
        $aFails.Add([ordered]@{
            source = "decisions"
            file   = $_.Name
            kind   = $kind
            when   = $_.LastWriteTime.ToUniversalTime().ToString("o")
        }) | Out-Null
    }
}

# 2) candidates.csv Lane A rows with reject/alternate
$csvPath = Join-Path $ai "kb\candidates.csv"
if (Test-Path $csvPath) {
    $rows = Import-Csv $csvPath
    foreach ($r in $rows) {
        $id = [string]$r.id
        if ($id -notlike "Candidate_*") { continue }
        $st = [string]$r.status
        if ($st -notin @("reject", "alternate", "fail")) { continue }
        $aFails.Add([ordered]@{
            source = "candidates.csv"
            preset = $id
            kind   = $st
            when   = ""
        }) | Out-Null
    }
}

# Unique fail count preferring decision files in lookback; fall back to csv Candidate_* fails
$fromDec = @($aFails | Where-Object { $_.source -eq "decisions" })
$failCount = if ($fromDec.Count -gt 0) { $fromDec.Count } else {
    @($aFails | Where-Object { $_.source -eq "candidates.csv" } | Select-Object -ExpandProperty preset -Unique).Count
}

$recommendB = ($failCount -ge $nEscalate)
$roster = Get-FemaRoster -RepoRoot $RepoRoot
$bParent = [string]$policy.preferred_b_parent
if (-not (Test-FemaLaneBParent -Roster $roster -Parent $bParent)) {
    $eligible = @(Get-FemaLaneBEligibleParents -Roster $roster)
    $bParent = if ($eligible.Count -gt 0) { [string]$eligible[0] } else { "" }
}

$plan = New-Object System.Collections.Generic.List[string]
$plan.Add("A") | Out-Null
if ($recommendB -and $bParent) {
    $plan.Add("B") | Out-Null
}

$utc = (Get-Date).ToUniversalTime().ToString("o")
$out = [ordered]@{
    schema              = "fema_dlr_p3_el7_policy_v0"
    ran_utc             = $utc
    lookback_days       = $LookbackDays
    default_lane        = [string]$policy.default_lane
    escalate_after      = $nEscalate
    a_fail_count        = $failCount
    recommend_b         = [bool]$recommendB
    max_lane_b_per_cycle = $maxB
    preferred_b_parent  = $bParent
    wave_plan           = @($plan)
    overnight_default   = [string]$policy.overnight_default
    promote             = $policy.promote
    next_commands       = @(
        "powershell -File ops\tester_queue\el7_enqueue.ps1 -Force -Max 3",
        $(if ($recommendB -and $bParent) {
            "powershell -File ops\tester_queue\enqueue_lane_b.ps1 -Preset Challenger_P1BASE_<thesis>_01 -Parent $bParent"
        } else {
            "# Lane B not recommended yet (need $nEscalate A fails; have $failCount)"
        })
    )
    note = "NO AUTO-PROMOTE. Advisor only - human must enqueue B explicitly. el7_enqueue stays Lane A."
}

$live = Join-Path $ai "data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
$outPath = Join-Path $live "dlr_el7_policy_latest.json"
($out | ConvertTo-Json -Depth 6) | Set-Content $outPath -Encoding utf8

Write-Host "=== DLR-P3 el7_policy ==="
Write-Host "a_fails=$failCount escalate_after=$nEscalate recommend_b=$recommendB parent=$bParent"
Write-Host "wave_plan=$($plan -join '+')"
Write-Host "wrote $outPath"
Write-Host "NO AUTO-PROMOTE - human decision.ps1 only"
