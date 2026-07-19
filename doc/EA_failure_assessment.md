# FEMA EURUSD — Weaknesses, Failure Profile & Loss Assessment

**Role:** Operator-facing forensic summary of how the edge fails — raw DNA, PRODUCTION residual risk, and what ERG rediscovery could / could not fix.  
**Status:** Post ERG-P7 · **Reject** ADX28 · PRODUCTION lock unchanged  
**Updated:** 2026-07-16  
**Sources:** [`baseline_profile.md`](baseline_profile.md) · [`ERG_P0_baseline_pack.md`](ERG_P0_baseline_pack.md) · [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md) · [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) · ERG-P1…P5 packs · [`../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md`](../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md)

> This is **not** a promote brief. It is a map of structural risk so operators know what the EA will still do when the pullback thesis is wrong.

---

## 0. Executive one-liner

FEMA on EURUSD is a **high-frequency small-TP harvest** that is **structurally short volatility expansion**. Wins are many and tiny (~$2–11 basket); losses are fewer but **fat-tailed** until capped. PRODUCTION (BSL $25 + ADX&lt;30) contains the steamroller enough to lock on 2026 — it does **not** remove the failure mode. Rediscovery proved most “quality” overlays either **do nothing**, **clip winners**, or **worsen drawdown**.

```text
Edge shape:   pennies from pullback grids
Failure mode: steamroller when pause ≠ pause (trend expansion / thin book)
Containment:  BSL25 + ADX30 (PRODUCTION) — mandatory, not optional
```

---

## 1. Weaknesses (structural)

### 1.1 Philosophy-level

| Weakness | Why it matters |
| --- | --- |
| **Assumes pullbacks revert** | Edge dies when M5 bias becomes a sustained expansion |
| **Optimises WR, not R-multiple** | Avg win ≪ avg loss even when “healthy” (~2.7 vs ~5 under BSL) |
| **No per-leg stop** | Risk is basket-only; depth adds exposure into the wrong move |
| **Fixed micro-lot, fixed $ TP/SL** | Dollar risk does not scale with ATR expansion; path risk still can stack |
| **EURUSD-specific** | Same stack on GBPUSD → G3 fail (PF ~0.80) — not a portable “grid alpha” |

### 1.2 Edge mechanics

| Layer | Weakness |
| --- | --- |
| **Grid deepen** | Against-move fills increase size into failure (steamroller fuel) |
| **Basket TP $10** | Caps upside; low Corr(profit, MFE) — leaves excursion on table by design |
| **ADX gate** | Binary; plateau is fragile (28 helped 2021–25, **hurt** canon vs ADX30 lock) |
| **Session / calendar toxins** | Hour **23**, **Tuesday**, **December** concentrate loss mass (raw histograms) |
| **Hold time** | Raw bag-holds to ~297d; even contained stacks average ~16–21h with multi-day tails |

### 1.3 What we tried and could not fix (ERG)

| Axis | Probe | Outcome | Weakness exposed |
| --- | --- | --- | --- |
| Containment | BSL20/25/30, MaxBars | **BSL25** centre; MaxBars reject | Time-stop churns; too-tight BSL wrecks path |
| Regime | ADX25/28/30, BrkSus, ATRP70 | **ADX28** wins research; **fails G1** | Regime gate is window-sensitive |
| Exit | Trail70, TP±20%, MaxBars | All reject | Trail clips AvgW; TP plateau locked at 10 |
| Entry | RSI, Candle | RSI **no-op**; Candle **DD×2** | Prior-bar colour wrong gate; default RSI inert |
| Canon | ADX28 vs PRODUCTION | **Reject** | Research win ≠ promote win |

**Residual weakness after PRODUCTION:** still a **negative payoff asymmetry** (lose ~2× what you win per trade) that must be offset by win rate + regime filter. Any filter that lowers WR without cutting steamrollers **fails**.

---

## 2. Failure profile

### 2.1 Canonical failure hypothesis

> When a pullback **does not revert** (trend expansion, breakout, thin liquidity), the grid **adds depth**, equity sinks with MAE, and without hard containment the exit is a **fat tail**. Classic **pennies in front of a steamroller**.

Evidence signature:

| Signal | Raw P1 2021–25 | Meaning |
| --- | ---: | --- |
| Corr(profit, MAE) | **0.76** | Adverse path ≈ outcome |
| Corr(profit, MFE) | **0.15** | Winners do not scale with favorable excursion |
| AvgW / AvgL | +2.60 / **−26.61** | ~10× asymmetry before BSL |
| Largest loss | **−$152** | Single path ≫ weeks of TPs |
| Max hold | **~297d** | Losers nursed until recover or ruin |

### 2.2 Failure taxonomy

| Class | Trigger | Path | Exit (raw) | Exit (PRODUCTION) |
| --- | --- | --- | --- | --- |
| **A. Steamroller** | Expansion vs bias | Deep grid · MAE → −$100s | Bag-hold / test end | Basket SL **−$25** |
| **B. Regime miss** | ADX already hot / rising | Entries into doomed chop→trend | Same as A | ADX≥30 blocks **new** entries (open basket still at risk) |
| **C. Session toxin** | Hour 23 / thin book | Gap / spike / rollover | Fat loss cluster | **Unblocked** in PRODUCTION (known residual) |
| **D. Calendar cluster** | December / Tue spikes | Correlated episode DD | Consecutive-loss DD mass | Partially mitigated by A+B only |
| **E. Clip / churn** | Bad “quality” overlays | Fewer good fills or early exits | Trail / candle / MaxBars | Rejected — do not re-enable blindly |

### 2.3 Stack comparison (failure behaviour)

| Stack | PF / DD (context) | Failure behaviour |
| --- | --- | --- |
| **P1-BASELINE** (no BSL/ADX) | 2021–25: PF 2.21 · DD **36%/41%** · 2026: PF **0.17** · DD **66%** | Unbounded MAE; headline PF can lie |
| **BSL25 only** | Research ~PF 1.02 · DD ~35% | Caps loss size; still too many steamroller *entries* |
| **PRODUCTION** BSL25+ADX30 | Canon PF **1.36** · DD **18%/21%** | Contained enough to lock; residual toxins remain |
| **ADX28 research** | 2021–25: PF 1.14 · DD 21.6% · Canon: PF **1.21** · DD **24.6%** | Better multi-year DD; **fails G1** vs lock |

### 2.4 Operator-visible failure signs

- Equity stair-steps down on a **cluster of −$25** basket SLs (healthy containment) vs a **smooth multi-day underwater** bag (BSL off / misconfigured).
- Journal missing `adx_gate=on` / `bsl=25` → you are **not** running PRODUCTION.
- WR stays high (~70%) while Net stagnates → **asymmetry tax**, not “broken entries.”
- June / Dec / hour-23 histograms light up red → toxin season, not random noise.

---

## 3. Loss assessment

### 3.1 Raw edge (P1-BASELINE · 2021–2025) — authority for DNA

| Metric | Value | Assessment |
| --- | ---: | --- |
| Loss deals | **29 / 687** (~4.2%) | Rare but dominate risk |
| Gross loss vs gross profit | −772 / +1708 | Losers ≈ **31%** of two-way mass |
| Avg / largest loss | **−26.61 / −152** | Fat tail; one loss ≈ **~58** avg wins |
| Balance / equity DD | **36% / 41%** | Unsuitable for deploy |
| Steamroller-path MAE (TP survivors) | to **−$395** | Paths go nuclear before rare recovery |

**Loss mass concentration (report toxins):** hour **23** · weekday **Tuesday** · month **December**.

### 3.2 Contained edge (PRODUCTION · canon 2026.01–07.31)

| Metric | Lock | Assessment |
| --- | ---: | --- |
| PF / Net | **1.36 / +$221** | Pass G1 bar |
| DD bal / eq | **18% / 21%** | Acceptable for lock — not “safe” |
| Typical trade shape | AvgW ~$2.7 · AvgL ~$5 · WR ~70% | Still **lose bigger than win**; WR carries expectancy |
| Risk unit | Basket SL **−$25** | Hard cap per failure episode |

### 3.3 Research survivor that failed promote (ADX28 · same canon)

| Metric | ADX28 | vs PRODUCTION |
| --- | ---: | ---: |
| PF | 1.21 | −0.15 |
| Net | +147.86 | −$73 |
| DD bal / eq | 24.6% / 27.3% | +6.6pp / +6pp |
| Trades | 443 | slightly more churn |

**Assessment:** Tighter ADX improved multi-year research DD but **increased canon drawdown and cut PF**. Loss control is **not monotonic** in AdxMax — plateau must be re-proven on the promote window.

### 3.4 Loss math operators should internalise

Under PRODUCTION-like payoff (~AvgW 2.7, AvgL 5.1, WR 70%):

```text
E[trade] ≈ 0.70×2.7 + 0.30×(−5.1) ≈ +0.36   (thin but positive)
Breakeven WR ≈ |AvgL| / (AvgW+|AvgL|) ≈ 5.1/7.8 ≈ 65%
```

A **5pp WR drop** without shrinking AvgL → expectancy ≈ flat/negative. That is why Candle (WR↓ + DD↑) and Trail (AvgW↓) failed: they tax the only thing paying for fat losses — **hit rate on small TPs**.

### 3.5 Capital / DD framing ($400 lock contract)

| Event | Approx equity hit |
| --- | --- |
| One BSL hit | −$25 ≈ **6.25%** of $400 |
| ~3 clustered BSL | ~**19%** — near lock DD budget |
| Raw steamroller (−$152) | **~38%** single path — why BSL is mandatory |
| Raw MAE path (−$395) then TP | Account stress **before** headline “win” |

---

## 4. What is *not* the weakness (avoid false fixes)

| Tempting story | Evidence against |
| --- | --- |
| “Need tighter TP” | TP8 failed (research DD blew out) |
| “Need wider TP / trail to catch MFE” | TP12 / Trail70 failed; MFE corr stays low by design |
| “Need candle / RSI quality” | RSI inert; Candle wrecked DD |
| “Need MaxBars instead of BSL” | MaxBars worse path than BSL25 |
| “ADX28 is strictly better” | Wins 2021–25 · **fails** 2026 G1 |
| “Port to GBPUSD” | G3 fail |

---

## 5. Residual risk register (PRODUCTION live)

| ID | Risk | Severity | Mitigation today | Open? |
| --- | --- | --- | --- | --- |
| R1 | Clustered −$25 SL sequence | High | ADX gate · operator pause policy | Yes — monitor |
| R2 | Hour-23 / rollover toxin | Med | None in lock (NO23 near-miss historically) | Optional new Discovery |
| R3 | December / calendar cluster | Med | None dedicated | Easy to overfit — deferred |
| R4 | ADX plateau drift | Med | Locked at 30; 28 rejected on canon | Do not retune casually |
| R5 | Symbol portability | High | EURUSD-only deploy | Hard rule |
| R6 | Telemetry gap (Agent baskets) | Low/ops | Trust MT5 deal report for P&L | Ops hygiene |
| R7 | Thin expectancy | Med | Do not add winner-clipping exits | Discipline |

---

## 6. Bottom line

| Question | Answer |
| --- | --- |
| What is the EA bad at? | Surviving **trend expansion** and **thin-session shocks** without containment |
| How do losses look? | Few, **large vs wins**, MAE-driven, often clustered by hour/weekday/month |
| What fixed the worst? | **Basket SL $25 + ADX&lt;30** (PRODUCTION) |
| What did ERG add? | Confirmation that exits/entries beyond the lock **don’t upgrade** G1; ADX28 is research-only |
| Deploy posture | **EURUSD PRODUCTION only** · treat DD budget as real · optional toxin hunts as *new* threads, not nostalgia |

**Related:** [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) · [`ERG_P0_baseline_pack.md`](ERG_P0_baseline_pack.md) · [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md) · [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) · thesis [`failureimprove.md`](failureimprove.md) · adaptive phases [`adaptive_selection_phases.md`](adaptive_selection_phases.md) (`ASI-P0` adopted · next `ASI-P1`)
