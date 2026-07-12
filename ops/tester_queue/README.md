# Windows tester queue (IS-P4-01)

**Goal:** Discovery / Strategy Tester jobs must **not** starve or overwrite the demo Common `FEMA_AI` path.

## Split

| Role | Path | Sync | Ingest |
| ---- | ---- | ---- | ------ |
| **Demo (EL4)** | `Common\Files\FEMA_AI\` | `ops/sync/sync.ps1 -Source demo` | `fema_ops ingest --source demo` |
| **Tester / Discovery** | `Tester\...\Agent-*\MQL5\Files\FEMA_AI\` | `ops/sync/sync.ps1 -Source tester` | `fema_ops ingest --source tester` |

Never point demo health at tester CSVs. Never run heavy optimizers on the same terminal instance that holds an open demo basket.

## Queue file

[`queue.json`](queue.json) — pending Discovery jobs (human / script fills; worker drains one at a time).

```powershell
powershell -File ops\tester_queue\enqueue.ps1 -Preset P2C-001_REG_ADX30 -Window "2026.01.01-2026.07.31" -Notes "EL7 candidate"
powershell -File ops\tester_queue\status.ps1
```

## Worker rules

1. One tester job at a time on the Discovery box (or dedicated Agent).
2. After run: copy Agent `FEMA_AI` → `ops/incoming/tester/` then `db-ingest` / `register`.
3. Demo box stays attached to PRODUCTION; no preset swap mid-basket.
4. MT5-in-Docker is **parked** (Wave 6) — Windows worker only.

## Parallelism without killing demo

- Prefer a **second MT5 terminal / VPS** for Tester.
- If same machine: schedule Discovery outside London/NY open, and never unload the demo EA chart.
