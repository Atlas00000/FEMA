# FEMA — Edge Discovery: GBPUSD M5

**Status:** **Discovery open** — no GBPUSD production candidate. EURUSD stack **does not port** unchanged.

**Parent doc:** [`Edge Discovery.md`](Edge Discovery.md) — EURUSD canonical (PRODUCTION PF 1.36 · locked).

**Test symbol / TF:** GBPUSD M5  
**Test window (canonical):** `2026.01.01` – `2026.07.31` · $400 · 1:500 · Every tick · `ProfitInPips=0`  
**EA version:** v1.20+  
**Preset source:** Reuse `Experts\FEMA\Presets\` — change **Symbol** to GBPUSD in Strategy Tester (Settings or manual).  
**Suggested tester naming:** `FEMA_GBPUSD_M5_{preset}.ini` in `MQL5\Profiles\Tester\` (create as you log runs).

**Journal check (PRODUCTION-class runs):** `adx_gate=on` · `bsl=25` · `exit=btp` · `entry=off`

---

## Why a separate track?

EURUSD PRODUCTION (**row 34** in parent log) on GBPUSD: **PF 0.80 · −$172 · 65% DD · 59% WR**. G3 cross-symbol **failed**.

GBPUSD is **not** a config copy. It needs its own containment + filter tuning. Lessons from EURUSD Phase 2 still apply in principle (basket TP + BSL model, don't widen grid, don't RTE/trail), but **parameter levels and gates may differ**.

---

## Pair comparison (same window, same EA)

| Preset | Symbol | PF | Net | Max DD | Win % | Trades | Takeaway |
| ------ | ------ | --- | --- | ------ | ----- | ------ | -------- |
| P1-BASELINE | EURUSD | 0.17 | −$245 | 66% bal | 83% | 30 | Steamroller — few closes, huge tails |
| **P1-BASELINE** | **GBPUSD** | **22.23** ⚠️ | **+$323** | **1.7% bal / 54% eq** | **95%** | **135** | High WR + net profit but **54% equity DD** — not deployable |
| PRODUCTION | EURUSD | **1.36** | **+$221** | 18% / 21% eq | 71% | 424 | 🏆 Deploy stack |
| PRODUCTION | GBPUSD | 0.80 | −$172 | 65% eq | 59% | 393 | BSL+ADX **hurts** vs raw P1 on this pair |

### Early hypothesis (GBPUSD)

1. **Raw grid mean-reverts more often** on GBPUSD (P1: 135 trades, 95% WR, many +$10 TPs) — pair is more oscillatory on M5.
2. **Without basket SL**, floating baskets still reach **~54% equity DD** — tail risk remains; balance DD looks safe (1.7%) because wins close before losses realize on balance.
3. **EURUSD PRODUCTION stack over-constrains** GBPUSD: BSL $25 + ADX30 may stop baskets that would have recovered (long WR 48% vs P1 long 93%).
4. **Tune direction:** Find GBPUSD-specific **BSL level** and **ADX threshold** (if any) — not assume EURUSD values.

> ⚠️ **P1 PF 22.23 is misleading** — tiny avg win (+$2.64) vs rare larger losses; high WR hides equity steamroller. Same lesson as EURUSD P1, different shape (more trades, smaller tails).

---

## GBPUSD edge model (working)

> **Candidate shape:** Trend pullback grid on GBPUSD M5 with **basket TP $10** — pair shows more natural mean-reversion than EURUSD without SL.

> **Open question:** What **basket SL** and **regime gate** contain 54% equity DD without killing the 95% WR mean-reversion cadence?

**Do not deploy** P1-BASELINE (+$323 / 54% eq DD) or EURUSD PRODUCTION (−$172) on live GBPUSD.

---

## Decision gates (GBPUSD)

| Gate | Criteria | Status |
| ---- | -------- | ------ |
| **G0** — P1 characterised | P1 run on GBPUSD; steamroller profile documented | ✅ Pass (row 1) |
| **G1** — Candidate | PF ≥ **1.2** and max DD ≤ **25%** (balance **and** equity) vs best prior row | ⏳ |
| **G2** — Production | Beats best candidate on PF **and** DD together; 2 consecutive windows or forward slice | ⏳ |
| **G3** — Cross-symbol (parent) | EURUSD PRODUCTION + GBPUSD candidate both PF ≥ 1.2 | ❌ Fail until GBPUSD G1 met |

**G1 rule (same as EURUSD):** Promote only if **PF and max DD beat the current best row together** — not win rate alone.

---

## Backtest results log

Fill as reports are uploaded. Keep date range and symbol consistent.


| #   | Preset | Task | Status | PF | Net P/L | Max DD % | Win % | Avg W | Avg L | Largest L | Trades | Notes |
| --- | ------ | ---- | ------ | --- | ------- | -------- | ----- | ----- | ----- | --------- | ------ | ----- |
| 1   | `P1-BASELINE` | P1 | ⚠️ **Steamroller** | 22.23 | +323 | 1.7% bal / **54% eq** | 95% | +2.64 | −2.17 | — | 135 | No BSL; hour 0 + Mon/Fri edge; Mar peak |
| 2   | `PRODUCTION` | EUR-port | ❌ **Rejected** | 0.80 | −172 | **65% eq** | 59% | +3.08 | −5.41 | — | 393 | EURUSD stack; long WR 48%; US h13–14 losses |


---

## Chart notes (row 1 — P1 GBPUSD)

| Dimension | Observation |
| --------- | ----------- |
| **Hours** | Spike entries **hour 0** (Asia); profits at 0, 6–8, 12–14 |
| **Weekdays** | **Monday** + **Friday** highest activity and profit |
| **Months** | **March** dominant; Feb/Jul secondary; Apr small loss |
| **Risk** | Balance DD tiny, **equity DD 54%** — floating baskets |

---

## Chart notes (row 2 — PRODUCTION GBPUSD)

| Dimension | Observation |
| --------- | ----------- |
| **Hours** | **US 13–14** largest losses |
| **Weekdays** | Wed/Fri loss-heavy vs Mon on P1 |
| **Months** | **May, Jul** large losses |
| **Longs** | **48% WR** — broken vs shorts 64% |

---

## Test queue (recommended order)

Work **one preset at a time**. Base: P1 learnings → find GBPUSD BSL → then gates.

```
Phase GBP-A — Failure containment (priority)
1. FEMA_GBPUSD_M5_P2A-002_BSL_15          ← tighter SL — does GBPUSD need less than $25?
2. FEMA_GBPUSD_M5_P2A-002_BSL_20
3. FEMA_GBPUSD_M5_P2A-002_BSL_25          ← EURUSD value; expect ≠ EUR result
4. FEMA_GBPUSD_M5_P2A-002_BSL_30          ← looser — P1 suggests recovery possible

Phase GBP-B — Regime (only after best BSL row)
5. FEMA_GBPUSD_M5_P2C-001_REG_ADX30       ← EUR production gate
6. FEMA_GBPUSD_M5_P2C-001_REG_ADX35       ← looser — PRODUCTION may over-filter
7. FEMA_GBPUSD_M5_P2C-001_REG_ADX25       ← tighter

Phase GBP-C — Session (after BSL+ADX candidate)
8. FEMA_GBPUSD_M5_P2D-001_SES_NO23        ← if rollover hours toxic on GBPUSD
9. Session whitelist / Fri block          ← only if hour chart shows clear loss windows

Skip until GBP candidate exists:
- P2E exit overlays (failed on EURUSD)
- P2F wider grid / candle confirm (failed on EURUSD)
- P3 strategy expansion
```

**Next run:** `P2A-002_BSL_25` on GBPUSD (same `.set` as EURUSD, symbol GBPUSD) — establishes whether $25 is wrong direction (tighter vs looser than EUR).

---

## Preset creation (tester)

Copy EURUSD tester `.ini`, change:

```ini
Symbol=GBPUSD
```

Example: duplicate `FEMA_EURUSD_M5_P2A-002_BSL_25.ini` → `FEMA_GBPUSD_M5_P2A-002_BSL_25.ini` (only `Symbol` line changes; inputs identical).

Chart/live: `Presets\PRODUCTION.set` on GBPUSD chart is **not** validated — use only after a row wins G1.

---

## Rejected / do not use (GBPUSD)

| Preset | PF | Net | Reason |
| ------ | --- | --- | ------ |
| EURUSD `PRODUCTION` port | 0.80 | −$172 | Row 2 — long WR collapse; do not deploy |
| `P1-BASELINE` live | 22.23 | +$323 | Row 1 — 54% equity DD; steamroller |

---

## EURUSD lessons to apply (and question)

| EURUSD result | Apply to GBPUSD? |
| ------------- | ---------------- |
| BSL_25 + basket TP core | ✅ Yes — but **SL dollar level** may differ |
| ADX30 gate | ❓ Test — may be too tight (PRODUCTION long WR 48%) |
| Wider grid (P2F) | ❌ Skip until candidate — failed on EUR |
| RTE / trail exits | ❌ Skip — failed on EUR |
| LDN/NY whitelist | ❌ Skip — failed on EUR (Asia hour 0 matters here too) |
| Session NO23 | ❓ Test after BSL — hour 0 is **profitable** on P1 |

---

## Next step

| | |
| --- | --- |
| **Current best** | None — no G1 candidate |
| **Row 1** | P1 GBPUSD — characterisation ✅ |
| **Row 2** | PRODUCTION port — rejected ❌ |
| **Next test** | `P2A-002_BSL_25` on GBPUSD M5 (then sweep 15/20/30) |
| **EURUSD** | Unchanged — `FEMA_EURUSD_M5_PRODUCTION` remains live track |

---

*Last updated: 2026-07-10 · rows 1–2*
