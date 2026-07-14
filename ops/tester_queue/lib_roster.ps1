# DLR-P2 — Shared roster helpers (dot-source from enqueue / decision / enqueue_lane_b)
# Usage: . (Join-Path $PSScriptRoot "lib_roster.ps1")

function Get-FemaRosterPath {
    param([string]$RepoRoot)
    return (Join-Path $RepoRoot "AI\kb\challenger_roster.json")
}

function Get-FemaRoster {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)
    $path = Get-FemaRosterPath -RepoRoot $RepoRoot
    if (-not (Test-Path $path)) {
        throw "DLR-P2: missing challenger roster at $path"
    }
    return (Get-Content -Raw $path | ConvertFrom-Json)
}

function Save-FemaRoster {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Roster
    )
    $path = Get-FemaRosterPath -RepoRoot $RepoRoot
    $Roster.updated = (Get-Date -Format "yyyy-MM-dd")
    ($Roster | ConvertTo-Json -Depth 10) | Set-Content -Path $path -Encoding utf8
}

function Get-FemaLaneBEligibleParents {
    param($Roster)
    $ids = New-Object System.Collections.Generic.List[string]
    foreach ($b in @($Roster.bases)) {
        if ($b.eligible_lane_b -eq $true) { $ids.Add([string]$b.id) | Out-Null }
    }
    foreach ($p in @($Roster.profiles)) {
        if ($p.eligible_lane_b -eq $true) {
            $ids.Add([string]$p.preset) | Out-Null
            if ($p.profile_id) { $ids.Add([string]$p.profile_id) | Out-Null }
        }
    }
    return @($ids | Select-Object -Unique)
}

function Test-FemaLaneBParent {
    param(
        [Parameter(Mandatory = $true)]$Roster,
        [Parameter(Mandatory = $true)][string]$Parent
    )
    if ($Parent -eq "PRODUCTION") { return $false }
    $ok = Get-FemaLaneBEligibleParents -Roster $Roster
    return ($ok -contains $Parent)
}

function Resolve-FemaProfileId {
    param(
        [string]$ProfileId,
        [string]$Preset,
        [string]$Parent
    )
    if ($ProfileId) { return $ProfileId }
    if ($Preset) { return ("prof_{0}" -f $Preset) }
    return ("prof_{0}" -f $Parent)
}

function Get-FemaMaxQueuedLaneB {
    param($Roster)
    $n = 2
    if ($Roster.policy -and $Roster.policy.max_queued_lane_b) {
        $n = [int]$Roster.policy.max_queued_lane_b
    }
    if ($n -lt 1) { $n = 1 }
    if ($n -gt 2) { $n = 2 }
    return $n
}

function Upsert-FemaProfileCard {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$Preset,
        [string]$ProfileId = "",
        [string]$Parent = "PRODUCTION",
        [string]$Lane = "A",
        [string]$Role = "candidate",
        [string]$Subsystem = "",
        [string]$Window = "2026.01.01-2026.07.31",
        [string]$Symbol = "EURUSD",
        [double]$PF = 0,
        [double]$DD = 0,
        [bool]$G1Pass = $false,
        [string]$Status = "alternate",
        [string]$FailureReason = "",
        [string]$RunId = "",
        [string]$Notes = "",
        [bool]$EligibleLaneB = $true
    )

    $ProfileId = Resolve-FemaProfileId -ProfileId $ProfileId -Preset $Preset -Parent $Parent
    $utc = (Get-Date).ToUniversalTime().ToString("o")
    $profilesDir = Join-Path $RepoRoot "AI\kb\profiles"
    New-Item -ItemType Directory -Force -Path $profilesDir | Out-Null

    $cardHt = [ordered]@{
        schema           = "fema_dlr_p2_profile_v0"
        profile_id       = $ProfileId
        preset           = $Preset
        parent           = $Parent
        lane_origin      = $Lane
        role             = $Role
        window           = $Window
        symbol           = $Symbol
        pf               = $PF
        dd               = $DD
        g1_pass          = [bool]$G1Pass
        status           = $Status
        failure_reason   = $FailureReason
        run_id           = $RunId
        eligible_lane_b  = [bool]$EligibleLaneB
        subsystem        = $Subsystem
        notes            = $Notes
        updated_utc      = $utc
    }
    $cardPath = Join-Path $profilesDir ($ProfileId + ".json")
    ($cardHt | ConvertTo-Json -Depth 6) | Set-Content -Path $cardPath -Encoding utf8
    $cardObj = ($cardHt | ConvertTo-Json -Depth 6) | ConvertFrom-Json

    $roster = Get-FemaRoster -RepoRoot $RepoRoot
    $newProfiles = @()
    $found = $false
    foreach ($p in @($roster.profiles)) {
        if (($p.profile_id -eq $ProfileId) -or ($p.preset -eq $Preset)) {
            $newProfiles += $cardObj
            $found = $true
        } else {
            $newProfiles += $p
        }
    }
    if (-not $found) {
        $newProfiles += $cardObj
    }
    $roster.profiles = $newProfiles
    Save-FemaRoster -RepoRoot $RepoRoot -Roster $roster

    return [PSCustomObject]@{ profile_id = $ProfileId; card_path = $cardPath }
}
