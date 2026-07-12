# Daily health / Observatory runbook (ESR-W05 / Wave 0)

**One command (preferred):**

```powershell
cd AI
python -m fema_ops pipeline
```

Skips health/fingerprint cleanly when demo CSV is header-only; re-run after a basket close.

## Manual steps

1. Sync **demo** CSVs: `cd AI && python -m fema_ops ingest --source demo`
2. Health: `python -m fema_ops health` (needs closed rows)
3. Fingerprint / drift: `python -m fema_ops fingerprint` · `python -m fema_ops drift`
4. Observatory: `python -m fema_ops observatory` → `data/live/observatory_daily.md`
5. Refresh status: `python -m fema_ops status`
6. Default: **do nothing** unless persistence warning / retire ladder

**Paths:** demo → `Terminal\Common\Files\FEMA_AI\` · tester → `Tester\...\Agent-*\FEMA_AI\`  
If `header_only=1`, wait for a basket close before trusting health on the demo path.

Optional: `python -m fema_ops ingest --source tester` after Discovery collects only.  
Full pipeline notes: [`ops_pipeline.md`](ops_pipeline.md)
