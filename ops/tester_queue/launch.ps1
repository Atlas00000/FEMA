# AER-P4-02/03/04 --- Drain queue head on Terminal B, wait, stamp, optional postrun
# Usage:
#   powershell -File ops\tester_queue\launch.ps1
#   powershell -File ops\tester_queue\launch.ps1 -DryRun
#   powershell -File ops\tester_queue\launch.ps1 -JobId job_xxx -SkipPostrun
#   powershell -File ops\tester_queue\launch.ps1 -Postrun -DD 0
#
# Guards: refuses Terminal A hash / exe. Requires Terminal B closed (or free for /config run).

param(
    [string]$JobId = "",
    [switch]$DryRun,
    [switch]$SkipPostrun,
    [switch]$Postrun,
    [double]$DD = 0.0,
    [int]$TimeoutMinutes = 180,
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

$pathsFile = Join-Path $PSScriptRoot "discovery_paths.json"
$paths = Get-Content -Raw -Path $pathsFile | ConvertFrom-Json
$b = $paths.terminal_b
$a = $paths.terminal_a

function Assert-DiscoveryOnly {
    $exe = [System.IO.Path]::GetFullPath($b.terminal_exe)
    $install = [System.IO.Path]::GetFullPath($b.install_dir)
    if ($exe -notlike "$install*") {
        throw "AER-P4-04 GUARD: terminal_exe not under Terminal B install: $exe"
    }
    if (-not (Test-Path $exe)) {
        throw "Terminal B exe missing: $exe"
    }
    if ($a.forbid_launch -and $b.data_hash -eq $a.data_hash) {
        throw "AER-P4-04 GUARD: Terminal B data_hash equals Terminal A --- refuse"
    }
    if ($install -match [regex]::Escape($a.data_hash)) {
        throw "AER-P4-04 GUARD: install path references Terminal A hash"
    }
    # Refuse launching D0E8... terminal64 if misconfigured
    $forbiddenExe = Join-Path $env:APPDATA ("MetaQuotes\Terminal\" + $a.data_hash)
    if ($exe -like "$forbiddenExe*") {
        throw "AER-P4-04 GUARD: refusing Terminal A path: $exe"
    }
    Write-Host "guard_ok terminal_b=$($b.data_hash) exe=$exe"
}

function Get-Queue {
    return (Get-Content -Raw -Path $QueuePath | ConvertFrom-Json)
}

function Save-Queue($q) {
    $q.updated = (Get-Date -Format "yyyy-MM-dd")
    ($q | ConvertTo-Json -Depth 8) | Set-Content -Path $QueuePath -Encoding utf8
}

function Select-Job($q) {
    if ($JobId) {
        $j = @($q.jobs | Where-Object { $_.id -eq $JobId }) | Select-Object -First 1
        if (-not $j) { throw "Job not found: $JobId" }
        if ($j.status -notin @("queued", "running", "failed")) {
            Write-Host "WARN: job status=$($j.status) --- launching anyway"
        }
        return $j
    }
    $j = @($q.jobs | Where-Object { $_.status -eq "queued" } | Sort-Object enqueued) | Select-Object -First 1
    if (-not $j) { throw "No queued jobs in $QueuePath" }
    return $j
}

function Set-JobProp($jobObj, [string]$Name, $Value) {
    if ($null -eq $jobObj.PSObject.Properties[$Name]) {
        $jobObj | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    } else {
        $jobObj.$Name = $Value
    }
}

function Parse-ReportDd([string]$reportHtm) {
    if (-not (Test-Path $reportHtm)) { return 0.0 }
    $html = Get-Content -Raw -Path $reportHtm -ErrorAction SilentlyContinue
    if (-not $html) { return 0.0 }
    # Prefer Maximal Balance Drawdown percent, e.g. 19.17%
    if ($html -match "Balance Drawdown Maximal[^0-9]*[\d\.]+ \(([\d\.]+)%\)") {
        return [double]$Matches[1]
    }
    if ($html -match "Maximal balance drawdown[^0-9]*[\d\.]+ \(([\d\.]+)%\)") {
        return [double]$Matches[1]
    }
    if ($html -match "\(([\d\.]+)%\)\s*</td>\s*</tr>\s*<tr[^>]*>\s*<td[^>]*>Equity Drawdown") {
        return [double]$Matches[1]
    }
    return 0.0
}

Assert-DiscoveryOnly

$q = Get-Queue
$job = Select-Job $q
Write-Host "selected $($job.id) preset=$($job.preset) window=$($job.window) status=$($job.status)"

$iniOut = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "build_ini.ps1") `
    -Preset $job.preset -Window $job.window -Symbol $job.symbol -JobId $job.id -RepoRoot $RepoRoot
$iniPath = ($iniOut | Select-Object -Last 1).ToString().Trim()
if (-not (Test-Path $iniPath)) { throw "build_ini failed: $iniPath" }

# Copy .ini next to a short path under Terminal B install (helps /config length + MT5 find)
$iniLocal = Join-Path $b.install_dir ("tester_queue_" + $job.id + ".ini")
Copy-Item $iniPath $iniLocal -Force
Write-Host "ini_local=$iniLocal"

if ($DryRun) {
    Write-Host "DryRun: would launch $($b.terminal_exe) /config:$iniLocal"
    exit 0
}

# Refuse if caller somehow points config at Terminal A Experts tree as working dir
$cfgFull = [System.IO.Path]::GetFullPath($iniLocal)
if ($cfgFull -match [regex]::Escape($a.data_hash)) {
    throw "AER-P4-04 GUARD: config path under Terminal A: $cfgFull"
}

# Mark running
foreach ($j in $q.jobs) {
    if ($j.id -eq $job.id) {
        Set-JobProp $j "status" "running"
        Set-JobProp $j "started" ((Get-Date).ToUniversalTime().ToString("o"))
        Set-JobProp $j "ini" $iniPath
    }
}
Save-Queue $q

# Ensure no stale Discovery terminal holding lock (do NOT kill Terminal A)
$aHash = $a.data_hash
Get-Process -Name "terminal64","terminal" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $p = $_.Path
        if ($p -and ($p -like "$($b.install_dir)*")) {
            Write-Host "stopping Terminal B process pid=$($_.Id)"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        } elseif ($p -and ($p -match [regex]::Escape($aHash))) {
            Write-Host "leave Terminal A running pid=$($_.Id)"
        }
    } catch {}
}
Start-Sleep -Seconds 2

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $b.terminal_exe
$psi.Arguments = "/config:$iniLocal"
$psi.WorkingDirectory = $b.install_dir
$psi.UseShellExecute = $false
Write-Host "launch: $($psi.FileName) $($psi.Arguments)"
$proc = [System.Diagnostics.Process]::Start($psi)
if (-not $proc) { throw "Failed to start Terminal B" }

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
Write-Host "waiting for ShutdownTerminal (timeout ${TimeoutMinutes}m) ..."
while (-not $proc.HasExited) {
    if ((Get-Date) -gt $deadline) {
        try { $proc.Kill() } catch {}
        $q = Get-Queue
        foreach ($j in $q.jobs) {
            if ($j.id -eq $job.id) {
                Set-JobProp $j "status" "failed"
                Set-JobProp $j "finished" ((Get-Date).ToUniversalTime().ToString("o"))
                $note = [string]$j.notes
                Set-JobProp $j "notes" (($note + " | timeout ${TimeoutMinutes}m").Trim())
            }
        }
        Save-Queue $q
        throw "Tester timeout after ${TimeoutMinutes} minutes"
    }
    Start-Sleep -Seconds 5
}
Write-Host "terminal exited code=$($proc.ExitCode)"

# Locate report
$reportBaseName = $job.id + "_" + ($job.preset -replace "[^A-Za-z0-9._-]", "_")
$searchRoots = @(
    $b.install_dir,
    (Join-Path $b.install_dir "reports"),
    (Join-Path $env:APPDATA ("MetaQuotes\Terminal\" + $b.data_hash))
)
$reportHtm = $null
foreach ($root in $searchRoots) {
    if (-not (Test-Path $root)) { continue }
    foreach ($ext in @(".htm", ".html")) {
        $c = Join-Path $root ($reportBaseName + $ext)
        if (Test-Path $c) { $reportHtm = $c; break }
    }
    if ($reportHtm) { break }
}
if (-not $reportHtm) {
    $candidates = @()
    foreach ($root in $searchRoots) {
        if (Test-Path $root) {
            $candidates += Get-ChildItem $root -Filter "*.htm" -ErrorAction SilentlyContinue
        }
    }
    $latest = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) { $reportHtm = $latest.FullName }
}

$parsedDd = 0.0
if ($reportHtm) {
    $parsedDd = Parse-ReportDd $reportHtm
    $destRep = Join-Path $PSScriptRoot ("reports\" + [IO.Path]::GetFileName($reportHtm))
    New-Item -ItemType Directory -Force -Path (Split-Path $destRep) | Out-Null
    Copy-Item $reportHtm $destRep -Force -ErrorAction SilentlyContinue
    Write-Host "report=$reportHtm parsed_dd=$parsedDd"
}

$q = Get-Queue
foreach ($j in $q.jobs) {
    if ($j.id -eq $job.id) {
        Set-JobProp $j "status" "finished"
        Set-JobProp $j "finished" ((Get-Date).ToUniversalTime().ToString("o"))
        Set-JobProp $j "report" $reportHtm
        if ($parsedDd -gt 0) { Set-JobProp $j "dd_balance_pct" $parsedDd }
    }
}
Save-Queue $q
Write-Host "marked finished: $($job.id)"

$doPostrun = $Postrun -or (-not $SkipPostrun)
# Default: run postrun without requiring -Postrun switch (SkipPostrun to disable)
if ($SkipPostrun) { $doPostrun = $false }
else { $doPostrun = $true }

if ($doPostrun) {
    $ddUse = if ($DD -gt 0) { $DD } elseif ($parsedDd -gt 0) { $parsedDd } else { 0.0 }
    $parts = $job.window -split "-"
    $wf = $parts[0]
    $wt = if ($parts.Count -gt 1) { $parts[1] } else { "2026.07.31" }
    Write-Host "postrun preset=$($job.preset) dd=$ddUse"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "postrun.ps1") `
        -Preset $job.preset -JobId $job.id -DD $ddUse -WindowFrom $wf -WindowTo $wt -RepoRoot $RepoRoot -QueuePath $QueuePath
}

# Artifact for scheduler / morning review
$live = Join-Path $RepoRoot "AI\data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
@{
    job       = "tester_launch"
    aer_phase = "AER-P4"
    ran_utc   = (Get-Date).ToUniversalTime().ToString("o")
    job_id    = $job.id
    preset    = $job.preset
    report    = $reportHtm
    dd        = $parsedDd
    ok        = $true
} | ConvertTo-Json | Set-Content (Join-Path $live "scheduler_last.json") -Encoding utf8

Write-Host "=== launch done ==="

