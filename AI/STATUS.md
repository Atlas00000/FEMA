# FEMA STATUS

_Generated: `2026-07-12T14:38:53Z` - refresh with `cd AI && python -m fema_ops status`_

## At a glance

| Field | Value |
| ----- | ----- |
| **Phase** | Wave 6 park freeze (no PARK features) |
| **Open ESR** | `Wave 6 park-freeze offline; after demo basket close run pipeline for on_demo_path` |
| **EA build** | v1.26 |
| **Preset** | `FEMA_EURUSD_M5_PRODUCTION` |
| **Health** | 91.72 / ladder `normal` / would_pause=`False` / formula=`health_v0` |
| **Health on demo path** | False |
| **Versions** | [`kb/versions.json`](kb/versions.json) · health=`health_v0` · cert_v=`1` · gates=`fema_gate_rules_v1` |
| **Lineage lock** | `20260101_PRODUCTION_13c52cd9` · parent=`P2A-002_BSL_25` |
| **Compat (shadow)** | `compatible` · score=`100.0` |
| **Sync source** | `demo` · age_h=`1.13` · stale=`False` · locked=`False` · rows=`0` · header_only=`True` |
| **Lock run_id** | `20260101_PRODUCTION_13c52cd9` |
| **Pause wire** | false (default - do not wire yet) |
| **Live baskets** | yes |

## Start here (agents)

1. [`../edgelifecycle.md`](../edgelifecycle.md) - spine
2. [`../infrascaleup.md`](../infrascaleup.md) - Ops Plane / §16 roadmap
3. This file - glance
4. [`kb/versions.json`](kb/versions.json) · [`kb/lineage.json`](kb/lineage.json) · [`kb/raci.md`](kb/raci.md)
5. [`certificate_PRODUCTION_EURUSD.json`](certificate_PRODUCTION_EURUSD.json) - bands
6. [`data/live/observatory_daily.md`](data/live/observatory_daily.md) - daily note
7. [`data/live/latest_baskets.csv`](data/live/latest_baskets.csv) - telemetry (gitignored)
8. [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) - lock profile

## Recent runs

| run_id | role | PF |
| ------ | ---- | -- |
| `20260101_P2F-003_RSI_EXH_c39a9dd0` | reject | 1.38 |
| `20260101_P2F-004_CONFIRM_b442d1cb` | reject | 0.94 |
| `20260101_PRODUCTION_26e9ba7e` | reject | 0.8 |

## Quick commands

```powershell
cd AI
python -m fema_ops ingest --source demo
python -m fema_ops health
python -m fema_ops fingerprint
python -m fema_ops observatory
python -m fema_ops status
python -m fema_ops ingest --source tester   # Discovery/tester only
```

## Doc map (spine only)

| Doc | Role |
| --- | ---- |
| [`edgelifecycle.md`](../edgelifecycle.md) | Spine / TOC |
| [`infrascaleup.md`](../infrascaleup.md) | Ops Plane + §16 roadmap |
| [`edgescaleuproadmap.md`](../edgescaleuproadmap.md) | Weekly ESR |
| [`edgecontainment.md`](../edgecontainment.md) | Vision / bands |
| [`Edge Discovery.md`](../Edge%20Discovery.md) | Lock table |
| [`kb/genome_PRODUCTION.md`](kb/genome_PRODUCTION.md) | Edge Genome v0 |
| [`kb/pause_policy.md`](kb/pause_policy.md) | EL6 pause |
| [`kb/raci.md`](kb/raci.md) | Governance RACI |
| [`kb/research_loop_sop.md`](kb/research_loop_sop.md) | Research loop |
| [`kb/retrain_rediscovery_policy.md`](kb/retrain_rediscovery_policy.md) | EL7 cadence |
| [`templates/daily_health.md`](templates/daily_health.md) | Daily runbook |
| [`aiedgecontain.md`](../aiedgecontain.md) | Contain archive |
| [`ai_enhance.md`](../ai_enhance.md) | Legacy archive |

## Notes

- Health artifact: `AI/data/live/health_latest.json`
- Fingerprint: `AI/data/live/fingerprint_latest.json`
- Sync heartbeat: `AI/data/live/sync_heartbeat.json`
- Observatory: `AI/data/live/observatory_daily.md`
- Live source excerpt: `synced_utc=2026-07-12T14:33:45.313366+00:00
source=demo
source_requested=demo
baskets_src=C:\Users\emili\AppData\Roaming\MetaQuotes\Terminal\Common\Files\FEMA_AI\EURUSD_20260707_ba`
- Live pause_new.flag present: `False`
- Fat CSVs under `AI/data/` are gitignored; schemas + templates are committed.
- **EL4:** prefer `--source demo` (Common `FEMA_AI`). Tester collect is not demo health.
