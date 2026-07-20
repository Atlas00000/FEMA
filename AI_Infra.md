# AI_Infra — FEMA AI systems inventory

**Purpose:** Flat catalogue of every distinct AI / ML / adaptive / scoring / shadow / gate-for-AI system that is **implemented**, **partial**, or **planned**.  
**Rule:** One system = one ID. Stacked presets are *compositions*, not separate systems. Structural non-ML gates (BSL, hard ADX, candle, RSI, trail) are **out of scope** here — see `system_audit.md` / ERG packs.  
**Updated:** 2026-07-19  
**Charter:** MT5 executes · Python scores · Human promotes

---

## `AI0-EVENT-LOG`

| Field | Value |
| ----- | ----- |
| **Name** | AI0 feature / event / basket CSV pipeline |
| **Status** | **implemented** · live |
| **Description** | EA writes basket-open features, events, and close labels to `Common\Files\FEMA_AI` for offline training and replay. Shared telemetry spine for AI*/EC*/ASI. |
| **Live MT5** | Yes — `InpUseAiEventLog` (default on in PRODUCTION) |
| **Key paths** | `Include/AI/AiEventLog.mqh` · `Include/AI/AiTypes.mqh` · `AI/build_dataset.py` · `AI/replay.py` · `AI/sync_from_agent.py` |
| **Track / phase** | AI0-INFRA · EX-13 · EL4 |
| **Notes** | Schemas `fema_baskets_v2` / `fema_events_v2` |

---

## `AI1-REGIME-ATLAS`

| Field | Value |
| ----- | ----- |
| **Name** | AI1 coarse regime atlas (descriptive) |
| **Status** | **implemented** · shadow / empty toxic list |
| **Description** | Nine coarse regimes + PF/WR scorecard; soft-skip list empty when no holdout-confirmed toxic ≤10%. |
| **Live MT5** | No |
| **Key paths** | `AI/regime_atlas.py` · `AI/data/regime_scorecard.*` · `ai_enhance.md` §AI1 |
| **Track / phase** | AI1-REGIME |
| **Notes** | Predecessor research; **not** the same as `ASI-REGIME` or `EC1-REGIME` |

---

## `AI2-FAIL-PRED`

| Field | Value |
| ----- | ----- |
| **Name** | AI2 failure / steamroller predictor |
| **Status** | **parked / rejected** · shadow only · do not wire |
| **Description** | GBDT/logistic P(fail) soft-skip under old “beat 2026” scoreboard; validate AUC ~coin-flip / fragile. |
| **Live MT5** | No |
| **Key paths** | `AI/failure_predictor.py` · `AI/data/ai2_*` · `ai_enhance.md` §AI2 |
| **Track / phase** | AI2-FAIL |
| **Notes** | Superseded conceptually by EC2 then `ASI-TEP-OPEN` |

---

## `AI3-EDGE-HEALTH`

| Field | Value |
| ----- | ----- |
| **Name** | AI3 offline edge health monitor |
| **Status** | **implemented** · research / shadow |
| **Description** | Rolling N-basket health 0–100 + stress-confirm pause shadow on research CSVs. |
| **Live MT5** | No |
| **Key paths** | `AI/edge_health.py` · `AI/data/ai3_*` · `ai_enhance.md` §AI3 |
| **Track / phase** | AI3-HEALTH |
| **Notes** | Distinct from `OP-HEALTH-V0` and planned `ASI-EDGE-HEALTH-PRED` |

---

## `AI4-EDGE-PROB`

| Field | Value |
| ----- | ----- |
| **Name** | AI4 edge probability / P(TP) confidence |
| **Status** | **parked / rejected** · logging-only |
| **Description** | GBDT/logistic P(TP); elite-only skip forbidden; no assist lift over AI2. |
| **Live MT5** | No |
| **Key paths** | `AI/edge_prob.py` · `AI/data/ai4_*` · `ai_enhance.md` §AI4 |
| **Track / phase** | AI4-PROB |
| **Notes** | Validate AUC worse than chance |

---

## `AI5-FUSION`

| Field | Value |
| ----- | ----- |
| **Name** | AI5 decision fusion (soft ensemble) |
| **Status** | **planned** |
| **Description** | Combine regime + fail + health (+ optional P(TP)) with approve-by-default soft fusion. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI5 |
| **Track / phase** | AI5-FUSION |
| **Notes** | Parallel concept to `EC5-FUSION` / `ASI-DYN-CONF` |

---

## `AI6-WIRE`

| Field | Value |
| ----- | ----- |
| **Name** | AI6 first opt-in EA soft gate (legacy plan) |
| **Status** | **planned / superseded** |
| **Description** | Proposed `InpUseAiGate` soft-skip after demo shadow. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI6 |
| **Track / phase** | AI6-WIRE |
| **Notes** | Functionally superseded by ASI `InpUseAiTepGate` / mid / regime inputs |

---

## `AI7-RETRAIN`

| Field | Value |
| ----- | ----- |
| **Name** | AI7 rolling retrain loop |
| **Status** | **planned** |
| **Description** | Scheduled retrain + model registry; promote only if holdout guardrail passes. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI7 · `AI/kb/retrain_rediscovery_policy.md` |
| **Track / phase** | AI7-RETRAIN |
| **Notes** | Parallel to `EC7-RETRAIN` |

---

## `AI8-BASKET-REC`

| Field | Value |
| ----- | ----- |
| **Name** | AI8 mid-basket recovery assist (legacy plan) |
| **Status** | **planned / superseded** |
| **Description** | Mid-basket P(recovery) early-close with stricter budget than entry skips. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI8 |
| **Track / phase** | AI8-BASKET |
| **Notes** | Superseded by `ASI-REC` + `ASI-MID-WARN-B`; do not conflate |

---

## `AI9-LIGHT-ADAPT`

| Field | Value |
| ----- | ----- |
| **Name** | AI9 light adaptive parameters (bounded) |
| **Status** | **planned / deferred** |
| **Description** | Tiny regime-conditioned tweaks (soft thresholds, cooldown) — not free EMA/TP/SL retune. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI9 |
| **Track / phase** | AI9-ADAPT |
| **Notes** | Forbidden wild param jumps without new research program |

---

## `AI-X-DEFERRED`

| Field | Value |
| ----- | ----- |
| **Name** | AI-X deferred vision layers |
| **Status** | **parked** · vision only |
| **Description** | Fine 30–50 regimes · elite ranking · market-memory k-NN · full RL · aggressive dynamic ADX/TP/SL · multi-model voting. |
| **Live MT5** | No |
| **Key paths** | `ai_enhance.md` §AI-X · `aiscaleupconcept.md` |
| **Track / phase** | deferred |
| **Notes** | Park until core contain / ASI stack stable |

---

## `EC0-DATA`

| Field | Value |
| ----- | ----- |
| **Name** | EC0 contain collect / split / labeled corpus |
| **Status** | **implemented** |
| **Description** | Frozen AI0 collect + repair IDs + train/holdout splits + zero-skip replay for edge-contain windows. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC0 · `AI/split_2020_2025.py` · `AI/repair_basket_ids.py` · `AI/data/EURUSD_baskets_2020_2025*.csv` |
| **Track / phase** | EC0-DATA |
| **Notes** | Guardrail windows (not beat-2026) |

---

## `EC1-REGIME`

| Field | Value |
| ----- | ----- |
| **Name** | EC1 regime atlas (contain splits) |
| **Status** | **implemented** · empty soft-skip |
| **Description** | Coarse regimes on 2020–23 / 24–25; no train-toxic ≤10% → approve-by-default empty mask. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC1 · `AI/regime_atlas.py` · `AI/data/regime_scorecard.*` |
| **Track / phase** | EC1-REGIME |
| **Notes** | Distinct from `AI1-REGIME-ATLAS` and `ASI-REGIME` |

---

## `EC1-NESTED`

| Field | Value |
| ----- | ----- |
| **Name** | EC1 nested regime toxic-gate calibrator |
| **Status** | **implemented** · research tooling |
| **Description** | Fit/cal/hold nested toxic packing with ≤10% share budget. |
| **Live MT5** | No |
| **Key paths** | `AI/regime_nested.py` |
| **Track / phase** | EC1 extension |
| **Notes** | Offline only |

---

## `EC2-FAIL`

| Field | Value |
| ----- | ----- |
| **Name** | EC2 failure / steamroller guardrail |
| **Status** | **parked / rejected** · shadow empty · do not wire |
| **Description** | GBDT/logistic P(fail) on contain windows; no cal policy hit prec≥50%+net≤0 → empty skip. |
| **Live MT5** | No |
| **Key paths** | `AI/failure_predictor.py` · `AI/data/ec2/*` · `aiedgecontain.md` §EC2 · `system_audit.md` PARK-05 |
| **Track / phase** | EC2-FAIL |
| **Notes** | Spine parked; rolling health preferred; logistic alt rejected |

---

## `EC3-HEALTH`

| Field | Value |
| ----- | ----- |
| **Name** | EC3 edge health / death pause (contain plan) |
| **Status** | **planned / largely superseded** |
| **Description** | Rolling health → pause new baskets when edge sick (contain charter). |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC3 |
| **Track / phase** | EC3-HEALTH |
| **Notes** | Ops `OP-HEALTH-V0` + EL6 is the shipped successor path |

---

## `EC4-PROB`

| Field | Value |
| ----- | ----- |
| **Name** | EC4 P(TP) confidence (permissive) |
| **Status** | **planned** |
| **Description** | Logging / tie-break only; never solo elite filter. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC4 |
| **Track / phase** | EC4-PROB |
| **Notes** | Parallel to `AI4-EDGE-PROB` |

---

## `EC5-FUSION`

| Field | Value |
| ----- | ----- |
| **Name** | EC5 soft fusion (contain) |
| **Status** | **planned** |
| **Description** | Health-critical pause + regime∩fail soft-skip + approve-default. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC5 |
| **Track / phase** | EC5-FUSION |
| **Notes** | Parallel to `AI5-FUSION` / `ASI-DYN-CONF` |

---

## `EC6-WIRE`

| Field | Value |
| ----- | ----- |
| **Name** | EC6 demo shadow → opt-in contain wire |
| **Status** | **planned** |
| **Description** | Proposed `InpUseAiContain` soft-skip/pause; engine DNA untouched. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC6 |
| **Track / phase** | EC6-WIRE |
| **Notes** | Not shipped; ASI gates are separate opt-ins |

---

## `EC7-RETRAIN`

| Field | Value |
| ----- | ----- |
| **Name** | EC7 contain retrain loop |
| **Status** | **planned** |
| **Description** | Calendar retrain + model registry; keep last-known-good on fail. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §EC7 |
| **Track / phase** | EC7-RETRAIN |
| **Notes** | Parallel to `AI7-RETRAIN` |

---

## `EC-X-DEFERRED`

| Field | Value |
| ----- | ----- |
| **Name** | EC deferred vision (mid early-close / adaptive EMA-TP-SL / fine regimes / RL) |
| **Status** | **parked** |
| **Description** | Explicitly deferred contain items that recreate RTE/trail failures or overfilter. |
| **Live MT5** | No |
| **Key paths** | `aiedgecontain.md` §Deferred |
| **Track / phase** | EC-X |
| **Notes** | Mid early-close later done via `ASI-MID-WARN-B` separately |

---

## `ASI-CHARTER`

| Field | Value |
| ----- | ----- |
| **Name** | Adaptive Selection Intelligence charter |
| **Status** | **implemented** · design law |
| **Description** | Selection over signal rewrite; permissive skips; no auto-promote; guardrails not gates. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` · `doc/failureimprove.md` · `AI/kb/search_map.md` |
| **Track / phase** | ASI-P0 · Tracks A–J |
| **Notes** | Adopted 2026-07-17 |

---

## `ASI-LABELS-DATASET`

| Field | Value |
| ----- | ----- |
| **Name** | ASI label schema + dataset builder |
| **Status** | **implemented** |
| **Description** | Steamroller / mid-steamroller / recover labels; leakage-safe open/warn features; train/calibrate/promote splits. |
| **Live MT5** | No |
| **Key paths** | `AI/kb/asi/label_schema.md` · `AI/fema_ops/asi/labels.py` · `dataset.py` · `features.py` · CLI `asi-build` / `asi-mid-build` / `asi-rec-build` / `asi-regime-build` |
| **Track / phase** | ASI-P1 (+ reused by P5/P6/P8) |
| **Notes** | Foundation for all ASI models |

---

## `ASI-IMPULSE-V0`

| Field | Value |
| ----- | ----- |
| **Name** | Impulse-score shadow skip (TEP v0 heuristic) |
| **Status** | **implemented** · superseded as primary gate |
| **Description** | Provisional skip if `impulse_score ≥ train p90` before logistic TEP; retained for baseline/ablation. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/asi/dataset.py` `shadow_skip_v0` · `AI/kb/asi/asi_shadow_v0.json` |
| **Track / phase** | ASI-P1-05 |
| **Notes** | Replaced as live candidate by `ASI-TEP-OPEN` |

---

## `ASI-TEP-OPEN`

| Field | Value |
| ----- | ----- |
| **Name** | Trend Expansion Predictor — open-basket steamroller gate |
| **Status** | **implemented** · **Alternate** |
| **Description** | Logistic P(steamroller \| open) → skip new basket when ≥ threshold (~0.65 long-train). |
| **Live MT5** | Opt-in — `InpUseAiTepGate` · PRODUCTION off |
| **Key paths** | `AI/fema_ops/asi/tep.py` · `gate.py` · `Include/AI/AiTepGate.mqh` · `Presets/ASI_P4_TEP_GUARD_01.set` · `AI/kb/asi/tep_gate_v1.txt` · `doc/ASI_P4_tep_guard_pack.md` · `AI/kb/decisions/20260719_ASI_P4_TEP_GUARD_01_Alternate.md` |
| **Track / phase** | Track **A** · ASI-P1…P4 |
| **Notes** | `roll_pf` capped at 5 in gate + event log after P≈1 bug |

---

## `ASI-TEP-SHADOW`

| Field | Value |
| ----- | ----- |
| **Name** | TEP offline shadow / guardrail review |
| **Status** | **implemented** |
| **Description** | Score registered runs with TEP; scorecard skip/DD columns; kill/observe review packs. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/asi/shadow.py` · CLI `asi-shadow` / `asi-review` · `AI/kb/asi/asi_p3_review_pack.*` · `asi_guardrail_review_pack.*` · `ops/tester_queue/scorecard.ps1` |
| **Track / phase** | ASI-P3 |
| **Notes** | Distinct from live gate `ASI-TEP-OPEN` |

---

## `ASI-MID-WARN-A`

| Field | Value |
| ----- | ----- |
| **Name** | Mid-basket steamroller warn — Mode A (log only) |
| **Status** | **implemented** |
| **Description** | At depth milestones 2…5, P(eventual steamroller) → journal `mid_warn`; no trade change. |
| **Live MT5** | Opt-in — `InpUseAiMidWarn` |
| **Key paths** | `AI/fema_ops/asi/midbasket.py` · `Include/AI/AiMidWarn.mqh` · `Presets/ASI_P5_TEP_MID_01.set` · `AI/kb/asi/mid_gate_v1.txt` · `mid_policy_adr.md` · `doc/ASI_P5_midbasket_pack.md` |
| **Track / phase** | Track **E** · ASI-P5 Mode A |
| **Notes** | Keep separate from Mode B |

---

## `ASI-MID-WARN-B`

| Field | Value |
| ----- | ----- |
| **Name** | Mid-basket early BSL — Mode B |
| **Status** | **implemented** · **Alternate** |
| **Description** | When mid-warn fires, close basket early (`exit_reason=MID_WARN`). |
| **Live MT5** | Opt-in — `InpUseAiMidEarlyBsl` (requires mid gate) |
| **Key paths** | Engine mid-BSL path · `Presets/ASI_P5_TEP_MID_BSL_01.set` · `AI/kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md` · `doc/ASI_P5_midbasket_pack.md` |
| **Track / phase** | Track **E** · ASI-P5 Mode B |
| **Notes** | Survival Alternate; do not merge into Mode A / P4 / PRODUCTION |

---

## `ASI-MID-WARN-C`

| Field | Value |
| ----- | ----- |
| **Name** | Mid-basket stop-deepen (freeze grid adds) |
| **Status** | **planned** |
| **Description** | On mid-warn, freeze further grid adds without forcing BSL. |
| **Live MT5** | No |
| **Key paths** | `AI/kb/asi/mid_policy_adr.md` (Mode C) |
| **Track / phase** | Track **E** · ASI-P5 Mode C |
| **Notes** | Explicitly not implemented |

---

## `ASI-REC`

| Field | Value |
| ----- | ----- |
| **Name** | Basket recovery probability |
| **Status** | **implemented** · **Alternate** · shadow only |
| **Description** | P(recover \| open, warn_depth) → KEEP / CAUTION / recommend early-BSL (advisory). |
| **Live MT5** | No — no `InpUseAiRec*` |
| **Key paths** | `AI/fema_ops/asi/recovery.py` · `AI/kb/asi/rec_*` · `rec_policy_adr.md` · `doc/ASI_P6_recovery_pack.md` · `AI/kb/decisions/20260719_ASI_P6_REC_SHADOW_Alternate.md` |
| **Track / phase** | Track **B** · ASI-P6 |
| **Notes** | Optional later: AND with mid-warn before Mode B |

---

## `ASI-COMPAT`

| Field | Value |
| ----- | ----- |
| **Name** | Market compatibility score (0–100 at signal) |
| **Status** | **planned** |
| **Description** | Permissive elite-only score from trend persist / pullback quality / vol / spread / EMA geometry. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` §P7 · `doc/failureimprove.md` §D |
| **Track / phase** | Track **D** · ASI-P7 |
| **Notes** | Distinct from ops birth-compat `OP-COMPAT-SCORE` |

---

## `ASI-REGIME`

| Field | Value |
| ----- | ----- |
| **Name** | Regime intelligence filter (9-state taxonomy) |
| **Status** | **implemented** · **AI preset** `aistack` · MQL opt-in wired |
| **Description** | Rule taxonomy at open → allow/caution/skip; live filter skips caution∪skip (`false_breakout`, `grind`, `rotation`). Full stack = TEP + mid + Mode B + regime. |
| **Live MT5** | Opt-in — load **`aistack`** · PRODUCTION lock unchanged · EA v1.29+ |
| **Key paths** | `AI/fema_ops/asi/regime.py` · `Include/AI/AiRegimeGate.mqh` · `AI/kb/asi/regime_gate_v1.txt` · `Presets/aistack.set` · `doc/ASI_P8_regime_pack.md` · `AI/kb/decisions/20260720_ASI_P8_TEP_MID_BSL_01_AI_Preset.md` |
| **Track / phase** | Track **G** · ASI-P8 |
| **Notes** | **`aistack`** G1 PF **1.27** / DD **14.2%** / +$175; 2018–25 PF **1.55** / DD **14.1%** / +$134. P8-only research only (long PF 1.01 / DD 66.3%) |

---

## `ASI-EDGE-HEALTH-PRED`

| Field | Value |
| ----- | ----- |
| **Name** | Edge health prediction (leading fade, ~3 weeks) |
| **Status** | **planned** |
| **Description** | Predict PF/DD fade; recommend EL7 / rediscovery (human still enqueues). |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` §P9 · `doc/failureimprove.md` §H |
| **Track / phase** | Track **H** · ASI-P9 |
| **Notes** | Distinct from rolling `OP-HEALTH-V0` / `AI3-EDGE-HEALTH` |

---

## `ASI-SESSION-INTEL`

| Field | Value |
| ----- | ----- |
| **Name** | Session intelligence (scale confidence) |
| **Status** | **planned** |
| **Description** | Probabilistic session confidence — scale exposure, don’t hard-blacklist hours/days. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` ASI-P10-01 · `doc/failureimprove.md` §C |
| **Track / phase** | Track **C** · ASI-P10+ |
| **Notes** | Distinct from hard `InpUseSessionBlock*` gates |

---

## `ASI-GRID-BREATHE`

| Field | Value |
| ----- | ----- |
| **Name** | Dynamic grid compression (ATR mult breathe) |
| **Status** | **planned** |
| **Description** | Recommend ATR multiplier breathe with expansion/compression — one-axis search_map only. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` ASI-P10-02 · `doc/failureimprove.md` §F · `AI/kb/search_map.md` |
| **Track / phase** | Track **F** · ASI-P10+ |
| **Notes** | Never free genetic search |

---

## `ASI-FAIL-MEMORY`

| Field | Value |
| ----- | ----- |
| **Name** | Failure memory (similarity to past losers) |
| **Status** | **planned** |
| **Description** | Skip when current open state resembles historical losing baskets. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` ASI-P10-03 · `doc/failureimprove.md` §I |
| **Track / phase** | Track **I** · ASI-P10+ |
| **Notes** | Related vision: market-memory k-NN in `AI-X-DEFERRED` |

---

## `ASI-DYN-CONF`

| Field | Value |
| ----- | ----- |
| **Name** | Dynamic confidence (compose A/D/G/C) |
| **Status** | **planned** |
| **Description** | Composite confidence from TEP / compatibility / regime / session; trade above threshold. |
| **Live MT5** | No |
| **Key paths** | `doc/adaptive_selection_phases.md` ASI-P10-04 · `doc/failureimprove.md` §J |
| **Track / phase** | Track **J** · ASI-P10+ |
| **Notes** | Spec after P4 + P7 + P8 |

---

## `OP-HEALTH-V0`

| Field | Value |
| ----- | ----- |
| **Name** | Certificate edge health (`health_v0`) |
| **Status** | **implemented** · shadow |
| **Description** | Weighted 0–100 from certificate bands + persistence ladder (Normal → … → Retire). |
| **Live MT5** | No (scores only until pause signed) |
| **Key paths** | `AI/fema_ops/health.py` · `scoring.py` · `AI/edge_health_cert.py` · `AI/data/live/health_latest.json` · `AI/certificate_PRODUCTION_EURUSD.json` |
| **Track / phase** | EL5 · OP-02 |
| **Notes** | Distinct from `AI3-EDGE-HEALTH` and `ASI-EDGE-HEALTH-PRED` |

---

## `OP-SCORING-BANDS`

| Field | Value |
| ----- | ----- |
| **Name** | Component band scorers (PF / TP / depth / MAE / regime share…) |
| **Status** | **implemented** |
| **Description** | Building blocks that map metrics → 0–100 for `health_v0`. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/scoring.py` |
| **Track / phase** | EL5 support |
| **Notes** | Includes `score_regime(adx_ok_share)` — ops metric, not `ASI-REGIME` |

---

## `OP-PAUSE-SHADOW`

| Field | Value |
| ----- | ----- |
| **Name** | EL6 pause-new shadow (`would_pause_new`) |
| **Status** | **implemented** · shadow |
| **Description** | Health ladder → recommend pause new baskets; FP backfill; write live flag file from ops. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/pause.py` · CLI `pause-flag` / `pause-check` · `AI/kb/pause_policy.md` |
| **Track / phase** | EL6 · OP-09 |
| **Notes** | Wire decision **not signed** |

---

## `OP-PAUSE-WIRE`

| Field | Value |
| ----- | ----- |
| **Name** | EL6 pause-new MT5 flag reader |
| **Status** | **partial / parked** · opt-in unsigned |
| **Description** | EA reads `FEMA_AI\pause_new.flag` and blocks new baskets when armed. |
| **Live MT5** | Opt-in — `InpReadPauseNewFlag` (default OFF) |
| **Key paths** | `Include/Core/Config.mqh` · Engine `RefreshPauseNewFlag` · `AI/kb/pause_policy.md` |
| **Track / phase** | EL6 · IS-EL6-01 |
| **Notes** | Keep OFF until EL5 demo trust ≥2w + human sign-off |

---

## `OP-FINGERPRINT`

| Field | Value |
| ----- | ----- |
| **Name** | Birth fingerprint / edge genome |
| **Status** | **implemented** |
| **Description** | Capture live/demo fingerprint vs certificate lock (ADX/BSL/etc.). |
| **Live MT5** | No (observability) |
| **Key paths** | `AI/fema_ops/fingerprint.py` · CLI `fingerprint` · `AI/kb/genome_PRODUCTION.md` · `AI/data/live/fingerprint_latest.json` |
| **Track / phase** | EL3/EL4 · OP-04 |
| **Notes** | PRODUCTION expects `adx_gate=on` · `bsl=25` |

---

## `OP-COMPAT-SCORE`

| Field | Value |
| ----- | ----- |
| **Name** | Ops birth-compatibility score (`fema_compatibility_v0`) |
| **Status** | **implemented** |
| **Description** | Score how compatible current path is with birth fingerprint; drives empty factory when compat=100. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/fingerprint.py` `score_compatibility` · `AI/data/live/compat_latest.json` |
| **Track / phase** | OP-04 |
| **Notes** | Distinct from planned `ASI-COMPAT` |

---

## `OP-DRIFT`

| Field | Value |
| ----- | ----- |
| **Name** | Drift detection |
| **Status** | **implemented** |
| **Description** | Birth / component / compat drift alerts for operator. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/drift.py` · CLI `drift` · `AI/data/live/drift_latest.json` |
| **Track / phase** | Ops Plane Wave 5 |
| **Notes** | Shadow alerts only |

---

## `OP-OBSERVATORY`

| Field | Value |
| ----- | ----- |
| **Name** | Daily observatory note |
| **Status** | **implemented** |
| **Description** | Operator daily rollup of health / source / action. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/observatory.py` · `AI/data/live/observatory_daily.md` |
| **Track / phase** | OP-06 |
| **Notes** | Human-facing digest |

---

## `OP-G1-GATE`

| Field | Value |
| ----- | ----- |
| **Name** | G1 validation / promote-demote gate |
| **Status** | **implemented** |
| **Description** | Hard PF≥1.36 **and** DD≤18% (plus stale-slice rules) for candidate promote research. |
| **Live MT5** | No |
| **Key paths** | `AI/kb/gate_rules.json` · `AI/fema_ops/gates.py` · CLI `gate-check` / `gate-polish` · `AI/kb/el2_promote_decision.md` |
| **Track / phase** | EL2 · AER-P6 |
| **Notes** | Human promote only |

---

## `OP-FACTORY`

| Field | Value |
| ----- | ----- |
| **Name** | Candidate factory / recommend (one-axis ≤3) |
| **Status** | **implemented** |
| **Description** | Recommend ≤3 one-subsystem clones from PRODUCTION / search_map; clone presets. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/factory.py` · CLI `recommend` / `factory` / `clone` · `AI/kb/search_map.md` · `Presets/manifest.json` |
| **Track / phase** | RD-02 · AER · INF-PRESET |
| **Notes** | Never invent free multi-key axes |

---

## `OP-EL7-REDISCOVERY`

| Field | Value |
| ----- | ----- |
| **Name** | EL7 re-discovery trigger / enqueue |
| **Status** | **implemented** · shadow / human-force |
| **Description** | Ladder → factory → tester queue; dry-run + policy advisor; never auto overnight without human open. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/el7.py` · CLI `el7-dry-run` · `ops/tester_queue/el7_enqueue.ps1` · `AI/kb/el7_rediscovery_runbook.md` |
| **Track / phase** | EL7 · RD-11 |
| **Notes** | `-Force` only when human opens |

---

## `OP-DLR`

| Field | Value |
| ----- | ----- |
| **Name** | Dual-lane rediscovery (Lane A + Lane B) |
| **Status** | **implemented** · MVP complete |
| **Description** | Default Lane A off PRODUCTION; escalate Lane B after ≥2 A fails via challenger roster. |
| **Live MT5** | No |
| **Key paths** | `doc/dual_lane_rediscovery_pipeline.md` · `AI/kb/dlr_policy.json` · `AI/kb/challenger_roster.*` · `ops/tester_queue/*` |
| **Track / phase** | DLR-P0…P3 |
| **Notes** | Auto-promote = false |

---

## `OP-AER`

| Field | Value |
| ----- | ----- |
| **Name** | Automated Edge Rediscovery pipeline tooling |
| **Status** | **implemented** |
| **Description** | Terminal B tester queue · scorecard · decision packs · register runs · human promote path. |
| **Live MT5** | No (Terminal A stays PRODUCTION) |
| **Key paths** | `automated_edge_rediscovery_pipeline.md` · `doc/edge_rediscovery_system.md` · `ops/tester_queue/` · `AI/fema_ops/runs.py` |
| **Track / phase** | AER-P0…P6 |
| **Notes** | Ops plane for rediscovery, not a model |

---

## `OP-CI-GATES`

| Field | Value |
| ----- | ----- |
| **Name** | CI schema / certificate gates |
| **Status** | **implemented** |
| **Description** | Repo CI checks for cert / gates / OpenAPI contracts. |
| **Live MT5** | No |
| **Key paths** | `AI/fema_ops/ci_gates.py` · CLI `ci-gates` · `.github/workflows` |
| **Track / phase** | OP-13 |
| **Notes** | Integrity, not trading |

---

## `OP-ARTIFACTS-DB`

| Field | Value |
| ----- | ----- |
| **Name** | Immutable artifacts + Postgres ingest |
| **Status** | **implemented** · Wave 1 tooling |
| **Description** | Archive basket CSVs; optional DB migrate/ingest for research store. |
| **Live MT5** | No |
| **Key paths** | CLI `artifacts-*` · `db-migrate` · `db-ingest` · `AI/fema_ops/` |
| **Track / phase** | Wave 1 · OP-10/OP-11 |
| **Notes** | Storage plane for AI datasets |

---

## `LT-ADAPTIVE-SIZING`

| Field | Value |
| ----- | ----- |
| **Name** | Adaptive basket / grid depth sizing by confidence |
| **Status** | **planned** · long-term |
| **Description** | Reduce max grid depth when edge confidence is low. |
| **Live MT5** | No |
| **Key paths** | `doc/failureimprove.md` §Long-Term |
| **Track / phase** | beyond ASI |
| **Notes** | Vision only |

---

## `LT-PORTFOLIO-DIVERSIFY`

| Field | Value |
| ----- | ----- |
| **Name** | Multi-EA portfolio diversification |
| **Status** | **planned** · long-term |
| **Description** | Run uncorrelated EAs so one strategy’s steamroller is offset by another’s favourable regime. |
| **Live MT5** | No |
| **Key paths** | `doc/failureimprove.md` · `edgecontainment.md` |
| **Track / phase** | vision |
| **Notes** | Portfolio layer |

---

## `LT-CAPITAL-ALLOC`

| Field | Value |
| ----- | ----- |
| **Name** | Capital allocation by Edge Health Score |
| **Status** | **planned** · long-term |
| **Description** | Allocate more capital to healthier EAs. |
| **Live MT5** | No |
| **Key paths** | `doc/failureimprove.md` · `edgecontainment.md` |
| **Track / phase** | vision |
| **Notes** | Depends on trusted health scores |

---

## `LT-CROSS-SYMBOL`

| Field | Value |
| ----- | ----- |
| **Name** | Cross-symbol confirmation context |
| **Status** | **planned** · long-term |
| **Description** | Use correlated markets (DXY / crosses) as context — not entry DNA rewrite. |
| **Live MT5** | No |
| **Key paths** | `doc/failureimprove.md` |
| **Track / phase** | vision |
| **Notes** | Context only |

---

## Naming collisions (keep distinct)

| Concept | IDs (do not merge) |
| ------- | ------------------ |
| Regime | `AI1-REGIME-ATLAS` · `EC1-REGIME` · `EC1-NESTED` · `ASI-REGIME` · `OP-SCORING-BANDS` |
| Failure / steamroller | `AI2-FAIL-PRED` · `EC2-FAIL` · `ASI-TEP-OPEN` · `ASI-MID-WARN-A` · `ASI-MID-WARN-B` |
| Recovery | `AI8-BASKET-REC` · `ASI-REC` · (`ASI-MID-WARN-B` action) |
| Edge health | `AI3-EDGE-HEALTH` · `EC3-HEALTH` · `OP-HEALTH-V0` · `ASI-EDGE-HEALTH-PRED` |
| Compatibility | `OP-COMPAT-SCORE` · `ASI-COMPAT` |
| Session | hard session inputs (not listed) · `ASI-SESSION-INTEL` |
| Confidence / fusion | `AI4-EDGE-PROB` · `EC4-PROB` · `AI5-FUSION` · `EC5-FUSION` · `ASI-DYN-CONF` |
| Pause | `OP-PAUSE-SHADOW` · `OP-PAUSE-WIRE` · (AI3 stress pause shadow) |

---

## Live MT5 AI opt-ins (PRODUCTION defaults)

| ID | Input | PRODUCTION default |
| -- | ----- | ------------------ |
| `AI0-EVENT-LOG` | `InpUseAiEventLog` | **on** |
| `ASI-TEP-OPEN` | `InpUseAiTepGate` | off |
| `ASI-MID-WARN-A` | `InpUseAiMidWarn` | off |
| `ASI-MID-WARN-B` | `InpUseAiMidEarlyBsl` | off |
| `ASI-REGIME` | `InpUseAiRegimeGate` | off |
| `OP-PAUSE-WIRE` | `InpReadPauseNewFlag` | off |

**AI preset load:** `Presets/aistack.set` enables TEP + mid + Mode B + regime (all **on** in preset). PRODUCTION chart stays on lock preset unless operator opts in.

---

## Related spine docs

| Doc | Role |
| --- | ---- |
| [`doc/adaptive_selection_phases.md`](doc/adaptive_selection_phases.md) | ASI phase tracker |
| [`doc/failureimprove.md`](doc/failureimprove.md) | Track A–J thesis |
| [`ai_enhance.md`](ai_enhance.md) | Legacy AI0–AI9 / AI-X |
| [`aiedgecontain.md`](aiedgecontain.md) | EC0–EC7 contain |
| [`system_audit.md`](system_audit.md) | Main/subsystem map |
| [`AI/STATUS.md`](AI/STATUS.md) | Operator glance |
| [`AI/kb/search_map.md`](AI/kb/search_map.md) | One-axis Discovery map |
