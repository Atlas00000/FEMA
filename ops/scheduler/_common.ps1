# Shared helpers for AER-P3 scheduled jobs

function Get-FemaRepoRoot {
    param([string]$ScriptRoot = $PSScriptRoot)
    return Split-Path (Split-Path $ScriptRoot -Parent) -Parent
}

function Write-SchedulerArtifact {
    param(
        [string]$RepoRoot,
        [string]$Job,
        [int]$ExitCode,
        [string]$Message = "",
        [hashtable]$Extra = @{}
    )
    $live = Join-Path $RepoRoot "AI\data\live"
    New-Item -ItemType Directory -Force -Path $live | Out-Null
    $payload = @{
        job        = $Job
        ran_utc    = (Get-Date).ToUniversalTime().ToString("o")
        exit_code  = $ExitCode
        ok         = ($ExitCode -eq 0)
        message    = $Message
        aer_phase  = "AER-P3"
    }
    foreach ($k in $Extra.Keys) { $payload[$k] = $Extra[$k] }
    $path = Join-Path $live "scheduler_last.json"
    ($payload | ConvertTo-Json -Depth 6) | Set-Content -Path $path -Encoding utf8
    return $path
}

function Write-SyncFailHeartbeat {
    param(
        [string]$RepoRoot,
        [string]$Source,
        [string]$Note
    )
    $hb = Join-Path $RepoRoot "AI\data\live\sync_heartbeat.json"
    @{
        synced_utc       = (Get-Date).ToUniversalTime().ToString("o")
        source           = $Source
        source_requested = $Source
        ok               = $false
        baskets_copied   = $false
        stale            = $false
        header_only      = $false
        baskets_locked   = $false
        wave             = "AER-P3"
        note             = $Note
    } | ConvertTo-Json | Set-Content -Path $hb -Encoding utf8
}

function Invoke-FemaSync {
    param(
        [string]$RepoRoot,
        [ValidateSet("demo", "tester")]
        [string]$Source
    )
    $sync = Join-Path $RepoRoot "ops\sync\sync.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $sync -Source $Source -RepoRoot $RepoRoot | Out-Host
    return [int]$LASTEXITCODE
}
