# Immutable run artifacts (IS-P3-01)

Layout: `runs/{run_id}/baskets.csv` (+ optional events/meta) + `manifest.json`.

```powershell
cd AI
python -m fema_ops artifacts-archive
python -m fema_ops db-rehydrate --run-id <run_id>
```

Fat CSVs are gitignored; this README is committed. Docker volume: `/var/fema/artifacts`.
