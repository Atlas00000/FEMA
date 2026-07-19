# Backtesting Guide

**Role:** Systematic design for backtesting FX edges — anti-overfitting process, time splits, curve analysis, and how FEMA applies it.  
**Charter:** MT5 executes · Python scores · Human promotes  
**Updated:** 2026-07-15  
**Related:** [`edge_rediscovery_system.md`](edge_rediscovery_system.md) · [`../AI/kb/gate_rules.json`](../AI/kb/gate_rules.json) · [`../AI/kb/search_map.md`](../AI/kb/search_map.md) · [`../AI/templates/promotion_checklist.md`](../AI/templates/promotion_checklist.md)

> This is **not** a click-by-click MT5 manual. It is the industry-standard **research process** we use to decide whether an edge is real enough to promote — and how to extend FEMA's canonical window model without fooling ourselves.

---

## 1. What backtesting is for (and what it is not)

Backtesting is **hypothesis testing under serial dependence**. It estimates whether a stated market behaviour (the edge) produces positive expectancy after frictions — not whether a parameter set happened to fit past noise.

| Backtesting **is** | Backtesting **is not** |
| --- | --- |
| Evidence that an edge survives time the model never saw | Proof of future profit |
| A filter to reject bad ideas cheaply | A substitute for forward / live validation |
| A way to compare candidates on equal terms | Permission to optimize until the curve looks good |

**FEMA rule:** Strategy Tester runs on **Terminal B only**. Tester CSVs score Discovery; they never feed demo health. Promotion requires G1 + human sign-off — never auto-promote.

---

## 2. Overfitting: the default outcome

If you search long enough, some parameter set **will** fit noise. Overfitting is the default; robustness is what you earn through process.

### 2.1 Sources of overfitting

| Source | Mechanism | FEMA mitigant |
| --- | --- | --- |
| **Parameter search** | Many knobs → knife-edge optimum | Search map: **one axis** per clone; frozen architecture |
| **Multiple comparisons** | Try 50 presets, pick the winner | Lane caps (A≤3, B≤1–2); roster + decision log (no amnesia) |
| **Slice cherry-picking** | Great on 2023 only | `STALE_SLICE` demote rule; canonical window for G1 |
| **Look-ahead / leakage** | Future bar info in signals | Closed-bar logic; HTF confirmation on formed bars |
| **Execution fantasy** | Zero spread, instant fills | Every tick; cost stress as robustness pack |
| **Post-hoc criteria** | "PF 1.4 is good enough" after seeing results | Pre-write success criteria; G1 = PF **and** DD together |

### 2.2 Degrees of freedom budget

Every free `Inp*` parameter increases fit risk. Treat complexity as a cost:

- **Frozen identity:** strategy type, risk %, magic, lot model, grid architecture — not search axes ([`search_map.md`](../AI/kb/search_map.md)).
- **One subsystem per candidate:** if ADX drifted, poke `adx` only — not ADX + session + grid.
- **Prefer plateaus over peaks:** an edge that only works at `InpAdxMax=27` is suspect; a band 25–30 that holds OOS is stronger.

---

## 3. Time structure: how to use multi-year data

Do **not** treat four years as one optimization playground and trust the total PF.

### 3.1 Canonical split (simple baseline)

For a ~4-year research horizon, use **chronological** splits (markets are serial; random shuffles leak regimes):

| Slice | Role | Typical share (4y) | Rules |
| --- | --- | --- | --- |
| **In-sample (IS)** | Develop / coarse tune | ~50–60% (~2–2.5y) | Iterate here only |
| **Validation** | Choose among survivors | ~20–25% (~0.8–1y) | Limited looks; stop when plateau |
| **Holdout (true OOS)** | Final pass/fail | ~20–25% (~0.8–1y) | **One look** — if fail, hypothesis lost |

**Holdout is sacred.** Re-tuning after a holdout fail and re-checking the same holdout converts it into IS. Extend with **new** calendar time or a fresh walk-forward fold.

### 3.2 Walk-forward (stronger than one cut)

Repeat: select on window A → test on the next window B → roll forward.

```text
|-- IS₁ --|-- OOS₁ --|-- IS₂ --|-- OOS₂ --| …
   train      test      train      test
```

**Aggregate all OOS segments** into one stitched walk-forward equity curve. Pass criteria apply to **stitched OOS**, not to the best single OOS month.

| Mode | When to use |
| --- | --- |
| **Anchored IS** | Fixed start date; IS grows — more data, slower to forget old regimes |
| **Rolling IS** | Fixed-length IS window — adapts faster; watch for recent-noise overfit |

For FEMA M5 grid edges, rolling or anchored with **parameter freeze per OOS segment** is standard practice.

### 3.3 Purge / embargo between folds

When train and test are adjacent, leave a **gap** (embargo) if features overlap across bars — e.g. multi-bar grid state, trailing logic, HTF EMA200 confirmation. Prevents label leakage at fold boundaries.

### 3.4 FEMA: two window concepts

FEMA currently operates two distinct window roles. Do not conflate them.

| Window | Current example | Role |
| --- | --- | --- |
| **Canonical lock window** | `2026.01.01`–`2026.07.31` EURUSD M5 | G1 compare vs PRODUCTION; birth certificate; fair A/B ranking |
| **Extended research window** | e.g. 2022–2025 (4y) | Walk-forward, holdout, regime slices — **robustness pack**, not a G1 substitute |

**G1 rule (today):** candidate vs PRODUCTION on the **same** canonical window. A win on 2023-only or 2025-only without canonical parity is a **stale-slice** — demote, do not promote ([`gate_rules.json`](../AI/kb/gate_rules.json) → `STALE_SLICE`).

**Adaptation path:** register extended-window runs in Run KB with distinct `window_hash`; attach walk-forward / holdout notes to promotion checklist; never replace canonical G1 without an explicit policy bump.

---

## 4. Equity curves: what to inspect

A single end PF hides structure. Always inspect **path**, not just **destination**.

### 4.1 Shape diagnostics

| Pattern | Interpretation |
| --- | --- |
| Smooth stair-step with noise | Often healthy if OOS matches |
| One vertical spike then flat | Few lucky trades or one regime — fragile |
| Long flat / underwater stretches | Regime-conditional edge — size and expectations must match |
| IS beautiful, OOS kinked or flat | Classic overfit signature |

### 4.2 Drawdown path

Report **max DD** and **time under water** (duration to recover). A 15% DD recovered in two weeks differs materially from 15% lasting nine months.

For grid systems: clustered losses in the same session/week indicate **concentration risk**, not average edge.

### 4.3 Stability metrics (pick 2–3; do not metric-shop)

| Metric | Use |
| --- | --- |
| Rolling PF / expectancy (3–6 month windows) | Drift detection across calendar |
| Monthly / quarterly P&L heatmap | Lumpy vs consistent |
| Profit concentration (top N trades ÷ net profit) | If top 5 ≈ most profit → fragile |
| Recovery factor / Calmar / ulcer index | Path severity companions to PF |

### 4.4 IS vs OOS overlay

Plot in-sample and out-of-sample on the same scale. Walk-forward: each OOS segment should look like a **weaker cousin** of IS, not a different strategy.

**FEMA data:** basket CSVs + `metrics.json` per `run_id` support rolling views; extended analysis can live in Python notebooks or future scorecard columns — not required for G1 pass, required for **Promote** confidence.

---

## 5. Anti-overfitting test battery

Run after parameters are **frozen** (or frozen per walk-forward segment). These are the industry-standard robustness pack.

### 5.1 Parameter sensitivity (neighbourhood / plateaus)

Perturb each tuned parameter ±10–20% (or adjacent discrete values).

| Result | Verdict |
| --- | --- |
| Wide plateau — neighbours still OOS-positive | Robust |
| Knife-edge — only one exact value works | Likely noise fit |

**FEMA:** Lane A one-axis clones make this tractable — sensitivity sweeps stay within a single `may_adapt_pairs.id`.

### 5.2 Monte Carlo / trade reshuffles

Resample trade order (bootstrap returns) many times → distribution of max DD and terminal equity.

Ask: *How often do we still meet DD/PF constraints?*

Most useful for **path-dependent** systems (grids, compounding). Treat as directional if independence assumptions are weak.

### 5.3 Cost and friction stress

Re-run with **worse** spread, commission, and slippage than broker average.

| Stress | Typical FX retail test |
| --- | --- |
| Base | Every tick, historical spread |
| +1 stress | Spread +0.5–1.0 pip equivalent |
| +2 stress | Spread +1.0–2.0 pip or fixed slippage per fill |

If the edge dies at modest cost inflation, it is not deployable — regardless of headline PF.

**FEMA contract:** $400 · every tick · `ProfitInPips=0` ([`discovery_paths.json`](../ops/tester_queue/discovery_paths.json)). Cost stress = **additional** runs with documented spread override — same preset, worse frictions.

### 5.4 Regime and calendar slices (no cherry-picking)

After freeze, break performance by:

- Trend vs range (ADX / ATR percentile buckets)
- Session (London / NY / Asia)
- High vs low volatility years within the research window
- Known structural breaks (policy shocks, liquidity regimes)

**Purpose:** know **when it fails**, not to drop bad months and inflate the curve. Session-only wins (e.g. X1 NO23: PF 1.477 but DD 19.17%) fail G1 on DD — regime knowledge explains *why*.

### 5.5 Cross-symbol transfer (G3)

An edge claimed as structural should show **related** behaviour on a sibling symbol with **same logic, minimal retune**.

| Outcome | Interpretation |
| --- | --- |
| Same sign of expectancy, softer metrics | Acceptable transfer |
| Total failure everywhere else | EURUSD-specific fit (or data artifact) |

**FEMA G3 (current):** PF ≥ 1.2 on ≥2 symbols — **fail** on GBPUSD (0.80). EURUSD-only deploy until G3 passes.

### 5.6 Sample size floor

| Timeframe | Rule of thumb |
| --- | --- |
| M5 discretionary / grid | Prefer **hundreds** of trades in OOS |
| Dozens of trades | High uncertainty — smaller size or extend window |

PRODUCTION birth: **424 trades** on canonical window — use as reference for minimum credible sample on comparable horizons.

---

## 6. Biases to design against (MT5-relevant)

| Bias | Symptom | Mitigant |
| --- | --- | --- |
| Look-ahead | Mid-bar fills on bar-close signals | Signal on closed bars; realistic fill model |
| Survivorship | Only test symbols that already look good | Pre-commit symbol list |
| Data-snooping | 200 presets → pick winner | Pre-register axes; candidate budget; holdout once |
| In-sample overfit | Optimize on full history | Time splits + walk-forward |
| Execution fantasy | Fixed tiny spread, instant grid fills | Every tick; cost stress |
| Stale-slice win | Great PF on wrong calendar slice | Canonical window for G1; `STALE_SLICE` demote |
| Compounding tricks | Curve shaped by deposit path | Report fixed-lot or risk-normalized equity |

MT5 Strategy Tester is infrastructure. **Scientific process lives outside the green "Passed" report.**

---

## 7. FEMA backtesting workflow (gates, not one run)

```text
Hypothesis + frozen architecture
        ↓
Define success criteria (PF + DD + trade count + stability) — BEFORE results
        ↓
IS development (extended window) — coarse search, reject non-plateaus
        ↓
Validation selection — 1–3 survivors, not 30
        ↓
Holdout OR stitched walk-forward OOS — pass/fail vs criteria
        ↓
Robustness pack — sensitivity · cost stress · regime breakdown · optional MC
        ↓
Canonical window run (Terminal B) — register run_id → G1 vs PRODUCTION
        ↓
Optional G3 cross-symbol
        ↓
Promotion checklist + human sign-off — never auto-promote
        ↓
Forward / demo / small live — backtest does not graduate itself
```

### 7.1 Discovery loop mapping

| Phase | Backtesting guide section | FEMA artifact |
| --- | --- | --- |
| Hypothesis | §2, §7 | System Profile · search map axis |
| Candidate generation | §2.2 | Factory clone · one axis |
| Tester execution | §6 | Terminal B · `discovery_paths.json` |
| Fair compare | §3.4 | Canonical window · G1 |
| Robustness | §5 | Walk-forward note on checklist |
| Transfer | §5.5 | G3 gate |
| Promote | §8 | `promotion_checklist.md` · decision log |

### 7.2 Lane A vs Lane B

| Lane | Backtest intent |
| --- | --- |
| **A — Localized** | Repair fade on PRODUCTION neighbourhood; same canonical window; one axis |
| **B — Challenger** | Hunt outside lock neighbourhood; roster profiles; same G1 rail |

Both lanes: identical tester contract, identical canonical window for G1, human promote only.

### 7.3 What G1 does and does not prove

| G1 proves | G1 does not prove |
| --- | --- |
| Beat PRODUCTION on PF **and** DD on same window | Edge works on unseen years (holdout) |
| Fair ranking of candidates this cycle | Parameter neighbourhood is wide |
| DD discipline (win rate alone insufficient) | Cross-symbol validity (see G3) |

G1 is necessary, not sufficient. **Promote** requires G1 + robustness evidence + human checklist.

---

## 8. Promotion readiness checklist (extended)

Use [`promotion_checklist.md`](../AI/templates/promotion_checklist.md) as the minimum bar. For full confidence, attach:

### 8.1 Required (current)

- [ ] Same tester contract ($400 · every tick · ProfitInPips=0)
- [ ] **G1:** PF ≥ PRODUCTION **and** max DD ≤ PRODUCTION
- [ ] Not stale-slice-only
- [ ] One subsystem diff
- [ ] KB + human sign-off

### 8.2 Robustness (recommended before Promote)

- [ ] **Walk-forward or holdout:** stitched OOS PF/DD vs pre-written hurdles — or explicit N/A with reason
- [ ] **Sensitivity:** ±10–20% on tuned key(s) — plateau note
- [ ] **Cost stress:** +0.5–1 pip equivalent — still acceptable PF/DD
- [ ] **Regime note:** which sessions/regimes carry edge vs bleed
- [ ] **Profit concentration:** top-5 trades as % of net — flag if >50%
- [ ] **Trade count:** OOS segment ≥ credible floor for timeframe

### 8.3 Forbidden (unchanged)

- Promote because AI says so
- Live param change without new Discovery cycle
- Auto-promote
- Stale-slice promote

---

## 9. Reading a "4-year success" vs failure

### 9.1 Credible multi-year story

- Positive expectancy on **stitched OOS / holdout**, not only full-sample IS
- Equity trends with noise; not one regime spike
- Parameter neighbours still alive under sensitivity
- Survives realistic cost inflation
- Drawdowns explainable (vol clusters), not mysterious
- Enough trades for the claim
- Optional: sibling symbol shows related behaviour

### 9.2 Weak multi-year story (reject or Alternate)

- Optimized on all four years, "validated" on the same chart
- 80% of profit from one quarter
- Only one magic parameter value works
- Dies when spread +1 point
- Monthly returns flip sign every other quarter with no regime rule
- Beats PRODUCTION on PF but breaches DD (see Candidate_X1)

---

## 10. Adapting this guide into the system

This section is the **implementation backlog** — process is defined here; automation can follow.

| Capability | Status | Target |
| --- | --- | --- |
| Canonical G1 on lock window | **Live** | `gate_rules.json` · `scorecard.ps1` |
| Stale-slice demote | **Live** | `STALE_SLICE` in gate rules |
| One-axis containment | **Live** | `search_map.json` · factory validate |
| Extended window registration | Partial | Run KB `window_hash` supports any dates |
| Walk-forward scorecard column | **Gap** | Add OOS PF/DD to morning pack |
| Sensitivity enqueue | **Gap** | ±recipe variants as linked runs |
| Cost stress preset | **Gap** | `tester_defaults.spread_stress` sibling ini |
| Regime breakdown from baskets | **Gap** | Python slice by session/ADX from CSV |
| G3 multi-symbol queue | **Gap** | G3 fail documented; GBPUSD re-test when ready |
| MC from basket P&L | **Gap** | Optional `fema_ops` robustness module |

**Policy principle:** new gates (G4 walk-forward, G5 cost stress) should be **additive** — fail robustness → Alternate or Reject, not auto-promote bypass.

---

## 11. Quick reference

### Tester contract (Terminal B)

| Field | Value |
| --- | --- |
| Symbol / TF | EURUSD M5 |
| Model | Every tick (model 0) |
| Deposit | $400 |
| Leverage | 500 |
| ProfitInPips | 0 |
| Canonical window | 2026.01.01 – 2026.07.31 |

### G1 bar (vs PRODUCTION lock)

| Metric | Rule |
| --- | --- |
| Profit factor | ≥ 1.36 |
| Max DD (balance %) | ≤ 18.0 |
| Window | Same as production benchmark |

### Time split template (4-year research)

```text
2022.01 – 2023.06   IS      (~18 mo)
2023.07 – 2024.06   VAL     (~12 mo)
2024.07 – 2025.12   HOLD    (~18 mo)   ← one look
2026.01 – 2026.07   CANON   G1 vs lock ← FEMA canonical
```

Adjust boundaries to market events; keep chronology; document in run metadata.

### Mental model

```text
Backtest → filter bad ideas
Walk-forward → filter time-overfit ideas
Cost stress → filter fantasy execution
G1 → filter worse-than-lock candidates
Human → filter everything else
Live → final filter
```

---

## Related paths

| Path | Role |
| --- | --- |
| [`edge_rediscovery_system.md`](edge_rediscovery_system.md) | Discover-plane overview |
| [`dual_lane_rediscovery_pipeline.md`](dual_lane_rediscovery_pipeline.md) | Lane A/B MVP |
| [`../AI/kb/gate_rules.json`](../AI/kb/gate_rules.json) | G1–G3 promotion gates |
| [`../AI/kb/search_map.md`](../AI/kb/search_map.md) | One-axis containment |
| [`../AI/templates/promotion_checklist.md`](../AI/templates/promotion_checklist.md) | Promote minimum bar |
| [`../ops/tester_queue/discovery_paths.json`](../ops/tester_queue/discovery_paths.json) | Terminal B tester defaults |
| [`../AI/kb/runs/README.md`](../AI/kb/runs/README.md) | Run ID + window hash |
| [`../AI/certificate_PRODUCTION_EURUSD.json`](../AI/certificate_PRODUCTION_EURUSD.json) | Lock birth metrics |
