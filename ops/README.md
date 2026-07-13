# FEMA Ops Plane (Waves 1 + 5)

**Charter:** MT5 executes; this plane stores, scores, serves read-only status. No promote endpoints.  
**Roadmap:** [`../infrascaleup.md`](../infrascaleup.md) §16.

## Layout

```text
ops/
  docker-compose.yml      # postgres + fema_ops + fema_api
  postgres/init/001_schema.sql
  api/                    # FastAPI read-only
  schemas/openapi.json    # CI snapshot (fema_ops ci-gates)
  sync/sync.ps1           # Windows → ops/incoming/{demo|tester}
  scheduler/              # AER-P3 Task Scheduler glue
  incoming/demo|tester/   # drop zone
  tester_queue/           # Discovery jobs ≠ demo (IS-P4-01)
```

## Quick start (Docker)

From **repo root** (`Experts/FEMA`):

```powershell
docker-compose -f ops/docker-compose.yml up -d --build
docker-compose -f ops/docker-compose.yml run --rm fema_ops db-migrate
docker-compose -f ops/docker-compose.yml run --rm fema_ops db-ingest --source demo --from-live
```

API (bearer token default `fema-dev-token`):

```powershell
curl -s -H "Authorization: Bearer fema-dev-token" http://localhost:8080/v1/status
```

## Artifacts + rehydrate (IS-P3-01)

Immutable store: `AI/data/artifacts/runs/{run_id}/` (Docker: `/var/fema/artifacts`). MinIO optional later — same key layout.

```powershell
cd AI
python -m fema_ops artifacts-archive --source demo
python -m fema_ops artifacts-list
# After DB wipe:
python -m fema_ops db-rehydrate --run-id <run_id>
```

## CI schema gates (IS-P3-02)

```powershell
cd AI
python -m fema_ops ci-gates
```

GitHub: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Drift (IS-DRIFT-01)

```powershell
python -m fema_ops drift
python -m fema_ops observatory
```

## Windows sync / tester queue / AER

Two-terminal Re-Discovery (`AER-P0`…`P6`) is live — see [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md).

```powershell
powershell -File ops\sync\sync.ps1 -Source demo
powershell -File ops\sync\sync.ps1 -Source tester

powershell -File ops\tester_queue\enqueue.ps1 -Preset Candidate_X1
powershell -File ops\tester_queue\status.ps1
powershell -File ops\tester_queue\launch.ps1 -DryRun
powershell -File ops\tester_queue\el7_enqueue.ps1 -Force -Max 3
powershell -File ops\tester_queue\drain.ps1 -Max 3
powershell -File ops\tester_queue\scorecard.ps1
powershell -File ops\tester_queue\decision.ps1 -Preset Candidate_X1 -PF 1.477 -DD 19.17 -Decision Reject -Signer "operator"
```

Scheduler (L1): [`scheduler/README.md`](scheduler/README.md) · Queue details: [`tester_queue/README.md`](tester_queue/README.md)
## Auth

Set `FEMA_API_TOKEN` in compose / env. API is **read-only** — no candidate create, promote, or retire routes.

## Env

| Variable | Purpose |
| --- | --- |
| `FEMA_DATABASE_URL` | `postgresql://fema:fema@host:5432/fema` |
| `FEMA_API_TOKEN` | Bearer token for `/v1/*` |
| `FEMA_REPO_ROOT` | Repo root (default parent of `AI/`) |

Module map: [`../AI/kb/platform_modules.md`](../AI/kb/platform_modules.md)
