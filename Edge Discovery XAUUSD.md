# FEMA — Edge Discovery: XAUUSD M5

**Status:** **Discovery open** — no XAUUSD production candidate. EURUSD stack **not validated** on gold.

**Parent doc:** [`Edge Discovery.md`](Edge Discovery.md) — EURUSD canonical (PRODUCTION PF 1.36 · locked).  
**Sibling tracks:** [`Edge Discovery GBPUSD.md`](Edge Discovery GBPUSD.md)

**Test symbol / TF:** XAUUSD M5  
**Test window (canonical):** `2026.01.01` – `2026.07.31` · $400 · 1:500 · Every tick · `ProfitInPips=0`  
**EA version:** v1.20+  
**Preset source:** Reuse `Experts\FEMA\Presets\` — set **Symbol=XAUUSD** in Strategy Tester.  
**Suggested tester naming:** `FEMA_XAUUSD_M5_{preset}.ini` in `MQL5\Profiles\Tester\`

**Spread note:** Gold spreads are often wider than EURUSD — watch `InpMaxSpreadPoints=30`; may need pair-specific cap after BSL sweep.

**Journal check (PRODUCTION-class runs):** `adx_gate=on` · `bsl=25` · `exit=btp` · `entry=off`

---

## Why a separate track?

EURUSD PRODUCTION does not port to other majors unchanged (GBPUSD row 34: PF 0.80 · −$172). XAUUSD has different volatility, spread, tick value, and session personality — requires its own tune.

P1-BASELINE on XAUUSD shows **strong mean-reversion cadence** (80% WR, +$373) but **32% equity DD** without basket SL — same steamroller family as GBPUSD P1, milder than GBPUSD (54% eq).

---

## Cross-pair P1 comparison

| Symbol | PF | Net | Max DD | Win % | Trades | Avg W / L | Notes |
| ------ | --- | --- | ------ | ----- | ------ | --------- | ----- |
| EURUSD | 0.17 | −$245 | 66% bal | 83% | 30 | +2.01 / −59.10 | Catastrophic tails, few closes |
| GBPUSD | 22.23 ⚠️ | +$323 | 1.7% bal / **54% eq** | 95% | 135 | +2.64 / −2.17 | Oscillatory; equity steamroller |
| **XAUUSD** | **9.77** ⚠️ | **+$373** | **2.5% bal / 32% eq** | **80%** | **81** | **+6.39 / −2.66** | Long-biased; fewer trades; smaller eq DD than GBP |

> ⚠️ **PF 9.77 is misleading** — high WR + small closed losses; **32% equity DD** means floating baskets still dangerous. Not deployable without BSL.

---

## Early hypothesis (XAUUSD)

1. **Mean-reversion works on M5 gold** without SL — 81 baskets, 80% WR, healthy avg win (+$6.39) vs avg loss (−$2.66) on closed trades.
2. **Long bias** — 62 long vs 19 short (80% long WR). May reflect Jan gold drift; re-test on full Jan–Jul window.
3. **Equity DD 32%** with only **2.5% balance DD** — classic floating-basket risk; BSL layer is required before any live consideration.
4. **Fewer trades than GBPUSD** (81 vs 135) — gold grids fire less often; each basket may carry more dollar P/L per leg.
5. **EURUSD PRODUCTION port untested** on XAUUSD — run as row 2 before assuming BSL helps or hurts.

---

## XAUUSD edge model (working)

> **Candidate shape:** Trend pullback grid on XAUUSD M5 with **basket TP $10** — gold mean-reverts on M5 often enough to close many baskets at TP without SL.

> **Open question:** What **basket SL** ($) contains **32% equity DD** down to ≤25% without destroying 80% WR? Dollar SL may need **scaling** vs FX (same $25 may be too tight or too loose on XAU).

**Do not deploy** P1-BASELINE (+$373 / 32% eq DD) on live XAUUSD.

---

## Decision gates (XAUUSD)

| Gate | Criteria | Status |
| ---- | -------- | ------ |
| **G0** — P1 characterised | P1 on XAUUSD; steamroller profile documented | ✅ Pass (row 1) |
| **G1** — Candidate | PF ≥ **1.2** and max DD ≤ **25%** (balance **and** equity) | ⏳ |
| **G2** — Production | Beats best candidate on PF **and** DD together | ⏳ |
| **G3** — Cross-symbol (parent) | EURUSD PRODUCTION + alt symbol candidate PF ≥ 1.2 | ❌ Pending |

**G1 rule:** Promote only if **PF and max DD beat the current best row together** — not win rate or PF alone.

---

## Backtest results log

| #   | Preset | Task | Status | PF | Net P/L | Max DD % | Win % | Avg W | Avg L | Largest L | Trades | Notes |
| --- | ------ | ---- | ------ | --- | ------- | -------- | ----- | ----- | ----- | --------- | ------ | ----- |
| 1   | `P1-BASELINE` | P1 | ⚠️ **Steamroller** | 9.77 | +373 | 2.5% bal / **32% eq** | 80% | +6.39 | −2.66 | −9.36 | 81 | No BSL; long bias 62L/19S; ⚠️ confirm full Jan–Jul window |

---

## Chart notes (row 1 — P1 XAUUSD)

| Dimension | Observation |
| --------- | ----------- |
| **Hours** | Spike **hour 0**; cluster **5–7** (London); sustained **12–19** (US) |
| **Weekdays** | **Thursday** most active; **Wednesday** lightest; Tue/Thu best profits |
| **Months** | Chart shows **January only** — ⚠️ **re-run on full `2026.01.01–2026.07.31`** before BSL sweep |
| **Direction** | **Long-heavy** (76% of trades) — check if trend artifact |
| **Risk** | Balance DD 2.5%, **equity DD 32%** — needs BSL |

---

## Test queue (recommended order)

```
⚠️ First: re-confirm row 1 on full Jan–Jul 2026 (monthly chart showed Jan-only)

Phase XAU-A — Failure containment
1. FEMA_XAUUSD_M5_P2A-002_BSL_15
2. FEMA_XAUUSD_M5_P2A-002_BSL_20
3. FEMA_XAUUSD_M5_P2A-002_BSL_25          ← EURUSD anchor
4. FEMA_XAUUSD_M5_P2A-002_BSL_30
5. FEMA_XAUUSD_M5_P2A-002_BSL_40          ← gold volatility — test looser cap

Phase XAU-B — EUR port baseline
6. FEMA_XAUUSD_M5_PRODUCTION                ← row 2 — does EUR stack help or hurt?

Phase XAU-C — Regime (after best BSL)
7. FEMA_XAUUSD_M5_P2C-001_REG_ADX30
8. FEMA_XAUUSD_M5_P2C-001_REG_ADX35       ← looser if ADX30 over-filters

Phase XAU-D — Practical
9. Spread filter sweep if rejects spike      ← InpMaxSpreadPoints 30→50→80

Skip until XAU candidate:
- P2E exit overlays · P2F grid/confirm · P3 expansion
```

**Next run:** Full-window **`P1-BASELINE`** confirm, then **`P2A-002_BSL_25`** on XAUUSD.

---

## Preset creation (tester)

Copy any EURUSD `.ini`, change:

```ini
Symbol=XAUUSD
```

Optional: duplicate `FEMA_EURUSD_M5_P1-BASELINE.ini` → `FEMA_XAUUSD_M5_P1-BASELINE.ini`.

---

## Rejected / do not use (XAUUSD)

| Preset | Reason |
| ------ | ------ |
| `P1-BASELINE` live | Row 1 — 32% equity DD; steamroller |
| EURUSD `PRODUCTION` (untested) | Do not deploy until row logged |

---

## EURUSD lessons to apply (and question)

| EURUSD result | Apply to XAUUSD? |
| ------------- | ---------------- |
| BSL + basket TP core | ✅ Yes — **$ level TBD** (consider 30–40 not only 25) |
| ADX30 gate | ❓ Test after BSL — long bias may need looser gate |
| Wider grid | ❌ Skip until candidate |
| RTE / trail / candle confirm | ❌ Skip — failed on EUR |
| Fixed $10 basket TP | ❓ Avg win already +$6.39 on P1 — TP may be hit faster; monitor |

---

## Next step

| | |
| --- | --- |
| **Current best** | None — no G1 candidate |
| **Row 1** | P1 XAUUSD — characterisation ✅ (confirm full window) |
| **Next test** | Full Jan–Jul P1 confirm → `P2A-002_BSL_25` |
| **EURUSD** | `FEMA_EURUSD_M5_PRODUCTION` — unchanged live track |

---

*Last updated: 2026-07-10 · row 1*
