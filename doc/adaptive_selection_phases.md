# Adaptive Selection Intelligence — Implementation Phases

**Status:** **`ASI-P5` COMPLETE (MVP)** (2026-07-19) · Mode A + Mode B **Alternate** presets (kept separate) · **`ASI-P4` Alternate** · PRODUCTION unchanged  
**IDs:** `ASI-*` (Adaptive Selection Intelligence)  
**Parent thesis:** [`failureimprove.md`](failureimprove.md)  
**Failure forensics:** [`EA_failure_assessment.md`](EA_failure_assessment.md)  
**Containment:** [`../AI/kb/search_map.md`](../AI/kb/search_map.md) · dual-lane [`dual_lane_rediscovery_pipeline.md`](dual_lane_rediscovery_pipeline.md)  
**Charter:** MT5 executes · Python scores · Human promotes  
**P5 pack:** [`ASI_P5_midbasket_pack.md`](ASI_P5_midbasket_pack.md)

### Adopted way forward

> Stop trying to make FEMA “better at trading.” Optimize **selection**: reject baskets that resemble historical steamrollers / low-compatibility regimes, while **preserving** the pullback-grid edge (similar WR · similar trade count · lower DD).

**Design law (permissive):** Prefer missed skips over false blocks. High confidence to skip only. Never thaw lots / execution / strategy type. Never auto-promote.

#### Adoption record (`ASI-P0`)

| Field | Value |
| ----- | ----- |
| Decision | **ADOPT** adaptive selection charter |
| Date | 2026-07-17 |
| Code | None in P0 — labels/model start at `ASI-P1` |
| Next ID | **ASI-P6** basket recovery **or** park |

### Guardrail candidate (`long_train`) + window review

Philosophy: **guardrails not gates** — pass kill criteria on holdout; do not require beating PRODUCTION.

| Field | Value |
| ----- | ----- |
| Train | **2018–2024** (2018 collect) |
| Holdout (calibrate) | 2025 |
| Threshold (post `roll_pf` fix) | **~0.650** |
| Review | `asi-review --guardrail` → **ok** |
| Gate file | `Common\Files\FEMA_AI\tep_gate_v1.txt` |
| Decision | **Alternate** (2026-07-19) — opt-in only |

| Tester window | PF | Net | DD | Trades |
| ------------- | --: | --- | --: | -----: |
| 2018–2025 | ~1.00 | ~−$30 | ~55% | ~6.9k |
| **2026.01–07** | **1.38** | +$243 | ~11% | 454 |
| **2025.01–2026.07** | **1.20** | +$407 | ~18% | 1,306 |

2026 windows are G1-competitive vs birth lock (~PF1.36 / DD18%) but **do not** promote the gate — keep Alternate.

Commands:
```bash
python -m fema_ops asi-build --split-profile long --no-promote
python -m fema_ops asi-train --strict --max-skip 0.08 --guardrail
python -m fema_ops asi-review --guardrail
```

To go **before 2020**: re-export baskets from MT5 tester (`FromDate=2018.01.01` or earlier) → `AI/data/EURUSD_baskets_*.csv`.

---

## 0. Scope split

| Class | Action |
| ----- | ------ |
| **Structural** | Accept — pullback miss, continuous expansion, avgL > avgW, grid short vol, basket adds exposure |
| **Adaptive** | Build — prediction / confidence gates that **skip or scale**, not rewrite entry/exit DNA |
| **Do not try** | More indicators, tighter TP, trail, candle/RSI overlays, free genetic search (see [`failureimprove.md`](failureimprove.md)) |

**Track priority (build order):**

| Pri | Track | Code |
| --- | ----- | ---- |
| 1 | **A** Trend Expansion Predictor (TEP) | `ASI-P1`…`P4` |
| 2 | **E** Steamroller Early Warning (mid-basket) | `ASI-P5` |
| 3 | **B** Basket Recovery Probability | `ASI-P6` |
| 4 | **D** Market Compatibility Score | `ASI-P7` |
| 5 | **G** Regime Intelligence | `ASI-P8` |
| 6 | **H** Edge Health Prediction | `ASI-P9` |
| 7 | **C / F / I / J** Session · grid breathe · failure memory · dynamic confidence | `ASI-P10+` |

Tracks **E** and **A** share features; **A** = gate at **basket open**; **E** = warn **during** basket. Do not merge into one hard filter.

---

## 1. Implementation phases & IDs

### Phase 0 — Charter & constraints · `ASI-P0` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P0-01` | Adaptive selection charter in `doc/` | **done** | This file |
| `ASI-P0-02` | Link from `failureimprove.md` + failure assessment | **done** | Cross-links + STATUS / audit / edge snapshot |
| `ASI-P0-03` | Non-goals locked (no structural “fixes”, no auto-promote, permissive skip) | **done** | §3 Non-goals |
| `ASI-P0-04` | Success contract written (DD ↓ · WR/n ≈ flat · steamroller rate ↓) | **done** | §2 Metrics + soft bands |
| `ASI-P0-05` | Map TEP to search-map bookkeeping (`regime_extra` / new axis note) | **done** | [`search_map.md`](../AI/kb/search_map.md) § ASI / TEP |

**Exit:** Design adopted; no model code required. **Phase 0 closed 2026-07-17.** Next: `ASI-P1-01`.

---

### Phase 1 — Labels & dataset · `ASI-P1` · **COMPLETE**

Offline only. No MT5 behaviour change.

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P1-01` | Define steamroller / expansion-fail label from Agent baskets+events | **done** | [`label_schema.md`](../AI/kb/asi/label_schema.md) · `fema_ops/asi/labels.py` |
| `ASI-P1-02` | Snapshot features at **basket-open** (no leakage) | **done** | `fema_ops/asi/features.py` · TEP v0 derived cols |
| `ASI-P1-03` | Build train/holdout splits on lock + research windows | **done** | [`splits.json`](../AI/kb/asi/splits.json) |
| `ASI-P1-04` | Baseline rates: steamroller %, PF, DD, n, WR on unlabeled PRODUCTION | **done** | [`asi_baseline_metrics.json`](../AI/kb/asi/asi_baseline_metrics.json) |
| `ASI-P1-05` | Shadow column: “would_skip @ threshold” vs actual PnL | **done** | [`asi_shadow_v0.json`](../AI/kb/asi/asi_shadow_v0.json) |

**Feature v0 (TEP):** EMA slope acceleration · ADX acceleration · ATR expansion rate · consecutive same-dir candles · distance from EMA · impulse score.

**Build:** `cd AI && python -m fema_ops asi-build`

**Exit:** Reproducible labeled dataset + baseline; human reviews label quality. **Phase 1 closed 2026-07-17.** Next: `ASI-P2-01`.

---

### Phase 2 — Offline TEP model · `ASI-P2` · **COMPLETE**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P2-01` | Train TEP → P(steamroller \| open) | **done** | [`tep_model.pkl`](../AI/kb/asi/tep_model.pkl) · [`tep_train_log.json`](../AI/kb/asi/tep_train_log.json) |
| `ASI-P2-02` | Calibration curve + choose **permissive** skip threshold | **done** | threshold **0.581** · skip **5%** on calibrate |
| `ASI-P2-03` | Holdout: steamroller recall vs winner false-skip rate | **done** | [`tep_model_card.json`](../AI/kb/asi/tep_model_card.json) · promote_frozen one-shot |
| `ASI-P2-04` | Ablation: acceleration vs static ADX/ATR (prove incremental value) | **done** | TEP full AUC **0.539** > static **0.528** > ADX **0.496** |
| `ASI-P2-05` | Freeze model card (features, window, threshold, non-goals) | **done** | [`tep_model_card.json`](../AI/kb/asi/tep_model_card.json) |

**Train:** `cd AI && python -m fema_ops asi-train`

**Exit:** Offline model beats ADX-only on calibrate AUC; skip ≤10%. **Phase 2 closed 2026-07-17.** Next: `ASI-P3-01`.

---

### Phase 3 — Shadow in ops loop · `ASI-P3` · **COMPLETE**

Still **no** live skip. Log what TEP would have done on Tester / live CSVs.

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P3-01` | Score each new registered run’s baskets with TEP offline | **done** | `asi-shadow` · `postrun` hook · `kb/asi/shadows/` |
| `ASI-P3-02` | Scorecard columns: skipped_n · skipped_pnl · DD_if_skipped | **done** | `scorecard.ps1` ASI cols |
| `ASI-P3-03` | Compare shadow vs PRODUCTION lock on canonical window | **done** | [`asi_p3_review_pack.md`](../AI/kb/asi/asi_p3_review_pack.md) |
| `ASI-P3-04` | Kill criteria: if false-skip winners dominate → retune threshold or stop | **done** | in [`tep_model_card.json`](../AI/kb/asi/tep_model_card.json) |

**Commands:** `python -m fema_ops asi-shadow --run-id <id>` · `python -m fema_ops asi-review`

**P3 review (2026-07-17, initial):** kill status **`kill`** on canon — precision 25% · 6 false-skip winners vs 2 steamrollers · net_skipped +$8 · DD proxy 18.14→18.37.

**Strict retune (2026-07-17):** `asi-build` + `asi-train --strict --max-skip 0.05` — added interaction features (`adx_x_atr_expand`, `slope_x_consec`, `impulse_x_dist`); calibrate AUC **0.553** (was 0.539). No threshold met strict gates (precision ≥40%, net_skipped ≤0, false winners ≤ steamrollers, skip ≤5%) → **empty skip** (threshold **1.0**). `asi-review`: **`empty_skip` / observe** — baseline PF **1.45** unchanged · DD **18.14%** unchanged. P4 live gate may be designed but TEP currently skips nothing.

**Exit:** Tooling complete; operator review pack filed. **Phase 3 closed 2026-07-17.** Next: `ASI-P4-01` **or** further model work.

---

### Phase 4 — TEP guardrail gate · `ASI-P4` · **COMPLETE** (Alternate)

First behaviour change: **skip new basket** when `P(steamroller) >= threshold`. Mid-grid untouched. **Promote bar = guardrail holdout**, not beat PRODUCTION on demo.

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P4-01` | Integration: export `tep_gate_v1.txt` + MQL `AiTepGate.mqh` | **done** | `asi-export-gate` · `Include/AI/AiTepGate.mqh` |
| `ASI-P4-02` | Candidate preset: `InpUseAiTepGate` on, threshold frozen | **done** | `Presets/ASI_P4_TEP_GUARD_01.set` |
| `ASI-P4-03` | Terminal B Tester run + register metrics | **done** | 2018–2025 · ~6877 trades · PF~1.00 · DD~55% |
| `ASI-P4-04` | Guardrail sign-off (holdout kill + operator) | **done** | Operator: keep as guardrail candidate |
| `ASI-P4-05` | If Alternate: profile on roster | **done** | `prof_ASI_P4_TEP_GUARD_01.json` · status `alternate` |
| `ASI-P4-06` | Human promote only | **done** | No promote — PRODUCTION unchanged |

**Decision (2026-07-19):** **Alternate** — keep opt-in guardrail; do not lock. Pack: [`ASI_P4_tep_guard_pack.md`](ASI_P4_tep_guard_pack.md) · [`20260719_ASI_P4_TEP_GUARD_01_Alternate.md`](../AI/kb/decisions/20260719_ASI_P4_TEP_GUARD_01_Alternate.md)

**Window addendum:** 2026.01–07 PF **1.38** · 2025–2026.07 PF **1.20** — competitive, still **not** a lock promote.

**Exit:** Track A MVP closed as **Alternate**. Next: `ASI-P5`.

```text
ASI-P0 charter
  └─► ASI-P1 labels/dataset
        └─► ASI-P2 offline TEP
              └─► ASI-P3 shadow ops
                    └─► ASI-P4 guardrail gate  ◄ COMPLETE — Alternate
                          └─► ASI-P5 mid-basket  ◄ COMPLETE — Mode A + Mode B Alternate
```

---

### Phase 5 — Steamroller early warning (mid-basket) · `ASI-P5` · **COMPLETE** (MVP)

Depends on P1 features; TEP open-gate decided (**Alternate**). Pack: [`ASI_P5_midbasket_pack.md`](ASI_P5_midbasket_pack.md).

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P5-01` | Label mid-basket “will become steamroller” from path (depth milestones) | **done** | [`label_schema.md`](../AI/kb/asi/label_schema.md) · `y_mid_steamroller` |
| `ASI-P5-02` | Features at warn time (open + accel + `warn_depth`; no outcome leakage) | **done** | `fema_ops/asi/midbasket.py` · `MID_STATIC` |
| `ASI-P5-03` | Action policy: warn only → optional early BSL (human-scoped) | **done** | [`mid_policy_adr.md`](../AI/kb/asi/mid_policy_adr.md) |
| `ASI-P5-04` | Offline + Mode A shadow + Mode B Tester (survival bar) | **done** | Mode A `ASI_P5_TEP_MID_01` · Mode B **Alternate** |

**Presets (keep separate):**

| Preset | Mode | Status |
| ------ | ---- | ------ |
| `ASI_P5_TEP_MID_01` | A — warn log | ready / research default for mid stack |
| `ASI_P5_TEP_MID_BSL_01` | B — early close `MID_WARN` | **Alternate** · [`20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md`](../AI/kb/decisions/20260719_ASI_P5_TEP_MID_BSL_01_Alternate.md) |

**Mode B survival (deposit 400):** 2026 PF **1.44** / DD~19% · 2018–25 PF **1.35** / DD~23% (vs TEP-only long ~PF1 / DD~55%). Promote bar = survival, not beat PRODUCTION.

**Exit:** Track E MVP closed. Do not merge Mode B into Mode A or PRODUCTION. Next: `ASI-P6` or park.

```text
ASI-P0 charter
  └─► … ASI-P4 guardrail  ◄ Alternate
        └─► ASI-P5 mid-basket  ◄ COMPLETE — Mode A + Mode B Alternate (own presets)
              └─► ASI-P6 recovery  ◄ next (optional)
```

---

### Phase 6 — Basket recovery probability · `ASI-P6` · **PENDING**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P6-01` | P(recover \| current basket state) | **pending** | Model + calibration |
| `ASI-P6-02` | Actions: keep · reduce depth · accept BSL early | **pending** | Policy map |
| `ASI-P6-03` | Shadow → Tester → G1 | **pending** | Decision pack |

---

### Phase 7 — Market compatibility score · `ASI-P7` · **PENDING**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P7-01` | 0–100 score at signal time (trend persist, pullback quality, vol, spread, EMA geometry) | **pending** | Score definition |
| `ASI-P7-02` | Permissive threshold (trade elite only when low) — not hard blacklist | **pending** | Threshold card |
| `ASI-P7-03` | Shadow → Tester → G1 | **pending** | Decision pack |

---

### Phase 8 — Regime intelligence · `ASI-P8` · **PENDING**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P8-01` | Regime taxonomy (pullback trend, grind, impulse, exhaustion, expansion, …) | **pending** | Label set |
| `ASI-P8-02` | Historical PF/DD per regime on lock data | **pending** | Regime scorecard |
| `ASI-P8-03` | Map regimes → allow / caution / skip (permissive) | **pending** | Policy table |
| `ASI-P8-04` | Shadow → Tester → G1 | **pending** | Decision pack |

---

### Phase 9 — Edge health prediction · `ASI-P9` · **PENDING**

| ID | Task | Status | Done when |
| -- | ---- | ------ | --------- |
| `ASI-P9-01` | Leading indicators of PF/DD fade (3-week horizon draft) | **pending** | Feature + label |
| `ASI-P9-02` | Hook to EL7 / rediscovery trigger (recommend only) | **pending** | Policy note — human still enqueues |
| `ASI-P9-03` | Shadow accuracy vs actual fade events | **pending** | Review pack |

---

### Phase 10+ — Secondary tracks · `ASI-P10` · **PENDING**

| ID | Track | Status | Done when |
| -- | ----- | ------ | --------- |
| `ASI-P10-01` | **C** Session intelligence (scale confidence, don’t blacklist) | **pending** | Spec + shadow |
| `ASI-P10-02` | **F** Dynamic grid compression (ATR mult breathe) | **pending** | Spec — search_map `atr`/`grid` one-axis only |
| `ASI-P10-03` | **I** Failure memory (similarity to past losers) | **pending** | Spec + shadow |
| `ASI-P10-04` | **J** Dynamic confidence (compose A/D/G/C) | **pending** | Spec after P4+P7+P8 |

---

## 2. Success contract (all adaptive tracks)

A candidate **passes research interest** on adaptive tracks if shadow/Tester shows:

| Metric | Direction | Band |
| ------ | --------- | ---- |
| Steamroller / fat-tail rate | ↓ | Primary research win |
| Guardrail kill (holdout) | pass | **Hard** for ASI-P4 wire |
| Max DD (G1) | ≤ PRODUCTION | Hard for **lock** promote only |
| PF (G1) | ≥ PRODUCTION | Hard for **lock** promote only |
| Trade count `n` | ≈ flat | Soft: ≥ **90%** of baseline (skip budget ≤10%) |
| Win rate | ≈ flat | Soft: within **±3 pp** |

**ASI-P4 guardrail path:** pass holdout kill + operator sign-off. **Do not** require beating PRODUCTION PF on 2026 demo to keep testing the gate.

Fail hard lock rows → **Reject** as PRODUCTION successor. Soft-band fail with DD/PF win → **Alternate** at most (roster profile; not lock).

**Anti-overfit gate (before promote):** walk-forward/holdout OK · skip rate ≤ cap · ablation > static ADX/ATR alone · threshold **frozen** before canonical G1 · optional parent-sensitivity (Lane B shadow). See §3a.

---

## 3. Non-goals (FEMA constraints)

- “Fixing” structural failures (eliminate all expansion losses)
- Restrictive stacks that starve pullback frequency
- More entry indicators / candle / RSI as primary ASI path
- Tighter TP / trailing as ASI substitutes
- Genetic multi-axis free search
- Auto-promote / Discovery on Terminal A live chart
- Thawing frozen architecture (see search_map)
- Tuning threshold on the canonical G1 window (fit/tune/promote must be separated)

### 3a. Anti-overfit constraints (charter)

| Rule | Practice |
| ---- | -------- |
| Time split | Train / tune / promote on **disjoint** spans; never random-shuffle baskets |
| No leakage | Features only knowable at basket-open (TEP) or warn-time (mid-basket) |
| Skip budget | Default ≤10% baskets skipped at chosen threshold |
| Simple first | Logistic / shallow model before ensembles |
| Ablation | Must beat static ADX/ATR / existing gates |
| One shot G1 | Freeze threshold **before** final canonical Tester promote run |

---

## 4. Dual-lane fit

| Lane | ASI use |
| ---- | ------- |
| **A** | TEP/threshold as one search-map-style axis off **PRODUCTION** |
| **B** | Same gate thesis off roster parent (`P1-BASELINE`, alternates) if A plateaus |
| **Scorecard** | Always vs PRODUCTION lock; record `asi_track` + model card id |

**Search-map bookkeeping (`ASI-P0-05`):** until MQL `Inp*` keys exist, tag Discovery jobs `subsystem=regime_extra` **or** thesis `tep` / `asi_tep` (observe / notes). When P4 adds inputs, either new map id `tep` **or** fold under `regime_extra` — do **not** invent a free multi-key axis. Detail: [`search_map.md`](../AI/kb/search_map.md).

---

## 5. Immediate next ID

| Field | Value |
| ----- | ----- |
| Now | **ASI-P6** basket recovery **or** park |
| Keep | `ASI_P4_TEP_GUARD_01` · `ASI_P5_TEP_MID_01` · `ASI_P5_TEP_MID_BSL_01` as **separate** Alternates |
| Never | Merge Mode B into Mode A / P4 / PRODUCTION without new decision |

```text
ASI-P0…P4 · COMPLETE (P4 Alternate)
  └─► ASI-P5 mid-basket · COMPLETE — Mode A + Mode B Alternate (own presets)
        └─► ASI-P6 recovery  ◄ next (optional)
```
