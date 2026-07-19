# ERG-P6 — Canonical G1 · test pack

**Phase:** ERG-P6 · **gate:** G1 vs PRODUCTION  
**Status:** ADX28 **G1 fail** · do **not** promote over PRODUCTION  
**Survivor tested:** [`ERG_P3_adx_ADX28_01.set`](../Presets/ERG_P3_adx_ADX28_01.set)  
**Prior:** [`ERG_P5_entry_pack.md`](ERG_P5_entry_pack.md) · Plan: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md)

> Research-window wins do not promote. Canonical `2026.01.01–2026.07.31` is the only G1 bar.

---

## G1 bar (PRODUCTION lock)

| Gate | Need |
| --- | --- |
| PF | ≥ **1.36** |
| DD bal | ≤ **18%** (eq ~21% reference) |
| Window | `2026.01.01–2026.07.31` · EURUSD M5 · $400 · Every tick |

**PRODUCTION lock (System Profile):** PF **1.36** · Net **+$221** · DD **18% / 21%** · ~424 trades · stack BSL25 + **ADX30** + TP10

---

## Research lineage (for context)

```text
P1-BASELINE → BSL25 → ADX28+TP10  = research centre (2021–25)
Rejected: BSL20/30 · MaxBars* · ADX25/30(research) · BrkSus · ATRP70
          · Trail70 · TP8/12 · RSI · Candle
```

On **2021–25**, ADX28 beat ADX30. On **canon 2026**, that ranking reverses vs the lock.

---

## Scorecard

| Preset | Window | PF | DD bal/eq | Net | vs G1 | Decision |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| **ADX28_01** | 2026.01–07.31 | **1.21** | **24.6% / 27.3%** | +147.86 | PF↓ DD↑ | **fail_g1** |
| PRODUCTION (lock) | same | **1.36** | **18% / 21%** | +221 | bar | locked |

### Result — `ERG_P3_adx_ADX28_01` canon (2026-07-16)

```text
Preset: ERG_P3_adx_ADX28_01  (BSL25 + ADX28 + TP10)
Window: 2026.01.01 – 2026.07.31  (canonical)
Trades: 443   WR: 69.30%   PF: 1.21   Net: +147.86
DD bal / eq: 24.62% / 27.27%
Avg win / avg loss: +2.73 / -5.07   ratio: 1.86×
Largest W/L: (from report) · RF: 0.93   Sharpe: 1.22
Hold avg: ~21.0h · max ~151h
vs PRODUCTION lock: PF 1.36→1.21 · Net +221→+148 · DD 18%→24.6%
Decision: fail_g1  (both legs)
Next: ERG-P7 · Reject promote · keep PRODUCTION
```

**G1 screen:**

| Gate | Need | Got | |
| --- | --- | --- | --- |
| PF ≥ 1.36 | ≥1.36 | **1.21** (−0.15) | **FAIL** |
| DD bal ≤ 18% | ≤18% | **24.62%** (+6.6pp) | **FAIL** |

**Read:** Multi-year ADX28 improvement does **not** transfer to the promote window. Tighter ADX (28 vs PRODUCTION 30) underperforms the lock on 2026 — more trades (443 vs ~424) with worse PF/DD. Not a near-miss; dual fail.

---

## ERG-P6 final

| Keep | Do not promote |
| --- | --- |
| **PRODUCTION** (BSL25 + ADX30 + TP10) on EURUSD | ADX28 as lock replacement |

**Optional later (not auto):** ERG-P2 session (hour 23) only as a *new* Discovery thread vs PRODUCTION — not as a patch to salvage ADX28 G1.

---

## Next — ERG-P7

**Done.** Human **Reject** signed 2026-07-16.  
- Checklist: [`../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md`](../AI/kb/decisions/20260716_190850_ERG_P3_adx_ADX28_01_Reject.md)  
- Profile: [`../AI/kb/profiles/prof_ERG_P3_adx_ADX28_01.json`](../AI/kb/profiles/prof_ERG_P3_adx_ADX28_01.json)  
- Log: [`../AI/kb/el2_promote_decision.md`](../AI/kb/el2_promote_decision.md)  
**PRODUCTION lock unchanged.**
