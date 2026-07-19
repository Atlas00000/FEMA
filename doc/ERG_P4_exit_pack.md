# ERG-P4 — Exit & trade management · test pack

**Phase:** ERG-P4 · **axis:** `basket_exit`  
**Status:** ERG-P4 **closed** · MaxBars/TP8/TP12/Trail70 all **fail as upgrades** · centre = **ADX28 + TP10**  
**Parent:** [`ERG_P3_adx_ADX28_01.set`](../Presets/ERG_P3_adx_ADX28_01.set)  
**Prior:** [`ERG_P3_regime_pack.md`](ERG_P3_regime_pack.md) · Plan: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md)

> Shape exits **after** BSL25 + ADX28. One axis per load. Prior Trail50/RTE failed G1 — Trail70 is a **new** thesis (later activate). MaxBars optional/low priority (failed on BSL-only in P1).

---

## Stack so far (do not undo)

```text
P1-BASELINE → BSL25 (P1 centre) → ADX28 (P3 centre) → P4 exit probes
Rejected: BSL20/30 · MaxBars* · ADX25/30 · BrkSus · ATRP70 · Trail70 · TP8 · TP12
```

**BSL:TP reference (ERG-P4-04):** **2.5:1** (25/10) **locked** — TP8/TP12 failed.

---

## Presets (load order)

| Order | File | Task | Diff vs ADX28 |
| --- | --- | --- | --- |
| **1st** | [`ERG_P4_bexit_Trail70_01.set`](../Presets/ERG_P4_bexit_Trail70_01.set) | **ERG-P4-02** | Trail on · activate **70%** · giveback 50% |
| 2nd | [`ERG_P4_bexit_TP8_01.set`](../Presets/ERG_P4_bexit_TP8_01.set) | ERG-P4-03 | `InpBasketTp=8` |
| 2nd | [`ERG_P4_bexit_TP12_01.set`](../Presets/ERG_P4_bexit_TP12_01.set) | ERG-P4-03 | `InpBasketTp=12` |
| last | [`ERG_P4_bexit_MaxBars480_01.set`](../Presets/ERG_P4_bexit_MaxBars480_01.set) | ERG-P4-01 | MaxBars=480 only — **optional / caution** |

**Load path:**  
`C:\Users\emili\AppData\Roaming\MetaQuotes\Terminal\158041E5204719DC59E8E86EAAE9D56B\MQL5\Profiles\Tester\`

Tester: EURUSD M5 · Every tick · $400 · ProfitInPips=0 · same multi-year window as P3 for compare, then canon later.

---

## Pass screen (vs ADX28 parent)

| Gate | Threshold |
| --- | --- |
| vs ADX28 | PF **↑** and/or DD **↓** (both preferred); must not wreck research DD≤25% |
| Anti-goal | Trail must not cut avg win hard while DD stays same/worse |
| BSL:TP | Document ratio; prefer stay near **2.5:1** unless clearly better |
| Canon later | G1 on survivors only |

ADX28 baseline (research): PF **1.14** · DD **21.6%/23.5%** · Net **+430** · WR **68%**

---

## Scorecard

| Preset | Window | PF | DD% | vs ADX28 | Decision |
| --- | --- | --- | --- | --- | --- |
| Trail70_01 | ~2021–2025 | **1.15** | **24.5 / 25.3** | PF↑ slight · DD **worse** · AvgW **clipped** | **fail_is** as upgrade |
| TP8_01 | ~2021–2025 | **1.04** | **50.8 / 53.8** | PF↓ DD **worse** | **fail_is** · reject tighter TP |
| TP12_01 | ~2021–2025 | **0.96** | **67.6 / 70.8** | PF↓ DD **worse** | **fail_is** · reject wider TP |
| MaxBars480_01 | ~2021–2025 | **1.05** | **43.6 / 44.7** | PF↓ DD **worse** | **fail_is** · reject |

### Result — `ERG_P4_bexit_Trail70_01` (2026-07-16)

```text
Preset: ERG_P4_bexit_Trail70_01  (ADX28 + Trail activate 70% / giveback 50%)
Window: multi-year from 2021 (MT5 report)
Trades: 2312   WR: 72.23%   PF: 1.15   Net: +466.61
DD bal / eq: 24.50% / 25.25%
Avg win / avg loss: +2.11 / -4.77   ratio: 2.26×
Largest W/L: +10.03 / -12.69
RF: 1.73   Sharpe: 1.35
Hold avg: ~12.7h · max ~144h  (ADX28 max was ~379h)
vs ADX28: PF 1.14→1.15 · Net +430→+467 · DD 21.6%→24.5% · AvgW 2.74→2.11 · WR 68%→72%
Decision: fail_is as upgrade (anti-goal: clips wins, DD not improved)
Next: Close P4 · research centre stays ADX28 · canon G1
```

**Screen vs ADX28 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat ADX28 DD | DD ≤ 21.6% | **24.5%** | **FAIL** |
| Research DD ≤ 25% | ≤25% bal | **24.5%** bal · **25.3%** eq | **PASS bal / border eq** |
| PF↑ | preferred | **+0.01** | weak |
| Anti-goal (don’t clip AvgW while DD worse) | AvgW intact | **2.74→2.11** | **FAIL** |

**Read:** Late trail raises WR and slightly lifts PF/Net by banking earlier, but **cuts average wins ~23%** and **worsens DD** vs clean ADX28 — Trail50-family failure with a softer surface. Not a promote add-on.

### ERG-P4 final

| Keep | Reject |
| --- | --- |
| **ADX28 + BSL25 + TP10** (no trail, no MaxBars) | Trail70, TP8, TP12, MaxBars480 |

### TP plateau (ERG-P4-03 / P4-04) — closed

| | TP8 | **ADX28 TP10** | TP12 |
| --- | ---: | ---: | ---: |
| PF / Net | 1.04 / +140 | **1.14 / +430** | 0.96 / −148 |
| DD bal | 50.8% | **21.6%** | 67.6% |
| WR / AvgW | 70% / 2.29 | **68% / 2.74** | 61% / 3.17 |
| BSL:TP | 3.125:1 | **2.5:1** | ~2.08:1 |

**ERG-P4-04:** Keep **2.5:1** (25/10). Both ±20% TP probes fail research path.

### Result — `ERG_P4_bexit_TP12_01` (2026-07-16)

```text
Preset: ERG_P4_bexit_TP12_01  (ADX28 + BasketTp=12)
Window: multi-year from 2021 (MT5 report)
Trades: 1650   WR: 61.45%   PF: 0.96   Net: -147.59
DD bal / eq: 67.60% / 70.81%
Avg win / avg loss: +3.17 / -5.29   ratio: 1.67×
Largest W/L: +12.07 / -13.61
BSL:TP = 25/12 ≈ 2.08:1
Hold avg: ~20h · max ~364h
vs ADX28: PF 1.14→0.96 · Net +430→-148 · DD 21.6%→67.6% · trades ↓ · WR ↓
Decision: fail_is
Next: Trail70_01 only remaining P4 probe; else close P4 on ADX28+TP10
```

**Screen vs ADX28 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat ADX28 DD | DD ≤ 21.6% | **67.6%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **67.6%** | **FAIL** |
| PF↑ | preferred | **0.96** | **FAIL** |

**Read:** Wider TP raises avg win but **misses more targets**, cuts WR, and lets baskets live longer underwater → DD blows out. Mirror image of TP8. Harvest point stays at **$10**.

### Result — `ERG_P4_bexit_TP8_01` (2026-07-16)

```text
Preset: ERG_P4_bexit_TP8_01  (ADX28 + BasketTp=8)
Window: multi-year from 2021 (MT5 report)
Trades: 2176   WR: 69.85%   PF: 1.04   Net: +140.07
DD bal / eq: 50.84% / 53.79%
Avg win / avg loss: +2.29 / -5.09   ratio: 2.22×
Largest W/L: +8.03 / -12.69
BSL:TP = 25/8 = 3.125:1  (broke 2.5:1 reference — tighter)
vs ADX28: PF 1.14→1.04 · Net +430→+140 · DD 21.6%→50.8% · WR 68%→70% · AvgW 2.74→2.29
Decision: fail_is
Next: TP12_01 then Trail70_01 — keep TP10 on ADX28 unless TP12 wins
```

**Screen vs ADX28 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat ADX28 DD | DD ≤ 21.6% | **50.8%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **50.8%** | **FAIL** |
| PF↑ | preferred | **1.04 &lt; 1.14** | **FAIL** |
| BSL:TP near 2.5:1 | ~2.5 | **3.125** | **broken / worse** |

**Read:** Tighter TP buys a bit of WR and smaller avg wins, but **path collapses** — more churn (2176 trades) and DD &gt;2× ADX28. Confirms harvest reliability lives near **TP10**, not scalping the basket harder.

### Result — `ERG_P4_bexit_MaxBars480_01` (2026-07-16)

```text
Preset: ERG_P4_bexit_MaxBars480_01  (ADX28 + MaxBars=480)
Window: multi-year from 2021 (MT5 report)
Trades: 2209   WR: 63.74%   PF: 1.05   Net: +173.91
DD bal / eq: 43.57% / 44.68%
Avg win / avg loss: +2.60 / -4.34   ratio: 1.67×
Largest L: -12.69
Hold: avg ~14h · max ~49h  (ADX28 max was ~379h — clock works)
vs ADX28: PF 1.14→1.05 · Net +430→+174 · DD 21.6%→43.6% · trades 1943→2209
Decision: fail_is
Next: Do not keep MaxBars · run Trail70_01 / TP probes
```

**Screen vs ADX28 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat ADX28 DD | DD ≤ 21.6% | **43.6%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **43.6%** | **FAIL** |
| PF↑ | preferred | **1.05 &lt; 1.14** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **1.67×** | **PASS** |

**Read:** MaxBars on ADX28 **does** cut bag-hold (max hold ~49h vs ~379h) but **churns more trades** and **doubles DD** vs the clean ADX28 path — same failure mode as P1 MaxBarsBSL. Time-stop is not an upgrade over BSL+ADX28. **Reject** for this cycle; keep ADX28 exit identity (TP10 / no MaxBars / trail TBD).

```text
Preset: ERG_P4_bexit_…
Window: …
Trades: …   WR: …   PF: …   Net: …
DD bal / eq: … / …
Avg win / avg loss: … / …
vs ADX28: PF Δ …  DD Δ …  AvgW Δ …
Decision: pass_is | fail_is | skip
Next: …
```

---

## After P4

- **P4 closed.** No exit probe beats ADX28+TP10 on research window  
- **Canon G1:** ADX28 **fail_g1** — keep **PRODUCTION** ([`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md))  
- Do not restack rejected MaxBars / trail / TP±20% / P3 rejects / P5 entry filters
