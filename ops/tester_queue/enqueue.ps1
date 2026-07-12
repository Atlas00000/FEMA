param(
  [Parameter(Mandatory = $true)][string]$Preset,
  [string]$Window = "2026.01.01-2026.07.31",
  [string]$Symbol = "EURUSD",
  [string]$Notes = "",
  [string]$QueuePath = ""
)
$ErrorActionPreference = "Stop"
if (-not $QueuePath) {
  $QueuePath = Join-Path $PSScriptRoot "queue.json"
}
$q = Get-Content -Raw -Path $QueuePath | ConvertFrom-Json
$id = "job_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$job = [ordered]@{
  id         = $id
  preset     = $Preset
  symbol     = $Symbol
  window     = $Window
  notes      = $Notes
  status     = "queued"
  enqueued   = (Get-Date).ToUniversalTime().ToString("o")
  started    = $null
  finished   = $null
  run_id     = $null
}
$list = @($q.jobs) + @($job)
$q.jobs = $list
$q.updated = (Get-Date -Format "yyyy-MM-dd")
($q | ConvertTo-Json -Depth 6) | Set-Content -Path $QueuePath -Encoding utf8
Write-Host "enqueued $id preset=$Preset"
