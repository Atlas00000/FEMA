# DLR-P1/P2 / AER - Enqueue a Discovery Tester job
# Usage:
#   powershell -File ops\tester_queue\enqueue.ps1 -Preset Candidate_X1
#   powershell -File ops\tester_queue\enqueue.ps1 -Preset Candidate_X3 -Lane A -Parent PRODUCTION -Subsystem adx
#   powershell -File ops\tester_queue\enqueue.ps1 -Preset Challenger_P1BASE_adx_01 -Lane B -Parent P1-BASELINE -Role challenger
#
# Defaults: lane=A parent=PRODUCTION role=candidate (Lane A retune of the lock).
# Lane A guards (DLR-P1-05): parent must be PRODUCTION; one subsystem only; max 3 queued Lane A.
# Lane B guards (DLR-P2): parent on challenger roster (not PRODUCTION); role=challenger; max 2 queued B.

param(
    [Parameter(Mandatory = $true)][string]$Preset,
    [string]$Window = "2026.01.01-2026.07.31",
    [string]$Symbol = "EURUSD",
    [string]$Notes = "",
    [ValidateSet("A", "B")][string]$Lane = "A",
    [string]$Parent = "PRODUCTION",
    [ValidateSet("candidate", "challenger")][string]$Role = "candidate",
    [string]$ProfileId = "",
    [string]$Subsystem = "",
    [string]$QueuePath = "",
    [string]$RepoRoot = ""
)
$ErrorActionPreference = "Stop"
if (-not $QueuePath) {
    $QueuePath = Join-Path $PSScriptRoot "queue.json"
}
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

. (Join-Path $PSScriptRoot "lib_roster.ps1")

if (-not $Parent) { $Parent = "PRODUCTION" }

if ($Lane -eq "A") {
    if ($Parent -ne "PRODUCTION") {
        throw "DLR-P1: Lane A requires -Parent PRODUCTION (got '$Parent')"
    }
    if ($Role -ne "candidate") {
        throw "DLR-P1: Lane A requires -Role candidate (got '$Role')"
    }
    if ($Subsystem -match "[,;|/]") {
        throw "DLR-P1: Lane A allows one subsystem only (got '$Subsystem')"
    }
    if ($Subsystem) {
        $mapPath = Join-Path $RepoRoot "AI\kb\search_map.json"
        if (Test-Path $mapPath) {
            $map = Get-Content -Raw $mapPath | ConvertFrom-Json
            $known = @($map.may_adapt_pairs | ForEach-Object { $_.id })
            if ($known -notcontains $Subsystem) {
                throw "DLR-P1: unknown Lane A subsystem '$Subsystem' (search_map: $($known -join ', '))"
            }
        }
    }
}

if ($Lane -eq "B") {
    if ($Role -eq "candidate") { $Role = "challenger" }
    if ($Role -ne "challenger") {
        throw "DLR-P2: Lane B requires -Role challenger (got '$Role')"
    }
    if ($Parent -eq "PRODUCTION") {
        throw "DLR-P2: Lane B parent must be a roster base/profile (not PRODUCTION). Use Lane A for lock retune."
    }
    $roster = Get-FemaRoster -RepoRoot $RepoRoot
    if (-not (Test-FemaLaneBParent -Roster $roster -Parent $Parent)) {
        $ok = (Get-FemaLaneBEligibleParents -Roster $roster) -join ", "
        throw "DLR-P2: parent '$Parent' not eligible for Lane B. Roster: $ok"
    }
    if (-not $ProfileId) {
        # Prefer existing profile for this parent preset; else new card id for the challenger preset
        $hit = @($roster.profiles | Where-Object { $_.preset -eq $Parent -or $_.profile_id -eq $Parent } | Select-Object -First 1)
        if ($hit) {
            $ProfileId = [string]$hit.profile_id
        } else {
            $ProfileId = Resolve-FemaProfileId -ProfileId "" -Preset $Preset -Parent $Parent
        }
    }
}

$q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
if ($Lane -eq "A") {
    $queuedA = @($q.jobs | Where-Object {
        $_.status -eq "queued" -and (
            (-not $_.lane) -or ($_.lane -eq "A")
        )
    })
    if ($queuedA.Count -ge 3) {
        throw "DLR-P1: Lane A wave full (already $($queuedA.Count) queued; max 3)"
    }
}
if ($Lane -eq "B") {
    if (-not $roster) { $roster = Get-FemaRoster -RepoRoot $RepoRoot }
    $maxB = Get-FemaMaxQueuedLaneB -Roster $roster
    $queuedB = @($q.jobs | Where-Object { $_.status -eq "queued" -and $_.lane -eq "B" })
    if ($queuedB.Count -ge $maxB) {
        throw "DLR-P2: Lane B cycle cap (already $($queuedB.Count) queued; max $maxB)"
    }
}

$id = "job_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$job = [ordered]@{
    id          = $id
    preset      = $Preset
    symbol      = $Symbol
    window      = $Window
    notes       = $Notes
    status      = "queued"
    enqueued    = (Get-Date).ToUniversalTime().ToString("o")
    started     = $null
    finished    = $null
    run_id      = $null
    lane        = $Lane
    parent      = $Parent
    role        = $Role
    profile_id  = $ProfileId
    subsystem   = $Subsystem
}
$list = @($q.jobs) + @($job)
$q.jobs = $list
$q.schema = "fema_tester_queue_v1"
$q.updated = (Get-Date -Format "yyyy-MM-dd")
$q.note = "DLR-P2: jobs carry lane/parent/role/profile_id/subsystem. Lane A<=3 queued, Lane B<=2. Demo path never uses this queue."
($q | ConvertTo-Json -Depth 6) | Set-Content -Path $QueuePath -Encoding utf8
Write-Host "enqueued $id preset=$Preset lane=$Lane parent=$Parent role=$Role profile_id=$ProfileId subsystem=$Subsystem"
