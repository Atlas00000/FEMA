# AER-P4-01 - Build Strategy Tester .ini for a queue job / preset
# Usage:
#   powershell -File ops\tester_queue\build_ini.ps1 -Preset Candidate_X1
#   powershell -File ops\tester_queue\build_ini.ps1 -Preset Candidate_X1 -Window "2026.01.01-2026.07.31" -JobId job_xxx

param(
    [Parameter(Mandatory = $true)][string]$Preset,
    [string]$Window = "2026.01.01-2026.07.31",
    [string]$Symbol = "EURUSD",
    [string]$JobId = "",
    [string]$RepoRoot = "",
    [string]$OutPath = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

$pathsFile = Join-Path $PSScriptRoot "discovery_paths.json"
$paths = Get-Content -Raw -Path $pathsFile | ConvertFrom-Json
$b = $paths.terminal_b
$d = $paths.tester_defaults

$dataRoot = Join-Path $env:APPDATA ("MetaQuotes\Terminal\" + $b.data_hash)
$testerProfiles = Join-Path $dataRoot "MQL5\Profiles\Tester"
$setName = if ($Preset.ToLower().EndsWith(".set")) { $Preset } else { "$Preset.set" }
$setPath = Join-Path $testerProfiles $setName
if (-not (Test-Path $setPath)) {
    throw "Preset not found on Terminal B: $setPath (copy Presets first)"
}

$ex5 = Join-Path $dataRoot ("MQL5\Experts\" + ($b.expert -replace "/", "\"))
if (-not (Test-Path $ex5)) {
    throw "FEMA.ex5 missing on Terminal B: $ex5 (compile in B MetaEditor)"
}

if ($Window -notmatch "^(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})$") {
    throw "Window must be YYYY.MM.DD-YYYY.MM.DD, got: $Window"
}
$fromDate = $Matches[1]
$toDate = $Matches[2]
# Clamp ToDate to today if future (history often lags)
$today = Get-Date -Format "yyyy.MM.dd"
if ($toDate -gt $today) { $toDate = $today }

$iniDir = Join-Path $PSScriptRoot "ini"
$reportDir = Join-Path $PSScriptRoot "reports"
New-Item -ItemType Directory -Force -Path $iniDir | Out-Null
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null

$safePreset = ($Preset -replace "[^A-Za-z0-9._-]", "_")
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = if ($JobId) { $JobId } else { "job_$stamp" }
if (-not $OutPath) {
    $OutPath = Join-Path $iniDir ("${base}_${safePreset}.ini")
}
$reportLeaf = "${base}_${safePreset}"

# Build [TesterInputs] from .set (Key=Value) - more reliable than ExpertParameters alone
$inputLines = New-Object System.Collections.Generic.List[string]
Get-Content $setPath | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith(";") -or $line.StartsWith("#")) { return }
    if ($line -match "^(Inp[A-Za-z0-9_]+)=(.*)$") {
        $k = $Matches[1]
        $v = $Matches[2].Trim()
        # Fixed param: value||value||step||value||N
        $inputLines.Add("$k=$v||$v||0||$v||N") | Out-Null
    }
}
if ($inputLines.Count -lt 5) {
    throw "Failed to parse TesterInputs from $setPath"
}

$iniBody = @"
; FEMA AER-P4 Discovery Tester config (ASCII)
; preset=$Preset job=$base window=$fromDate-$toDate
; Terminal B only - refuse Terminal A launch in launch.ps1
[Tester]
Expert=$($b.expert)
Symbol=$Symbol
Period=$($d.period)
Optimization=$($d.optimization)
Model=$($d.model)
FromDate=$fromDate
ToDate=$toDate
ForwardMode=0
Deposit=$($d.deposit)
Currency=$($d.currency)
ProfitInPips=$($d.profit_in_pips)
Leverage=$($d.leverage)
ExecutionMode=0
Visual=$($d.visual)
Report=$reportLeaf
ReplaceReport=$($d.replace_report)
ShutdownTerminal=$($d.shutdown_terminal)
UseLocal=1
UseRemote=0
UseCloud=0
[TesterInputs]
$($inputLines -join "`r`n")
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($OutPath, $iniBody.TrimStart() + "`r`n", $utf8NoBom)

Write-Host "wrote $OutPath"
Write-Host "expert=$($b.expert) inputs=$($inputLines.Count) $fromDate->$toDate deposit=$($d.deposit) ProfitInPips=$($d.profit_in_pips) Leverage=$($d.leverage)"
Write-Output $OutPath
