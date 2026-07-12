# Retrain / rediscovery policy (RG-POL-01)

**Status:** Policy only — **no live wire**. Offline / shadow scoring may run anytime.

| Cadence | What | Trigger | Action | Forbidden |
| ------- | ---- | ------- | ------ | --------- |
| **Daily** | Health + Observatory | Ingest + `fema_ops health` / `observatory` | Log ladder · sync heartbeat | Retune EA |
| **Feature refresh** | Derived features / fingerprint (Wave 3+) | Schema change or ≥14d demo with trusted ingest | Recompute offline; bump `versions.json` feature_store when it exists | Change live entries |
| **AI model (shadow)** | Offline predictors | Explicit research ticket | Train/eval on archived runs only | Drive lots / TP / SL / EMA |
| **Full Edge Discovery (EL7)** | New candidates → EL2 → optional new lock | See triggers below | Snapshot lock as parent/retired → EL1 ≤3 candidates | Auto-promote |

## EL7 Discovery triggers (human opens; Watch does not author)

Open Re-Discovery when **any** of:

1. Primary-window ladder stays `re_discovery` or `retire` **and** persistence warning is active (3 deteriorate / 2 recover — certificate).
2. Operator judgment after ≥2 weeks trusted **demo** health (not Tester collect) with repeated `watch` / `investigate` and unexplained drift tags.
3. Charter change (new symbol/TF) — treat as new edge, not a live retune.

Do **not** open EL7 for a single bad day (`ignore_single_bad_day` in certificate).

## After trigger

1. Record reason in Observatory / STATUS open ESR.
2. Set lineage: `retired_run_id` = current lock `run_id` (see [`lineage.json`](lineage.json)).
3. Follow [`research_loop_sop.md`](research_loop_sop.md) → EL1 → EL2 → human promote (EL3) or stay on last acceptable lock (EL7-005).

## Explicit non-goals

- Weekly panic retunes.
- Model retrain as a driver of live risk (parked — Wave 6 / INF-DEF).
- Automatic Generate → Validate → Promote.
