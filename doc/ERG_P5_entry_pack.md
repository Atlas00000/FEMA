# ERG-P5 — Entry quality · test pack

**Phase:** ERG-P5 · **axis:** `entry_filter`  
**Status:** ERG-P5 **closed** · Candle **fail** · RSI **no-op** · centre stays **ADX28 + TP10**  
**Parent:** [`ERG_P3_adx_ADX28_01.set`](../Presets/ERG_P3_adx_ADX28_01.set)  
**Prior:** [`ERG_P4_exit_pack.md`](ERG_P4_exit_pack.md) · Plan: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md)

> Skip low-quality first fills **after** BSL25 + ADX28 + TP10. **One entry axis per preset** (do not combine candle + RSI). HTF parked (ERG-P5-03).

---

## Stack so far (do not undo)

```text
P1-BASELINE → BSL25 → ADX28 + TP10  = research centre
Rejected: BSL20/30 · MaxBars* · ADX25/30 · BrkSus · ATRP70 · Trail70 · TP8 · TP12 · RSI_01 · Candle_01
Research centre unchanged: ADX28 + BSL25 + TP10
```

**Locked:** BSL:TP **2.5:1** (25/10) · no trail · no MaxBars · ADX max **28**.

---

## Presets (both ready)

| Order | File | Task | Diff vs ADX28 |
| --- | --- | --- | --- |
| either | [`ERG_P5_entry_Candle_01.set`](../Presets/ERG_P5_entry_Candle_01.set) | **ERG-P5-01** | `InpUseCandleConfirm=true` |
| either | [`ERG_P5_entry_RSI_01.set`](../Presets/ERG_P5_entry_RSI_01.set) | **ERG-P5-02** | `InpUseRsiExhaustionFilter=true` (RSI 14 · buy max 70 · sell min 30) |
| parked | — | ERG-P5-03 | HTF — reopen only if loser atlas shows HTF mismatch |

**What each filter does**

| Probe | Gate |
| --- | --- |
| Candle | Prior closed M5: buy needs close>open · sell needs close<open |
| RSI | Block buy if RSI>70 · block sell if RSI<30 (defaults) |

**Load path:**  
`C:\Users\emili\AppData\Roaming\MetaQuotes\Terminal\158041E5204719DC59E8E86EAAE9D56B\MQL5\Profiles\Tester\`

Tester: EURUSD M5 · Every tick · $400 · ProfitInPips=0 · same multi-year window as ADX28 for compare.

**Journal check after Load:** `bsl=25` · `adx_gate=on` · AdxMax **28** · `InpBasketTp=10` · candle **or** RSI on (not both).

---

## Pass screen (vs ADX28 parent)

| Gate | Threshold |
| --- | --- |
| vs ADX28 | PF **↑** and/or DD **↓** (both preferred); keep research DD≤**25%** |
| Anti-goal | Must not starve trade count into noise while DD stays same/worse |
| AvgW | Prefer not clipping the ~$2.74 mean win without DD benefit |
| Canon later | Only survivors → G1 on `2026.01.01–2026.07.31` |

**ADX28 baseline (research):** PF **1.14** · DD **21.6%/23.5%** · Net **+430** · WR **68%** · AvgW **2.74**

---

## Scorecard

| Preset | Window | PF | DD% | vs ADX28 | Decision |
| --- | --- | --- | --- | --- | --- |
| Candle_01 | ~2021–2025 | **1.08** | **45.3 / 46.0** | PF↓ Net↓ DD **much worse** | **fail_is** · reject |
| RSI_01 | ~2021–2025 | **1.14** | **21.6 / 23.5** | **identical** to parent | **fail_is** · reject (no-op) |

### Result — `ERG_P5_entry_Candle_01` (2026-07-16)

```text
Preset: ERG_P5_entry_Candle_01  (ADX28 + prior-bar candle confirm)
Window: multi-year from 2021 (MT5 report)
Trades: 1461   WR: 65.43%   PF: 1.08   Net: +201.88
DD bal / eq: 45.33% / 45.99%
Avg win / avg loss: +2.92 / -5.13   ratio: 1.76×
Largest W/L: +10.02 / -14.84
RF: 0.65   Sharpe: 0.51
Hold avg: ~18.7h · max ~195h
vs ADX28: PF 1.14→1.08 · Net +430→+202 · DD 21.6%→45.3% · trades 1943→1461 · AvgW 2.74→2.92
Decision: fail_is (filters fills but worsens path — DD doubles)
Next: Close P5 · research centre = ADX28 · ERG-P6 canon G1
```

**Screen vs ADX28:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| Beat ADX28 DD or PF | DD↓ and/or PF↑ | PF **↓** · DD **45%** | **FAIL** |
| Research DD ≤ 25% | ≤25% | **45.3%** | **FAIL** |
| Anti-goal (don’t starve / wreck) | useful filter | trades ↓ · path worse | **FAIL** |

**Read:** Candle confirm cuts ~25% of fills and slightly lifts AvgW, but **destroys DD containment** and halves net. Prior-bar color is the wrong quality gate for this grid.

### Result — `ERG_P5_entry_RSI_01` (2026-07-16)

```text
Preset: ERG_P5_entry_RSI_01  (ADX28 + RSI exhaustion 14/70/30)
Window: multi-year from 2021 (MT5 report)
Trades: 1943   WR: 67.88%   PF: 1.14   Net: +430.45
DD bal / eq: 21.58% / 23.46%
Avg win / avg loss: +2.74 / -5.11   ratio: 1.86×
vs ADX28: identical path (no-op)
Decision: fail_is as upgrade
```

### ERG-P5 final

| Keep | Reject |
| --- | --- |
| **ADX28 + BSL25 + TP10** (no candle, no RSI) | Candle_01 · RSI_01 · HTF parked |

---

## Next (ERG-P6)

Research survivor = **`ERG_P3_adx_ADX28_01`** → canon G1 **fail** (PF 1.21 · DD 24.6%). Keep **PRODUCTION**. See [`ERG_P6_g1_pack.md`](ERG_P6_g1_pack.md).
