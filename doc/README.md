# `doc/` — operator & design notes

High-level markdown that is **not** the lifecycle spine lives here so the repo root stays neat.

| Doc | Role |
| --- | ---- |
| [`backtesting_guide.md`](backtesting_guide.md) | Systematic backtesting design · anti-overfitting · FEMA gate mapping |
| [`baseline_profile.md`](baseline_profile.md) | P1-BASELINE nature · EURUSD trading philosophy · win/loss DNA |
| [`ERG_P0_baseline_pack.md`](ERG_P0_baseline_pack.md) | ERG-P0 complete · metrics archive · loser atlas · frozen criteria |
| [`ERG_P1_containment_pack.md`](ERG_P1_containment_pack.md) | ERG-P1 BSL presets · load order · scorecard |
| [`ERG_P3_regime_pack.md`](ERG_P3_regime_pack.md) | ERG-P3 ADX/regime presets · score vs BSL25 |
| [`ERG_P4_exit_pack.md`](ERG_P4_exit_pack.md) | ERG-P4 exit probes on ADX28 · Trail70 / TP / MaxBars |
| [`ERG_P5_entry_pack.md`](ERG_P5_entry_pack.md) | ERG-P5 entry filters on ADX28 · Candle / RSI |
| [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md) | ERG-P6 canonical G1 · ADX28 vs PRODUCTION |
| [`EA_failure_assessment.md`](EA_failure_assessment.md) | Weaknesses · failure profile · loss assessment (post ERG) |
| [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) | Isolate P1 edge · phased ERG tasks · context presets · quality/exits |
| [`edge_rediscovery_system.md`](edge_rediscovery_system.md) | Discover-plane snapshot + changelog |
| [`adaptive_selection_phases.md`](adaptive_selection_phases.md) | ASI tracks · `ASI-P8` Complete · **AI preset** `aistack` |
| [`ASI_P4_tep_guard_pack.md`](ASI_P4_tep_guard_pack.md) | TEP gate deploy · window review |
| [`ASI_P5_midbasket_pack.md`](ASI_P5_midbasket_pack.md) | Mid-basket Mode A + Mode B (own presets) |
| [`ASI_P6_recovery_pack.md`](ASI_P6_recovery_pack.md) | Basket recovery P(recover) · shadow Alternate |
| [`ASI_P8_regime_pack.md`](ASI_P8_regime_pack.md) | Regime taxonomy · **AI preset** deploy · allow/caution/skip |
| [`dual_lane_rediscovery_pipeline.md`](dual_lane_rediscovery_pipeline.md) | Hybrid dual-lane MVP · `DLR-P0`…`P3` **complete** |
| [`localizaed_tuning.md`](localizaed_tuning.md) | Why localized retune vs full Discovery |

**Still at repo root (spine / entry):** `README.md` · `edgelifecycle.md` · `system_audit.md` · `automated_edge_rediscovery_pipeline.md` · `infrascaleup.md` · … until intentionally migrated.

**Rule going forward:** add new guides, snapshots, and changelogs under `doc/`; link them from `README.md` / `AI/STATUS.md` as needed.
