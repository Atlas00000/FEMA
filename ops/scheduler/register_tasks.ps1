# Register Windows Task Scheduler jobs for AER-P3 (run once as your user).
#   powershell -ExecutionPolicy Bypass -File ops\scheduler\register_tasks.ps1
#   powershell -ExecutionPolicy Bypass -File ops\scheduler\register_tasks.ps1 -Uninstall

param([switch]$Uninstall)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$demoCmd = Join-Path $here "run_demo.cmd"
$testCmd = Join-Path $here "run_tester.cmd"

if ($Uninstall) {
    foreach ($t in @("FEMA_Ops_Demo", "FEMA_Ops_Tester_Morning", "FEMA_Ops_Tester_0615", "FEMA_Ops_Tester_0630", "FEMA_Ops_Tester_0645")) {
        cmd /c "schtasks /Delete /TN $t /F 2>nul"
        Write-Host "removed $t (if existed)"
    }
    exit 0
}

Write-Host "demo=$demoCmd"
Write-Host "tester=$testCmd"

schtasks /Create /F /TN "FEMA_Ops_Demo" /TR "`"$demoCmd`"" /SC MINUTE /MO 15 /ST 07:00 /RL LIMITED
Write-Host "created FEMA_Ops_Demo (every 15 min from 07:00)"

schtasks /Create /F /TN "FEMA_Ops_Tester_Morning" /TR "`"$testCmd`"" /SC DAILY /ST 06:00 /RL LIMITED
Write-Host "created FEMA_Ops_Tester_Morning at 06:00"

foreach ($st in @("06:15", "06:30", "06:45")) {
    $tn = "FEMA_Ops_Tester_$($st -replace ':','')"
    schtasks /Create /F /TN $tn /TR "`"$testCmd`"" /SC DAILY /ST $st /RL LIMITED | Out-Null
    Write-Host "created $tn at $st"
}

Write-Host ""
Write-Host "Verify: schtasks /Query /TN FEMA_Ops_Demo /FO LIST"
