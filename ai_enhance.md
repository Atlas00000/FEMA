# FEMA — AI Enhance (Edge Preservation Layer)

**Status:** Planning · offline-first · not wired to live execution yet  
**Depends on:** Locked EURUSD PRODUCTION stack ([`System Profile EURUSD.md`](System Profile EURUSD.md))  
**Vision source:** [`aiscaleupconcept.md`](aiscaleupconcept.md)  
**Not this project:** Edge discovery, new entries, strategy replacement, aggressive overfiltering  

---

## Philosophy

The execution engine already has the edge. AI does **not** invent buys/sells.

```
PRODUCTION Engine  →  candidate basket / add / hold
         │
         ▼
AI Edge Preservation Layer
         │
    Approve | Soft-skip | Delay | Reduce | Suspend | Adapt
         │
         ▼
    Execution (unchanged logic)
```

**Primary objective:** Know when the edge is present, degrading, or gone — then **protect capital** without starving the engine of its good trades.

**Secondary effects (not the direct target):** higher WR, better PF/Sharpe, lower DD, fewer steamroller-path baskets.

### Hard rules (from Phase 2)

| Rule | Why |
| ---- | --- |
| Engine stays frozen | PRODUCTION entries/exits are validated |
| Prefer **skip bad** over **pick elite** | Overfiltering killed edge (HTF, ATRP70, LDN_NY, CONFIRM) |
| Soft gates, **low** skip rates | Protect, don’t redesign |
| Offline proof before wire | No forward-test dependency for early phases |
| Retrain on rolling data | Keep edge alive as regimes drift |
| Cap signal reduction | e.g. AI may remove ≤10–15% of PRODUCTION candidates |

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

## Soft-gate policy (default everywhere)

AI gates are **failure filters**, not quality lotteries.

| Setting | Default intent |
| ------- | -------------- |
| **Skip only the worst tail** | Top ~10–15% failure-risk candidates |
| **Approve by default** | If uncertain → **trade** (engine edge wins) |
| **Confidence / P(TP) thresholds** | Permissive — block only when P(fail) is clearly elevated |
| **Trade-count budget** | Max −10% to −15% vs PRODUCTION baseline on same window |
| **Promotion (AI-G1)** | Offline: PF ≥ baseline **and** DD ≤ baseline **and** trades ≥ 85% of baseline |
| **No elite-only mode** | Never “Elite/Good only” until proven under AI-G1 |

Example (illustrative — tune offline, do not hardcode early):

```
P(basket hits BSL | features) ≥ 0.55  → soft-skip   # only clear failure risk
P(fail) < 0.55                        → approve     # default = trade
```

Not:

```
P(TP) ≥ 0.85 → trade   # too strict — overfilter
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
**Objective:** Make offline training and replay possible. No model decisions.

### Deliverables

| ID | Deliverable |
| -- | ----------- |
| `AI0-001` | **Basket/trade event log** — every candidate touch, fill, add, basket TP, basket SL, skip reason |
| `AI0-002` | **Feature snapshot at decision time** — EMA geometry, ATR, ADX, level index, spread, session, slope, distance EMA100, recent WR/PF |
| `AI0-003` | **Outcome labels** — hit TP / hit BSL / MAE / MFE / bars alive / max depth |
| `AI0-004` | **Offline dataset builder** — CSV/Parquet from tester + (later) demo logs |
| `AI0-005` | **Replay harness** — apply hypothetical skip masks to PRODUCTION trade list; report PF/WR/DD/trade count |
| `AI0-006` | **Baseline freeze** — PRODUCTION metrics locked as compare target |

### Exit criteria

- Can rebuild a labeled dataset from a full Jan–Jul (or longer) PRODUCTION run  
- Replay harness reproduces baseline when skip-rate = 0  

**No forward testing required.**

---

## AI1 — Regime atlas (coarse, descriptive)

**ID:** `AI1-REGIME`  
**Objective:** Map **few** regimes to historical edge quality — not 30–50 states yet.

### Start with ~6–10 regimes (expand later)

Examples aligned with known FEMA behaviour:

| Regime (coarse) | Expected edge |
| --------------- | ------------- |
| Pullback-in-trend (shallow) | Strong |
| Grinding / slow trend | Good |
| Expansion / impulse | Poor |
| High-ADX / runaway | Poor (partially covered by ADX30) |
| Compression / micro-range | Mixed–good |
| Session-boundary / thin | Elevated fail risk |
| Transition / chop | Mixed |

### Tasks

| ID | Task |
| -- | ---- |
| `AI1-001` | Define regime features + clustering or rule+model hybrid |
| `AI1-002` | Attach per-regime PF, WR, avg W/L, BSL rate, DD contribution |
| `AI1-003` | Publish **regime scorecard** (offline) — which states to soft-avoid |
| `AI1-004` | Set **permissive** regime skip list (only clearly toxic states) |

### Gate policy

- Skip **only** regimes with clear historical PF ≪ 1 **and** material BSL rate  
- If regime uncertain → **allow trade**  
- Target: regime filter alone removes ≤10% of baskets  

### Exit criteria

- Scorecard stable across train/holdout **time splits** (not random shuffle only)  
- Replay: DD ↓ or flat, PF ≥ baseline, trades ≥ 90%  

**Still offline / shadow.**

---

## AI2 — Failure predictor (highest ROI model)

**ID:** `AI2-FAIL`  
**Objective:** Predict **P(basket hits BSL or deep MAE)** at basket start — skip the steamroller path.

This matches Layer 12 in the vision doc and Phase 2’s core lesson: **contain / avoid bad paths**, don’t chase elite winners.

### Tasks

| ID | Task |
| -- | ---- |
| `AI2-001` | Label `y = 1` if basket → BSL or MAE beyond threshold |
| `AI2-002` | Train offline classifier/regressor (start simple: logistic / GBDT) |
| `AI2-003` | Calibrate probabilities; pick **high-recall-on-failures is NOT the goal** — pick **high precision on skips** |
| `AI2-004` | Threshold search under soft policy (skip ≤10–15%) |
| `AI2-005` | Shadow log: would-skip vs actual outcome |

### Threshold philosophy

```
Skip when model is confident this looks like a LOSER path.
Do not require model to be confident this looks like a WINNER.
```

### Exit criteria (offline replay)

| Metric | Pass |
| ------ | ---- |
| Trade count | ≥ 85–90% of baseline |
| PF | ≥ baseline |
| Max DD | ≤ baseline |
| WR | ≥ baseline (expected if skips are true failures) |
| Skipped set | Majority would have been losers (precision on skip) |

---

## AI3 — Edge health monitor

**ID:** `AI3-HEALTH`  
**Objective:** Detect **edge degradation / death** from rolling live-like metrics — reduce participation before large DD.

### Monitors (rolling windows)

| Signal | Example use |
| ------ | ----------- |
| Rolling PF | Soft reduce if below floor |
| Rolling WR | Soft reduce if collapsing |
| Rolling expectancy | Primary health score |
| Rolling BSL rate | Rising fail share |
| Rolling MAE | Path quality |
| Time underwater / recovery | Stress |

### Tasks

| ID | Task |
| -- | ---- |
| `AI3-001` | Define rolling windows (e.g. last N baskets / M days) |
| `AI3-002` | Health score 0–100 (descriptive first) |
| `AI3-003` | Soft actions: normal → caution (fewer adds / higher bar) → pause new baskets |
| `AI3-004` | Offline: would health have paused before worst DD episodes? |

### Soft action ladder (not binary kill)

| Health | Action |
| ------ | ------ |
| High | Full PRODUCTION behaviour |
| Medium | Slightly stricter AI2 threshold only |
| Low | Pause **new** baskets; manage open normally |
| Critical | Full suspend new entries |

Do **not** tighten basket TP/SL here.

### Exit criteria

- Catches known bad stretches in historical replay with limited false pauses  
- False pause rate low enough that trade budget still holds  

---

## AI4 — Edge probability / confidence (permissive)

**ID:** `AI4-PROB`  
**Objective:** Estimate P(hit basket TP) or similarity to historical winners — used as **secondary** soft signal.

### Tasks

| ID | Task |
| -- | ---- |
| `AI4-001` | Train P(TP) or winner-similarity model |
| `AI4-002` | Use as **tie-break / mild boost to AI2**, not standalone elite filter |
| `AI4-003` | Confidence score for logging / explainability |

### Threshold philosophy

- Low P(TP) alone is **not** enough to skip unless AI2 also elevated **or** regime is toxic  
- Avoid “only trade confidence ≥ X” modes  

### Exit criteria

- Adds lift **on top of AI2** in ablation, or is demoted to logging-only  

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

## Promotion gate — AI-G1

Offline (and later demo) compare vs frozen PRODUCTION baseline on the **same** window + holdout:

| Criterion | Pass |
| --------- | ---- |
| Profit factor | ≥ baseline |
| Max DD (bal & eq) | ≤ baseline |
| Win rate | ≥ baseline (preferred) or flat if DD clearly better |
| Trade count | ≥ **85%** of baseline (soft protect, not starve) |
| Skip precision | Skipped set mostly losers / high-BSL |
| Stability | Passes on time-based holdout, not only in-sample |

**Fail AI-G1 → do not wire / do not promote retrain.**

This is intentionally milder on “improvement size” than edge-discovery wild targets: **protect and slightly improve**, don’t chase huge PF jumps.

---

## Suggested build order (practical)

```
AI0  Pipeline + logger + replay          ← do first, fully
AI1  Coarse regime scorecard             ← descriptive
AI2  Failure model + soft threshold      ← main edge protector
AI3  Health monitor                      ← edge-death detector
AI5  Fusion (AI2+AI1+AI3)                ← before wire
AI4  Prob model                          ← only if ablation helps
AI6  Shadow → opt-in soft gate in EA
AI7  Retrain registry
AI8 / AI9  only if still needed
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

What AI should **not** promise: doubling profit by trading less “only elite” setups. That path already failed in Phase 2 filters.

---

## One-line charter

> **Build infra and soft failure/regime/health models offline; approve by default; skip only clear anti-edge; wire only under AI-G1; retrain to keep the PRODUCTION edge alive — never replace it.**

---

*Related: [`aiscaleupconcept.md`](aiscaleupconcept.md) · [`System Profile EURUSD.md`](System Profile EURUSD.md) · [`Edge Discovery.md`](Edge Discovery.md)*
