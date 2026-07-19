# ERG-P3 — Regime detection (ADX) · test pack

**Phase:** ERG-P3 · **axis:** `adx` (then `regime_extra`)  
**Status:** ERG-P3 **complete** · winner = **ADX28** · BrkSus/ATRP70/ADX25/30 **reject**  
**Parent:** [`ERG_P1_bexit_BSL25_01.set`](../Presets/ERG_P1_bexit_BSL25_01.set) (BSL25 centre — MaxBars rejected)  
**Prior:** [`ERG_P1_containment_pack.md`](ERG_P1_containment_pack.md) · Plan: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md)

> Skip steamroller regimes. **One axis per load.** No MaxBars. No session mash.

---

## Presets (load order)


| Order | File | Task | Diff |
| --- | --- | --- | --- |
| **1st** | [`ERG_P3_adx_ADX30_01.set`](../Presets/ERG_P3_adx_ADX30_01.set) | **ERG-P3-01** | BSL25 + `InpUseAdxGate=true` (max 30) |
| 2nd | [`ERG_P3_adx_ADX28_01.set`](../Presets/ERG_P3_adx_ADX28_01.set) | ERG-P3-02 | AdxMax=**28** |
| 2nd | [`ERG_P3_adx_ADX25_01.set`](../Presets/ERG_P3_adx_ADX25_01.set) | ERG-P3-02 | AdxMax=**25** (often hurts — plateau bound only) |
| 3rd | [`ERG_P3_regime_BrkSus_01.set`](../Presets/ERG_P3_regime_BrkSus_01.set) | ERG-P3-03 | Breakout suspend on BSL25 (**ADX off**) — after ADX scored |
| last | [`ERG_P3_regime_ATRP70_01.set`](../Presets/ERG_P3_regime_ATRP70_01.set) | ERG-P3-04 | ATR%70 on BSL25 — last resort |

**Note:** `ERG_P3_adx_ADX30_01` ≡ PRODUCTION keys on research window (BSL25+ADX30). Compare to BSL25 multi-year and later canonical G1.

---

## How to run (Terminal B)

**Load path:**  
`C:\Users\emili\AppData\Roaming\MetaQuotes\Terminal\158041E5204719DC59E8E86EAAE9D56B\MQL5\Profiles\Tester\`

1. Inputs → Load **`ERG_P3_adx_ADX30_01`**  
2. EURUSD M5 · Every tick · $400 · ProfitInPips=0  
3. Start **IS** `2021.01.01`–`2022.12.31` if possible; else same multi-year window as P1 for apples-to-apples vs BSL25  
4. Journal: `adx_gate=on` · `bsl=25`  
5. Score vs BSL25 parent (below) before ADX28/25

---

## Pass screen (vs BSL25 parent)

| Gate | Threshold |
| --- | --- |
| vs BSL25 | PF **↑** and/or DD **↓** (both preferred) |
| Research DD | Aim ≤ **25%** bal (frozen P0); must beat BSL25’s **35.3%** |
| avgL/avgW | Stay ≤ **6×** |
| Canonical later | G1: PF≥1.36 · DD≤18% on `2026.01.01–2026.07.31` |

---

## Scorecard

| Preset | Window | PF | DD% | vs BSL25 | Decision |
| --- | --- | --- | --- | --- | --- |
| ADX30_01 | ~2021–2025 | **1.02** | **47.9 / 50.1** | PF flat · DD **worse** | **fail_is** · not plateaucentre |
| ADX28_01 | ~2021–2025 | **1.14** | **21.6 / 23.5** | PF↑ DD↓ **both** | **pass_is** · **P3 winner** |
| ADX25_01 | ~2021–2025 | **1.05** | **50.3 / 51.6** | PF↑ DD **worse** | **fail_is** · reject tight |
| BrkSus_01 | ~2021–2025 | **1.02** | **42.5 / 44.8** | PF flat · DD **worse** | **fail_is** · reject vs ADX28 |
| ATRP70_01 | ~2021–2025 | **0.74** | **101 / 102** | PF↓ DD wipe | **fail_is** · **reject** |

### Result — `ERG_P3_regime_BrkSus_01` (2026-07-15)

```text
Preset: ERG_P3_regime_BrkSus_01  (BSL25 + BreakoutSuspend · ADX off)
Window: multi-year from 2021 (MT5 report)
Trades: 1984   WR: 65.88%   PF: 1.02   Net: +81.14
DD bal / eq: 42.45% / 44.77%
Avg win / avg loss: +2.72 / -5.13   ratio: 1.89×
Largest L: -13.83
vs BSL25: PF flat · Net +67→+81 · DD 35.3%→42.5% (worse)
vs ADX28: PF 1.14→1.02 · Net +430→+81 · DD 21.6%→42.5%
Decision: fail_is · not a substitute for ADX28
Next: Canon G1 on ADX28 only — do not stack BrkSus
```

**Screen vs BSL25 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat BSL25 DD | DD &lt; 35.3% | **42.5%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **42.5%** | **FAIL** |
| PF↑ | preferred | **flat 1.02** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **1.89×** | **PASS** |

**Read:** Breakout suspend alone ≈ BSL25 with slightly worse path — no regime edge like ADX28. ERG-P3-03 **closed reject**. Do not mash BrkSus onto ADX28 without a new one-axis thesis later.

### Result — `ERG_P3_regime_ATRP70_01` (2026-07-15)

```text
Preset: ERG_P3_regime_ATRP70_01  (BSL25 + ATR% max 70 · ADX off)
Window: multi-year from 2021 (MT5 report)
Trades: 756   WR: 60.71%   PF: 0.74   Net: -405.29
DD bal / eq: 101.12% / 101.56%
Avg win / avg loss: +2.48 / -5.20   ratio: 2.10×
Largest L: -12.72
vs BSL25: PF 1.02→0.74 · Net +67→-405 · DD 35%→101%
vs ADX28: PF 1.14→0.74 · DD 22%→101%
Decision: fail_is · reject (matches prior Discovery ATRP70 hurt)
Next: Ignore ATR% · proceed ADX28 canon G1
```

**Screen vs BSL25 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat BSL25 DD | DD &lt; 35.3% | **~101%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **~101%** | **FAIL** |
| PF↑ | preferred | **0.74** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **2.10×** | **PASS** (irrelevant) |

**Read:** ATR%70 on BSL25 alone **destroys** the edge — trade count collapses (1994→756), expectancy dies, path wiped. Confirms ERG-P3-04 as last-resort reject. Do **not** stack ATR% onto ADX28.

### Plateau close — ADX25 / 28 / 30 (2026-07-15)

| | BSL25 | ADX25 | **ADX28** | ADX30 | BrkSus | ATRP70 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PF / Net | 1.02 / +67 | 1.05 / +148 | **1.14 / +430** | 1.02 / +61 | 1.02 / +81 | **0.74 / −405** |
| DD bal | 35.3% | 50.3% | **21.6%** | 47.9% | 42.5% | **~101%** |

**ERG-P3 verdict:** **ADX28 only.** All other P3 probes fail research screen vs BSL25 and/or ADX28.

### Result — `ERG_P3_adx_ADX30_01` (2026-07-15)

```text
Preset: ERG_P3_adx_ADX30_01  (BSL25 + ADX max 30)
Window: multi-year from 2021 (MT5 report)
Trades: 1981   WR: 65.93%   PF: 1.02   Net: +61.30
DD bal / eq: 47.94% / 50.14%
Avg win / avg loss: +2.71 / -5.16   ratio: 1.90×
Largest L: -12.86   RF: 0.15   Sharpe: 0.16
vs BSL25: PF flat · Net ≈ same · DD 35%→48% (worse)
vs ADX28: PF 1.14→1.02 · Net +430→+61 · DD 22%→48%
Decision: fail_is
Next: Keep ADX28 · canon window 2026.01.01–2026.07.31 on ADX28
```

**Screen vs BSL25 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat BSL25 DD | DD &lt; 35.3% | **47.9%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **47.9%** | **FAIL** |
| PF↑ and/or DD↓ | both preferred | neither vs BSL25 | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **1.90×** | **PASS** |

**Read:** On 2021–25, ADX30 behaves like “BSL with a weak gate” — expectancy ≈ BSL25, path **worse**. The working band is nearer **28**, not 25 (too tight) or 30 (too loose for this sample). Sensitivity: ADX28 is a point estimate — after canon G1, optional ±1 (27/29) only if promoting.

### Result — `ERG_P3_adx_ADX28_01` (2026-07-15)

```text
Preset: ERG_P3_adx_ADX28_01  (BSL25 + ADX max 28)
Window: multi-year from 2021 (MT5 report)
Trades: 1943   WR: 67.88%   PF: 1.14   Net: +430.35
DD bal / eq: 21.58% / 23.46%
Avg win / avg loss: +2.74 / -5.10   ratio: 1.86×
Largest L: -12.69   RF: 1.88   Sharpe: 1.04
Hold avg: ~16h · max ~379h
vs BSL25: PF 1.02→1.14 · Net +67→+430 · DD 35.3%→21.6%
vs ADX25: DD 50%→22% · PF 1.05→1.14 · Net +148→+430
Decision: pass_is · **P3 research centre (plateau closed)**
Next: Canon window 2026.01.01–2026.07.31 G1 vs PRODUCTION
```

**Screen vs BSL25 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat BSL25 DD | DD &lt; 35.3% | **21.6%** | **PASS** |
| Research DD ≤ 25% | ≤25% | **21.6%** | **PASS** |
| PF↑ and/or DD↓ | both preferred | **both** | **PASS** |
| avgL/avgW ≤ 6× | ≤6× | **1.86×** | **PASS** |

**Read:** ADX28 cleared research DD and beat BSL25. Plateau closed with ADX30 fail — **keep 28**, do not default to PRODUCTION’s 30 on this sample.

### Result — `ERG_P3_adx_ADX25_01` (2026-07-15)

```text
Preset: ERG_P3_adx_ADX25_01  (BSL25 + ADX max 25)
Window: multi-year from 2021 (MT5 report)
Trades: 1844   WR: 65.94%   PF: 1.05   Net: +147.71
DD bal / eq: 50.31% / 51.59%
Avg win / avg loss: +2.76 / -5.10   ratio: 1.85×
Largest L: -12.69   Hold avg: ~16.5h · max ~378h
vs BSL25: PF 1.02→1.05 · Net +67→+148 · DD 35.3%→50.3% (worse)
Decision: fail_is
Next: Load ERG_P3_adx_ADX30_01 (do not prefer ADX25)
```

**Screen vs BSL25 / P0:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat BSL25 DD | DD ≤ 35.3% | **50.3%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **50.3%** | **FAIL** |
| PF↑ allowed if DD↓ | DD must improve | PF↑ DD↓ **no** | **FAIL** |
| avgL/avgW ≤ 6× | ≤6× | **1.85×** | **PASS** |

**Read:** Tighter ADX25 slightly lifts PF/Net via selection, but **path DD deteriorates** vs BSL-only. Rejected as plateau bound.

```text
Preset: ERG_P3_adx_…
Window: …
Trades: …   WR: …   PF: …   Net: …
DD bal / eq: … / …
Avg win / avg loss: … / …   ratio: …
vs BSL25: PF Δ …  DD Δ …
Decision: pass_is | fail_is | plateau_ok
Next: …
```

---

## After ADX plateau (closed)

- **Research centre:** `ERG_P3_adx_ADX28_01`  
- **Rejected:** ADX25, ADX30, **BrkSus**, **ATRP70**  
- **Next:** optional **ERG-P4** exits on ADX28 ([`ERG_P4_exit_pack.md`](ERG_P4_exit_pack.md)) **or** jump to canonical G1 on ADX28  
- Do **not** stack rejected regime filters onto ADX28  

## Secondary P3 probes (done)

- ADX30, BrkSus, ATRP70 all **fail_is** on research window — centre remains ADX28.
