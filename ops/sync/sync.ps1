# FEMA Windows worker sync (Wave 1 / IS-P0-01)
# Copies Common/Terminal FEMA_AI CSVs into ops/incoming/{demo|tester}
# Schedule via Task Scheduler every 15 min, or run manually.
#
# Usage:
#   powershell -File ops\sync\sync.ps1 -Source demo
#   powershell -File ops\sync\sync.ps1 -Source tester

param(
    [ValidateSet("demo", "tester")]
    [string]$Source = "demo",
    [string]$Magic = "20260707",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

$Incoming = Join-Path $RepoRoot "ops\incoming\$Source"
New-Item -ItemType Directory -Force -Path $Incoming | Out-Null

$AppData = $env:APPDATA
$candidates = @()

if ($Source -eq "demo") {
    $candidates += Join-Path $AppData "MetaQuotes\Terminal\Common\Files\FEMA_AI"
    Get-ChildItem (Join-Path $AppData "MetaQuotes\Terminal") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $candidates += Join-Path $_.FullName "MQL5\Files\FEMA_AI"
    }
} else {
    Get-ChildItem (Join-Path $AppData "MetaQuotes\Tester") -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        Get-ChildItem $_.FullName -Recurse -Directory -Filter "FEMA_AI" -ErrorAction SilentlyContinue | ForEach-Object {
            $candidates += $_.FullName
        }
    }
}

$pattern = "EURUSD_${Magic}_baskets.csv"
$src = $null
foreach ($dir in $candidates) {
    $p = Join-Path $dir $pattern
    if (Test-Path $p) {
        $src = Get-Item $p
        break
    }
}

if (-not $src) {
    Write-Host "sync_fail: no $pattern under $Source paths"
    exit 2
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
try {
    Copy-Item $src.FullName (Join-Path $Incoming $src.Name) -Force
    $stem = $src.Name -replace "_baskets\.csv$", ""
    foreach ($suf in @("_events.csv", "_run.meta.txt", "_run_config.json")) {
        $sib = Join-Path $src.DirectoryName ($stem + $suf)
        if (Test-Path $sib) {
            Copy-Item $sib (Join-Path $Incoming (Split-Path $sib -Leaf)) -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "sync_ok source=$Source file=$($src.FullName) bytes=$($src.Length) -> $Incoming"
    # Also refresh AI live pointers via Python when available
    $ai = Join-Path $RepoRoot "AI"
    if (Test-Path (Join-Path $ai "fema_ops")) {
        Push-Location $ai
        python -m fema_ops ingest --source $Source --magic $Magic 2>$null
        Pop-Location
    }
    exit 0
} catch {
    Write-Host "sync_partial_or_fail: $_"
    # Write heartbeat stub
    $hb = Join-Path $RepoRoot "AI\data\live\sync_heartbeat.json"
    @{
        synced_utc = (Get-Date).ToUniversalTime().ToString("o")
        source = $Source
        baskets_src = $src.FullName
        baskets_bytes = $src.Length
        baskets_locked = $true
        wave = "IS-W1"
        note = "$_"
    } | ConvertTo-Json | Set-Content -Path $hb -Encoding UTF8
    exit 4
}
