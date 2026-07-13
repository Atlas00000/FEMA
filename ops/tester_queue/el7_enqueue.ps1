# AER-P5-02 - EL7 dry-run -> factory clones -> enqueue (max 3)
# Usage:
#   powershell -File ops\tester_queue\el7_enqueue.ps1           # only if open_discovery=true
#   powershell -File ops\tester_queue\el7_enqueue.ps1 -Force    # human opened EL7 (ignore ladder)
#   powershell -File ops\tester_queue\el7_enqueue.ps1 -Force -Max 2 -Subsystems session,adx
#
# NEVER promotes. NEVER applies lineage retire (--apply) unless -ApplyLineage (still no promote).

param(
    [int]$Max = 3,
    [switch]$Force,
    [switch]$ApplyLineage,
    [string]$Subsystems = "",
    [string]$Window = "2026.01.01-2026.07.31",
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
if ($Max -lt 1 -or $Max -gt 3) { throw "Max must be 1..3" }

$ai = Join-Path $RepoRoot "AI"
$paths = Get-Content -Raw (Join-Path $PSScriptRoot "discovery_paths.json") | ConvertFrom-Json
$bHash = $paths.terminal_b.data_hash
$testerProfiles = Join-Path $env:APPDATA ("MetaQuotes\Terminal\$bHash\MQL5\Profiles\Tester")
$presetsDir = Join-Path $RepoRoot "Presets"

Write-Host "=== AER-P5-02 el7_enqueue Force=$Force Max=$Max ==="

Push-Location $ai
try {
        if ($ApplyLineage) {
            python -m fema_ops el7-dry-run --apply
        } else {
            python -m fema_ops el7-dry-run
        }
        $el7Path = Join-Path $ai "kb\el7_dry_run_latest.json"
        $el7 = Get-Content -Raw $el7Path | ConvertFrom-Json
        $open = [bool]$el7.trigger.open_discovery
        Write-Host "el7 open_discovery=$open reason=$($el7.trigger.reason) ladder=$($el7.trigger.ladder)"

        if (-not $open -and -not $Force) {
            Write-Host "skip enqueue: Discovery not open (pass -Force when human opens EL7)"
            $skip = [ordered]@{
                schema   = "fema_aer_p5_el7_enqueue_v0"
                ran_utc  = (Get-Date).ToUniversalTime().ToString("o")
                enqueued = @()
                skipped  = $true
                reason   = "open_discovery=false"
                note     = "No auto-promote. Human must -Force or wait for ladder trigger."
            }
            $liveSkip = Join-Path $RepoRoot "AI\data\live"
            New-Item -ItemType Directory -Force -Path $liveSkip | Out-Null
            ($skip | ConvertTo-Json -Depth 5) | Set-Content (Join-Path $liveSkip "el7_enqueue_latest.json") -Encoding utf8
            exit 0
        }

    python -m fema_ops recommend
    $rec = Get-Content -Raw (Join-Path $ai "data\live\factory_recommend.json") | ConvertFrom-Json
    $cloneable = @($rec.cloneable)
    Write-Host "recommend cloneable=$($cloneable.Count)"

    $subs = @()
    if ($Subsystems) {
        $subs = @($Subsystems.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    } elseif ($cloneable.Count -gt 0) {
        $subs = @($cloneable | Select-Object -First $Max | ForEach-Object { $_.subsystem })
    } else {
        # Default EL7 first-wave axes when compat is green but human forced Discovery
        $subs = @("session", "adx", "grid") | Select-Object -First $Max
        Write-Host "no cloneable mismatches - using default wave: $($subs -join ',')"
    }

    $enqueued = New-Object System.Collections.Generic.List[object]
    $i = 0
    foreach ($sub in $subs) {
        if ($enqueued.Count -ge $Max) { break }
        Write-Host "factory --apply --subsystem $sub"
        $facOut = & python -m fema_ops factory --apply --subsystem $sub 2>&1 | Out-String
        Write-Host $facOut.Trim()
        if ($LASTEXITCODE -ne 0) {
            Write-Host "factory failed for $sub - continue"
            continue
        }
        $presetId = $null
        if ($facOut -match 'cloned id=(\S+)') {
            $presetId = $Matches[1]
        }
        if (-not $presetId) {
            $setGuess = Get-ChildItem $presetsDir -Filter "Candidate_*.set" |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
            if ($setGuess) { $presetId = [IO.Path]::GetFileNameWithoutExtension($setGuess.Name) }
        }
        if (-not $presetId) {
            Write-Host "no candidate id after factory"
            continue
        }
        $set = Get-Item (Join-Path $presetsDir ($presetId + ".set")) -ErrorAction SilentlyContinue
        if (-not $set) {
            Write-Host "missing Presets\$presetId.set"
            continue
        }
        # Avoid re-enqueueing same preset if already queued
        $q = Get-Content -Raw $QueuePath | ConvertFrom-Json
        $dup = @($q.jobs | Where-Object { $_.preset -eq $presetId -and $_.status -eq "queued" })
        if ($dup.Count -gt 0) {
            Write-Host "already queued $presetId - skip"
            continue
        }
        New-Item -ItemType Directory -Force -Path $testerProfiles | Out-Null
        Copy-Item $set.FullName $testerProfiles -Force
        # Also refresh repo Experts FEMA Presets on Terminal B if present
        $bPresets = Join-Path $env:APPDATA ("MetaQuotes\Terminal\$bHash\MQL5\Experts\FEMA\Presets")
        if (Test-Path $bPresets) { Copy-Item $set.FullName $bPresets -Force }

        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "enqueue.ps1") `
            -Preset $presetId -Window $Window -Notes "AER-P5 EL7 factory subsystem=$sub" -QueuePath $QueuePath
        $enqueued.Add([ordered]@{
            preset = $presetId
            subsystem = $sub
            set = $set.Name
        }) | Out-Null
        $i++
        Start-Sleep -Seconds 1  # unique job_ ids
    }
} finally {
    Pop-Location
}

$out = [ordered]@{
    schema         = "fema_aer_p5_el7_enqueue_v0"
    ran_utc        = (Get-Date).ToUniversalTime().ToString("o")
    force          = [bool]$Force.IsPresent
    open_discovery = [bool]$open
    enqueued       = @($enqueued | ForEach-Object { [PSCustomObject]$_ })
    max            = [int]$Max
    note           = "NO AUTO-PROMOTE. Next: drain.ps1 then human checklist."
}
$live = Join-Path $RepoRoot "AI\data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
($out | ConvertTo-Json -Depth 6) | Set-Content (Join-Path $live "el7_enqueue_latest.json") -Encoding utf8
Write-Host "enqueued_n=$($enqueued.Count) -> AI/data/live/el7_enqueue_latest.json"
Write-Host "=== el7_enqueue done (no promote) ==="
