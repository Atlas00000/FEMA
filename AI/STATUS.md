# FEMA STATUS

_Generated: `2026-07-20` (ASI AI preset) - refresh health with `cd AI && python -m fema_ops status`_

## At a glance

| Field | Value |
| ----- | ----- |
| **Phase** | Wave 6 park freeze · **AI preset** `aistack` (alias `ASI_P8_TEP_MID_BSL_01`) · EA **v1.29** · PRODUCTION lock unchanged · P7 pending |
| **Open ESR** | Wave 6 park-freeze; after demo basket close run pipeline for `on_demo_path` |
| **EA build** | v1.29 |
| **Preset** | `FEMA_EURUSD_M5_PRODUCTION` (lock) · **AI preset** `aistack` |
| **Lineage lock** | `20260101_PRODUCTION_13c52cd9` · parent=`P2A-002_BSL_25` |
| **Re-Discovery** | Terminal B · Lane A default · Lane B after ≥2 A fails · human promote only |
| **Pause wire** | false (default - do not wire yet) |

## Start here (agents)

1. [`../edgelifecycle.md`](../edgelifecycle.md) - spine
2. [`../system_audit.md`](../system_audit.md) - main/subsystem map
3. [`../doc/edge_rediscovery_system.md`](../doc/edge_rediscovery_system.md) - Discover snapshot + changelog
4. [`../doc/dual_lane_rediscovery_pipeline.md`](../doc/dual_lane_rediscovery_pipeline.md) - Hybrid dual-lane (`DLR-P3` complete · MVP)
5. [`../doc/adaptive_selection_phases.md`](../doc/adaptive_selection_phases.md) - Adaptive selection (`ASI-P8` Complete · **AI preset** `aistack`)
5b. [`../AI_Infra.md`](../AI_Infra.md) - Flat inventory of every AI system (unique IDs)
6. [`../automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) - AER phases (`P0`…`P6`)
7. [`../infrascaleup.md`](../infrascaleup.md) - Ops Plane / §16 roadmap
8. This file - glance
9. [`kb/versions.json`](kb/versions.json) · [`kb/lineage.json`](kb/lineage.json) · [`kb/raci.md`](kb/raci.md)
10. [`certificate_PRODUCTION_EURUSD.json`](certificate_PRODUCTION_EURUSD.json) - bands
11. [`data/live/observatory_daily.md`](data/live/observatory_daily.md) - daily note
12. [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) - lock profile

## AI preset results (`aistack` · 2026-07-20)

| Window | Preset | PF | Net | Eq DD | Trades | Role |
| ------ | ------ | --: | ---: | ----: | -----: | ---- |
| **2026 G1** | **`aistack`** | **1.27** | +$175 | **14.2%** | 437 | **AI preset** |
| **2026 G1** | `ASI_P8_REGIME_01` | 1.40 | +$246 | 17.5% | 445 | research only |
| **2026 G1** | PRODUCTION lock | 1.36 | +$221 | ~18% | ~424 | birth lock |
| **2018–25** | **`aistack`** | **1.55** | +$134 | **~14%** | 361 | **survives** |
| **2018–25** | `ASI_P8_REGIME_01` | 1.01 | +$91 | **~66%** | 7021 | fails survival |

Promote bar = guardrails + profitable survival — not G1 PF alone. PRODUCTION unchanged.  
Pack: [`../doc/ASI_P8_regime_pack.md`](../doc/ASI_P8_regime_pack.md) · decision: [`kb/decisions/20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md`](kb/decisions/20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md)

## Recent Discovery (AER 2026-07-13)

| preset | PF | DD | G1 | decision |
| ------ | --: | --: | --- | -------- |
| `Candidate_X1` (NO23) | 1.477 | 19.17% | fail | Reject `dd_breach` |
| `Candidate_X2` (FriClose) | 1.432 | 18.13% | fail | Alternate `dd_breach` |

Checklists: [`kb/decisions/`](kb/decisions/) · log: [`kb/el2_promote_decision.md`](kb/el2_promote_decision.md)

## Quick commands

```powershell
cd AI
python -m fema_ops ingest --source demo
python -m fema_ops health
python -m fema_ops fingerprint
python -m fema_ops observatory
python -m fema_ops status
python -m fema_ops ingest --source tester   # Discovery/tester only

# Terminal B Re-Discovery (repo root)
powershell -File ops\tester_queue\drain.ps1 -Max 3
powershell -File ops\tester_queue\scorecard.ps1
```

## Doc map (spine only)

| Doc | Role |
| --- | ---- |
| [`edgelifecycle.md`](../edgelifecycle.md) | Spine / TOC |
| [`system_audit.md`](../system_audit.md) | Main systems · subsystems · status |
| [`doc/edge_rediscovery_system.md`](../doc/edge_rediscovery_system.md) | Discover snapshot + changelog |
| [`doc/dual_lane_rediscovery_pipeline.md`](../doc/dual_lane_rediscovery_pipeline.md) | Hybrid dual-lane · `DLR-P3` complete (MVP) |
| [`doc/adaptive_selection_phases.md`](../doc/adaptive_selection_phases.md) | Adaptive selection · `ASI-P8` Complete · **AI preset** |
| [`doc/ASI_P8_regime_pack.md`](../doc/ASI_P8_regime_pack.md) | P8 regime + AI preset deploy |
| [`doc/ASI_P4_tep_guard_pack.md`](../doc/ASI_P4_tep_guard_pack.md) | P4 deploy + window review |
| [`doc/ASI_P5_midbasket_pack.md`](../doc/ASI_P5_midbasket_pack.md) | P5 Mode A + Mode B (own presets) |
| [`doc/failureimprove.md`](../doc/failureimprove.md) | Structural vs adaptive failure thesis |
| [`AI/kb/challenger_roster.md`](kb/challenger_roster.md) | Lane B bases + profile cards |
| [`AI/kb/dlr_policy.json`](kb/dlr_policy.json) | EL7 A-default · escalate B after N A-fails |
| [`automated_edge_rediscovery_pipeline.md`](../automated_edge_rediscovery_pipeline.md) | A/B Re-Discovery · AER phases |
| [`infrascaleup.md`](../infrascaleup.md) | Ops Plane + §16 roadmap |
| [`edgescaleuproadmap.md`](../edgescaleuproadmap.md) | Weekly ESR |
| [`edgecontainment.md`](../edgecontainment.md) | Vision / bands |
| [`Edge Discovery.md`](../Edge%20Discovery.md) | Lock table |
| [`kb/genome_PRODUCTION.md`](kb/genome_PRODUCTION.md) | Edge Genome v0 |
| [`kb/pause_policy.md`](kb/pause_policy.md) | EL6 pause |
| [`kb/raci.md`](kb/raci.md) | Governance RACI |
| [`kb/research_loop_sop.md`](kb/research_loop_sop.md) | Research loop |
| [`kb/retrain_rediscovery_policy.md`](kb/retrain_rediscovery_policy.md) | EL7 cadence |
| [`kb/el7_rediscovery_runbook.md`](kb/el7_rediscovery_runbook.md) | EL7 steps + AER hooks |
| [`templates/daily_health.md`](templates/daily_health.md) | Daily runbook |
| [`aiedgecontain.md`](../aiedgecontain.md) | Contain archive |
| [`ai_enhance.md`](../ai_enhance.md) | Legacy archive |

## Notes

- Health artifact: `AI/data/live/health_latest.json`
- Fingerprint: `AI/data/live/fingerprint_latest.json`
- Sync heartbeat: `AI/data/live/sync_heartbeat.json`
- Discovery scorecard: `AI/data/live/discovery_scorecard_latest.md`
- Observatory: `AI/data/live/observatory_daily.md`
- Live pause_new.flag present: `False`
- Fat CSVs under `AI/data/` are gitignored; schemas + templates are committed.
- **EL4:** prefer `--source demo` (Common `FEMA_AI`). Tester collect is not demo health.
- **AER:** never auto-promote; Terminal A stays on PRODUCTION until signed G1 pass + redeploy.
