param([string]$QueuePath = "")
$ErrorActionPreference = "Stop"
if (-not $QueuePath) {
  $QueuePath = Join-Path $PSScriptRoot "queue.json"
}
$q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
Write-Host "tester_queue max_concurrent=$($q.max_concurrent) jobs=$($q.jobs.Count)"
foreach ($j in $q.jobs) {
  Write-Host ("  {0}  {1}  {2}  {3}" -f $j.status, $j.id, $j.preset, $j.window)
}
$queued = @($q.jobs | Where-Object { $_.status -eq "queued" })
Write-Host "queued=$($queued.Count)  (drain on Discovery box only — never demo Common)"
