# FEMA — Edge Discovery & Refinement Roadmap

**Status:** **Production verified** — `FEMA_EURUSD_M5_PRODUCTION` · PF **1.36** · +$221 · 18% DD · 424 trades · Sharpe 1.90

**Test symbol / TF:** EURUSD M5  
**Test window (canonical):** `2026.01.01` – `2026.07.31` · $400 · 1:500 · Every tick · `ProfitInPips=0`  
**Preset location:** `MQL5\Profiles\Tester\`  
**Production load:** `FEMA_EURUSD_M5_PRODUCTION.ini` or `FEMA_EURUSD_M5_P2C-001_REG_ADX30.ini` (identical)

**Critical:** `InpUseAdxGate=true` · `InpAdxMax=30` — without this you get BSL_25 bare (PF 1.27, +$176).

---

## Edge Model (validated by BSL_25)

> **Edge:** Trend pullback continuation with **basket exits** — many small +$10 basket wins (~71–73% WR) when price mean-reverts toward EMA20 inside an EMA20/EMA100 trend.

> **How it trades:** Floating ATR grid — adds legs on pullbacks, closes the **whole basket** at +$10 TP or **−$25 SL**. Basket-level stop contains tail risk; legs float until basket exit. Per-leg SL, stacked P2A layers, and extended cooldowns **erode** this edge.

**Implication:** The edge lives in **BSL_25 + basket TP** — PF ~1.3 on 2026. Regime gates (ATRP70, ADX25, HTF) mostly **hurt** on the current window. Filter **sessions** next (P2D), not volatility/trend strength.

## 2026 Window — Validated Baselines (canonical)


| Preset | Task | PF | Net P/L | Max DD | Win % | Trades | Verdict |
| ------ | ---- | --- | ------- | ------ | ----- | ------ | ------- |
| **`FEMA_EURUSD_M5_PRODUCTION`** | PRODUCTION | **1.36** | **+$221** | 18% bal / 21% eq | 71% | 424 | 🏆 **PRODUCTION** (verified) |
| `FEMA_EURUSD_M5_P2A-002_BSL_25` | P2A-002 | 1.27 | +$176 | ~17% bal / ~21% eq | 70% | 424 | Control — `adx_gate=off` |
| `FEMA_EURUSD_M5_P2C002_ATRP70` | P2C-002 | 0.94 | −$38 | ~32% bal / ~35% eq | 65% | 376 | ❌ Rejected 2026 |

**Gate G1 (2026):** PF **and** max DD together. **Winner: BSL_25 stack** (PF 1.27–1.36, DD ~18%). ATRP70 **fails** — do not deploy on 2026 data.

## Production Candidate


| Field | Value |
| ----- | ----- |
| **Preset** | **`FEMA_EURUSD_M5_PRODUCTION`** (alias: `P2C-001_REG_ADX30`) |
| **Load file** | `FEMA_EURUSD_M5_PRODUCTION.ini` |
| **Task ID** | P2C-001 |
| **Config** | BSL_25 + **ADX(14)>30 gate** + basket TP $10 · HTF off · ATR gate off |
| **PF** | **1.36** |
| **Net P/L** | **+$221** |
| **Max DD** | **18%** balance / 21% equity |
| **Win %** | **71%** |
| **Trades** | **424** |
| **Sharpe** | **1.90** |
| **Journal check** | `InpUseAdxGate=true` · `adx_gate=on` · `bsl=25` |

**Do not deploy without ADX gate** — bare BSL_25 gives PF 1.27 (+$176). P2D builds on this preset.

---

## Alternates (logged — not promoted)

Presets that show merit but are not the current production candidate. Keep testing; promote only if PF **and** max DD beat the candidate together.


| Preset                             | Task ID | Role                   | PF   | Net P/L | Max DD | Win % | Trades | Why alternate                          |
| ---------------------------------- | ------- | ---------------------- | ---- | ------- | ------ | ----- | ------ | -------------------------------------- |
| `FEMA_EURUSD_M5_P2A-002_BSL_25`    | P2A-002 | **2026 control**       | 1.27 | +$176   | ~18%   | 70%   | 424    | Same stack as candidate; PF slightly lower |
| `FEMA_EURUSD_M5_P2C-002_REG_ATRP70`| P2C-002 | **2025 slice only**    | 1.34 | +$181   | 18%    | 73%   | 349    | Fails 2026 (PF 0.94) — do not deploy   |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR15` | P2A-001 | Prev. candidate        | 1.02 | +$39    | 26%    | 42%   | 1,819  | Structure SL; superseded by BSL_25     |
| `FEMA_EURUSD_M5_P2A-002_BSL_15`    | P2A-002 | High-return            | 1.06 | +$87    | 43% ❌  | 61%   | 1,166  | DD fails G1; tighter basket SL         |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR20` | P2A-001 | Low-DD R:R             | 0.91 | −$56    | 22%    | 21%   | 1,229  | Strong R:R; unprofitable Jan–Feb       |


**Next:** P2D session filters on **BSL_25 / ADX30** base (PF 1.36 benchmark).

```
1. FEMA_EURUSD_M5_P2D-001_SES_NO23          ← next
```

Completed (P2C — 2026 verdict):

```
    P2C-001 REG_ADX30     ← 🏆 2026 candidate (row 22) — PF 1.36
    P2C-002 REG_ATRP70    ← ❌ rejected on 2026 (row 21) — PF 0.94
    P2C-001 REG_ADX25     ← rejected 2025 (row 15)
    P2C-003…005           ← rejected (rows 18–20)
```

Completed (P2B):

```
    FEMA_EURUSD_M5_P2B-001_HTF_H1          ← rejected (row 12)
    FEMA_EURUSD_M5_P2B-002_HTF_H4          ← rejected (row 13)
    FEMA_EURUSD_M5_P2B-003_HTF_SLOPE       ← rejected (row 14) — identical to H1
```

---

## Rejected (do not use)


| Preset                                   | Task ID | PF   | Net P/L | Reason                                                  |
| ---------------------------------------- | ------- | ---- | ------- | ------------------------------------------------------- |
| `FEMA_EURUSD_M5_P1-BASELINE`             | P1      | 0.17 | −$245   | No failure containment                                  |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR15_RAW`   | P2A-001 | 0.00 | −$20    | Fixed ATR SL too tight; 0% WR                           |
| `FEMA_EURUSD_M5_P2A-ALL_FULL`            | P2A-ALL | 1.00 | +$6     | Full stack erodes edge vs ATR15 isolate                 |
| `FEMA_EURUSD_M5_P2A-003_TIME_48B`        | P2A-003 | 0.17 | −$245   | Time exit only; mirrors P1 baseline — no SL             |
| `FEMA_EURUSD_M5_P2A-003_TIME_96B`        | P2A-003 | 0.17 | −$245   | Identical to 48B/P1 — time exit likely not firing (bug) |
| `FEMA_EURUSD_M5_P2A-004_DEPTH_L3`        | P2A-004 | 0.17 | −$245   | Depth cap L3 only; identical to P1 — no SL              |
| `FEMA_EURUSD_M5_P2A-005_CD_10B`          | P2A-005 | 1.00 | −$7     | BSL $20 + 10b SL cooldown; breakeven, 32% DD            |
| `FEMA_EURUSD_M5_P2B-001_HTF_H1`          | P2B-001 | 0.85 | −$171   | H1 EMA200 cuts edge; PF/DD worse than BSL_25            |
| `FEMA_EURUSD_M5_P2B-002_HTF_H4`          | P2B-002 | 0.79 | −$166   | H4 EMA200 stricter cut; still worse PF/DD               |
| `FEMA_EURUSD_M5_P2B-003_HTF_SLOPE`       | P2B-003 | 0.85 | −$171   | Bit-identical to H1 — slope added no filter             |
| `FEMA_EURUSD_M5_P2C-001_REG_ADX25`       | P2C-001 | 0.80 | −$162   | ADX>25 block; −65% trades, worse PF/DD (2025)           |
| `FEMA_EURUSD_M5_P2C-002_REG_ATRP70`      | P2C-002 | 0.94 | −$38    | **2026 fail** — PF/DD worse than BSL_25; 2025 row 17 only |
| `FEMA_EURUSD_M5_P2C-003_REG_EMASEP_3ATR` | P2C-003 | 0.95 | −$61    | EMA sep >3×ATR; worse PF/DD vs BSL_25                   |


---

## Backtest Results Log

Fill in as reports are uploaded. Keep date range consistent across rows.


| #   | Preset                    | Task ID | Status            | PF       | Net P/L  | Max DD %     | Win %   | Avg W | Avg L  | Largest L | Trades | Notes                                              |
| --- | ------------------------- | ------- | ----------------- | -------- | -------- | ------------ | ------- | ----- | ------ | --------- | ------ | -------------------------------------------------- |
| 1   | `P1-BASELINE`             | P1      | ❌ Rejected        | 0.17     | −245     | 66%          | 83%     | +2.01 | −59.10 | −59.38    | 30     | No SL                                              |
| 2   | `P2A-001_PSL_ATR15_RAW`   | P2A-001 | ❌ Rejected        | 0.00     | −20      | 5%           | 0%      | —     | −0.34  | −0.66     | 59     | Fixed ATR SL too tight                             |
| 3   | `P2A-001_PSL_ATR20`       | P2A-001 | ⭐ Alternate       | 0.91     | −56      | 22%          | 21%     | +2.28 | −0.66  | −4.67     | 1229   | Strong R:R; unprofitable Jan–Feb                   |
| 4   | `P2A-001_PSL_ATR15`       | P2A-001 | ⭐ Alternate       | 1.02     | +39      | 26%          | 42%     | +2.25 | −1.60  | −6.10     | 1819   | Prev. candidate; structure SL                      |
| 5   | `P2A-002_BSL_15`          | P2A-002 | ⭐ Alternate       | 1.06     | +87      | 43%          | 61%     | +2.16 | −3.14  | −9.39     | 1166   | Basket SL $15; DD fails G1                         |
| 6   | `P2A-002_BSL_25`          | P2A-002 | ⭐ Prev. candidate | 1.15     | +165     | 18%          | 73%     | +2.15 | −4.98  | −7.01     | 831    | Superseded by ATRP70                               |
| 7   | `P2A-003_TIME_48B`        | P2A-003 | ❌ Rejected        | 0.17     | −245     | 66%          | 83%     | +2.01 | −59.10 | −59.38    | 30     | **Same as P1** — time exit alone; check date range |
| 8   | `P2A-003_TIME_96B`        | P2A-003 | ❌ Rejected        | 0.17     | −245     | 66%          | 83%     | +2.01 | −59.10 | −59.38    | 30     | **Identical to 48B/P1** — time exit not firing     |
| 9   | `P2A-004_DEPTH_L3`        | P2A-004 | ❌ Rejected        | 0.17     | −245     | 66%          | 83%     | +2.01 | −59.10 | −59.38    | 30     | Depth L3 only; **same as P1** — no exit layer      |
| 10  | `P2A-005_CD_10B`          | P2A-005 | ❌ Rejected        | 1.00     | −7       | 32%          | 66%     | +2.13 | −4.07  | −8.09     | 1019   | BSL $20 + 10b SL cooldown; Jan–Jul                 |
| 11  | `P2A-ALL_FULL`            | P2A-ALL | ❌ Rejected        | 1.00     | +6       | 28%          | 42%     | +2.23 | −1.61  | −5.98     | 1882   | Full stack worse than candidate                    |
| 12  | `P2B-001_HTF_H1`          | P2B-001 | ❌ Rejected        | 0.85     | −171     | 57%          | 67%     | +2.26 | −5.35  | −24.25    | 662    | H1 EMA200 + BSL_25; **worse than candidate**       |
| 13  | `P2B-002_HTF_H4`          | P2B-002 | ❌ Rejected        | 0.79     | −166     | 61%          | 64%     | +2.26 | −5.09  | −11.64    | 427    | H4 EMA200 + BSL_25; **worse than H1**              |
| 14  | `P2B-003_HTF_SLOPE`       | P2B-003 | ❌ Rejected        | 0.85     | −171     | 57%          | 67%     | +2.26 | −5.35  | −24.25    | 662    | **Identical to H1** — slope inert on EMA200        |
| 15  | `P2C-001_REG_ADX25`       | P2C-001 | ❌ Rejected        | 0.80     | −162     | 53%          | 63%     | +3.53 | −7.45  | —         | 287    | ADX>25; −65% trades, worse PF/DD                   |
| 16  | `P2C-001_REG_ADX30`       | P2C-001 | 📁 2025 only       | 1.00     | +3       | 33%          | 70%     | +2.59 | −6.12  | −25.18    | 505    | 2025 slice — superseded by row 22                    |
| 17  | `P2C-002_REG_ATRP70`      | P2C-002 | 📁 2025 only       | 1.34     | +181     | 18%          | 73%     | +2.79 | −5.65  | −17.17    | 349    | 2025 slice — **fails 2026** (see row 21)           |
| 18  | `P2C-003_REG_EMASEP_3ATR` | P2C-003 | ❌ Rejected        | 0.95     | −61      | 33%          | 69%     | +2.27 | −5.24  | −23.85    | 715    | EMA sep >3×ATR; worse than ATRP70                  |
| 19  | `P2C-004_REG_SLOPE`       | P2C-004 | ❌ Rejected        | 1.15     | +28      | 8%           | 68%     | +5.73 | −10.85 | −23.78    | 57     | EMA20 slope; **57 trades** — check date range      |
| 20  | `P2C-005_BRK_SUSPEND`     | P2C-005 | ❌ Rejected        | 1.10     | +112     | 17% / 21% eq | 72%     | +2.22 | −5.24  | −27.04    | 753    | Breakout >3×ATR; PF fails vs ATRP70                |
| 21  | `P2C002_ATRP70`           | P2C-002 | ❌ Rejected 2026   | 0.94     | −38      | ~32% / ~35% eq | 65%     | —     | —      | —         | 376    | 2026 — ATR gate hurts edge vs BSL_25                 |
| 22  | `P2C-001_REG_ADX30`       | P2C-001 | 🏆 **Candidate**   | **1.36** | **+221** | **18% / 21% eq** | **71%** | +2.77 | −5.04  | −8.65     | 424    | **2026 canonical** — PF ~1.3 target met              |


---

## Remaining Test Queue

**P2A ✅ · P2B ✅ · P2C ✅ (2026).** Candidate: **`P2C-001_REG_ADX30` / BSL_25** · PF 1.36. ATRP70 closed.


| Phase     | Next action                                       |
| --------- | ------------------------------------------------- |
| **P2C**   | ✅ Closed — BSL_25 wins 2026; ATRP70 rejected      |
| **P2D**   | Session filters on **BSL_25** base                |
| **P2E/F** | Only if G2 not yet met after filters              |
| **P3/P4** | After G3                                          |


---

## Lessons from Testing (so far)

### P2A-001 implementation note (v1.11)

- `InpSlUseGridStructure=true` (default) — SL placed beyond remaining grid depth, not fixed ATR from entry.
- `InpSlUseGridStructure=false` — legacy fixed ATR SL (`_RAW` preset). **Do not use for production.**

### Pattern shift after P2A-001


| Era               | Profile                             | Problem                                        |
| ----------------- | ----------------------------------- | ---------------------------------------------- |
| P1 baseline       | High WR, huge tail losses           | Steamroller                                    |
| P2A-001 RAW       | 0% WR, tiny losses                  | SL too tight                                   |
| **P2A-001 ATR20** | Low WR, small losses, decent wins   | Churn — 102 max consecutive losses             |
| **P2A-001 ATR15** | **PF 1.02, 42% WR, bounded losses** | Higher DD (26%), 1,819 trades, avg loss −$1.60 |


### P2A-001 ATR15 vs ATR20 (head-to-head)


| Metric             | ATR15               | ATR20               | Better             |
| ------------------ | ------------------- | ------------------- | ------------------ |
| Profit factor      | **1.02**            | 0.91                | ATR15              |
| Net P/L            | **+$39**            | −$56                | ATR15              |
| Win rate           | **42%**             | 21%                 | ATR15              |
| Avg win / avg loss | 2.25 / 1.60 (1.4:1) | 2.28 / 0.66 (3.4:1) | ATR20 (R:R)        |
| Max DD             | 26%                 | **22%**             | ATR20              |
| Trades             | 1,819               | **1,229**           | ATR20 (less churn) |
| Largest loss       | −6.10               | **−4.67**           | ATR20              |
| Sharpe             | **0.34**            | −1.85               | ATR15              |
| Max consec. losses | 45                  | 102                 | ATR15              |


Tighter structure buffer (1.5×) → more stops but **better win rate** and net profit. Wider buffer (2.0×) → fewer stops, better R:R, but not profitable on shorter sample.

### P2A-001 ATR15 vs P2A-ALL_FULL (same Jan–Jul window)


| Metric             | ATR15 isolate | ALL_FULL    | Better              |
| ------------------ | ------------- | ----------- | ------------------- |
| Profit factor      | **1.02**      | 1.00        | ATR15               |
| Net P/L            | **+$39**      | +$6         | ATR15               |
| Win rate           | 42%           | 42%         | Tie                 |
| Avg win / avg loss | 2.25 / 1.60   | 2.23 / 1.61 | Tie                 |
| Max DD             | **26%**       | 29%         | ATR15               |
| Trades             | **1,819**     | 1,882       | ATR15               |
| Sharpe             | **0.34**      | 0.05        | ATR15               |
| Largest loss       | −6.10         | **−5.98**   | ALL_FULL (marginal) |


**Conclusion:** ~~Use ATR15 isolate as P2A base~~ **Superseded by BSL_25.** Stacked P2A layers do not improve over basket SL alone. P2B+ filters next.

**Recommendation:** Basket SL $25 outperforms $15 on risk-adjusted basis. **Use BSL_25 as P2A base** for remaining isolates and P2B.

### P2A-002 BSL_25 vs BSL_15 vs ATR15 (basket SL sweep)


| Metric             | BSL_25 🏆   | BSL_15      | ATR15       |
| ------------------ | ----------- | ----------- | ----------- |
| Profit factor      | **1.15**    | 1.06        | 1.02        |
| Net P/L            | **+$165**   | +$87        | +$39        |
| Max DD             | **18%**     | 43% ❌       | 26%         |
| Win rate           | **73%**     | 61%         | 42%         |
| Avg win / avg loss | 2.15 / 4.98 | 2.16 / 3.14 | 2.25 / 1.60 |
| Trades             | **831**     | 1,166       | 1,819       |
| Sharpe             | **1.08**    | 0.73        | 0.34        |
| Largest loss       | −7.01       | −9.39       | −6.10       |
| Gate G1            | **Pass**    | Fail (DD)   | Pass        |


**Mechanism:** Wider basket SL ($25 vs $15) lets baskets recover before stop-out → higher WR, lower DD, fewer trades, best net. Still no per-trade SL — legs float until basket exit.

### P2A-003 TIME_48B / TIME_96B — time exit isolate (rejected)


| Metric   | TIME_48B | TIME_96B | P1 Baseline | BSL_25 candidate |
| -------- | -------- | -------- | ----------- | ---------------- |
| PF       | 0.17     | 0.17     | 0.17        | 1.15             |
| Net P/L  | −$245    | −$245    | −$245       | +$165            |
| Trades   | 30       | 30       | 30          | 831              |
| Avg loss | −$59.10  | −$59.10  | −$59.10     | −$4.98           |


**Both variants identical to P1 baseline** — 30 trades, steamroller profile (25W then 5 tail losses). Jan entries → Jul losses on chart despite 48/96-bar cap.

**🐛 Likely bug:** `OnBasketStart()` is called *after* `OpenMarket()` succeeds, so `HasOpenPositions()` is already true and the basket start time is never set → `AgeBars()` always returns 0 → time exit never fires. **48B vs 96B producing bit-identical results confirms the layer had zero effect.**

**Fix needed before re-testing P2A-003:** set basket start time on first fill (check position count == 1 after open, or call `OnBasketStart` before exposure updates).

**Conclusion:** Time exit is a **supplement**, not a replacement for SL — but current P2A-003 isolates are **invalid** until the basket-age bug is fixed. Do not use P2A-003 in isolation.

### P2A-004 DEPTH_L3 — max entry depth isolate (rejected)


| Metric   | DEPTH_L3 | P1 Baseline | BSL_25 candidate |
| -------- | -------- | ----------- | ---------------- |
| PF       | 0.17     | 0.17        | 1.15             |
| Net P/L  | −$245    | −$245       | +$165            |
| Trades   | 30       | 30          | 831              |
| Avg loss | −$59.10  | −$59.10     | −$4.98           |


**Identical to P1 baseline** — caps grid to L1–L3 (no L4/L5 adds) but provides **no exit mechanism**. Losing baskets still float Jan→Jul.

**Implementation looks correct** (`level.index > m_max_entry_depth` skip in EntryEngine). Bit-identical results likely mean **no basket in this window reached L4/L5 anyway** — depth cap had nothing to cut. Re-test on full Jan–Jul range after fixing date-range consistency; expect rejection without SL regardless.

**Conclusion:** Depth cap limits **exposure growth**, not **loss containment**. Use only as a supplement on top of BSL_25, not in isolation.

### P2A-005 CD_10B — SL cooldown isolate (rejected)


| Metric    | CD_10B                    | BSL_25 candidate         | BSL_15 alternate         |
| --------- | ------------------------- | ------------------------ | ------------------------ |
| Config    | BSL $20 + 10b SL cooldown | BSL $25 + 1b SL cooldown | BSL $15 + 1b SL cooldown |
| PF        | 1.00                      | **1.15**                 | 1.06                     |
| Net P/L   | −$7                       | **+$165**                | +$87                     |
| Max DD    | 32%                       | **18%**                  | 43%                      |
| Win %     | 66%                       | **73%**                  | 61%                      |
| Trades    | 1,019                     | 831                      | 1,166                    |
| Avg W / L | +2.13 / −4.07             | +2.15 / −4.98            | +2.16 / −3.14            |
| Sharpe    | −0.05                     | **1.08**                 | 0.73                     |


**First P2A isolate on full Jan–Jul window** (1,019 trades, both directions). Not a pure cooldown test — preset includes **BSL $20** so cooldown can fire.

**Mechanism:** 10-bar pause after basket SL blocks re-entry into recovering setups. Combined with tighter $20 basket SL vs $25 → more stop-outs, fewer recoveries, breakeven net.

**Conclusion:** Keep **1-bar** post-SL cooldown (BSL_25 default). Extended cooldown is **harmful**, not protective. Do not add CD_10B to production stack.

### P2A phase summary (complete)


| Layer        | Isolate             | Verdict                                   |
| ------------ | ------------------- | ----------------------------------------- |
| Basket SL    | BSL_15 / **BSL_25** | **BSL_25 wins** — only profitable isolate |
| Per-trade SL | ATR15 / ATR20       | ATR15 alternate; structure SL viable      |
| Time exit    | 48B / 96B           | Rejected — bug + no SL; re-test after fix |
| Depth cap    | L3                  | Rejected alone — no exit                  |
| SL cooldown  | CD_10B              | Rejected — hurts vs BSL_25                |
| Full stack   | ALL_FULL            | Rejected — layers erode edge              |


**P2A base for P2B+:** `P2A-002_BSL_25`. Fix `OnBasketStart` bug before re-testing time exit supplements.

### P2A-002 BSL_15 vs P2A-001 ATR15 (basket SL only vs structure SL only)


| Metric             | BSL_15          | ATR15           | Notes                        |
| ------------------ | --------------- | --------------- | ---------------------------- |
| Profit factor      | **1.06**        | 1.02            | BSL_15                       |
| Net P/L            | **+$87**        | +$39            | BSL_15 — best net so far     |
| Win rate           | **61%**         | 42%             | BSL_15 — no per-leg SL       |
| Avg win / avg loss | 2.16 / **3.14** | **2.25 / 1.60** | BSL_15: bigger basket losses |
| Max DD             | 43% ❌           | **26%** ✅       | ATR15 passes G1              |
| Trades             | **1,166**       | 1,819           | BSL_15 — less churn          |
| Sharpe             | **0.73**        | 0.34            | BSL_15                       |
| Largest loss       | −9.39           | **−6.10**       | ATR15                        |
| Gate G1            | **Fails** (DD)  | **Passes**      | —                            |


**Mechanism:** BSL_15 has **no per-trade SL** — legs run until basket TP (+$10) or basket SL (−$15). Higher win rate but larger average loss when basket stops out. Net profit higher; drawdown unacceptable for G1.

**Recommendation:** ~~Keep ATR15 as candidate~~ **Superseded by BSL_25.** Optional future hybrid `ATR15 + BSL_25` — test only if a P2B+ filter improves candidate first.

### Session signals (from ATR15 + BSL_25 runs — apply to P2D)


| Window             | Observation                  | Future filter      |
| ------------------ | ---------------------------- | ------------------ |
| Hour 0 (Asia open) | High entries, net negative   | P2D candidate      |
| Hours 6–12         | Core activity                | Keep               |
| Hour 13 (US)       | High volume, mixed           | Monitor            |
| Hours 12–15        | Peak entries (EU/US overlap) | Core session       |
| Hours 18–21        | Mostly losses                | P2D candidate      |
| Friday             | Losses > profits             | P2D-002 candidate  |
| Mar                | Highest trade volume         | Monitor            |
| Jan vs Jul         | Jan heavy, Jul light         | Confirm test range |


---

## Executive Diagnosis (P1 baseline — historical)

The EA exhibits a classic **high win-rate / negative expectancy** profile:


| Metric             | Value                          | Implication                                 |
| ------------------ | ------------------------------ | ------------------------------------------- |
| Win rate           | 83.33% (25W / 5L)              | Entry logic finds mean-reversion pockets    |
| Profit factor      | 0.17                           | Edge is destroyed by tail losses            |
| Avg win            | +2.01                          | Wins are small and consistent               |
| Avg loss           | −59.10                         | Losses are ~29× larger than wins            |
| Largest win / loss | +2.87 / −59.38                 | No cap on adverse excursion                 |
| Max drawdown       | 65.65% balance / 78.16% equity | Account-level risk is unacceptable          |
| Total trades       | 30 (all long)                  | Strategy 2 bias active; no shorts in sample |
| MAE correlation    | 0.97                           | Underwater trades stay underwater and grow  |


**Core finding:** The EA **can** harvest small oscillations around EMA pullbacks. It **cannot** survive trend extension or grid stacking without failure containment. You are not missing entries — you are missing **downside governance**.

> Picking up pennies in front of a steamroller: 25 small wins, then 5 losses erase everything.

---

## What We Know (Fundamental Patterns)

### Wins — what is working

1. **Pullback entries in established uptrend** — All 30 trades were long; EMA20 > EMA100 filter prevented counter-trend shorts.
2. **Grid level touches below EMA** — Price dipping to ATR-spaced levels and reverting produces quick small profits.
3. **Basket TP at ~$10** — When the basket nets +$10, all legs close; average win ~$2/deal aligns with partial basket closes or single-leg wins bundled together.
4. **High MFE correlation (0.86)** — Favorable moves happen quickly when conditions suit mean reversion.
5. **Quiet / oscillating sessions** — Profits distributed across hours 4–5, 17–19 with no single dominant loss hour among winners.

### Losses — what is failing

1. **No per-trade stop loss** — Positions have SL = 0. Adverse moves are unbounded.
2. **No basket stop loss** — A underwater basket can accumulate up to `Max Open Trades` (5) with no forced exit.
3. **Grid stacking into trend** — Each new level adds exposure in the same direction as price moves away from EMA (averaging into a trend, not a range).
4. **MAE tail (0.97 correlation)** — The further price moves against the basket, the larger the eventual loss; no time or distance cut-off.
5. **Temporal risk clusters:**
  - **Hour 23** — Largest hourly loss bar (rollover / thin liquidity / spread widening).
  - **Sunday** — Largest daily loss (weekend gap / session open).
  - **Jan entry → Jul loss** — At least one position held months underwater before forced close.
6. **Streak fragility** — 25 consecutive wins, then 5 consecutive losses. A short losing streak dominates a long winning streak.

### Conditions we can infer


| Condition                                        | EA behaviour                                            | Edge quality     |
| ------------------------------------------------ | ------------------------------------------------------- | ---------------- |
| Uptrend + shallow pullback to grid level         | Quick revert toward EMA                                 | **Strong**       |
| Range / slow trend (EMA20 ≈ slope flat)          | Multiple level touches, basket TP hits                  | **Good**         |
| Trend acceleration (EMA20 steep, price extended) | Grid keeps buying lower                                 | **Poor**         |
| High ATR expansion                               | Levels too tight relative to move; stacking accelerates | **Poor**         |
| Rollover / Sunday open                           | Spread + gap risk                                       | **Avoid**        |
| Trend reversal (EMA20 crosses EMA100)            | Longs held into new downtrend                           | **Catastrophic** |


---

## When the EA Performs vs Underperforms

*Updated post-BSL_25. P1 steamroller profile fixed by basket SL; focus shifts to **which pullbacks** produce +$10 TP vs −$25 SL.*

### Performs well (optimise toward)

- **Confirmed EMA20/EMA100 trend** — both directions (BSL_25: 596 short / 423 long, shorts higher WR)
- **Shallow pullbacks L1–L2** — quickest revert to EMA; basket TP before L4/L5 stack
- **London / NY overlap** — core session for basket TP hits
- **Basket closes at +$10 TP** before deep grid stacking — ~73% of cycles
- **Moderate ADX / flat ATR** — mean-reversion regime favours small basket wins

### Underperforms (filter or block in P2B–P2D)

- **Pullback → continuation** — grid adds legs, basket drifts to −$25 SL (main anti-edge)
- **Deep grid levels (L4–L5)** — more exposure per cycle before TP or SL
- **Hour 23 / Sunday / Friday late** — session boundary risk (P2D targets)
- **ATR spike / ADX > 25** — volatility expansion; levels too tight (P2C targets)
- **Counter-HTF entries** — M5 pullback against H1 trend (P2B targets)
- **Extended SL cooldown** — blocks re-entry into recovering setups (confirmed harmful)

---

## Edge Hypothesis — validated ✅

> **Edge:** In a confirmed EMA20/EMA100 trend, shallow pullbacks to ATR-spaced levels revert enough to capture small basket profits (+$10 TP) before trend resumes.

> **Anti-edge:** When pullback becomes trend continuation or volatility expansion, grid stacking adds exposure without revert. **BSL $25** caps basket loss (~−$5 avg) instead of unbounded MAE.

**BSL_25 math (Jan–Jul):**

```
Win rate:     73%  |  Avg win: +$2.15  |  Avg loss: −$4.98  |  PF: 1.15
Basket model: ~73% of cycles hit +$10 TP; ~27% hit −$25 SL — asymmetry is acceptable
Target for P2B+: improve PF and DD by skipping bad pullback regimes, not tightening exits
```

---

## Preset Naming Convention (for streamlined testing)

Save presets in MT5 Strategy Tester / EA inputs using this format:

```
FEMA_{SYMBOL}_{TF}_{TASKID}_{VARIANT}
```


| Segment | Example   | Meaning                            |
| ------- | --------- | ---------------------------------- |
| SYMBOL  | EURUSD    | Test instrument                    |
| TF      | M5        | Chart timeframe                    |
| TASKID  | P2A-001   | Roadmap task ID (see tables below) |
| VARIANT | PSL_ATR15 | Parameter shorthand                |


**Location:** `MQL5\Profiles\Tester\`

**Phase 2A presets (implemented):**


| Preset file                                | Task ID     | What it tests                                  |
| ------------------------------------------ | ----------- | ---------------------------------------------- |
| `FEMA_EURUSD_M5_P1-BASELINE.set`           | P1-BASELINE | Phase 1 control — all P2A off                  |
| `FEMA_EURUSD_M5_P2A-ALL_FULL.set`          | P2A-ALL     | P2A-001…005 combined                           |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR15.set`     | P2A-001     | Per-trade SL — grid structure, 1.5× buffer     |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR20.set`     | P2A-001     | Per-trade SL — grid structure, 2.0× buffer     |
| `FEMA_EURUSD_M5_P2A-001_PSL_ATR15_RAW.set` | P2A-001     | Legacy fixed 1.5× ATR from entry — failed test |
| `FEMA_EURUSD_M5_P2A-002_BSL_15.set`        | P2A-002     | Basket SL = $15                                |
| `FEMA_EURUSD_M5_P2A-002_BSL_25.set`        | P2A-002     | Basket SL = $25 **(candidate / P2B+ base)**    |
| `FEMA_EURUSD_M5_P2A-003_TIME_48B.set`      | P2A-003     | Max basket age 48 bars                         |
| `FEMA_EURUSD_M5_P2A-003_TIME_96B.set`      | P2A-003     | Max basket age 96 bars                         |
| `FEMA_EURUSD_M5_P2A-004_DEPTH_L3.set`      | P2A-004     | Max entry depth L3                             |
| `FEMA_EURUSD_M5_P2A-005_CD_10B.set`        | P2A-005     | 10-bar cooldown after basket SL                |


**Phase 2B presets (v1.12 — inherit BSL_25 base):**


| Preset file                            | Task ID | What it tests              |
| -------------------------------------- | ------- | -------------------------- |
| `FEMA_EURUSD_M5_P2B-001_HTF_H1.set`    | P2B-001 | H1 EMA200 direction filter |
| `FEMA_EURUSD_M5_P2B-002_HTF_H4.set`    | P2B-002 | H4 EMA200 direction filter |
| `FEMA_EURUSD_M5_P2B-003_HTF_SLOPE.set` | P2B-003 | H1 EMA200 + slope gate     |


**Future presets (P2D+):**


| Preset file                           | Task ID | What it tests                |
| ------------------------------------- | ------- | ---------------------------- |
| `FEMA_EURUSD_M5_P2D-001_SES_NO23.set` | P2D-001 | Block hour 23 entries        |
| `FEMA_EURUSD_M5_P2E-001_EXIT_RTE.set` | P2E-001 | Return-to-EMA basket exit    |
| `FEMA_EURUSD_M5_P2E-003_TRAIL_50.set` | P2E-003 | Basket trail at 50% giveback |


**Phase 2C presets (v1.13 — inherit BSL_25 base, HTF off):**


| Preset file                                  | Task ID | What it tests                         |
| -------------------------------------------- | ------- | ------------------------------------- |
| `FEMA_EURUSD_M5_P2C-001_REG_ADX25.set`       | P2C-001 | Block when ADX(14) > 25               |
| `FEMA_EURUSD_M5_P2C-001_REG_ADX30.set`       | P2C-001 | Block when ADX(14) > 30               |
| `FEMA_EURUSD_M5_P2C002_ATRP70.set`           | P2C-002 | **2026 canonical** — ATR > 70th pct (100 bars) |
| `FEMA_EURUSD_M5_P2C-002_REG_ATRP70.set`      | P2C-002 | Legacy 2025 slice — historical row 17 only |
| `FEMA_EURUSD_M5_P2C-003_REG_EMASEP_3ATR.set` | P2C-003 | Block when |EMA20−EMA100| > 3×ATR     |
| `FEMA_EURUSD_M5_P2C-004_REG_SLOPE.set`       | P2C-004 | EMA20 slope must align with direction |
| `FEMA_EURUSD_M5_P2C-005_BRK_SUSPEND.set`     | P2C-005 | Block when |price−EMA20| > 3×ATR      |


**Testing protocol (P2B+):**

1. **Baseline for comparison:** `FEMA_EURUSD_M5_P2A-002_BSL_25` on Jan–Jul (PF 1.15, DD 18%).
2. Run **one filter change** per preset on top of BSL_25 config.
3. Log: PF, DD, net, avg W/L, trade count.
4. Promote only if **PF and max DD beat BSL_25 together**. Win rate alone is misleading.
5. Do **not** combine multiple untested filters in one preset.

---

## Implementation Roadmap (Phased with IDs)

Work one ID at a time. Do not combine IDs in a single test until the individual ID has been validated.

---

### Phase 2A — Failure Containment ✅ Complete (v1.11)

> **Objective:** Cap tail losses without removing the entry edge.  
> **Result:** **BSL_25 wins.** Basket SL is the containment layer; per-leg SL and stacked layers erode edge.  
> **Gate G1:** ✅ Pass — PF 1.15, DD 18%, largest loss −$7.01 (~3.3× avg win)


| ID          | Task                         | Status   | Verdict                                |
| ----------- | ---------------------------- | -------- | -------------------------------------- |
| **P2A-001** | Per-trade ATR / structure SL | ✅ Tested | Alternate (ATR15); not production base |
| **P2A-002** | Basket stop loss             | ✅ Tested | **BSL_25 = candidate**                 |
| **P2A-003** | Max basket age (time exit)   | ✅ Tested | Rejected — bug + supplement only       |
| **P2A-004** | Max grid depth               | ✅ Tested | Rejected alone — no exit               |
| **P2A-005** | Cooldown after basket SL     | ✅ Tested | Rejected — 10b hurts vs 1b             |
| **P2A-ALL** | Full stack combined          | ✅ Tested | Rejected — layers erode edge           |


**Production exit stack:** Basket TP $10 → Basket SL $25 → 1-bar post-SL cooldown. Per-trade SL optional supplement only.

**Code fix before re-testing P2A-003:** `OnBasketStart` basket-age bug.

---

### Phase 2B — HTF Directional Filter ✅ Implemented (v1.12)

> **Objective:** Only open pullback baskets when higher-timeframe structure agrees. Blocks entries where M5 pullback is actually counter to H1/H4 trend — the main anti-edge (pullback → continuation).  
> **Base preset:** `P2A-002_BSL_25` + one HTF gate per test.  
> **Module:** `Include/Indicators/HtfFilter.mqh` — uses last completed HTF bar (shift 1).


| ID          | Task           | Status        | Test preset         |
| ----------- | -------------- | ------------- | ------------------- |
| **P2B-001** | H1 EMA200 bias | ✅ Implemented | `P2B-001_HTF_H1`    |
| **P2B-002** | H4 EMA200 bias | ✅ Implemented | `P2B-002_HTF_H4`    |
| **P2B-003** | HTF slope gate | ✅ Implemented | `P2B-003_HTF_SLOPE` |


**Inputs:** `InpUseHtfFilter`, `InpHtfTimeframe`, `InpHtfEmaPeriod` (200), `InpHtfRequireSlope`

**Success criteria:** Fewer −$25 basket SL hits without killing +$10 TP frequency. Expect lower trade count, higher PF or lower DD.

### P2B-001 HTF_H1 — rejected vs BSL_25


| Metric    | HTF_H1        | BSL_25 candidate | Delta               |
| --------- | ------------- | ---------------- | ------------------- |
| PF        | 0.85          | **1.15**         | −0.30               |
| Net P/L   | −$171         | **+$165**        | −$336               |
| Max DD    | 57%           | **18%**          | +39pp               |
| Win %     | 67%           | **73%**          | −6pp                |
| Trades    | 662           | 831              | −169                |
| Avg W / L | +2.26 / −5.35 | +2.15 / −4.98    | similar asymmetry   |
| Sharpe    | −1.23         | **1.08**         | worse               |
| Long WR   | 55%           | —                | longs hurt more     |
| Short WR  | 73%           | —                | shorts still decent |


**Mechanism:** H1 EMA200 reduced trades (−20%) but did **not** improve basket quality — DD exploded (18% → 57%) and PF collapsed. Filter likely blocked some mean-reverting pullbacks that BSL_25 was harvesting, while remaining baskets still hit −$25 SL (largest loss −$24.25 ≈ full basket SL).

**Conclusion:** Plain H1 close>EMA200 is too blunt for this pullback-basket edge. Continue H4 / slope isolates; if they also fail, skip HTF bias and move to P2C regime gates (ADX/ATR).

### P2B-002 HTF_H4 — rejected vs BSL_25


| Metric    | HTF_H4        | HTF_H1        | BSL_25 candidate |
| --------- | ------------- | ------------- | ---------------- |
| PF        | 0.79          | 0.85          | **1.15**         |
| Net P/L   | −$166         | −$171         | **+$165**        |
| Max DD    | 61%           | 57%           | **18%**          |
| Win %     | 64%           | 67%           | **73%**          |
| Trades    | 427           | 662           | 831              |
| Avg W / L | +2.26 / −5.09 | +2.26 / −5.35 | +2.15 / −4.98    |
| Sharpe    | −1.31         | −1.23         | **1.08**         |


**Mechanism:** H4 is stricter than H1 (−49% trades vs BSL_25) but still fails Gate G1. Same asymmetry preserved; every month looks net-negative on the P/L chart. Stricter HTF bias = fewer baskets, not better baskets.

**Pattern so far:** Both H1 and H4 EMA200 filters degrade the BSL_25 edge. Expect slope gate (P2B-003) to filter even harder — run it for completeness, then move to P2C if it fails.

### P2B-003 HTF_SLOPE — rejected (identical to H1)


| Metric    | HTF_SLOPE     | HTF_H1        | BSL_25 candidate |
| --------- | ------------- | ------------- | ---------------- |
| PF        | 0.85          | 0.85          | **1.15**         |
| Net P/L   | −$171         | −$171         | **+$165**        |
| Max DD    | 57%           | 57%           | **18%**          |
| Trades    | 662           | 662           | 831              |
| Avg W / L | +2.26 / −5.35 | +2.26 / −5.35 | +2.15 / −4.98    |


**Bit-identical to P2B-001** — 1-bar H1 EMA200 slope never rejected an extra signal in this window. EMA200 moves too slowly for bar1 vs bar2 slope to matter once price is already on the correct side of the average.

### P2B phase summary (complete — all rejected)


| Preset    | PF   | Net   | DD  | Trades vs BSL_25 | Verdict           |
| --------- | ---- | ----- | --- | ---------------- | ----------------- |
| HTF_H1    | 0.85 | −$171 | 57% | −20%             | ❌ Rejected        |
| HTF_H4    | 0.79 | −$166 | 61% | −49%             | ❌ Rejected        |
| HTF_SLOPE | 0.85 | −$171 | 57% | −20%             | ❌ Rejected (= H1) |


**Lesson:** M5 EMA20/100 already supplies directional bias for this edge. Adding slow HTF EMA200 **cuts good pullback baskets** without reducing −$25 SL rate enough. Keep `InpUseHtfFilter=false` on production (BSL_25).

**Next:** P2C regime gates (ADX / ATR) on BSL_25 base — gate **volatility environment**, not a second trend filter.

---

### Phase 2C — Regime Detection & Volatility Gates ✅ Implemented (v1.13)

> **Objective:** Skip baskets when mean-reversion edge is weak — strong trends, ATR expansion, overextended EMA separation.  
> **Base preset:** BSL_25 only (`InpUseHtfFilter=false`).  
> **Module:** `Include/Indicators/RegimeFilter.mqh` — one gate per preset isolate.


| ID          | Task                    | Status        | Test preset                              |
| ----------- | ----------------------- | ------------- | ---------------------------------------- |
| **P2C-001** | ADX trend-strength gate | ✅ Implemented | `P2C-001_REG_ADX25`, `P2C-001_REG_ADX30` |
| **P2C-002** | ATR percentile gate     | ✅ Implemented | `P2C-002_REG_ATRP70`                     |
| **P2C-003** | EMA separation gate     | ✅ Implemented | `P2C-003_REG_EMASEP_3ATR`                |
| **P2C-004** | EMA slope gate          | ✅ Implemented | `P2C-004_REG_SLOPE`                      |
| **P2C-005** | Breakout suspend        | ✅ Implemented | `P2C-005_BRK_SUSPEND`                    |


**Inputs:** `InpUseAdxGate`, `InpAdxMax`, `InpUseAtrPercentileGate`, `InpUseEmaSepGate`, `InpUseEmaSlopeGate`, `InpUseBreakoutSuspend`

**Success criteria:** Fewer −$25 basket SL hits without killing +$10 TP rate. Beat BSL_25 on **PF + DD** together.

### P2C-001 REG_ADX25 — rejected vs BSL_25


| Metric    | ADX25         | BSL_25 candidate | Delta           |
| --------- | ------------- | ---------------- | --------------- |
| PF        | 0.80          | **1.15**         | −0.35           |
| Net P/L   | −$162         | **+$165**        | −$327           |
| Max DD    | 53%           | **18%**          | +35pp           |
| Win %     | 63%           | **73%**          | −10pp           |
| Trades    | 287           | 831              | −65%            |
| Avg W / L | +3.53 / −7.45 | +2.15 / −4.98    | worse asymmetry |
| Sharpe    | −1.81         | **1.08**         | worse           |
| Long WR   | 54%           | —                | weak            |
| Short WR  | 70%           | —                | better          |


**Mechanism:** ADX>25 gate slashed trade count but **removed more good pullback baskets than bad ones**. Avg loss nearly doubled vs BSL_25 (−$7.45 vs −$5.00) — remaining baskets still hit full basket SL. Hour 13 / Monday clusters show heavy losses.

**Conclusion:** ADX gate family **rejected** — wrong filter type for this edge. Looser ADX30 recovers trade count but stays breakeven with 33% DD. Use ATR percentile (ATRP70) instead.

### P2C-001 REG_ADX30 — rejected vs ATRP70 candidate


| Metric    | ADX30         | ADX25         | ATRP70 🏆     |
| --------- | ------------- | ------------- | ------------- |
| PF        | 1.00          | 0.80          | **1.34**      |
| Net P/L   | +$3           | −$162         | **+$181**     |
| Max DD    | 33%           | 53%           | **18%**       |
| Win %     | 70%           | 63%           | **73%**       |
| Trades    | 505           | 287           | 349           |
| Avg W / L | +2.59 / −6.12 | +3.53 / −7.45 | +2.79 / −5.65 |
| Sharpe    | 0.03          | −1.81         | **1.98**      |


**Mechanism:** Loosening ADX 25→30 adds back trades (+76%) and flips to breakeven, but DD remains unacceptable (33% vs 18%). ADX filters trend **strength**; this edge needs to avoid volatility **expansion** (ATRP70), not moderate ADX trends.

**ADX family closed** — do not use `InpUseAdxGate` in production stack.

### P2C phase summary (2026 — final)

| Preset | PF | Net | DD | Trades | 2026 verdict |
| ------ | --- | --- | --- | ------ | ------------ |
| **BSL_25 / ADX30** | **1.36** | **+$221** | **18%** | 424 | 🏆 **Deploy** |
| ATRP70 | 0.94 | −$38 | ~35% | 376 | ❌ Rejected |
| ADX25 | 0.80 | −$162 | 53% | 287 | ❌ Rejected (2025) |

**Lesson:** The ~1.3 PF edge is **BSL_25 + basket exits**, not regime gates. ATRP70 looked good on a 2025 slice; it **does not hold** on 2026. Do not re-test ATRP70 unless window changes.

### P2C-002 REG_ATRP70 — promoted on 2025 slice only 📁

Historical row 17. **Not valid for 2026 deployment.** See row 21.

### P2C-003 REG_EMASEP_3ATR — rejected vs ATRP70


| Metric    | EMASEP_3ATR   | ATRP70 🏆     |
| --------- | ------------- | ------------- |
| PF        | 0.95          | **1.34**      |
| Net P/L   | −$61          | **+$181**     |
| Max DD    | 33%           | **18%**       |
| Win %     | 69%           | **73%**       |
| Trades    | 715           | 349           |
| Avg W / L | +2.27 / −5.24 | +2.79 / −5.65 |
| Sharpe    | −0.41         | **1.98**      |


**Mechanism:** Blocking when EMA20−EMA100 > 3×ATR removes overextended-trend baskets but keeps the bad ones — same steamroller asymmetry (69% WR, avg loss 2.3× avg win). More trades than ATRP70 (+105%) with worse quality.

**Conclusion:** EMA separation gate is wrong filter — edge needs moderate EMA spread for pullback grids. Do not stack on ATRP70.

### P2C-005 BRK_SUSPEND — rejected vs ATRP70


| Metric            | BRK_SUSPEND   | ATRP70 🏆     |
| ----------------- | ------------- | ------------- |
| PF                | 1.10          | **1.34**      |
| Net P/L           | +$112         | **+$181**     |
| Max DD (bal / eq) | 17% / **21%** | **18% / 18%** |
| Win %             | 72%           | **73%**       |
| Trades            | 753           | 349           |
| Avg W / L         | +2.22 / −5.24 | +2.79 / −5.65 |
| Sharpe            | 0.78          | **1.98**      |


**Mechanism:** Blocking when price−EMA20 > 3×ATR is profitable (+$112) but **dilutes** the ATRP70 edge — more trades (+116%), lower PF, worse equity DD. Overlap with ATR percentile gate; breakout block is redundant once vol expansion is already filtered.

**Conclusion:** Do not stack BRK_SUSPEND on ATRP70. Volatility filter (ATRP70) is sufficient.

### P2C-004 REG_SLOPE — rejected vs ATRP70


| Metric    | SLOPE          | ATRP70 🏆     |
| --------- | -------------- | ------------- |
| PF        | 1.15           | **1.34**      |
| Net P/L   | +$28           | **+$181**     |
| Max DD    | 8% eq          | **18%**       |
| Win %     | 68%            | **73%**       |
| Trades    | **57**         | 349           |
| Avg W / L | +5.73 / −10.85 | +2.79 / −5.65 |
| Sharpe    | 1.79           | **1.98**      |


**⚠️ Date range check:** Only 57 trades, entries Jan–Feb only on chart — likely **shorter window** than ATRP70 Jan–Jul batch. Re-run on full range to confirm; PF still below ATRP70.

**Mechanism:** EMA20 slope alignment over-filters — cuts trade count by 84% vs ATRP70. Lower DD (8%) but PF 1.15 and +$28 net don't beat candidate. Worse loss asymmetry (avg loss 1.9× avg win).

**Conclusion:** Slope gate is wrong filter for M5 pullback edge (same lesson as HTF slope). Do not use.

### P2C phase summary (2025 historical — superseded by row 22)


| Preset      | PF       | Net       | DD      | Trades | 2025 verdict      |
| ----------- | -------- | --------- | ------- | ------ | ----------------- |
| ADX25       | 0.80     | −$162     | 53%     | 287    | ❌                 |
| ADX30       | 1.00     | +$3       | 33%     | 505    | ❌                 |
| ATRP70      | 1.34     | +$181     | 18%     | 349    | 📁 2025 only       |
| EMASEP      | 0.95     | −$61      | 33%     | 715    | ❌                 |
| SLOPE       | 1.15     | +$28      | 8%*     | 57     | ❌ (*short window) |
| BRK_SUSPEND | 1.10     | +$112     | 17%/21% | 753    | ❌                 |


**P2C verdict (2026):** **BSL_25 stack wins.** Regime gates do not beat bare BSL_25 on 2026. Production stack: **`P2A-002_BSL_25`** (PF 1.36, row 22).

**Next:** P2D session filters on **BSL_25** base.

---

### Phase 2D — Session & Time Filters

> **Objective:** Block entries in windows where basket TP rate drops or −$25 SL rate rises. Session filters do not change exit logic — they prevent bad baskets from opening.  
> **Base preset:** BSL_25 (`P2A-002_BSL_25` / row 22 benchmark PF 1.36).


| ID          | Task                | Module(s) | Description                                           | Test preset          | Priority            |
| ----------- | ------------------- | --------- | ----------------------------------------------------- | -------------------- | ------------------- |
| **P2D-001** | Block rollover hour | `Filters` | No new legs 22:00–00:00 broker time (hour 23 losses). | `P2D-001_SES_NO23`   | **1**               |
| **P2D-002** | Friday close block  | `Filters` | No new baskets after Friday 20:00.                    | `P2D-002_SES_NOFRI`  | 2                   |
| **P2D-003** | Sunday open block   | `Filters` | No entries first 2 hours Sunday.                      | `P2D-003_SES_NOSUN`  | 3                   |
| **P2D-004** | Session whitelist   | `Filters` | London (08–12) + NY (13–17) only.                     | `P2D-004_SES_LDN_NY` | 4 — may over-filter |


---

### Phase 2E — Exit Mode Expansion

> **Objective:** Tune basket exit asymmetry. **Caution:** BSL_25 already optimises TP/SL balance — new exit modes must beat it on PF + DD, not just reduce avg loss.  
> **Base preset:** BSL_25 + promoted P2B/C/D stack.


| ID          | Task                   | Module(s)              | Description                                                            | Test preset            | Priority                 |
| ----------- | ---------------------- | ---------------------- | ---------------------------------------------------------------------- | ---------------------- | ------------------------ |
| **P2E-001** | Return-to-EMA exit     | `ExitEngine`           | Close basket when price returns to EMA20 (natural mean-revert target). | `P2E-001_EXIT_RTE`     | **1 — aligns with edge** |
| **P2E-003** | Basket trailing profit | `ExitEngine`           | Trail after basket profit > 50% of TP; exit on giveback.               | `P2E-003_TRAIL_50`     | 2                        |
| **P2E-002** | Per-trade ATR TP       | `ExitEngine`           | TP each leg at 0.5–1.0× ATR — **conflicts with basket model**.         | `P2E-002_TPT_ATR05`    | Low — test last          |
| **P2E-004** | Partial basket close   | `ExitEngine`           | Close best leg at 1× ATR; rest to basket TP.                           | `P2E-004_PARTIAL_1LEG` | Low                      |
| **P2E-005** | Exit mode selector     | `Config`, `ExitEngine` | Enum: BasketTP / RTE / Trail.                                          | `P2E-005_MODE_{name}`  | After isolates           |


**Deprioritised:** Per-leg TP (P2E-002) breaks the basket-exit model that makes BSL_25 work.

---

### Phase 2F — Entry Quality & Grid Refinement

> **Objective:** Fewer, higher-quality pullback baskets — shallower grids, better spacing, confirmation. Reduces −$25 SL frequency without touching exit stack.  
> **Base preset:** BSL_25 + promoted filters.


| ID          | Task                  | Module(s)                   | Description                                                    | Test preset                                | Priority        |
| ----------- | --------------------- | --------------------------- | -------------------------------------------------------------- | ------------------------------------------ | --------------- |
| **P2F-001** | Wider grid spacing    | `GridManager`               | ATR multiplier 1.0 → 1.5 → 2.0 (fewer, deeper pullbacks only). | `P2F-001_GRID_ATR15`, `P2F-001_GRID_ATR20` | **1**           |
| **P2F-004** | Candle confirmation   | `EntryEngine`               | Level touch + bullish/bearish close.                           | `P2F-004_CONFIRM`                          | 2               |
| **P2F-003** | RSI exhaustion filter | `Indicators`, `EntryEngine` | No buy RSI > 70; no sell RSI < 30.                             | `P2F-003_RSI_EXH`                          | 3               |
| **P2F-002** | One entry per level   | `GridManager`               | Enforce no re-fire until basket closes.                        | `P2F-002_1PERLEVEL`                        | Verify existing |
| **P2F-005** | Risk-based sizing     | `LotSizing`                 | `InpRiskPercent` scaled to basket SL distance.                 | `P2F-005_RISK_1PCT`                        | After G2 pass   |


---

### Phase 3 — Execution & Strategy Expansion

> **Objective:** Deferred from Phase 1. Enter only after **G2 pass** (PF ≥ 1.0, DD ≤ 25%) on BSL_25 + filter stack. Do not add complexity to an unprofitable base.


| ID         | Task                         | Description                                                                                            | Test preset           |
| ---------- | ---------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------- |
| **P3-001** | Pending-order grid           | Limits at grid levels; rebuild on EMA shift ≥ 0.25×ATR. May improve fill quality on shallow pullbacks. | `P3-001_PENDING_GRID` |
| **P3-002** | Strategy mode switching      | Enum for Strategy 1/2/3/4/5/6.                                                                         | `P3-002_STRAT_{n}`    |
| **P3-003** | Strategy 3 symmetric grid    | Bidirectional range grid + ADX gate.                                                                   | `P3-003_STRAT3_SYM`   |
| **P3-004** | Strategy 5 adaptive spacing  | ATR percentile widens grid.                                                                            | `P3-004_STRAT5_ADAPT` |
| **P3-005** | Strategy 6 breakout recovery | Auto suspend + re-anchor (extends P2C-005).                                                            | `P3-005_STRAT6_BRK`   |


---

### Phase 4 — Portfolio & Scale

> **Objective:** Scale the validated basket-exit edge across symbols. Requires G3 pass (PF ≥ 1.2, 2+ symbols).


| ID         | Task                      | Description                           |
| ---------- | ------------------------- | ------------------------------------- |
| **P4-001** | Multi-symbol portfolio    | One EA per chart; shared risk budget. |
| **P4-002** | Correlation guard         | Block if correlated pair in drawdown. |
| **P4-003** | Walk-forward optimisation | Per-regime parameter sets (not ML).   |


---

## Recommended Implementation Order

Driven by BSL_25 learnings: **regime gates first**, exit tweaks last, no stacked untested layers.

```
── P2A complete ──
BSL_25     Basket SL $25                    ✅ candidate (PF 1.15, DD 18%)

── P2B: when to open baskets ──
P2B-001    H1 EMA200 filter                 ❌ rejected
P2B-002    H4 EMA200 filter                 ❌ rejected
P2B-003    HTF slope gate                   ❌ rejected (= H1)

── P2C: skip bad MR regimes ──
P2C-001    ADX gate (< 25 / 30)             ← next test
P2C-002    ATR percentile gate
P2C-003    EMA separation gate
P2C-004    EMA slope gate
P2C-005    Breakout suspend

── P2D: session windows ──
P2D-001    Block hour 23
P2D-002    Friday close block

── P2E: exit tuning (only if filters plateau) ──
P2E-001    Return-to-EMA exit               aligns with pullback edge
P2E-003    Basket trailing profit

── P2F: entry quality ──
P2F-001    Wider grid spacing
P2F-004    Candle confirmation
P2F-005    Risk-based sizing                after G2

── Phase 3+ (after G2/G3) ──
P3-001     Pending-order grid
P4-001     Multi-symbol
```

**Do not revisit:** P2A full stack, per-leg SL as primary exit, extended SL cooldown, time exit until `OnBasketStart` fixed.

---

## Metrics to Track per Preset (your testing sheet)


| Field                | Why                                              |
| -------------------- | ------------------------------------------------ |
| Preset name          | Traceability                                     |
| Profit factor        | Primary success metric                           |
| Max DD %             | Failure containment check                        |
| Win rate             | Secondary (do not optimise alone)                |
| Avg win / avg loss   | Asymmetry ratio (target < 5:1)                   |
| Largest loss         | Must be bounded after P2A                        |
| Trade count          | Ensure filters do not over-filter to < 10 trades |
| Long / short split   | Confirm bias matches regime                      |
| Avg basket legs      | Stacking depth per cycle                         |
| Avg hold time (bars) | Time exit effectiveness                          |
| PF by hour (manual)  | Session filter validation                        |
| PF by grid level     | Depth filter validation                          |


---

## Decision Gates (when to advance phases)


| Gate                   | Criteria                                            | Status                               | Action             |
| ---------------------- | --------------------------------------------------- | ------------------------------------ | ------------------ |
| **G1** — P2A complete  | PF ≥ 0.8, max DD ≤ 35%, largest loss bounded        | ✅ **Pass** (BSL_25: PF 1.15, DD 18%) | Proceed to P2B     |
| **G2** — After P2B+C+D | PF ≥ 1.0, max DD ≤ 25% on filter stack              | ⏳                                    | Proceed to P2E/F   |
| **G3** — After P2E+F   | PF ≥ 1.2, Sharpe > 0, 2+ symbols validated          | ⏳                                    | Proceed to Phase 3 |
| **G4** — Phase 3       | Pending grid improves fill rate without DD increase | ⏳                                    | Proceed to Phase 4 |


If **G2 fails** after P2B+C+D: edge may be EURUSD M5-specific — test GBPUSD / XAUUSD on BSL_25 before more complexity.

---

## Quick Reference — Phase 1 vs Phase 2 Boundary


| Capability         | Phase 1     | Phase 2A (v1.11)                    |
| ------------------ | ----------- | ----------------------------------- |
| Per-trade SL       | ❌           | ✅ P2A-001 + `InpSlUseGridStructure` |
| Basket SL          | ❌           | ✅ P2A-002                           |
| Time exit          | ❌           | ✅ P2A-003                           |
| Max entry depth    | ❌           | ✅ P2A-004                           |
| SL cooldown        | ❌           | ✅ P2A-005                           |
| HTF filter         | ❌           | ✅ P2B-001…003 (v1.12)               |
| ADX / ATR regime   | ❌           | ✅ P2C-001…005 (v1.13)               |
| Session filter     | ❌           | P2D-*                               |
| Return-to-EMA exit | ❌           | P2E-001                             |
| Trailing basket    | ❌           | P2E-003                             |
| Risk % sizing      | Stub only   | P2F-005                             |
| Auto SUSPENDED     | Manual only | P2C-005                             |
| Pending grid       | ❌           | P3-001                              |
| Strategy switching | ❌           | P3-002                              |


---

## Next Step


|                |                                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------------- |
| **Candidate**  | **`FEMA_EURUSD_M5_PRODUCTION`** 🏆 · PF **1.36** · +$221 |
| **P2C**        | ✅ Closed — BSL_25 wins 2026; ATRP70 rejected                                      |
| **v1.14 fix**  | Grid rebuild deferred while basket open — prevents duplicate L1/L2 on new M5 bar |
| **Next phase** | **P2D** — session filters on **BSL_25** base                                     |


