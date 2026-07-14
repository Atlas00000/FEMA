# DLR-P2-03 — Enqueue a Lane B (multi-base challenger) Discovery job
# Usage:
#   powershell -File ops\tester_queue\enqueue_lane_b.ps1 -Preset Challenger_P1BASE_adx_01 -Parent P1-BASELINE -Subsystem adx
#   powershell -File ops\tester_queue\enqueue_lane_b.ps1 -Preset Challenger_X2_htf_01 -Parent Candidate_X2
#
# Parent must be on AI/kb/challenger_roster.json (base or eligible profile). Never PRODUCTION.
# Caps: max 2 queued Lane B (separate from Lane A). NO AUTO-PROMOTE.

param(
    [Parameter(Mandatory = $true)][string]$Preset,
    [Parameter(Mandatory = $true)][string]$Parent,
    [string]$Window = "2026.01.01-2026.07.31",
    [string]$Symbol = "EURUSD",
    [string]$Notes = "",
    [string]$ProfileId = "",
    [string]$Subsystem = "",
    [string]$QueuePath = "",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
if (-not $QueuePath) {
    $QueuePath = Join-Path $PSScriptRoot "queue.json"
}

. (Join-Path $PSScriptRoot "lib_roster.ps1")

if ($Parent -eq "PRODUCTION") {
    throw "DLR-P2: use enqueue.ps1 -Lane A for PRODUCTION. Lane B parents come from the challenger roster."
}

$roster = Get-FemaRoster -RepoRoot $RepoRoot
if (-not (Test-FemaLaneBParent -Roster $roster -Parent $Parent)) {
    $ok = (Get-FemaLaneBEligibleParents -Roster $roster) -join ", "
    throw "DLR-P2: parent '$Parent' not on roster. Eligible: $ok"
}

if (-not $ProfileId) {
    $hit = @($roster.profiles | Where-Object { $_.preset -eq $Parent -or $_.profile_id -eq $Parent } | Select-Object -First 1)
    if ($hit) { $ProfileId = [string]$hit.profile_id }
    elseif (@($roster.bases | Where-Object { $_.id -eq $Parent }).Count -gt 0) {
        $ProfileId = Resolve-FemaProfileId -ProfileId "" -Preset $Preset -Parent $Parent
    } else {
        $ProfileId = Resolve-FemaProfileId -ProfileId "" -Preset $Preset -Parent $Parent
    }
}

if (-not $Notes) {
    $Notes = "DLR-P2 Lane B parent=$Parent"
}

Write-Host "=== DLR-P2-03 enqueue_lane_b parent=$Parent preset=$Preset ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "enqueue.ps1") `
    -Preset $Preset -Window $Window -Symbol $Symbol -Notes $Notes `
    -Lane B -Parent $Parent -Role challenger -ProfileId $ProfileId -Subsystem $Subsystem `
    -QueuePath $QueuePath -RepoRoot $RepoRoot

$out = [ordered]@{
    schema     = "fema_dlr_p2_enqueue_b_v0"
    ran_utc    = (Get-Date).ToUniversalTime().ToString("o")
    preset     = $Preset
    parent     = $Parent
    profile_id = $ProfileId
    lane       = "B"
    role       = "challenger"
    subsystem  = $Subsystem
    note       = "NO AUTO-PROMOTE. Challenger must pass G1 then human decision.ps1."
}
$live = Join-Path $RepoRoot "AI\data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
($out | ConvertTo-Json -Depth 4) | Set-Content (Join-Path $live "lane_b_enqueue_latest.json") -Encoding utf8
Write-Host "wrote AI/data/live/lane_b_enqueue_latest.json"
