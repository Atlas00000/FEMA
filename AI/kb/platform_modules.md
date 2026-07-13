# Edge Operations Platform — module map (IS-PLAT-01)

Labels on **shipped** pieces. Not a rewrite / not a new monolith.

| Module | What it is today | Primary artifacts / CLI |
| ------ | ---------------- | ----------------------- |
| **Observatory** | Daily operator note | `fema_ops observatory` · `observatory_daily.md` |
| **Health Engine** | Certificate `health_v0` + persistence | `fema_ops health` · `health_latest.json` |
| **Drift Detection** | Birth / component / compat alerts | `fema_ops drift` · `drift_latest.json` |
| **Candidate Factory** | Recommend ≤3 + one-axis clone | `recommend` · `factory` · `clone` |
| **Knowledge Base** | Runs, lineage, genome, experiments | `AI/kb/*` · `experiments` |
| **Validation Engine** | Gates G1+ · scorecard | `gate_rules.json` · `gate-check` · `gate-polish` |
| **Promotion Pipeline** | Human-only EL2/EL3 · AER-P6 pack | `raci.md` · checklist · `decision.ps1` · `cert-confirm` |
| **Archive System** | Immutable run blobs + rehydrate | `AI/data/artifacts/runs/{run_id}/` · `db-rehydrate` |
| **Sync / Ingest** | Windows → drop zone → live/DB | `ops/sync/sync.ps1` · `ingest` · `db-ingest` |
| **Read API** | Status / health / runs (no write) | `ops/api` · bearer auth |
| **Tester Queue** | Discovery ≠ demo · AER L0–L3 | `ops/tester_queue/` · [`automated_edge_rediscovery_pipeline.md`](../../automated_edge_rediscovery_pipeline.md) |

**Charter:** MT5 executes · Python thinks · Human promotes.  
**Parked:** auto-promote, live retune, MT5-in-Docker, full UI (Wave 6).
