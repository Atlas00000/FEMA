//+------------------------------------------------------------------+
//| Config.mqh — Phase 1 input parameters                            |
//+------------------------------------------------------------------+
#ifndef FEMA_CONFIG_MQH
#define FEMA_CONFIG_MQH

#include "Types.mqh"

input group "=== Indicators ==="
input int    InpEmaFastPeriod   = 20;
input int    InpEmaTrendPeriod  = 100;
input int    InpAtrPeriod       = 14;
input double InpAtrMultiplier   = 1.0;

input group "=== Grid ==="
input int    InpGridLevels      = 5;
input double InpGridRebuildAtr  = 0.25;

input group "=== Basket & Exit ==="
input double InpBasketTp        = 10.0;

input group "=== Phase 2A: Failure Containment ==="
input bool   InpUsePerTradeSl   = false;
input double InpSlAtrMultiplier = 1.5;
input bool   InpSlUseGridStructure = true;
input bool   InpUseBasketSl     = true;
input double InpBasketSl        = 25.0;
input int    InpMaxBasketBars   = 0;
input int    InpMaxEntryDepth   = 5;
input int    InpCooldownBarsAfterSl = 1;

input group "=== Phase 2B: HTF Filter ==="
input bool   InpUseHtfFilter    = false;
input ENUM_TIMEFRAMES InpHtfTimeframe = PERIOD_H1;
input int    InpHtfEmaPeriod    = 200;
input bool   InpHtfRequireSlope = false;

input group "=== Phase 2C: Regime Gates ==="
input bool   InpUseAdxGate          = true;
input double InpAdxMax              = 30.0;
input int    InpAdxPeriod           = 14;
input bool   InpUseAtrPercentileGate = false;
input double InpAtrPercentileMax    = 70.0;
input int    InpAtrPercentileLookback = 100;
input bool   InpUseEmaSepGate        = false;
input double InpEmaSepAtrMult       = 3.0;
input bool   InpUseEmaSlopeGate      = false;
input bool   InpUseBreakoutSuspend   = false;
input double InpBreakoutAtrMult     = 3.0;

input group "=== Phase 2D: Session Filters ==="
input bool   InpUseSessionBlockNo23       = false;
input bool   InpUseSessionBlockFriClose   = false;
input bool   InpUseSessionBlockSunOpen    = false;
input bool   InpUseSessionWhitelistLdnNy  = false;

input group "=== Phase 2E: Exit Modes ==="
input bool   InpUseExitRte              = false;
input double InpRteMinProfit            = 0.0;
input bool   InpUseBasketTrail          = false;
input double InpBasketTrailActivatePct  = 50.0;
input double InpBasketTrailGivebackPct  = 50.0;

input group "=== Phase 2F: Entry Quality ==="
input bool   InpUseCandleConfirm        = false;
input bool   InpUseRsiExhaustionFilter  = false;
input int    InpRsiPeriod               = 14;
input double InpRsiBuyMax               = 70.0;
input double InpRsiSellMin              = 30.0;

input group "=== Position Sizing ==="
input double InpBaseLot         = 0.01;
input double InpRiskPercent     = 0.0;

input group "=== Risk Filters ==="
input bool   InpSpreadFilter    = true;
input int    InpMaxSpreadPoints = 30;
input int    InpSlippagePoints  = 5;
input int    InpCooldownBars    = 1;
input int    InpMaxOpenTrades   = 5;
input double InpMinEquity       = 0.0;

input group "=== Trade Control ==="
input ulong  InpMagicNumber     = 20260707;
input ENUM_FEMA_TRADE_PERMISSION InpTradePermission = FEMA_PERM_BOTH;
input bool   InpManualSuspend   = false;

input group "=== EL6: Pause-new (opt-in wire) ==="
input bool   InpReadPauseNewFlag = false;  // OFF = shadow only; ON reads FEMA_AI\\pause_new.flag
input string InpPauseNewFlagFile = "FEMA_AI\\pause_new.flag";  // local + Common Files

input group "=== Logging ==="
input ENUM_FEMA_LOG_MODE InpLogMode = FEMA_LOG_DETAILED;

input group "=== AI0: Event Pipeline ==="
input bool   InpUseAiEventLog = true;  // CSV features/events/labels to Common\\Files\\FEMA_AI

input group "=== ASI-P4: TEP guardrail gate (opt-in) ==="
input bool   InpUseAiTepGate = false;  // Skip new basket when offline TEP P(steamroller) >= threshold
input string InpAiTepGateFile = "FEMA_AI\\tep_gate_v1.txt";  // Common\\Files or MQL5\\Files

input group "=== ASI-P5: Mid-basket steamroller warn (opt-in) ==="
input bool   InpUseAiMidWarn = false;  // Log mid_warn when P(eventual steamroller|depth) >= threshold
input string InpAiMidGateFile = "FEMA_AI\\mid_gate_v1.txt";  // Common\\Files or MQL5\\Files
input bool   InpUseAiMidEarlyBsl = false;  // Mode B: close basket early when mid_warn fires (requires MidWarn)

#endif
