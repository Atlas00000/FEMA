# Baseline Profile — P1-BASELINE on EURUSD

**Role:** Characterisation of the **raw FEMA edge** — trading philosophy, market worldview, and behavioural DNA — before BSL, ADX, and session overlays.  
**Preset:** [`Presets/P1-BASELINE.set`](../Presets/P1-BASELINE.set)  
**Status:** Characterisation only · **not for deploy** · parent for Edge Rediscovery  
**Updated:** 2026-07-15  
**ERG-P0 pack:** [`ERG_P0_baseline_pack.md`](ERG_P0_baseline_pack.md) · `run_id` `20210101_P1-BASELINE_60e646e5`  
**Related:** [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) (PRODUCTION lock) · [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) · [`backtesting_guide.md`](backtesting_guide.md) · [`../AI/kb/el0_baseline_inventory.md`](../AI/kb/el0_baseline_inventory.md)

> **Baseline ≠ PRODUCTION.** This document describes what the EA *is* at its birth stack: pullback grid + basket TP, **no failure containment**. PRODUCTION is the same philosophy with BSL + ADX bolted on. Rediscovery starts here so we do not confuse *edge shape* with *deployable stack*.

---

## 1. Identity

| | |
| --- | --- |
| **Name** | P1-BASELINE |
| **Strategy class** | Strategy 2 — **Pullback Continuation** |
| **Family** | Floating EMA Grid (FEMA) |
| **Instrument / TF** | **EURUSD M5** (characterised here; not portable as-is) |
| **Role in lineage** | Row 1 Discovery · steamroller characterisation · Lane B roster seed |
| **What is on** | EMA bias · ATR grid · basket TP $10 · fixed 0.01 lot · spread filter |
| **What is off** | Basket SL · ADX · HTF · ATR% · session blocks · trail · RTE · candle · RSI |

```text
P1-BASELINE = “believe the pullback will return; scale in; take $10; survive somehow”
PRODUCTION  = same belief + “if it doesn’t return, cut at −$25” + “don’t enter when ADX is hot”
```

---

## 2. Trading philosophy (EURUSD)

### 2.1 Market worldview

FEMA’s baseline does **not** try to catch breakouts, fade every tick, or ride multi-day trends for large R multiples. It assumes:

1. **EURUSD M5 spends meaningful time oscillating inside a short-horizon trend** defined by EMA20 vs EMA100.  
2. **Pullbacks to ATR distance are usually pauses**, not reversals of the bias.  
3. **Many small, high-probability recovers** beat rare large directional bets — *if* failures can be lived with.  
4. **Microstructure noise averages out** at shallow grid spacing (ATR×1.0); the edge is statistical, not clairvoyant.

On EURUSD specifically, this worldview fits a pair that:

- Is **liquid and mean-reverting at intraday pullback scale** more often than exotic crosses  
- Still experiences **macro steamrollers** (policy, risk-on/off, thin hours) that invalidate “shallow pause” assumptions  
- Rewards **patient basket management** when price chops around EMA20 — and punishes **bag-holding** when trend expands

The baseline **trusts the chop** and **under-prepares for expansion**. That is its philosophical signature.

### 2.2 What the baseline is trying to be

| Intent | Expression |
| --- | --- |
| **Direction** | Trade **with** M5 bias only (long grids in uptrend, short in downtrend) |
| **Entry** | Scale into **pullbacks**, not breakouts |
| **Profit model** | High frequency of **small basket TPs** (~$10 whole basket) |
| **Risk model (raw)** | Hope / time / eventual mean reversion — **no hard basket fail** |
| **Execution** | Market fills at levels · no pendings · fixed micro lot |

**Philosophical one-liner:** *Pennies in a friendly EURUSD grind — until the grind becomes a freight train.*

### 2.3 What the baseline refuses to be

| Not this | Why |
| --- | --- |
| Trend-following runner | Basket TP caps winners; MFE correlation stays low |
| Pure mean-reversion to EMA exit | Return-to-EMA (RTE) was tested later and failed — baseline uses **fixed $ TP**, not “back to fair value” |
| Symmetric two-way grid | Bias filter forbids buying dips against a clear downtrend (and vice versa) |
| Martingale-by-intent | Depth increases *as price goes against*, which *behaves* like scaling — but philosophy is “average into pause,” not “double until profit” |
| Multi-pair system | Edge was discovered and characterised on **EURUSD**; portfolio thinking is out of scope for baseline |

### 2.4 Risk philosophy (the uncomfortable truth)

At P1, risk philosophy is **implicit**:

- Legs have **no per-trade stop**  
- Basket has **no SL**  
- Losers can stay open for **days to months**  
- Survival depends on **account equity absorbing MAE** until price returns or the operator/test ends  

So the baseline’s honesty is: **it optimises for being right often**, not for **being wrong safely**. That is why it is characterisation-only — and why Discovery’s first irreversible lesson was **containment before sophistication**.

---

## 3. Mechanics — how belief becomes orders

```text
                    EMA20 vs EMA100
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
         Uptrend bias              Downtrend bias
         buy-grid only             sell-grid only
              │                         │
              └────────────┬────────────┘
                           ▼
              Floating centre = EMA20
              rebuild if centre shifts ≥ 0.25×ATR
                           ▼
              Grid levels: ATR(14)×1.0 · up to 5
              1 market fill per level · max 5 opens
                           ▼
              Whole-basket close at +$10 TP
              (BSL OFF · ADX OFF · sessions OFF)
```

| Layer | Baseline behaviour | Philosophical role |
| --- | --- | --- |
| **Bias** | EMA20 vs EMA100 | “Only trade pullbacks that agree with short trend” |
| **Centre** | EMA20 floating | “Fair value drifts; grid follows it” |
| **Spacing** | ATR×1.0 · 5 levels | “Stay close enough that shallow pauses pay” |
| **Entry** | Touch → market | “Fill the pause, don’t chase breakout pendings” |
| **Winner exit** | Basket **+$10** | “Harvest often; don’t wait for home runs” |
| **Loser exit** | *None hard-coded* | “Wait for the pause thesis to come true” |

---

## 4. Nature of wins (the edge you can trust)

### 4.1 Anatomy of a baseline winner

| Trait | Typical |
| --- | --- |
| Setup | Bias on · price tags L1–L2 · pullback is a **pause** |
| Path | Revert toward EMA20 · basket equity climbs to **+$10** · flat close |
| Size | Deal-level avg win ~**$2–3** (basket TP shared across reporting) |
| Feel | Quiet, frequent, boring — “another small green” |
| Regime | Moderate movement · ADX not explosive · liquid session |

**Winner narrative:** EURUSD briefly steps away from EMA20 inside a trend; the grid catches it; mean reversion inside the bias closes the basket for a small fixed profit. Repeat.

### 4.2 What high win rate *means* philosophically

On the **2021–2025** characterisation run:

| | |
| --- | --- |
| Win rate | **~95.8%** |
| Avg win | **+$2.60** |
| Largest win | **+$11.10** |
| Corr(profit, MFE) | **0.15** |

High WR is not “prophecy.” It is the natural outcome of:

1. Taking **asymmetric easy targets** ($10 basket)  
2. Letting many interruptions resolve  
3. **Avoiding cutting winners early** with trails/RTE  

The baseline is a **frequency engine**. MFE correlation near zero says: *even when price runs further in your favour, you do not harvest it — by design.* Philosophy = **harvest reliability**, not **magnitude**.

### 4.3 Direction neutrality

Long and short win rates track closely (~97.7% / ~95.5% on that multi-year run). The edge is **structural pullback behaviour on EURUSD M5**, not a bullish EURUSD macro bet.

---

## 5. Nature of losses (the steamroller)

### 5.1 Anatomy of a baseline loser

| Trait | Typical |
| --- | --- |
| Setup | **Same entry** as a winner — bias + grid touch |
| Path | Pullback **fails**; grid adds depth; MAE grows |
| Exit | Soft / delayed / nonexistent → eventually a **large** closed loss |
| Size | Avg loss can be **~10×** avg win when uncapped |
| Feel | Slow bleed · multi-day hold · sudden “how is DD this deep?” |

**Loser narrative:** The market was not pausing — it was **continuing**. The baseline’s belief (“it will come back”) is exactly wrong; without BSL, the account finances that belief.

### 5.2 Steamroller mathematics (why philosophy fails open-ended)

From characterisation evidence:

| Window | Story |
| --- | --- |
| **2021–2025** | PF **2.21**, net **+$937**, but DD **36–40%**, avg L **−$26.61**, max L **−$152**, max hold **~297 days** — profitable **in totals**, brutal **in path** |
| **2026.01–07 (canonical)** | PF **0.17**, net **−$245**, DD **66%**, avg L ~**−$59** — same philosophy, hostile regime sample |

```text
Gross profit can look excellent
        while
a few MAE-driven losses erase months of pennies
        and
recovery factor ≈ 1 means one DD cycle ≈ all the net
```

**Philosophical reading:** The baseline **has an entry edge** and **lacks a survival contract**. Metrics that ignore path (especially on lucky windows) flatter it.

### 5.3 MAE / MFE signature

| Correlation | Reading |
| --- | --- |
| Profits vs **MAE** high (~0.76) | When wrong, **how far** price goes against you **is** the outcome |
| Profits vs **MFE** low (~0.15) | When right, **extra excursion is discarded** at fixed TP |

That is the DNA of **asymmetric containment needs**: leave winners alone (or only carefully trail); **force-cap losers**.

---

## 6. Time, sessions, and EURUSD structure

Baseline has **no session filter** — so the reports reveal the *natural* footprint of the philosophy.

### 6.1 Where the philosophy thrives

| Condition | Why it fits EURUSD baseline |
| --- | --- |
| Mild trend / oscillating pullbacks | Pause thesis true |
| London → NY overlap liquidity | Cleaner fills around ATR levels |
| Asia included | Discovery showed stripping Asia (LDN/NY-only) **hurts** the later stack — baseline earns some of its pennies quietly |
| Shallow depth (L1–L2) exits | Grid thesis validated before stacking |

### 6.2 Where the philosophy breaks

| Condition | Why |
| --- | --- |
| **Hour ~23 / rollover** | Thin book, gaps, toxic holdover — loss spikes in multi-year P1 |
| **Trend expansion / high ADX** | Pullbacks are fuel, not pauses |
| **Deep L4–L5 baskets** | Scaling into a moving train |
| **December / holiday liquidity** (observed P1) | Steamrollers cost more, mean reversion arrives late |
| **Clustered adverse days** (e.g. heavy Tuesday loss bars) | Usually **few large baskets**, not a “weekday alpha” |

### 6.3 Holding-time philosophy

Avg hold measured in **days**, max hold in **months** on raw P1 means:

> Baseline treats time as a **healer**, not a **risk factor**.

That is the opposite of a scalper’s clock. Any rediscovery that keeps “time heals” without a max-bars or BSL reintroduces bag-holding risk.

---

## 7. Behavioural profile summary

```text
PERSONALITY
  Patient · high-conviction on pullback mean reversion · stubborn on losers
  Prefers many small greens over few large ones
  Directionally disciplined (bias filter) · risk-path undisciplined (no BSL)

BELIEFS
  EURUSD M5 pullbacks to ATR×1 usually revert inside EMA20/100 trend
  Fixed $10 basket TP is “enough”
  Survival can wait

BLIND SPOTS
  Expansion regimes · thin hours · calendar illiquidity · clustered DD
  Confuses long hold with resilience

SUPERPOWER
  Entry quality / frequency when the market agrees with the pause thesis

KRYPTONITE
  Uncapped MAE · steamroller continuations · hope-based exits
```

---

## 8. Metrics dossier (characterisation — not promotion)

### 8.1 Multi-year research window (operator report)

| | **P1-BASELINE · 2021.01.01–2025.12.31** |
| --- | --- |
| Deposit / model | $400 · every tick · 100% HQ |
| Net / PF | **+$936.62 / 2.21** |
| Gross P / Gross L | +1708 / −772 |
| DD bal / eq | **36.14% / 40.55%** |
| Recovery factor | **1.10** |
| Trades / WR | **687 / 95.78%** |
| Avg W / Avg L | **+2.60 / −26.61** |
| Largest W / L | +11.10 / **−152.06** |
| Short WR / Long WR | 95.50% / 97.70% |
| Hold min / avg / max | ~3m / **~9d** / **~297d** |

### 8.2 Canonical window (Discovery / EL0)

| | **P1-BASELINE · 2026.01.01–2026.07.31** |
| --- | --- |
| Net / PF | **−$245 / 0.17** |
| WR | ~83% |
| Avg loss | ~**−$59** |
| Max DD | **~66%** bal |
| Verdict | **Rejected** — steamroller · `run_id` `20260101_P1-BASELINE_4a41623a` |

### 8.3 How to read both without lying to yourself

| Mistake | Correction |
| --- | --- |
| “PF 2.21 → deploy P1” | Path DD and 2026 collapse disagree |
| “WR 96% → edge is insane” | Uncapped losses buy that WR |
| “Ignore 2021–25 because 2026 failed” | Multi-year shows **shape** of wins/toxins for rediscovery |
| “Ignore 2026 because 2021–25 worked” | Canonical G1 is the promote bar ([`backtesting_guide.md`](backtesting_guide.md)) |

---

## 9. Lineage: baseline → contained edge

```text
P1-BASELINE          philosophy naked
        │
        │  + Basket SL $25
        ▼
P2A-002_BSL_25       same entries · failures capped
        │
        │  + ADX(14) < 30
        ▼
PRODUCTION           philosophy deployable on EURUSD (lock window)
```

| Lesson | Meaning for rediscovery |
| --- | --- |
| Entry edge predated PRODUCTION | Do not “fix” EURUSD by inventing a new strategy type |
| Containment created deployability | ERG-P1 before exotic filters |
| ADX improved BSL, didn’t replace it | Regime gate ≠ stop-loss |
| Filters that cut Asia / winners often failed | Protect frequency; don’t strip the quiet pennies |

Full PRODUCTION philosophy & lock metrics: [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md).

---

## 10. Implications for Edge Rediscovery

Work **with** this baseline personality:

| Do | Don’t |
| --- | --- |
| Cap losers (BSL, max bars) | Chase higher WR — already saturated |
| Filter toxins (23:00, expansion) that feed MAE | Over-filter sessions that fund the penny engine |
| Preserve shallow ATR×1 + bias + $10 TP DNA | Widen grid / flip to breakout chasing |
| Test one axis · respect IS/VAL/HOLD + canonical G1 | Optimise 2021–25 until PF peaks |

Task board: [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md).

---

## 11. One-page card

```text
BASELINE   P1-BASELINE · EURUSD M5 · Pullback Continuation · no BSL · no ADX
PHILOSOPHY Trade shallow pauses inside EMA20/100 bias; harvest many +$10 baskets;
           hope losers return — time as healer, not clock
WINS       Very high WR · small fixed TP · low MFE harvest · both sides
LOSSES     Rare · MAE-driven · can be huge · multi-day/month bag-holds
EURUSD FIT Liquid intraday oscillation helps; macro/thin-hour expansion hurts
2021–25    PF 2.21 · DD ~36–40% · RF 1.10 — edge shape yes, path no
2026       PF 0.17 · DD ~66% — naked philosophy fails the lock window
NEXT       Contain → regime → toxins → exits · never promote raw P1
```

---

## Related paths

| Path | Role |
| --- | --- |
| [`../Presets/P1-BASELINE.set`](../Presets/P1-BASELINE.set) | Load file |
| [`../System Profile EURUSD.md`](../System%20Profile%20EURUSD.md) | PRODUCTION personality + lock |
| [`Edge_Rediscovery_guide.md`](Edge_Rediscovery_guide.md) | Phased isolation from this baseline |
| [`backtesting_guide.md`](backtesting_guide.md) | Anti-overfit process |
| [`../AI/kb/el0_baseline_inventory.md`](../AI/kb/el0_baseline_inventory.md) | Lineage metrics |
| [`../AI/certificate_PRODUCTION_EURUSD.json`](../AI/certificate_PRODUCTION_EURUSD.json) | Locked birth certificate |
