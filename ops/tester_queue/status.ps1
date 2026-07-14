param([string]$QueuePath = "")
$ErrorActionPreference = "Stop"
if (-not $QueuePath) {
  $QueuePath = Join-Path $PSScriptRoot "queue.json"
}
$q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
Write-Host "tester_queue schema=$($q.schema) max_concurrent=$($q.max_concurrent) jobs=$($q.jobs.Count)"
foreach ($j in $q.jobs) {
  $lane = if ($j.lane) { $j.lane } else { "A?" }
  $parent = if ($j.parent) { $j.parent } else { "-" }
  $role = if ($j.role) { $j.role } else { "-" }
  Write-Host ("  {0}  {1}  {2}  lane={3} parent={4} role={5}  {6}" -f $j.status, $j.id, $j.preset, $lane, $parent, $role, $j.window)
}
$queued = @($q.jobs | Where-Object { $_.status -eq "queued" })
$queuedA = @($queued | Where-Object { (-not $_.lane) -or ($_.lane -eq "A") })
$queuedB = @($queued | Where-Object { $_.lane -eq "B" })
Write-Host "queued=$($queued.Count) laneA_queued=$($queuedA.Count)/3  laneB_queued=$($queuedB.Count)/2  (drain on Discovery box only - never demo Common)"
