# FEMA — System Profile for EURUSD

**Status:** Production locked · Phase 2 complete  
**Preset:** `FEMA_EURUSD_M5_PRODUCTION` (alias `P2C-001_REG_ADX30`)  
**Load:** `FEMA_EURUSD_M5_PRODUCTION.ini` · `Presets/PRODUCTION.set`  
**Canonical window:** `2026.01.01` – `2026.07.31` · EURUSD M5 · $400 · 1:500 · Every tick · `ProfitInPips=0`  
**EA version at lock:** v1.20  

**Journal must show:** `adx_gate=on` · `bsl=25` · `InpUseAdxGate=true` · `InpAdxMax=30`  
Without ADX gate you get bare BSL_25 (PF 1.27, +$176) — not PRODUCTION.

---

## 1. System profile

### What it is

FEMA on EURUSD is a **Strategy 2 — Pullback Continuation** floating EMA grid:

| Layer | Behaviour |
| ----- | --------- |
| **Bias** | EMA20 vs EMA100 — buy grids only in uptrend, sell grids only in downtrend |
| **Center** | EMA20 (rebuild on new bar if EMA shifts ≥ 0.25 × ATR) |
| **Spacing** | ATR(14) × 1.0 · 5 levels · max 5 open trades · 1 fill per level |
| **Entry** | Market orders when price touches a grid level (no pendings) |
| **Exit (primary)** | Close **entire basket** at **+$10** TP |
| **Exit (risk)** | Close **entire basket** at **−$25** SL |
| **Regime gate** | Block new entries when ADX(14) ≥ 30 |
| **Sizing** | Fixed 0.01 lots · spread filter ≤ 30 points · 1-bar cooldown |

Legs float with **no per-leg SL**. Risk is governed at basket level only.

### Locked stack (PRODUCTION)

```
EMA20 / EMA100 trend filter
+ ATR×1.0 floating grid (5 levels, market)
+ Basket TP $10
+ Basket SL $25
+ ADX(14) < 30 gate
+ HTF off · ATR percentile off · session filters off
+ RTE / trail / candle confirm / RSI off
```

### What it is not

| Rejected idea | Evidence |
| ------------- | -------- |
| Pure mean-reversion / return-to-EMA exit | P2E-001 RTE · PF 0.54 |
| Symmetric bidirectional grid | Conflicts Strategy 2; not promoted |
| Wider ATR spacing | P2F ATR15/20 · PF 0.93–1.08 |
| HTF EMA200 filter | P2B · PF 0.79–0.85 |
| ATR percentile / tight ADX25 | P2C · hurts 2026 |
| London/NY-only sessions | P2D-004 · PF 1.05, DD 40% (Asia edge lost) |
| Basket trail | P2E-003 · PF 1.10, cuts winners |
| Candle confirmation | P2F-004 · PF 0.94, DD 51% |

### Scope of the edge

- **Symbol-specific:** EURUSD M5 only. Same PRODUCTION preset on GBPUSD → PF 0.80, −$172 (G3 fail).
- **Not a multi-pair port** without per-symbol BSL / ADX retune.

---

## 2. Edge profile

### Hypothesis (validated)

> In a confirmed EMA20/EMA100 trend, **shallow** pullbacks to ATR-spaced levels revert enough to hit **+$10 basket TP** often enough that, with **−$25 basket SL** capping failures, expectancy is positive (~PF 1.3).

### Edge mechanics

| Component | Role |
| --------- | ---- |
| **Trend filter** | Avoids fighting the dominant M5 bias |
| **Shallow grid (ATR×1.0)** | Captures L1–L2 mean-reversion; deeper spacing removes the edge |
| **Basket TP $10** | Harvests many small wins (~71% WR) |
| **Basket SL $25** | Converts steamroller tails into bounded ~−$5 avg losses |
| **ADX &lt; 30** | Light chop/trend-strength gate; +PF vs bare BSL_25 without cutting trade count |

### Where the edge lives

| Condition | Edge quality |
| --------- | ------------ |
| Confirmed trend + shallow L1–L2 pullback | **Strong** |
| Range / slow trend, multiple level touches → basket TP | **Good** |
| London / EU–US overlap (hours ~6–15) | **Core** |
| Quiet oscillating sessions | **Good** |
| Pullback that becomes continuation → stack to BSL | **Anti-edge (contained)** |
| Deep L4–L5 stacking before exit | **Weak** |
| ADX spike / ATR expansion | **Poor** |
| Hour 23 / thin liquidity / Friday late | **Elevated risk** |
| Trend acceleration away from EMA | **Poor** |

### What destroys the edge

1. **No basket SL** (P1) — avg loss −$59, PF 0.17  
2. **Tightening exits** (RTE, trail) — cuts winners faster than losses  
3. **Widening grid** — skips the shallow pullbacks that pay  
4. **Over-filtering** (HTF, ATRP70, LDN_NY whitelist) — removes Asia / good regimes  
5. **Stacked P2A layers** (per-leg SL + long cooldown + depth) — erodes PF vs BSL alone  

### Promotion gate (G1)

Promote an alternate only if **PF and max DD** both beat PRODUCTION together.  
NO23 (PF 1.40) and NOFRI (PF 1.38) beat PF/net but fail G1 on DD (+0.1–1%).

---

## 3. Trade profile

### Canonical PRODUCTION metrics (row 22)

| Metric | Value |
| ------ | ----- |
| Trades | **424** |
| Win rate | **71%** |
| Avg win | **+$2.77** |
| Avg loss | **−$5.04** |
| Largest loss | **−$8.65** |
| Payoff (avg W / \|avg L\|) | **0.55** |
| Approx. expectancy / trade | **+$0.52** |
| Profit factor | **1.36** |

```
Expectancy ≈ 0.71 × 2.77 + 0.29 × (−5.04) ≈ +$0.52 / trade
```

Classic **high win-rate / asymmetric payoff** profile: wins are frequent and small; losses are less frequent but ~1.8× larger. Edge comes from **frequency × containment**, not from R:R &gt; 1.

### Winners — what they look like

| Trait | Detail |
| ----- | ------ |
| **Trigger** | Price touches grid below EMA (long) or above EMA (short) in trend direction |
| **Path** | Shallow revert toward EMA20; basket reaches +$10 before deep stacking |
| **Typical size** | ~+$2–3 per closed deal (basket TP shared across legs / deal reporting) |
| **Depth** | Mostly L1–L2; exits before L4–L5 dominate |
| **Regime** | Moderate ADX, non-expanding ATR, oscillating pullback |
| **Sessions** | Core activity hours 6–15; also profitable pockets in quieter hours |
| **Share of cycles** | ~71% of closed trades (PRODUCTION); historically ~73% under bare BSL_25 |

**Winner narrative:** “Pennies” harvested repeatedly when the pullback is a pause, not a new leg of the trend.

### Losers — what they look like

| Trait | Detail |
| ----- | ------ |
| **Trigger** | Same entry logic — pullback that **fails to revert** |
| **Path** | Grid adds legs with price; floating P/L drifts to **−$25 basket SL** |
| **Typical size** | Avg **−$5.04**; largest logged **−$8.65** (contained vs P1 −$59) |
| **Depth** | More often involves deeper levels / multi-leg exposure |
| **Regime** | Trend continuation, volatility expansion, session boundaries |
| **Share of cycles** | ~29% of trades |

**Loser narrative:** Same setup as winners; the difference is **path after entry**. BSL turns the old steamroller into a fixed-size failure.

### Evolution: P1 steamroller → PRODUCTION

| | P1 (no SL) | PRODUCTION (BSL25 + ADX30) |
| - | ---------- | -------------------------- |
| Win % | 83% | 71% |
| Avg win | +$2.01 | +$2.77 |
| Avg loss | **−$59.10** | **−$5.04** |
| Largest L | −$59.38 | −$8.65 |
| PF | 0.17 | **1.36** |
| Max DD | 66% / 78% eq | **18% / 21% eq** |

The entry edge was always present. **Failure containment** made it deployable.

### Session / calendar colour (from discovery, not PRODUCTION-only)

| Window | Observation |
| ------ | ----------- |
| Hours 6–15 | Core activity / overlap |
| Hour 0 (Asia) | High entries; historically mixed/negative — but **LDN_NY whitelist kills Asia edge** (do not strip) |
| Hours 18–21 / Hour 23 | Elevated loss risk |
| Friday late | Losses &gt; profits (NOFRI near-miss; not promoted) |
| Jan vs Jul | Jan heavier volume; Jul lighter — confirm full-window tests |

---

## 4. Current performance & key metrics

### Headline (PRODUCTION · Jan–Jul 2026)

| Metric | Value |
| ------ | ----- |
| **Profit factor** | **1.36** |
| **Net P/L** | **+$221** |
| **Return on $400** | **~+55%** (7 months, tester) |
| **Max DD (balance)** | **18%** |
| **Max DD (equity)** | **21%** |
| **Win rate** | **71%** |
| **Trades** | **424** (~2.0 / day over ~212 calendar days) |
| **Sharpe** | **1.90** |
| **Avg win / avg loss** | +$2.77 / −$5.04 |
| **Largest loss** | −$8.65 |
| **Expectancy / trade** | ~+$0.52 |

### Controls & alternates (same window)

| Preset | PF | Net | DD | Role |
| ------ | -- | --- | -- | ---- |
| **PRODUCTION** | **1.36** | **+$221** | **18% / 21%** | 🏆 Locked |
| BSL_25 (ADX off) | 1.27 | +$176 | ~17% / 21% | Control — ADX adds ~+$45 PF lift |
| P2D NO23 | 1.40 | +$237 | 19% / 22% | Strong alternate — G1 fail (DD) |
| P2D NOFRI | 1.38 | +$229 | 18.1% / 21.2% | Near-miss — G1 fail (DD +0.1%) |
| ATRP70 | 0.94 | −$38 | ~32% / 35% | Rejected on 2026 |

### Risk envelope (live expectations)

| Item | Guidance |
| ---- | -------- |
| **Account model tested** | $400 · 0.01 lot · 1:500 |
| **Per-basket risk** | Cap ≈ $25 (BSL) ≈ **6.25%** of $400 test deposit |
| **Observed max DD** | ~18–21% — plan live risk around **≥ this** as a floor, not a ceiling |
| **Tail** | Largest loss −$8.65 in sample; BSL is the hard cap per basket |
| **Correlation risk** | Do not assume GBPUSD/XAUUSD behave like EURUSD |

### Deployment checklist

1. Load `FEMA_EURUSD_M5_PRODUCTION.ini` (Settings tab) or `PRODUCTION.set`  
2. Confirm journal: `v1.20+`, `adx_gate=on`, `bsl=25`  
3. Symbol **EURUSD** · TF **M5** only for this profile  
4. Demo first; do not port preset to other pairs without discovery  
5. Promote changes only under **G1** (PF **and** DD)

---

## 5. One-page summary

```
SYSTEM   Strategy 2 pullback grid · EMA20/100 · ATR×1 · market · basket TP$10 / SL$25 · ADX<30
EDGE     Shallow trend pullbacks revert to +$10 often; BSL caps the rest → PF ~1.3
WINNERS  ~71% · +$2.77 avg · L1–L2 · moderate ADX · core sessions
LOSERS   ~29% · −$5.04 avg · continuation / deep stack · capped by BSL$25
PERF     +$221 · PF 1.36 · DD 18%/21% · Sharpe 1.90 · 424 trades · Jan–Jul 2026
SCOPE    EURUSD M5 only · Phase 2 locked · G3 fail on GBPUSD port
```

---

*Source of truth for test rows: [`Edge Discovery.md`](Edge Discovery.md) · Concept lock: [`concept.md`](concept.md) · Preset: [`Presets/PRODUCTION.set`](Presets/PRODUCTION.set)*
