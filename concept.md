We are building an MT5 Expert Advisor (EA) centred around the following trading concept and system architecture:
[Floating EMA Grid (FEG)

The Floating EMA Grid (FEG) is a dynamic, mathematics-based adaptive grid Expert Advisor designed to keep its trading structure centered around a continuously moving estimate of market fair value rather than a fixed price. Unlike traditional grids that anchor all pending orders to the first trade or a manually defined level, the FEG continuously recalculates its center using an Exponential Moving Average (EMA). As the EMA moves with price, the entire grid shifts accordingly, allowing the EA to remain aligned with changing market conditions. This significantly reduces one of the largest weaknesses of conventional grids: becoming trapped around outdated price levels after sustained trends.

Core Trading Edge

The primary edge is based on dynamic mean reversion around a moving equilibrium.

The assumptions are:

Price rarely moves in a straight line indefinitely.
Markets constantly oscillate around a dynamic fair value.
The EMA provides a continuously updating estimate of that fair value.
Short-term overextensions away from the EMA tend to partially retrace before continuing.

Instead of betting that price returns to an old entry price, the EA assumes price will frequently rotate around the moving EMA.

Market Type

Best suited for:

Slow trending markets
Range-bound markets
Pullback markets
Swinging trends
Low-to-medium volatility sessions

Less suitable for:

Strong one-directional momentum
News spikes
Flash crashes
Extremely thin liquidity
Recommended Instruments

Excellent

EURUSD
GBPUSD
USDJPY
AUDUSD
XAUUSD (with wider spacing)

Good

NASDAQ
DAX
US30

Avoid

Exotic currency pairs
Extremely illiquid CFDs
Recommended Timeframes

Primary timeframe

M5

Alternative

M15
M30

Higher timeframe filter

H1 EMA direction
H4 EMA direction (optional)

The grid should execute from a single timeframe while optionally using one higher timeframe only for directional filtering.

Trading Frequency

Expected trades

Normal conditions

10–40 entries/day

Active sessions

40–100 entries/day

High-volatility periods

100+ entries/day (with adaptive spacing)

The frequency depends primarily on volatility rather than fixed market hours.

Recommended Indicators
Primary Indicator
EMA (20, 50, or adaptive EMA)

Purpose

Dynamic grid center
Volatility
ATR(14)

Purpose

Grid spacing
TP distance
Emergency stop distance
Trend Filter (optional)
EMA 200
EMA slope
ADX

Purpose

Reduce counter-trend exposure
Momentum Filter (optional)
RSI
Stochastic

Purpose

Avoid entering after exhaustion
Volatility Filter
ATR Percentile

Purpose

Determine whether to:

Expand spacing
Compress spacing
Suspend trading
Grid Construction

The grid center is recalculated continuously:

Center = EMA(50)

Spacing

Grid Distance = ATR × Multiplier

Example

Buy Level 1

EMA − 1 ATR

Buy Level 2

EMA − 2 ATR

Buy Level 3

EMA − 3 ATR

Sell Level 1

EMA + 1 ATR

Sell Level 2

EMA + 2 ATR

Sell Level 3

EMA + 3 ATR

Whenever the EMA changes significantly, pending orders are cancelled and rebuilt around the new center.

Trading Strategies
Strategy 1 — Pure Mean Reversion

Indicators

EMA
ATR

Entry

Buy below EMA
Sell above EMA

Exit

Close near EMA

Best for

Ranging markets
Strategy 2 — Pullback Continuation

Indicators

EMA20
EMA100
ATR

Conditions

Uptrend

EMA20 above EMA100

Only buy grids

Downtrend

EMA20 below EMA100

Only sell grids

Edge

Avoids fighting strong trends.

Strategy 3 — Symmetrical Bidirectional Grid

Indicators

EMA
ATR

Places

Buy limits below EMA
Sell limits above EMA

Advantages

Captures oscillations in both directions
Maximizes participation during sideways markets
Strategy 4 — EMA Rotation Scalper

Small grid

Small TP

High frequency

Ideal for

London session
New York session
Strategy 5 — Adaptive Expansion Grid

Spacing increases automatically as ATR rises.

Benefits

Fewer poor entries during volatile periods
Reduced order clustering
Strategy 6 — EMA Breakout Recovery

If price breaks significantly away from the EMA:

Suspend new entries
Wait for stabilization
Re-anchor the grid around the new EMA

This prevents the EA from continuously averaging into runaway trends.

Recommended Lot Sizing
Conservative Research

Fixed

0.01 lots
Moderate

Dynamic

Lots = Equity × Risk Coefficient

Example

0.02 lots per $1,000

Aggressive Account Flipping

Base

0.10 lots

Increase only after realized profits rather than after floating losses to avoid mechanically compounding adverse moves.

Entry Conditions

Buy

Price below EMA
ATR within acceptable range
Spread below maximum
No news filter violation
Grid level reached

Sell

Price above EMA
ATR valid
Spread acceptable
Grid level touched
Exit Methods

Primary

Return to EMA

Alternative

Fixed ATR TP
Basket TP
Equity target
Dynamic trailing profit
Strengths
Continuously follows market equilibrium
Avoids fixed-center grid drift
Performs well during prolonged oscillations
Adapts automatically to changing price levels
Simple mathematical foundation
Computationally efficient
Suitable for high-frequency execution
Can operate with or without directional bias
Works across multiple asset classes
Easy to optimize and extend
Weaknesses
Vulnerable to sustained one-way trends without adequate filters
Frequent order rebuilding can increase execution overhead
Moving averages lag during rapid reversals
Poor parameter selection can lead to excessive trading or sparse coverage
Whipsaw conditions may generate repeated small losses
Theoretical Edge

The Floating EMA Grid exploits the observation that financial markets often exhibit temporary deviations from a dynamic equilibrium rather than remaining fixed around a single historical price. The EMA serves as a continuously updated estimate of this equilibrium, reflecting recent price action while smoothing short-term noise. By anchoring grid levels to the EMA instead of a static reference, the EA effectively "moves with the market," reducing the probability of becoming stranded around obsolete price levels. Combined with volatility-adjusted spacing, the system seeks to harvest repeated oscillations around fair value while remaining responsive to evolving market structure, making it a versatile foundation for adaptive grid-based trading.]
Current Development Scope (Phase 1):
The focus right now is strictly on building the automated execution engine based on the selected indicators and signal logic. We are intentionally keeping the system lightweight and modular at this stage.
Important:
Do NOT introduce advanced filtering, AI layers, session filters, portfolio management, adaptive optimisation, or overengineered logic yet.
Do NOT add unnecessary complexity outside the core execution workflow.
The goal is simply to automate trade execution reliably using the selected indicators and trading conditions.
Core Objective:
Build a configurable execution engine capable of:
Reading indicator values and market conditions in real time
Evaluating entry conditions
Executing buy/sell trades automatically
Managing basic trade risk
Providing clean parameter configuration for optimization and future scaling
Execution Engine Requirements:
Configurable indicator inputs
Configurable entry conditions
Buy/sell execution logic
Support for market orders initially
Clean order validation before execution
Low-latency and lightweight processing
Modular architecture for future expansion
Basic Risk Management & Position Sizing:
Include foundational risk and trade management features only, such as the following:
Fixed lot size input
Optional risk-based position sizing (% (risk per trade)
Stop Loss (fixed points/pips or ATR-based if applicable)
Take Profit configuration
Risk-to-reward ratio support
Maximum spread filter
Slippage control
Maximum simultaneous open trades
Basic cooldown between trades
Magic number management
Equity/balance safety checks
Configurable trading permissions (buy only / sell only / both)
One Symbol vs Multi-Symbol
Use:
Single symbol
Single timeframe
Based strictly on the current chart
This is the correct decision for Phase 1.
Benefits:
Simpler execution flow
Easier debugging
Lower CPU usage
Cleaner state management
More reliable order tracking
Avoids synchronization complexity
Architecture assumption:
One EA instance per chart
One symbol context
One timeframe context
Avoid for now:
multi-symbol scanning
centralized portfolio engine
cross-chart communication
symbol routing
correlation logic
Future extensibility:
Your modular structure should still isolate the following:
signal engine
execution engine
risk engine
This makes future multi-symbol expansion possible without rewriting the core.
The EA should:
Be modular and extensible
Use clean separation of concerns
Support future integration of:
filters
session logic
AI optimization
volatility layers
portfolio controls
advanced trade management
multi-strategy routing
Architecture Goals:
Clean and maintainable codebase
Production-style folder structure
Clear module responsibilities
Configurable engine design
Scalable architecture without premature complexity
High execution reliability
Easy debugging and testing
Suggested Focus Areas:
Signal evaluation pipeline
Indicator management system
Trade execution module
Risk management module
Position sizing engine
Configuration/input management
Logging and debugging utilities
State and trade tracking
What I need from you:
Design the execution engine architecture
Define module responsibilities and execution workflow
Recommend an MT5 production-grade folder structure
Suggest industry best practices for EA development
Keep implementation practical, scalable, and efficient
Avoid unnecessary abstraction or feature creep
Prioritize configurability, maintainability, and execution reliability
The current objective is NOT strategy perfection or advanced intelligence.
The objective is building a strong, configurable execution foundation first.
gap filled
Floating EMA Grid (FEG) — Phase 1 Gap Decisions
Execution Model
Choose: Market-only execution
Execute market orders when price reaches a calculated grid level
No pending orders in v1
Simpler execution and avoids constant cancel/rebuild overhead
Single Default Strategy (v1)
Strategy 2 – Pullback Continuation
EMA20 + EMA100 directional bias
ATR-based floating grid around EMA20
Trade only in trend direction
Other strategies become optional modes in later versions
Locked Default Parameters
EMA Fast: 20
EMA Trend: 100
ATR Period: 14
ATR Multiplier: 1.0
Grid Levels: 5 per side
Max Open Positions: 5
Base Lot: 0.01
Risk Mode: Fixed Lots (default)
Spread Filter: Enabled
Slippage: 5 points (input)
Magic Number: User Input
Grid Rebuild Rule
Recalculate on new bar only
Rebuild only if EMA shifts by ≥ 0.25 × ATR
Existing positions remain untouched
Grid levels updated for future entries only
No cancel/replace since v1 uses market execution
Primary Exit Policy
Basket Take Profit (Primary)
Close all positions when basket reaches target profit
ATR TP and Return-to-EMA remain optional future modes
Bar vs Tick Processing

On New Bar

Update EMA
Update ATR
Update market state
Recalculate grid

On Every Tick

Monitor entry levels
Manage open trades
Check basket TP
Check emergency exits
Order Type Matrix
Market Orders ✅
Buy Limit ❌
Sell Limit ❌
Buy Stop ❌
Sell Stop ❌
Partial fills handled via MT5 execution
No order modification
No pending order replacement
Broker Constraints

Validate before every order:

SYMBOL_TRADE_STOPS_LEVEL
SYMBOL_TRADE_FREEZE_LEVEL
SYMBOL_VOLUME_MIN
SYMBOL_VOLUME_MAX
SYMBOL_VOLUME_STEP
SYMBOL_FILLING_MODE
SYMBOL_TRADE_MODE
Account Margin Mode
Hedging vs Netting compatibility
Position Tracking
One Magic Number per EA instance

Comment format:

FEG_L2_BUY
FEG_L3_SELL
Track:
Grid Level
Basket ID
Direction
Entry Time
Basket Manager maintains trade grouping
State Machine
IDLE
 ↓
READY
 ↓
IN_TRADE
 ↓
BASKET_MANAGEMENT
 ↓
COOLDOWN
 ↓
READY

Additional safety state:

SUSPENDED

Triggered by:

Extreme ATR
Spread spike
Manual pause
Error Handling
Retry failed orders: 3 attempts
Adaptive slippage retry
Normalize invalid lot sizes
Recalculate invalid SL/TP
Log all trade server errors
Abort after repeated failures
Logging Contract

Log:

Timestamp
EMA
ATR
Grid Center
Grid Level
Signal
Entry Price
Basket ID
Order Result
Profit
Drawdown
Spread
State

Modes:

Detailed (Strategy Tester)
Minimal (Live)
Folder / Module Structure
FEG/

Core/
    Engine
    StateMachine
    Config

Indicators/
    EMA
    ATR

Grid/
    GridBuilder
    GridManager

Trading/
    EntryEngine
    ExitEngine
    BasketManager
    TradeManager

Risk/
    LotSizing
    Filters
    Exposure

Broker/
    SymbolInfo
    Execution
    Validation

Utils/
    Logger
    Helpers
    Statistics

AI/
    (Reserved)

FEMA.mq5
Optimization Inputs

Expose in Strategy Tester:

EMA Period
EMA Trend Period
ATR Period
ATR Multiplier
Grid Levels
Basket TP
Base Lot
Risk %
Spread Filter
Max Spread
Cooldown Bars
Max Open Trades

Hardcode:

State Machine
Logging
Trade Tracking
Basket Logic
Error Recovery
Breakout / Suspend Logic
Excluded from Phase 1
Only create placeholder interface/state
No breakout detection or automatic suspension logic yet
HTF Filter
Excluded from Phase 1
No EMA200
No ADX
No RSI
Single-chart timeframe only
HTF filter added in Phase 2
Initial Implementation Scope (FEMA.mq5)

Implement:

Input parameters
Indicator handles (EMA20, EMA100, ATR14)
State machine
Grid calculation
Market execution engine
Basket manager
Position tracking
Risk validation
Logging
Error handling

Defer:

AI layer
Pending-order grids
Multi-timeframe filters
Strategy switching
Adaptive optimization
Breakout recovery
Advanced volatility regime detection