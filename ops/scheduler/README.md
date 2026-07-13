# AER-P3 — Scheduled sync / pipeline (L1)

**Charter:** Terminal A demo watch and Terminal B tester ingest on separate schedules. No auto-promote. G1 still needs `postrun.ps1 -DD`.

## Tasks

| Task | Script | Schedule (default) |
| ---- | ------ | ------------------- |
| **FEMA_Ops_Demo** | `scheduled_demo.ps1` | Every 15 min, 07:00–23:00 |
| **FEMA_Ops_Tester_*** | `scheduled_tester.ps1` | Daily 06:00, 06:15, 06:30, 06:45 |

## Install (once)

```powershell
powershell -ExecutionPolicy Bypass -File ops\scheduler\register_tasks.ps1
```

Remove:

```powershell
powershell -ExecutionPolicy Bypass -File ops\scheduler\register_tasks.ps1 -Uninstall
```

## Manual test

```powershell
powershell -File ops\scheduler\scheduled_demo.ps1
powershell -File ops\scheduler\scheduled_tester.ps1
```

## Artifacts

| File | Purpose |
| ---- | ------- |
| `AI/data/live/scheduler_last.json` | Last scheduled job result |
| `AI/data/live/sync_heartbeat.json` | Sync ok/fail (Observatory reads) |
| `AI/data/live/logs/scheduled_*.log` | Daily log per job |

## After overnight Tester

Scheduler only **sync + ingest**. For register + G1:

```powershell
powershell -File ops\tester_queue\postrun.ps1 -Preset Candidate_X1 -DD 19.17
```

## IDs

`AER-P3-01` … `AER-P3-04` — see [`automated_edge_rediscovery_pipeline.md`](../../automated_edge_rediscovery_pipeline.md) (`AER-P0`…`P6` tooling complete 2026-07-13).
