# FEMA — AI Enhance (legacy exploration)

**Status:** **Archived / reference** — superseded for new work by [`aiedgecontain.md`](aiedgecontain.md)  
**Why kept:** AI0–AI4 tooling notes, early 2024–2026 collects, beat-2026 experiments  
**Do not use this file as the active AI build plan** — that is **AI Edge Contain**.

**Active plan:** [`aiedgecontain.md`](aiedgecontain.md) · [`AI/windows.json`](AI/windows.json) · [`AI/README.md`](AI/README.md)  
**Depends on:** Locked EURUSD PRODUCTION ([`System Profile EURUSD.md`](System Profile EURUSD.md))  
**Vision source:** [`aiscaleupconcept.md`](aiscaleupconcept.md)

---

## Legacy note (pre-contain)

The sections below document the older “AI Enhance” pass that scored models against **2026 PRODUCTION** (AI-G1 beat-baseline). That mixed **demo edge** with **AI school grade**. New work uses **guardrails on 2020–2025** instead — see contain doc.

---

## Philosophy

The execution engine already has the edge. AI does **not** invent buys/sells.

```
PRODUCTION Engine (demo / live)  →  candidate basket / add / hold
         │
         ▼
AI Edge Preservation Layer   ← GUARDRAILS, not performance gates
         │
    Approve | Soft-skip | Delay | Reduce | Suspend | Adapt
         │
         ▼
    Execution (unchanged logic)
```

**Primary objective:** Know when the edge is present, degrading, or gone — then **protect capital** without starving the engine of its good trades.

**Secondary effects (not the direct target):** higher WR, better PF/Sharpe, lower DD, fewer steamroller-path baskets.

### Guardrails vs gates (2026-07-11 lock)

| | **Guardrail (what we want)** | **Gate (what we were overdoing)** |
| - | ---------------------------- | --------------------------------- |
| Job | Catch steamrollers / edge death | Beat 2026 PRODUCTION PF/DD |
| Default | **Approve** — engine trades | Skip until AI “wins” the scoreboard |
| Build data | **2020–2025** with internal splits | Force every model to lift 2026 lock |
| Demo now | Run **PRODUCTION as-is** | Block progress until AI > demo window |
| Success | Bad-path precision · DD damage avoided · ≤15% pause/skip | PF ≥ 2026 baseline or reject everything |

AI0–AI4 work stays useful as tooling; the **scoreboard** changes. We no longer treat “2026 always looks better than AI” as failure of the layer — that window is the **edge under demo**, not the AI schoolyard.

### Hard rules (from Phase 2)

| Rule | Why |
| ---- | --- |
| Engine stays frozen | PRODUCTION entries/exits are validated |
| Prefer **skip bad** over **pick elite** | Overfiltering killed edge (HTF, ATRP70, LDN_NY, CONFIRM) |
| Soft guardrails, **low** skip rates | Protect, don’t redesign |
| Offline proof before wire | Demo runs engine; AI shadows until safe |
| Retrain on rolling data | Keep guardrails alive as regimes drift |
| Cap signal reduction | e.g. AI may remove ≤10–15% of candidates |

---

## Data windows (locked)

| Role | Window | Purpose |
| ---- | ------ | ------- |
| **Live / demo edge** | Ongoing (incl. 2026) | **PRODUCTION unchanged** — not an AI beat-this target |
| **AI collect** | **2020.01.01 → 2025.12.31** | One AI0 tester run → offline splits |
| **AI train** | **2020.01.01 → 2023.12.31** | Fit regime / fail / health / prob |
| **AI holdout (guardrail quality)** | **2024.01.01 → 2025.12.31** | Did guardrails catch bad paths? Precision · DD cut · ≤15% budget |
| **Optional later sanity** | 2026 Jan–Jul (demo-era) | Shadow only — must not starve PRODUCTION |

**Symbol / stack:** EURUSD M5 · `FEMA_EURUSD_M5_PRODUCTION` (BSL $25 + ADX<30 + basket TP $10)

### Rules

1. **Demo trades PRODUCTION.** AI build does **not** need to beat demo/2026 metrics.  
2. **Train 2020–23 → score guardrails on 2024–25 holdout** (bad-path catch, not PF trophy).  
3. Report metrics **per window** — never one blended PF as “AI vs PRODUCTION”.  
4. Soft-skip / pause ≤10–15% on the **holdout** window.  
5. Optional 2026 shadow later: approve-by-default; abort if it starves the live edge.  
6. AI0 collect: tester `2020.01.01 → 2025.12.31`, then `python AI/split_2020_2025.py`.

### Guardrail pass (build bar)

| Check | Pass |
| ----- | ---- |
| Approve by default | Uncertain → trade |
| Budget | Skip/pause ≤15% of holdout baskets |
| Bad-path quality | Skipped/paused set mostly losers / BSL · net avoided ≤ 0 |
| Stress | Helps before known DD troughs on train/holdout |
| Trade count | ≥85% of unfiltered holdout |
| **Not required** | PF ≥ 2026 PRODUCTION demo baseline |

### Baselines (reference only)

| Window | Role |
| ------ | ---- |
| 2026 Jan–Jul PRODUCTION | **Demo edge freeze** (`AI/baseline.json`) — live reference, not AI school gate |
| 2024–2025 baskets | Prior long-window characterisation (fade years) |
| 2020–2025 (pending collect) | New AI build corpus — see [`AI/windows.json`](AI/windows.json) |

### Prior captures (kept for history)

**2024→2026.07** AI0: 490 baskets · full PF 1.06 · 2026 slice PF 1.36 — showed edge concentration in demo window (why “beat 2026” was the wrong build game).

**2015→2026 attempt:** incomplete (CSV only 2015 H1) — archived `dataset_2015H1.csv`.

---

## Anti-goals (explicit)

| Do not | Reason |
| ------ | ------ |
| Ask AI “where to buy/sell” | Engine already does that |
| Require high confidence to trade (e.g. only score ≥80) | Overfilters; Phase 2 proved this pattern fails |
| 30–50 regimes on day one | Unstable labels, sparse stats |
| Dynamic ADX/TP/SL wild swings | Curve-fit risk; change engine character |
| Optimize profit as sole reward | DD and edge death matter more |
| Wire models before pipeline + offline lift | Premature live risk |

---

## Soft-guardrail policy (default everywhere)

AI layers are **failure / death filters**, not quality lotteries and not “beat PRODUCTION” contests.

| Setting | Default intent |
| ------- | -------------- |
| **Skip/pause only the worst tail** | Top ~10–15% clear failure / stress |
| **Approve by default** | If uncertain → **trade** (engine edge wins) |
| **Build holdout** | **2024–2025** guardrail quality (not 2026 demo PF) |
| **Trade-count budget** | ≥85% of unfiltered holdout baskets |
| **Wire later** | Only after holdout guardrail pass + demo shadow doesn’t starve PRODUCTION |
| **No elite-only mode** | Never “only high P(TP)” |
| **2026 / demo** | Live edge reference — optional sanity, not the school gate |

Example (illustrative — tune offline):

```
P(basket hits BSL | features) clearly elevated  → soft-skip   # guardrail
uncertain                                       → approve     # default = trade
```

Not:

```
P(TP) ≥ 0.85 → trade        # elite gate
AI PF must beat 2026 demo   # wrong scoreboard
```

---

## Architecture (target)

```
Market + Engine state
        │
        ▼
Feature Extraction + Trade/Basket Logger     ← AI0
        │
        ▼
Offline Dataset + Labels                     ← AI0 / AI1
        │
   ┌────┼────────────────────┐
   ▼    ▼                    ▼
Regime  Failure / Edge     Edge Health       ← AI1–AI4
stats   Probability        Monitor
   │    │                    │
   └────┴────────┬───────────┘
                 ▼
        Decision Fusion (soft)               ← AI5
                 │
        [shadow / offline replay only]
                 │
        Wire to EA when AI-G1 passes         ← AI6
                 │
        Retrain schedule                     ← AI7
                 │
        Optional: basket recovery / light adapt ← AI8–AI9
```

---

## Phase map

| Phase | ID | Name | Wire to EA? | Goal |
| ----- | -- | ---- | ----------- | ---- |
| 0 | **AI0** | Pipeline & infra | No | Log everything needed to train |
| 1 | **AI1** | Regime atlas (coarse) | No | Know which states pay / hurt |
| 2 | **AI2** | Failure predictor | Shadow only | Skip steamroller-path starts |
| 3 | **AI3** | Edge health monitor | Shadow → soft | Detect edge death early |
| 4 | **AI4** | Edge probability / confidence | Shadow | Soft entry gate (permissive) |
| 5 | **AI5** | Decision fusion | Shadow | Combine AI2–AI4 without overfilter |
| 6 | **AI6** | First live wire | Yes (opt-in) | Deploy soft skip under AI-G1 |
| 7 | **AI7** | Retrain loop | Yes | Rolling retrain, keep edge alive |
| 8 | **AI8** | Basket recovery assist | Optional | Mid-basket DD cut (careful) |
| 9 | **AI9** | Light adaptive params | Optional | Tiny bounded tweaks only |
| — | **AI-X** | Deferred | — | RL, 50-state taxonomy, elite ranking, memory search |

---

## AI0 — Pipeline & infra

**ID:** `AI0-INFRA`  
**Status:** **Complete (v1.22)** — dataset + replay verified 2026-07-11  
**Objective:** Make offline training and replay possible. No model decisions.

### Deliverables

| ID | Deliverable | Status |
| -- | ----------- | ------ |
| `AI0-001` | **Basket/trade event log** | ✅ 178,311 event rows |
| `AI0-002` | **Feature snapshot at decision time** | ✅ |
| `AI0-003` | **Outcome labels** | ✅ 108 baskets · 28 fails (25.9%) |
| `AI0-004` | **Offline dataset builder** | ✅ `AI/data/dataset.csv` |
| `AI0-005` | **Replay harness** | ✅ zero-skip matches full sample |
| `AI0-006` | **Baseline freeze** | ✅ deal + basket metrics in `AI/baseline.json` |

### Verified PRODUCTION capture (2026-07-11)

| | MT5 report | Basket CSV replay |
| - | ---------- | ----------------- |
| Net | +$240.16 | +$240.20 |
| PF | 1.40 | 1.40 |
| DD bal | 18.14% | 18.14% |
| Count | 429 deals | **108 baskets** |

CSV live path in tester: `Tester\...\Agent-*\MQL5\Files\FEMA_AI\` (Common may stay header-only while agent holds the lock).

### Exit criteria

- [x] Rebuild labeled dataset from full Jan–Jul PRODUCTION run  
- [x] Replay harness reproduces sample when skip-rate = 0  

**Next data collect:** ✅ Long window landed (2024→2026.07) — see Data windows § Long-window capture.  

**Next phase:** **AI0 collect 2020→2025** (PRODUCTION + AI log) → `split_2020_2025.py` → rebuild AI1–AI4 as **guardrails** on 2020–23 / 2024–25 (not beat-2026).

---

## AI1 — Regime atlas (coarse, descriptive)

**ID:** `AI1-REGIME`  
**Status:** **Complete (offline)** — 2026-07-11  
**Objective:** Map **few** regimes to historical edge quality — not 30–50 states yet.

### Tasks

| ID | Task | Status |
| -- | ---- | ------ |
| `AI1-001` | Rule-based regime labels (9 coarse states) | ✅ `AI/regime_atlas.py` |
| `AI1-002` | Per-regime PF / WR / BSL / net | ✅ scorecard |
| `AI1-003` | Publish regime scorecard | ✅ `AI/data/regime_scorecard.md` |
| `AI1-004` | Permissive soft-skip list | ✅ **empty** (no holdout-confirmed toxic ≤10%) |

### Key findings (108 PRODUCTION baskets)

| Regime | N | PF | Note |
| ------ | - | -- | ---- |
| `shallow_pullback` | 40 | **1.58** | Core edge |
| `high_adx` | 20 | **3.62** | Still good under ADX&lt;30 gate |
| `expansion` | 8 | 2.80 | Small / strong |
| `asia_open` | 6 | 2.01 | Keep (do not strip Asia) |
| `compression` | 16 | 0.88 | Soft weak — not skip (share + holdout mixed) |
| `late_session` | 12 | 0.56 full | Train PF 0.40 but **holdout PF 1.20** → watch only |

### Soft-skip verdict

- **Toxic list: none** — approve-by-default preserved  
- `late_session` on watchlist only (failed holdout confirmation)  
- Gates pass with skip-rate 0 (baseline unchanged)  
- **Not wired to EA**

### Exit criteria

- [x] Scorecard on time split (train 70 / hold 38) — *within 2026-only sample*  
- [x] Replay: skip≤10%, PF/DD/trade gates (vacuously pass with empty skip)  

**Rerun when long-window CSV lands:** train = **2024–2025**, holdout/validate = **2026 Jan–Jul** (see Data windows). Soft-skip still empty unless toxic on train **and** weak on 2026 validate.

**Next:** Guardrail rebuild — collect **2020–2025** AI0 CSV, then retrain AI1–AI4 on train/holdout splits (see Data windows).

---

## AI2 — Failure predictor (highest ROI model)

**ID:** `AI2-FAIL`  
**Status:** **Complete (offline shadow)** — 2026-07-11 · **not wireable**  
**Objective:** Predict **P(basket hits BSL or deep MAE)** at basket start — skip the steamroller path.

This matches Layer 12 in the vision doc and Phase 2’s core lesson: **contain / avoid bad paths**, don’t chase elite winners.

### Tasks

| ID | Task | Status |
| -- | ---- | ------ |
| `AI2-001` | Label `y = 1` if basket → BSL or MAE beyond threshold | ✅ `y_fail` in dataset |
| `AI2-002` | Train offline classifier (logistic / GBDT) | ✅ `AI/failure_predictor.py` |
| `AI2-003` | High precision on skips (not high recall) | ✅ scored; validate weak |
| `AI2-004` | Soft policy: lock skip **quantile** on late-train cal (≤5–15%) | ✅ |
| `AI2-005` | Shadow log: would-skip vs actual outcome | ✅ `AI/data/ai2_shadow.csv` |

### Run

```bash
python AI/repair_basket_ids.py          # once if basket_id all = 1 (pre-v1.23 logs)
python AI/failure_predictor.py --model gbdt
# artifacts: AI/data/ai2_report.{json,md} · ai2_skip_ids.txt · ai2_shadow.csv
```

### Results (locked quantile → single 2026 validate eval)

| Model | Status | Skip | y_fail prec | AUC val | AI-G1 |
| ----- | ------ | ---- | ----------- | ------- | ----- |
| **GBDT (primary)** | `fragile_shadow_g1_thin_sample` | 5.5% (6) | 50% | **0.48** | PASS (PF 1.36→1.40, DD 18.6→18.3) |
| Logistic | `reject_shadow` | 15% | 35% | 0.56 | FAIL (trade budget / mix) |

**Why not wire:** Validate ranking is ~coin-flip (AUC 0.48); G1 lift sits on only **6** skips. Train looks strong → classic non-transfer. Keep PRODUCTION unfiltered; AI2 stays shadow until features/health signals improve transfer.

Also repaired pre-v1.23 logs (`basket_id` was always `1`) via `AI/repair_basket_ids.py` → sequential offline UIDs.

### Threshold philosophy

```
Skip when model is confident this looks like a LOSER path.
Do not require model to be confident this looks like a WINNER.
```

### Exit criteria (offline replay)

| Metric | Pass | This run |
| ------ | ---- | -------- |
| Trade count | ≥ 85–90% of baseline | ✅ |
| PF | ≥ baseline | ✅ (fragile) |
| Max DD | ≤ baseline | ✅ (fragile) |
| WR | ≥ baseline | ✅ |
| Skipped set majority losers | Prefer ≥50% | ⚠ 50% y_fail / 33% loser · n=6 |
| Rank quality | AUC val ≳ 0.55 | ❌ 0.48 |

---

## AI3 — Edge health monitor

**ID:** `AI3-HEALTH`  
**Status:** **Complete (offline shadow)** — 2026-07-11 · **not wireable** (`reject_shadow`)  
**Objective:** Detect **edge degradation / death** from rolling live-like metrics — reduce participation before large DD.

### Monitors (rolling windows)

| Signal | Example use |
| ------ | ----------- |
| Rolling PF | Soft reduce if below floor |
| Rolling WR | Soft reduce if collapsing |
| Rolling expectancy | Primary health score |
| Rolling BSL rate | Rising fail share |
| Rolling window DD | Stress (not lifetime peak — clears after recovery) |
| Health 0–100 | high / medium / low / critical ladder |

### Tasks

| ID | Task | Status |
| -- | ---- | ------ |
| `AI3-001` | Rolling windows (last N baskets) | ✅ default N=20 (calibrated) |
| `AI3-002` | Health score 0–100 | ✅ `AI/edge_health.py` |
| `AI3-003` | Soft ladder + stress-confirm pause | ✅ |
| `AI3-004` | Offline: pause before worst DD episodes | ✅ train **3/3** troughs caught |

### Run

```bash
python AI/edge_health.py
# artifacts: AI/data/ai3_report.{json,md} · ai3_shadow.csv · ai3_pause_ids.txt
```

### Results

| Slice | Pause | Pause y_fail | DD / PF effect | Notes |
| ----- | ----- | ------------ | -------------- | ----- |
| Train 2024–25 | ~32% | — | DD 65%→~42% · trough catch **3/3** | Useful death detector on fade years |
| **Validate 2026** | **6.4%** (7) | **14%** · net paused **+$35** | PF 1.36→**1.31** · AI-G1 **FAIL** | Pauses too many winners |

**Why not wire:** Health/pause catches train steamroller stretches, but on the 2026 lock it **over-pauses winners** (approve-by-default violated in practice). Keep as shadow feature for AI5; do not pause live yet.

### Soft action ladder (not binary kill)

| Health | Action |
| ------ | ------ |
| High | Full PRODUCTION behaviour |
| Medium | Trade (caution log) |
| Low / Critical | Pause **new** baskets only with stress confirm (roll_exp<0 & roll_pf<1 + roll_dd/BSL heat) |

Do **not** tighten basket TP/SL here.

### Exit criteria

| Criterion | This run |
| --------- | -------- |
| Catches bad stretches (train) | ✅ 3/3 troughs |
| Limited false pauses / trade budget on validate | ❌ pause quality weak · G1 fail |

---

## AI4 — Edge probability / confidence (permissive)

**ID:** `AI4-PROB`  
**Status:** **Complete (logging-only)** — 2026-07-11 · **not wireable** (`logging_only_weak_rank`)  
**Objective:** Estimate P(hit basket TP) — **secondary** soft signal only.

### Tasks

| ID | Task | Status |
| -- | ---- | ------ |
| `AI4-001` | Train P(TP) model (GBDT / logistic) | ✅ `AI/edge_prob.py` |
| `AI4-002` | Tie-break / mild boost to AI2 (ablations) | ✅ no lift |
| `AI4-003` | Confidence shadow log | ✅ `AI/data/ai4_shadow.csv` |

### Run

```bash
python AI/edge_prob.py --model gbdt
# artifacts: AI/data/ai4_report.{json,md} · ai4_shadow.csv
```

### Results (2026 validate)

| Policy | Skip% | PF | AI-G1 | Note |
| ------ | ----- | -- | ----- | ---- |
| Baseline | 0% | 1.36 | PASS | — |
| AI4 low-P(TP) only | 10% | 1.32 | FAIL | Forbidden elite-style — loser prec 18% |
| AI2 only | 5.5% | 1.40 | PASS | Fragile (from AI2) |
| AI2 ∩ low-P(TP) | 2.7% | 1.31 | FAIL | No assist lift |
| AUC train / val | — | — | — | **0.71 / 0.40** (anti-transfer) |

**Why logging-only:** validate ranking is **worse than chance** (AUC 0.40). AI4-only skip hurts PF; intersection with AI2 does not improve skip quality. Keep scores for AI5 explainability — never “trade only high P(TP)”.

### Threshold philosophy

- Low P(TP) alone is **not** enough to skip unless AI2 also elevated **or** regime is toxic  
- Avoid “only trade confidence ≥ X” modes  

### Exit criteria

| Criterion | This run |
| --------- | -------- |
| Adds lift on top of AI2 | ❌ |
| Else demote to logging-only | ✅ |

---

## AI5 — Decision fusion (soft ensemble)

**ID:** `AI5-FUSION`  
**Objective:** Combine regime + failure + health (+ optional prob) with **approve-by-default**.

### Fusion rule (v1)

```
IF health == Critical           → suspend new baskets
ELSE IF regime in toxic_set
     AND fail_p >= soft_fail_th → skip
ELSE IF fail_p >= soft_fail_th  → skip
ELSE                            → approve   # default
```

Optional later: recovery model votes only mid-basket (AI8).

### Tasks

| ID | Task |
| -- | ---- |
| `AI5-001` | Implement fusion in replay harness |
| `AI5-002` | Ablations: AI2-only vs AI2+regime vs full |
| `AI5-003` | Lock soft thresholds that pass AI-G1 |
| `AI5-004` | Explainability dump per decision (regime, fail_p, health, action) |

### Exit criteria

- Best ablation passes AI-G1 on holdout time split  
- Skip rate within budget  

---

## AI6 — First wire to EA (opt-in)

**ID:** `AI6-WIRE`  
**Objective:** Attach fusion as **optional soft gate** in front of entry — engine untouched.

### Tasks

| ID | Task |
| -- | ---- |
| `AI6-001` | EA input: `InpUseAiGate` (default false) |
| `AI6-002` | Load offline-exported model/thresholds (file or compiled table) |
| `AI6-003` | Shadow mode in demo: log decisions, still trade |
| `AI6-004` | Soft-skip mode only after shadow agreement with offline |
| `AI6-005` | Kill switch + fallback to pure PRODUCTION |

### Exit criteria

- Demo shadow matches offline replay within tolerance  
- Soft-skip mode: metrics not worse than PRODUCTION over agreed window  

**Still no requirement for formal forward-test program** — but demo shadow is the safety net before soft-skip.

---

## AI7 — Retrain loop (keep edge alive)

**ID:** `AI7-RETRAIN`  
**Objective:** Periodically retrain on **recent** baskets so models track regime drift.

### Tasks

| ID | Task |
| -- | ---- |
| `AI7-001` | Rolling dataset policy (e.g. last N months / last K baskets — not all history forever) |
| `AI7-002` | Scheduled offline retrain job |
| `AI7-003` | Holdout check vs previous model (must pass AI-G1 or keep old) |
| `AI7-004` | Model registry + version pin in EA |
| `AI7-005` | Drift alarms: feature distribution / BSL rate / health |

### Policy

```
New model promotes only if offline AI-G1 passes
AND skip-rate budget holds
ELSE keep previous model
```

Forget obsolete regimes gradually; do not hard-delete all history on day one — use weighted / rolling windows.

---

## AI8 — Basket recovery assist (optional, later)

**ID:** `AI8-BASKET`  
**Objective:** Mid-basket P(recovery) to **early-close** only clear doomed baskets — DD tool, not profit tool.

### Caution

Phase 2 rejected RTE and trail. Early close must be **rarer and stricter** than entry skips, or it will recreate those failures.

| ID | Task |
| -- | ---- |
| `AI8-001` | Label recovery vs BSL from mid-basket states |
| `AI8-002` | Offline: early-close only when P(recover) very low |
| `AI8-003` | Compare to BSL-only path — must improve DD without crushing PF |

Promote only if AI-G1 passes with **stricter** skip budget (e.g. ≤5% of baskets early-closed).

---

## AI9 — Light adaptive parameters (optional, bounded)

**ID:** `AI9-ADAPT`  
**Objective:** Tiny regime-conditioned tweaks — **not** free optimization of EMA/TP/SL.

### Allowed (examples)

| Param | Bound |
| ----- | ----- |
| Soft fail threshold | ± small |
| Max new baskets / day when health medium | reduce slightly |
| Cooldown after BSL | 1 → 2 bars max |

### Forbidden without new research program

- Wild EMA period jumps (20 → 18 “because model said so”)  
- Basket TP/SL retune as primary AI output  
- ATR multiplier expansion (already rejected in P2F)  

---

## AI-X — Deferred (vision only)

From [`aiscaleupconcept.md`](aiscaleupconcept.md) — park until AI0–AI7 are stable:

| Vision layer | Defer reason |
| ------------ | ------------ |
| 30–50 fine regimes | Sparse; start AI1 coarse |
| Elite/Good-only ranking | Overfilter risk |
| Market memory k-NN at scale | Infra-heavy; try after AI2 |
| Full RL policy | Needs stable reward + lots of data |
| Aggressive dynamic ADX/TP/SL | Changes engine character |
| Multi-model voting circus | Add only after single failure model works |

---

## Promotion — guardrail bar (replaces “beat 2026” AI-G1)

**Build / iterate** on holdout **2024–2025** (after train **2020–2023**):

| Criterion | Pass |
| --------- | ---- |
| Approve by default | Uncertain → trade |
| Trade count | ≥ **85%** of unfiltered holdout |
| Skip/pause budget | ≤ **15%** |
| Bad-path precision | Skipped/paused mostly losers / BSL · net avoided ≤ 0 |
| Stress | Helps before known DD troughs |
| **Not required** | PF ≥ 2026 PRODUCTION demo baseline |

**Wire to EA (later)** only if:
1. Holdout guardrail bar passes, **and**
2. Optional demo/2026 **shadow** does not starve PRODUCTION (approve-by-default, budget holds).

Legacy name **AI-G1** in older reports meant “beat 2026 PRODUCTION.” That is **retired as the build gate**. `AI/baseline.json` remains the **demo edge freeze**, not the AI school scoreboard.

---

## Suggested build order (practical)

```
AI0  Collect 2020–2025 + split             ← next collect
AI1  Regime atlas on 2020–23 / 2024–25
AI2  Failure guardrail (bad-path precision)
AI3  Health / death pause
AI4  P(TP) logging / tie-break only
AI5  Fusion (approve-by-default)
AI6  Demo shadow → opt-in soft guardrail
AI7  Retrain registry
```

---

## How this maps to “supercharge” metrics

| Metric | How AI helps (without overfilter) |
| ------ | --------------------------------- |
| **Win rate** | Remove a thin tail of failure-path baskets |
| **DD** | Skip / pause when fail_p or health says edge is absent |
| **PF / expectancy** | Same winners kept; fewer −$25 paths |
| **Sharpe** | Smoother equity if bad clusters cut |
| **Edge lifetime** | Health + retrain detect and adapt when edge fades |

What AI should **not** promise: doubling profit by trading less “only elite” setups — or beating the demo PRODUCTION scoreboard as a homework grade.

---

## One-line charter

> **Run PRODUCTION on demo as the edge; build AI as guardrails on 2020–2025 train/holdout; approve by default; skip/pause only clear anti-edge; never replace the engine — and stop treating 2026 demo metrics as the AI build gate.**

---

*Related: [`aiscaleupconcept.md`](aiscaleupconcept.md) · [`System Profile EURUSD.md`](System Profile EURUSD.md) · [`Edge Discovery.md`](Edge Discovery.md)*
