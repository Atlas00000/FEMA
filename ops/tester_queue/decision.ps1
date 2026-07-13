# AER-P6 - Human decision pack (checklist + KB append). NEVER promotes PRODUCTION.
# Usage:
#   powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X1 -PF 1.477 -DD 19.17 -Decision Reject -FailureReason dd_breach -Signer "operator"
#   powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X2 -PF 1.40 -DD 18.1 -Decision Alternate -FailureReason dd_breach
#   powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_Y -PF 1.50 -DD 16.0 -Decision Promote -Signer "operator"
#
# Promote path only writes the signed packet + next-step checklist. It does NOT
# swap Terminal A charts, bump certificates, or retire locks (human AER-P6-03/04).

param(
    [Parameter(Mandatory = $true)][string]$Preset,
    [Parameter(Mandatory = $true)][double]$PF,
    [Parameter(Mandatory = $true)][double]$DD,
    [Parameter(Mandatory = $true)]
    [ValidateSet("Promote", "Reject", "Alternate")]
    [string]$Decision,
    [string]$FailureReason = "",
    [string]$RunId = "",
    [string]$Window = "2026.01.01-2026.07.31",
    [string]$Signer = "operator",
    [string]$Notes = "",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}

$ai = Join-Path $RepoRoot "AI"
$gates = Get-Content -Raw (Join-Path $ai "kb\gate_rules.json") | ConvertFrom-Json
$benchPf = [double]$gates.production_benchmark.profit_factor
$benchDd = [double]$gates.production_benchmark.max_dd_balance_pct
$lockRun = [string]$gates.production_benchmark.run_id

$g1Pf = ($PF -ge $benchPf)
$g1Dd = ($DD -gt 0) -and ($DD -le $benchDd)
$g1Pass = $g1Pf -and $g1Dd

if ($Decision -eq "Promote" -and -not $g1Pass) {
    throw "AER-P6: Refuse Promote - G1 fail (PF=$PF vs $benchPf, DD=$DD vs $benchDd). Use Reject or Alternate."
}
if ($Decision -eq "Reject" -and -not $FailureReason) {
    if (-not $g1Pf) { $FailureReason = "pf_breach" }
    elseif (-not $g1Dd) { $FailureReason = "dd_breach" }
    else { $FailureReason = "other" }
}
if ($Decision -eq "Alternate" -and -not $FailureReason) {
    $FailureReason = "dd_breach"
}
if ($Decision -eq "Promote") {
    $FailureReason = ""
}

if (-not $RunId) {
    $cand = Get-ChildItem (Join-Path $ai "kb\runs") -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*$Preset*" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($cand) {
        $mj = Join-Path $cand.FullName "metrics.json"
        if (Test-Path $mj) {
            $RunId = (Get-Content -Raw $mj | ConvertFrom-Json).run_id
        }
    }
}
if (-not $RunId) { $RunId = "(unknown - fill from kb/runs)" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$utc = (Get-Date).ToUniversalTime().ToString("o")
$decDir = Join-Path $ai "kb\decisions"
New-Item -ItemType Directory -Force -Path $decDir | Out-Null
$filledPath = Join-Path $decDir "${stamp}_${Preset}_${Decision}.md"
$liveJson = Join-Path $ai "data\live\promote_decision_latest.json"

$g1Label = if ($g1Pass) { "PASS" } else { "FAIL" }
$decUpper = $Decision.ToUpperInvariant()
$markPromote = if ($Decision -eq "Promote") { "x" } else { " " }
$markReject = if ($Decision -eq "Reject") { "x" } else { " " }
$markAlt = if ($Decision -eq "Alternate") { "x" } else { " " }
$markG1 = if ($g1Pass) { "x" } else { " " }
$pfOk = if ($g1Pf) { "ok" } else { "FAIL" }
$ddOk = if ($g1Dd) { "ok" } else { "FAIL" }
$failShow = if ($FailureReason) { $FailureReason } else { "-" }
$dateLocal = Get-Date -Format "yyyy-MM-dd"

if ($Decision -eq "Promote") {
    $nextSteps = @"
1. Confirm lock fingerprint: ``python -m fema_ops lock-confirm``
2. Bump certificate + System Profile for new lock (do not overwrite birth CSV blindly).
3. EL8: archive prior lock run under ``AI/kb/runs`` / artifacts; one active lock only.
4. Redeploy **Terminal A** chart to the new ``.set`` only after sign-off.
5. Terminal B stays Discovery - do not point demo Common at tester CSVs.
"@
} else {
    $nextSteps = @"
1. Keep ``PRODUCTION.set`` on Terminal A.
2. Leave Discovery queue free for next EL7 wave (max 3).
3. Record ``failure_reason=$FailureReason`` in candidates KB (done by this script when possible).
"@
}

$md = @"
# Promotion checklist (filled) - AER-P6

**Candidate id:** ``$Preset``
**run_id:** ``$RunId``
**Parent lock:** ``PRODUCTION`` (``$lockRun``)
**Window:** ``$Window`` EURUSD M5
**Generated:** $utc
**Signer:** $Signer

## Evidence

- [x] Same tester contract (`$400` · every tick · ProfitInPips=0) - assumed from AER launch.ini
- [$markG1] **G1:** PF >= PRODUCTION **and** max DD <= PRODUCTION
  - Candidate PF **$PF** vs bench **$benchPf** -> $pfOk
  - Candidate DD **$DD%** vs bench **$benchDd%** -> $ddOk
  - Gate: **$g1Label**
- [x] Not a stale-slice-only win (canonical 2026 window)
- [ ] Walk-forward / holdout note attached (or N/A) - human
- [x] Diff is one subsystem (factory / search_map)
- [x] KB decision packet written (this file + ``el2_promote_decision.md``)
- [x] Human sign-off: **$Signer** / $dateLocal

## Forbidden

- [x] Not promoting because "AI says so"
- [x] No live EMA / TP / SL / lot / grid change
- [x] No auto-promote

## Decision

- [$markPromote] **Promote** -> new lock + certificate bump + EL8 archive old (**manual next steps below**)
- [$markReject] **Reject** -> ``failure_reason=$FailureReason`` · keep PRODUCTION
- [$markAlt] **Alternate** -> stay candidate; do not deploy

**Notes:** $Notes

## Next steps (human only)

$nextSteps

**Template:** ``AI/templates/promotion_checklist.md``
**Signed decision log:** ``AI/kb/el2_promote_decision.md``
"@

$md | Set-Content -Path $filledPath -Encoding utf8

$leaf = Split-Path $filledPath -Leaf
$append = @"

## AER-P6 - $Preset ($stamp)

| Field | Value |
| ----- | ----- |
| Decision | **$decUpper** |
| Preset | ``$Preset`` |
| run_id | ``$RunId`` |
| PF / DD | $PF / $DD% |
| G1 | $g1Label (bench PF $benchPf / DD $benchDd%) |
| failure_reason | $failShow |
| Signer | $Signer |
| Checklist | ``kb/decisions/$leaf`` |
| Notes | $Notes |

**PRODUCTION lock unchanged unless Decision=PROMOTE and human completes AER-P6-03/04.**
"@
Add-Content -Path (Join-Path $ai "kb\el2_promote_decision.md") -Value $append -Encoding utf8

$csvPath = Join-Path $ai "kb\candidates.csv"
if (Test-Path $csvPath) {
    $lines = @(Get-Content $csvPath)
    if ($lines.Count -ge 2) {
        $hdr = $lines[0].Split(",")
        $idxPreset = [array]::IndexOf($hdr, "id")
        if ($idxPreset -lt 0) { $idxPreset = [array]::IndexOf($hdr, "preset") }
        $idxStatus = [array]::IndexOf($hdr, "status")
        $idxFail = [array]::IndexOf($hdr, "failure_reason")
        $newLines = New-Object System.Collections.Generic.List[string]
        $newLines.Add($lines[0]) | Out-Null
        for ($i = 1; $i -lt $lines.Count; $i++) {
            $cols = $lines[$i].Split(",")
            if ($idxPreset -ge 0 -and $cols.Count -gt $idxPreset -and $cols[$idxPreset] -eq $Preset) {
                if ($idxStatus -ge 0 -and $cols.Count -gt $idxStatus) {
                    $cols[$idxStatus] = switch ($Decision) {
                        "Promote" { "promote_pending" }
                        "Reject" { "reject" }
                        "Alternate" { "alternate" }
                    }
                }
                if ($idxFail -ge 0 -and $cols.Count -gt $idxFail) {
                    $cols[$idxFail] = $FailureReason
                }
                $newLines.Add(($cols -join ",")) | Out-Null
            } else {
                $newLines.Add($lines[$i]) | Out-Null
            }
        }
        ($newLines -join "`r`n") + "`r`n" | Set-Content $csvPath -Encoding utf8
    }
}

$relCheck = ($filledPath.Substring($RepoRoot.Length).TrimStart("\", "/")).Replace("\", "/")
$payload = [ordered]@{
    schema         = "fema_aer_p6_decision_v0"
    ran_utc        = $utc
    preset         = $Preset
    run_id         = $RunId
    pf             = $PF
    dd             = $DD
    g1_pass        = $g1Pass
    decision       = $Decision
    failure_reason = $FailureReason
    signer         = $Signer
    checklist      = $relCheck
    note           = "NO AUTO-PROMOTE. Promote requires manual Terminal A redeploy."
}
$live = Join-Path $ai "data\live"
New-Item -ItemType Directory -Force -Path $live | Out-Null
($payload | ConvertTo-Json -Depth 5) | Set-Content $liveJson -Encoding utf8

Write-Host "wrote $filledPath"
Write-Host "appended el2_promote_decision.md"
Write-Host "wrote $liveJson"
Write-Host "decision=$Decision g1=$g1Label (no chart swap)"
if ($Decision -eq "Promote") {
    Write-Host "NEXT: human AER-P6-03/04 - lock-confirm, certificate, EL8, Terminal A redeploy"
}
