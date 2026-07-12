# FEMA AI live export (INF-EXPORT)

Stable repo-local pointers for humans and agents. **Do not** hardcode `Tester\Agent-...\` paths in scripts.

## After a tester or demo run

```powershell
# From repo root (Experts/FEMA)
.\AI\sync_from_agent.ps1
# or
python AI/sync_from_agent.py
```

That copies the newest `*_baskets.csv` / `*_events.csv` / `*_run.meta.txt` into this folder and refreshes:

| File | Role |
| ---- | ---- |
| `latest_baskets.csv` | Canonical baskets for health / ingest |
| `latest_events.csv` | Canonical events |
| `latest_run.meta.txt` | Fingerprint / run_id (if present) |
| `latest_source.txt` | Where the files were copied from |
| `health_latest.json` / `.md` | Certificate `health_v0` report (`python -m fema_ops health`) |
| `health_state.json` | Persistence streaks (deteriorate / recover) |

## Health (after sync)

```powershell
cd AI
python -m fema_ops health
```

Shadow only — glance ladder; do not wire pause yet.

## Manual copy (≤10 lines)

1. Open `%APPDATA%\MetaQuotes\Tester\<terminal_id>\Agent-*\MQL5\Files\FEMA_AI\`
2. Pick the newest `EURUSD_*_baskets.csv` (and matching `_events.csv`)
3. Copy into `AI/data/live/`
4. Rename/copy to `latest_baskets.csv` and `latest_events.csv`
5. Run health/ingest against `AI/data/live/latest_baskets.csv`

CSV data here is gitignored; only this README stays in git.
