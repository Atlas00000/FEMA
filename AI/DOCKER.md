# FEMA Docker (INF-DOCKER)

**Scope:** Python `fema_ops` only. **No** MetaTrader, Strategy Tester, or Wine.

## Build (repo root)

```powershell
docker build -f AI/Dockerfile -t fema-ops .
```

## Run health (mount data)

```powershell
# PowerShell — repo root Experts/FEMA
docker run --rm `
  -v "${PWD}/AI/data:/work/AI/data" `
  -v "${PWD}/AI/kb:/work/AI/kb" `
  -v "${PWD}/Presets:/work/Presets" `
  fema-ops health

docker run --rm `
  -v "${PWD}/AI/data:/work/AI/data" `
  -v "${PWD}/AI/kb:/work/AI/kb" `
  fema-ops status
```

## Compose

```powershell
docker compose -f AI/docker-compose.yml build
docker compose -f AI/docker-compose.yml run --rm fema_ops health
docker compose -f AI/docker-compose.yml run --rm fema_ops pause-check
```

## Notes

- `FEMA_REPO_ROOT=/work` so `Presets/` resolves next to `AI/`
- Fat CSVs stay on the host under `AI/data/` (gitignored)
- Deferred: MT5 in Docker (`INF-DEF-001`)
