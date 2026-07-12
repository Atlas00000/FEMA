# Daily ops pipeline (infra — no need to wait for demo health)

Runs offline anytime. **Health scores demo only when closed baskets exist.**

```powershell
cd AI
python -m fema_ops pipeline                  # demo ingest; skips health if header-only
python -m fema_ops pipeline --with-ci        # + schema gates
python -m fema_ops pipeline --with-db        # + Postgres ingest (FEMA_DATABASE_URL)
```

After first demo basket close (EA can stay on if unlocked, or brief unload):

```powershell
python -m fema_ops pipeline
# expect health_ran=True and STATUS on_demo_path=true
```

Artifact: `AI/data/live/pipeline_latest.json`

Manual steps (same chain): [`daily_health.md`](daily_health.md)
