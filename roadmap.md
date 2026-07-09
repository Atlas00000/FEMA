# FEMA Phase 1 — Execution Engine Roadmap

**Goal:** Deliver a working, single-symbol automated execution engine for Strategy 2 (Pullback Continuation) using market orders only. You handle all testing.

**Reference:** Locked decisions in `concept.md` (gap-filled section).

**Compile policy:** Do not compile mid-week. Write all files for the week, then compile once at the end and test. Every week ends with a fully compilable EA — use stubs or no-op paths for modules not yet active.

---

## Phase 1 Definition of Done

The execution engine is complete when the EA, on a single chart/symbol/timeframe:

- Reads EMA(20), EMA(100), and ATR(14) on each new bar
- Builds a floating grid centered on EMA(20) with ATR spacing (5 levels per side, trend-direction only)
- Fires market entries when price touches a grid level (buy in uptrend, sell in downtrend)
- Validates broker constraints before every order
- Enforces spread filter, max open trades, slippage, and cooldown
- Tracks positions by magic number with `FEG_L{n}_{BUY|SELL}` comments
- Closes the basket when basket TP is reached
- Logs key state/events (detailed in tester, minimal live)
- Retries failed orders up to 3 times, then aborts gracefully

---

## Explicitly Out of Scope (Do Not Build)

| Category | Deferred to later |
|----------|-------------------|
| Pending orders | Buy/sell limits, stops, modify, cancel/replace |
| Other strategies | Strategies 1, 3, 4, 5, 6 and strategy switching |
| HTF filters | EMA 200, ADX, RSI, multi-timeframe logic |
| Breakout / suspend | Real detection logic (placeholder state only) |
| Alternative exits | Return-to-EMA, per-trade ATR TP as active modes |
| AI / session / news | All filtering layers |
| Multi-symbol | Scanning, routing, portfolio, cross-chart comms |
| Adaptive optimization | Auto-tuning, regime detection |
| Risk-based sizing | Optional stub input only; fixed lots is default v1 behavior |

If a feature is not listed in **Definition of Done**, it is out of scope for Phase 1.

---

## Architecture (Minimal, No Over-Engineering)

One EA per chart. `FEMA.mq5` is a thin orchestrator; logic lives in `.mqh` includes.

```
FEMA/
├── FEMA.mq5
├── FEMA.mqproj
└── Include/
    ├── Core/
    │   ├── Config.mqh          # Input parameters + defaults
    │   ├── Types.mqh           # Enums, structs (Signal, GridLevel, Basket)
    │   ├── StateMachine.mqh    # IDLE → READY → IN_TRADE → BASKET_MANAGEMENT → COOLDOWN
    │   └── Engine.mqh          # OnInit / OnTick pipeline coordinator
    ├── Indicators/
    │   └── Indicators.mqh      # EMA fast, EMA trend, ATR handles + cache
    ├── Grid/
    │   └── GridManager.mqh     # Center, levels, rebuild rule
    ├── Trading/
    │   ├── EntryEngine.mqh     # Level touch detection + direction filter
    │   ├── ExitEngine.mqh      # Basket TP check
    │   ├── BasketManager.mqh   # Group positions, basket P/L
    │   └── TradeManager.mqh    # Open/close helpers, comment format
    ├── Risk/
    │   ├── LotSizing.mqh       # Fixed lot (v1); risk % input accepted but not active
    │   ├── Filters.mqh         # Spread, max trades, cooldown
    │   └── Exposure.mqh        # Open position count by magic
    ├── Broker/
    │   ├── SymbolInfo.mqh      # Stops level, freeze, volume, filling mode
    │   ├── Validation.mqh      # Pre-trade checks
    │   └── Execution.mqh       # CTrade wrapper, retry, slippage
    └── Utils/
        ├── Logger.mqh
        └── Helpers.mqh         # Price/lot normalization, bar detection
```

**Rules to avoid over-engineering:**

- No abstract base classes or plugin frameworks
- No dependency injection containers
- No separate files per trivial one-liner
- One responsibility per module; call downstream modules directly
- `SUSPENDED` state exists as an enum + manual input toggle only — no breakout logic behind it

---

## Execution Workflow (Target State)

```
OnTick
  │
  ├─ Helpers: is new bar?
  │     └─ yes → Indicators.Update() → GridManager.RebuildIfNeeded()
  │
  ├─ StateMachine: current state gate
  │
  ├─ Risk.Filters: spread, max trades, cooldown, equity check
  │     └─ fail → return (stay READY or COOLDOWN)
  │
  ├─ EntryEngine: price touched unreached grid level in trend direction?
  │     └─ yes → Broker.Validation → Broker.Execution (market)
  │              → TradeManager tag comment → State → IN_TRADE
  │
  ├─ BasketManager: update basket P/L
  │
  ├─ ExitEngine: basket TP hit?
  │     └─ yes → close all basket positions → COOLDOWN
  │
  └─ Logger: write tick summary (throttled in live)
```

---

## Weekly Implementation Plan

Each week: implement all listed files → **compile once** → test per the week's checklist.

---

### Week 1 — Foundation & Observability

**Objective:** Compilable EA skeleton that reads indicators, runs the state machine, and logs market data. No orders placed.

| Module | Deliverable |
|--------|-------------|
| `Config.mqh` | All Phase 1 inputs with locked defaults (EMA 20/100, ATR 14, multiplier 1.0, grid levels 5, basket TP, base lot 0.01, spread filter, slippage 5, magic number, buy/sell/both permission, log mode) |
| `Types.mqh` | `EState`, `EDirection`, `SGridLevel`, `SSignal` structs |
| `StateMachine.mqh` | State enum transitions; starts in `READY`; `SUSPENDED` via input flag only |
| `Indicators.mqh` | Create/release handles; `Update()` on new bar; expose EMA fast, EMA trend, ATR, trend direction |
| `Logger.mqh` | `LogDetailed()` / `LogMinimal()`; timestamp, EMA, ATR, state |
| `Helpers.mqh` | `IsNewBar()`, symbol point/digits helpers |
| `Engine.mqh` | Wire OnInit (indicator init, state init) and OnTick (new bar refresh + log) |
| `FEMA.mq5` | Include Engine; delegate OnInit/OnDeinit/OnTick |
| Stubs | Empty compilable stubs for Grid, Trading, Risk, Broker modules referenced by Engine but not called yet |

**End-of-week compile & test (your side):**

- [ ] EA attaches without errors
- [ ] Journal shows EMA/ATR values updating on new bar
- [ ] State reads `READY` (or `SUSPENDED` when input enabled)
- [ ] No trade attempts in logs

---

### Week 2 — Grid & Signal Logic

**Objective:** Grid builds on new bar; entry signals detected and logged. Still no orders.

| Module | Deliverable |
|--------|-------------|
| `GridManager.mqh` | Center = EMA(20); levels = center ± n × ATR × multiplier; rebuild on new bar if center shifted ≥ 0.25 × ATR; track which levels have fired |
| `EntryEngine.mqh` | Trend filter: EMA20 > EMA100 → buy only; EMA20 < EMA100 → sell only; detect level touch on tick; respect trading permission input |
| `Exposure.mqh` | Count open positions by magic (read-only this week) |
| `Engine.mqh` | Extend pipeline: after indicator update → grid rebuild → entry check → log signal (direction, level, price) |
| Stubs | `Broker/Execution.mqh` returns false; `BasketManager` no-op |

**End-of-week compile & test (your side):**

- [ ] Grid levels logged on new bar (center + 5 buy/sell levels per side)
- [ ] Grid rebuilds only when shift threshold met
- [ ] Signals logged when price crosses a level in trend direction
- [ ] Counter-trend signals suppressed (uptrend → no sell signals)
- [ ] Still zero orders sent

---

### Week 3 — Risk, Broker Validation & Market Execution

**Objective:** EA places real market orders on demo when conditions are met.

| Module | Deliverable |
|--------|-------------|
| `SymbolInfo.mqh` | Cache stops level, freeze level, min/max/step volume, filling mode, trade mode, margin mode |
| `Validation.mqh` | Pre-trade check: spread, stops distance, lot validity, trade allowed, freeze level |
| `LotSizing.mqh` | Fixed lot from input; normalize to `SYMBOL_VOLUME_STEP` |
| `Filters.mqh` | Max spread filter, max open trades, cooldown (bars since last entry) |
| `Execution.mqh` | `CTrade` market buy/sell; slippage input; 3-attempt retry with adaptive slippage; log server errors |
| `TradeManager.mqh` | Open position; set comment `FEG_L{n}_{BUY\|SELL}`; track grid level per ticket |
| `Engine.mqh` | Signal → risk filters → validation → execution → state `IN_TRADE` |
| Stubs | `ExitEngine` / `BasketManager` return false (positions stay open) |

**End-of-week compile & test (your side):**

- [ ] Market order opens on demo when level touched
- [ ] Comment format correct on open positions
- [ ] Order rejected when spread exceeds max (verify in log)
- [ ] Order rejected when max open trades reached
- [ ] Cooldown blocks rapid re-entry
- [ ] Invalid lot auto-normalized or rejected with log entry
- [ ] Failed order retries up to 3 times

---

### Week 4 — Basket Management, Exit & Completion

**Objective:** Full execution loop — entries, basket tracking, basket TP close, cooldown, error abort. Phase 1 complete.

| Module | Deliverable |
|--------|-------------|
| `BasketManager.mqh` | Group all positions by magic; sum floating P/L; basket ID per cycle |
| `ExitEngine.mqh` | Close all basket positions when combined profit ≥ basket TP input |
| `Exposure.mqh` | Full integration with max open trades gate |
| `StateMachine.mqh` | Complete transitions: `IN_TRADE` → `BASKET_MANAGEMENT` → `COOLDOWN` → `READY`; abort to `SUSPENDED` after repeated execution failures |
| `Engine.mqh` | Full pipeline from workflow diagram; no stubs remaining |
| `FEMA.mqproj` | Register all `.mqh` paths used by `FEMA.mq5` |
| Optimization inputs | Expose listed tester inputs; hardcode state machine, logging verbosity, basket internals |

**End-of-week compile & test (your side):**

- [ ] Multiple positions accumulate in one basket
- [ ] Basket TP closes all positions simultaneously
- [ ] After basket close, cooldown prevents immediate re-entry
- [ ] State machine cycles correctly through full loop
- [ ] Repeated order failures move EA to `SUSPENDED`
- [ ] Strategy Tester optimization runs on exposed inputs
- [ ] Full tick log shows: EMA, ATR, grid center, level, signal, entry price, basket ID, result, profit, spread, state

---

## Module Responsibility Summary

| Module | Responsibility | Calls |
|--------|----------------|-------|
| `Engine` | Orchestrates tick pipeline | All modules |
| `StateMachine` | Gate behavior by state | — |
| `Indicators` | Indicator handles + trend direction | — |
| `GridManager` | Level prices, rebuild rule, fired flags | `Indicators` |
| `EntryEngine` | Level touch + trend-direction filter | `GridManager`, `Indicators` |
| `Filters` | Spread, cooldown, max trades | `Exposure` |
| `LotSizing` | Normalize lot size | `SymbolInfo` |
| `Validation` | Broker constraint checks | `SymbolInfo` |
| `Execution` | Send market orders with retry | `CTrade` |
| `TradeManager` | Comment tagging, ticket tracking | — |
| `BasketManager` | Basket P/L aggregation | `TradeManager` |
| `ExitEngine` | Basket TP trigger | `BasketManager`, `Execution` |
| `Logger` | Structured logging | — |

---

## Input Parameters (v1)

| Input | Default | Optimizable |
|-------|---------|-------------|
| EMA Fast Period | 20 | Yes |
| EMA Trend Period | 100 | Yes |
| ATR Period | 14 | Yes |
| ATR Multiplier | 1.0 | Yes |
| Grid Levels | 5 | Yes |
| Basket TP (account currency) | TBD | Yes |
| Base Lot | 0.01 | Yes |
| Risk % | 0 (disabled) | Yes (inactive v1) |
| Max Spread (points) | TBD | Yes |
| Slippage (points) | 5 | No |
| Cooldown Bars | TBD | Yes |
| Max Open Trades | 5 | Yes |
| Magic Number | User set | No |
| Trade Direction | Both | No |
| Manual Suspend | false | No |
| Log Mode | Detailed / Minimal | No |

Set `Basket TP`, `Max Spread`, and `Cooldown Bars` defaults during Week 1 implementation based on instrument testing preferences.

---

## Risk Checklist (Before Calling Phase 1 Done)

- [ ] Tested on hedging and netting account types (or document supported mode)
- [ ] Tested with `SYMBOL_TRADE_STOPS_LEVEL` > 0
- [ ] Verified no pending orders are ever placed
- [ ] Verified grid levels do not affect already-open positions on rebuild
- [ ] Confirmed single-symbol binding (chart symbol only)
- [ ] No HTF, AI, session, or breakout code paths active

---

## What Comes After Phase 1 (Not Now)

- Pending-order grid (cancel/rebuild on EMA shift)
- Strategy mode switching (1, 3, 4, 5, 6)
- HTF directional filter (Phase 2)
- Return-to-EMA and per-trade ATR TP exit modes
- Risk-based position sizing (activate existing input)
- Breakout recovery / automatic `SUSPENDED`
- Multi-symbol portfolio layer

---

## Summary Timeline

| Week | Focus | Orders? | Compile |
|------|-------|---------|---------|
| 1 | Scaffold, config, indicators, state, logging | No | Once at end |
| 2 | Grid builder, trend filter, signal detection | No | Once at end |
| 3 | Broker validation, risk filters, market execution | Yes | Once at end |
| 4 | Basket TP, exit, cooldown, error abort, completion | Yes | Once at end |

**Total: 4 weeks to Phase 1 completion.** Each week produces a compilable EA; only Week 3 onward places trades.
