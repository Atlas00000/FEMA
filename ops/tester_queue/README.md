# Windows tester queue (IS-P4-01 + AER-P4 + AER-P5 + AER-P6)

**Goal:** Discovery / Strategy Tester jobs must **not** starve or overwrite the demo Common `FEMA_AI` path.

**Hard rule:** scripts enqueue / launch / drain / score — they **never** promote PRODUCTION (`PARK-01`).

## Split

| Role | Path | Sync | Ingest |
| ---- | ---- | ---- | ------ |
| **Demo (EL4)** | `Common\Files\FEMA_AI\` | `ops/sync/sync.ps1 -Source demo` | `fema_ops ingest --source demo` |
| **Tester / Discovery** | `Tester\...\Agent-*\MQL5\Files\FEMA_AI\` | `ops/sync/sync.ps1 -Source tester` | `fema_ops ingest --source tester` |

Never point demo health at tester CSVs. Never run heavy optimizers on the same terminal instance that holds an open demo basket.

## Paths (Terminal B)

[`discovery_paths.json`](discovery_paths.json) — install `C:\MT5_FEMA_Discovery`, data hash `0E1EDD...`. Launch **refuses** Terminal A (`D0E8...`).

## Queue

```powershell
powershell -File ops\tester_queue\enqueue.ps1 -Preset Candidate_X1 -Window "2026.01.01-2026.07.31"
powershell -File ops\tester_queue\status.ps1
```

## AER-P4 — Scripted Tester launch

```powershell
# Preview .ini + guard only
powershell -File ops\tester_queue\launch.ps1 -DryRun

# Drain queue head on Terminal B (closes B if open; leaves A alone)
# Waits for ShutdownTerminal=1, stamps queue, runs postrun (sync/register/G1 if DD parsed)
powershell -File ops\tester_queue\launch.ps1

# Build ini only
powershell -File ops\tester_queue\build_ini.ps1 -Preset Candidate_X1

# Skip auto postrun
powershell -File ops\tester_queue\launch.ps1 -SkipPostrun
```

Manual postrun (if needed):

```powershell
powershell -File ops\tester_queue\postrun.ps1 -Preset Candidate_X1 -DD 19.17
```

## AER-P5 — Multi-job drain + EL7

```powershell
# Fill queue from EL7 (skips if open_discovery=false unless -Force)
powershell -File ops\tester_queue\el7_enqueue.ps1
powershell -File ops\tester_queue\el7_enqueue.ps1 -Force -Max 3

# Overnight: FIFO drain, one-at-a-time, max 3
powershell -File ops\tester_queue\drain.ps1 -Max 3
powershell -File ops\tester_queue\drain.ps1 -DryRun

# Morning scorecard (read-only)
powershell -File ops\tester_queue\scorecard.ps1
```

## AER-P6 — Human decision pack

```powershell
# Fill checklist + append el2_promote_decision.md (never swaps Terminal A)
powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X1 -PF 1.477 -DD 19.17 -Decision Reject -FailureReason dd_breach -Signer "operator"
powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X2 -PF 1.4316 -DD 18.13 -Decision Alternate -FailureReason dd_breach -Signer "operator"

# Promote only after G1 pass; still requires manual lock/EL8/Terminal A redeploy
powershell -File ops\tester_queue\decision.ps1 -Preset <id> -PF <pf> -DD <dd> -Decision Promote -Signer "operator"
```

## Worker rules

1. One tester job at a time on Terminal B.
2. Close Strategy Tester UI on B before `launch.ps1` (script stops B `terminal64` under Discovery install only).
3. After run: Agent `FEMA_AI` -> sync/postrun; human still promotes.
4. MT5-in-Docker is **parked** (Wave 6).
5. No auto-promote cron, endpoint, or script path.

## Artifacts

| Path | Purpose |
| ---- | ------- |
| `ops/tester_queue/ini/` | Generated `.ini` copies |
| `C:\MT5_FEMA_Discovery\tester_queue_*.ini` | Launch `/config` target |
| `C:\MT5_FEMA_Discovery\reports/` | MT5 HTML reports |
| `ops/tester_queue/reports/` | Copied reports |
| `AI/data/live/scheduler_last.json` | Last launch summary |
| `AI/data/live/el7_enqueue_latest.json` | Last EL7 enqueue plan |
| `AI/data/live/drain_latest.json` | Last drain batch |
| `AI/data/live/discovery_scorecard_latest.{json,md}` | Morning G1 pack |
| `AI/kb/decisions/*.md` | Filled promotion checklists |
| `AI/data/live/promote_decision_latest.json` | Last AER-P6 decision packet |
