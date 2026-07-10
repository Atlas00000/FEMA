# FEMA — Production Preset Spec

**Purpose:** Single reference for the locked **PRODUCTION** stack and tester preset.  
**Stack ID:** `PRODUCTION` / `P2C-001_REG_ADX30` (BSL_25 + ADX>30 gate)  
**Validated EA build:** FEMA v1.16+  
**Companion docs:** `roadmap.md` (engine build), `Edge Discovery.md` (full phase history)

---

## 1. What Production Is

| Layer | Task | Setting | Role |
|-------|------|---------|------|
| **Core** | Phase 1 | EMA20/100 + ATR14 grid | Pullback continuation on M5 |
| **P2A-002** | BSL_25 | Basket SL $25, no per-leg SL | Failure containment |
| **P2C-001** | ADX30 | Block new baskets when ADX(14) > 30 | Quality filter — improves PF vs bare BSL |

**One-line config:** `BSL_25 + InpUseAdxGate=true + InpAdxMax=30`

**Must stay OFF:** per-trade SL, ATR percentile gate, HTF filter, EMA-sep/slope, breakout suspend, session filters (until P2D tested).

---

## 2. Benchmark (Jan–Jul 2026) — verified

| Metric | Production | BSL_25 control |
|--------|------------|----------------|
| **Preset** | `FEMA_EURUSD_M5_PRODUCTION` | `FEMA_EURUSD_M5_P2A-002_BSL_25` |
| **Profit factor** | **1.36** | 1.27 |
| **Net P/L** | **+$221** | +$176 |
| **Max DD** | **18%** bal / **21%** eq | ~17% bal / ~21% eq |
| **Win rate** | **71%** | 70% |
| **Trades** | **424** | 424 |
| **Sharpe** | **1.90** | 1.35 |
| **Avg win / loss** | +$2.77 / −$5.04 | +$2.76 / −$5.07 |
| **Largest loss** | −$8.65 | −$8.65 |
| **Short WR** | 76% | 74% |
| **Long WR** | 65% | 64% |

**Gate G1:** Beat control on **PF and max DD together**. Production passes.

---

## 3. Tester Settings (lock these)

| Setting | Value |
|---------|-------|
| Symbol | EURUSD |
| Timeframe | M5 |
| **From** | **2026.01.01** |
| **To** | **2026.07.31** |
| Model | Every tick (Model=0) |
| Deposit | 400 USD |
| Leverage | 1:500 |
| **Profit in pips** | **OFF** (`ProfitInPips=0`) |

**Load method:** Strategy Tester → **Settings** → `FEMA_EURUSD_M5_PRODUCTION.ini`  
**Journal must show:** `InpUseAdxGate=true` · `adx_gate=on` · `bsl=25`

**Deploy preset files:** Copy `Presets/PRODUCTION.set` to `MQL5\Profiles\Tester\FEMA_EURUSD_M5_PRODUCTION.set` and use paired `.ini` from same folder.

---

## 4. Production Inputs (all explicit)

```ini
InpUsePerTradeSl=false
InpUseBasketSl=true
InpBasketSl=25.0
InpBasketTp=10.0
InpUseAdxGate=true
InpAdxMax=30.0
InpAdxPeriod=14
InpUseAtrPercentileGate=false
InpUseHtfFilter=false
InpUseEmaSepGate=false
InpUseEmaSlopeGate=false
InpUseBreakoutSuspend=false
InpMagicNumber=20260707
InpLogMode=0
```

Full values: `Presets/PRODUCTION.set`

---

## 5. What Not To Use

| Preset | Why |
|--------|-----|
| ATRP70 (P2C-002) | PF 0.94 on 2026 — rejected |
| Bare BSL_25 without ADX | PF 1.27 — control only |
| 2025 ATRP70 row (PF 1.34) | Different window — not reproducible on 2026 |

---

## 6. Next Phase

**P2D** — session filters on **PRODUCTION** base. One filter per preset; promote only if PF **and** DD beat PRODUCTION (1.36 / 18%).
