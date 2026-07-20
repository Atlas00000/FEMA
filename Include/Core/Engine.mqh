//+------------------------------------------------------------------+
//| Engine.mqh — OnInit / OnTick pipeline coordinator                |
//+------------------------------------------------------------------+
#ifndef FEMA_ENGINE_MQH
#define FEMA_ENGINE_MQH

#include "Config.mqh"
#include "StateMachine.mqh"
#include "../Indicators/Indicators.mqh"
#include "../Indicators/HtfFilter.mqh"
#include "../Indicators/RegimeFilter.mqh"
#include "../Grid/GridManager.mqh"
#include "../Trading/EntryEngine.mqh"
#include "../Trading/ExitEngine.mqh"
#include "../Trading/BasketManager.mqh"
#include "../Trading/TradeManager.mqh"
#include "../Risk/Exposure.mqh"
#include "../Risk/Filters.mqh"
#include "../Risk/SessionFilter.mqh"
#include "../Risk/LotSizing.mqh"
#include "../Broker/SymbolInfo.mqh"
#include "../Broker/Validation.mqh"
#include "../Broker/Execution.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"
#include "../AI/AiEventLog.mqh"
#include "../AI/AiTepGate.mqh"
#include "../AI/AiMidWarn.mqh"
#include "../AI/AiRegimeGate.mqh"

#define FEMA_EXECUTION_FAILURE_LIMIT 3

// Market-closed / session-edge rejects must not permanently kill long backtests.
bool FemaIsTransientOrderFail(const int retcode)
  {
   return (retcode == TRADE_RETCODE_MARKET_CLOSED ||
           retcode == TRADE_RETCODE_REQUOTE ||
           retcode == TRADE_RETCODE_PRICE_OFF ||
           retcode == TRADE_RETCODE_CONNECTION ||
           retcode == TRADE_RETCODE_TIMEOUT ||
           retcode == TRADE_RETCODE_PRICE_CHANGED ||
           retcode == TRADE_RETCODE_TOO_MANY_REQUESTS);
  }

bool FemaMarketTradeable(const string symbol)
  {
   const long mode = SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
   return (mode == SYMBOL_TRADE_MODE_FULL ||
           mode == SYMBOL_TRADE_MODE_LONGONLY ||
           mode == SYMBOL_TRADE_MODE_SHORTONLY ||
           mode == SYMBOL_TRADE_MODE_CLOSEONLY);
  }

class CFemaEngine
  {
private:
   CFemaLogger           m_logger;
   CFemaHelpers          m_helpers;
   CFemaStateMachine     m_state;
   CFemaIndicators       m_indicators;
   CFemaHtfFilter        m_htf;
   CFemaRegimeFilter     m_regime;
   CFemaGridManager      m_grid;
   CFemaEntryEngine      m_entry;
   CFemaExitEngine       m_exit;
   CFemaBasketManager    m_basket;
   CFemaTradeManager     m_trade_manager;
   CFemaExposure         m_exposure;
   CFemaFilters          m_filters;
   CFemaSessionFilter    m_session;
   CFemaLotSizing        m_lot_sizing;
   CFemaSymbolInfo       m_symbol_info;
   CFemaValidation       m_validation;
   CFemaExecution        m_execution;
   CFemaAiEventLog       m_ai_log;
   CFemaAiTepGate        m_tep_gate;
   CFemaAiMidWarn        m_mid_warn;
   CFemaAiRegimeGate     m_regime_gate;
   int                   m_tep_pending_consec;
   int                   m_regime_pending_consec;
   int                   m_prev_position_count;
   bool                  m_pause_new_active;

   void              WireLoggers()
     {
      m_state.SetLogger(m_logger);
      m_indicators.SetLogger(m_logger);
      m_htf.SetLogger(m_logger);
      m_regime.SetLogger(m_logger);
      m_grid.SetLogger(m_logger);
      m_filters.SetLogger(m_logger);
      m_lot_sizing.SetLogger(m_logger);
      m_validation.SetLogger(m_logger);
      m_execution.SetLogger(m_logger);
      m_basket.SetLogger(m_logger);
      m_exit.SetLogger(m_logger);
      m_ai_log.SetLogger(m_logger);
      m_tep_gate.SetLogger(m_logger);
      m_mid_warn.SetLogger(m_logger);
      m_regime_gate.SetLogger(m_logger);
     }

   string            JsonEsc(const string s) const
     {
      string out = s;
      StringReplace(out, "\\", "\\\\");
      StringReplace(out, "\"", "\\\"");
      return out;
     }

   string            BuildRunConfigJson() const
     {
      // INF-EA-001: edge-defining Inp* snapshot (certificate fingerprint family).
      string j = "{";
      j += "\"ea_build\":\"" + JsonEsc(FEMA_VERSION) + "\",";
      j += "\"preset_id\":\"PRODUCTION\",";
      j += "\"symbol\":\"" + JsonEsc(_Symbol) + "\",";
      j += "\"timeframe\":\"" + EnumToString(_Period) + "\",";
      j += "\"run_id\":\"" + JsonEsc(m_ai_log.RunId()) + "\",";
      j += "\"InpEmaFastPeriod\":" + IntegerToString(InpEmaFastPeriod) + ",";
      j += "\"InpEmaTrendPeriod\":" + IntegerToString(InpEmaTrendPeriod) + ",";
      j += "\"InpAtrPeriod\":" + IntegerToString(InpAtrPeriod) + ",";
      j += "\"InpAtrMultiplier\":" + DoubleToString(InpAtrMultiplier, 4) + ",";
      j += "\"InpGridLevels\":" + IntegerToString(InpGridLevels) + ",";
      j += "\"InpGridRebuildAtr\":" + DoubleToString(InpGridRebuildAtr, 4) + ",";
      j += "\"InpBasketTp\":" + DoubleToString(InpBasketTp, 2) + ",";
      j += "\"InpUseBasketSl\":" + (InpUseBasketSl ? "true" : "false") + ",";
      j += "\"InpBasketSl\":" + DoubleToString(InpBasketSl, 2) + ",";
      j += "\"InpMaxEntryDepth\":" + IntegerToString(InpMaxEntryDepth) + ",";
      j += "\"InpUseAdxGate\":" + (InpUseAdxGate ? "true" : "false") + ",";
      j += "\"InpAdxMax\":" + DoubleToString(InpAdxMax, 1) + ",";
      j += "\"InpAdxPeriod\":" + IntegerToString(InpAdxPeriod) + ",";
      j += "\"InpUseHtfFilter\":" + (InpUseHtfFilter ? "true" : "false") + ",";
      j += "\"InpUseAtrPercentileGate\":" + (InpUseAtrPercentileGate ? "true" : "false") + ",";
      j += "\"InpUseSessionBlockNo23\":" + (InpUseSessionBlockNo23 ? "true" : "false") + ",";
      j += "\"InpUseSessionBlockFriClose\":" + (InpUseSessionBlockFriClose ? "true" : "false") + ",";
      j += "\"InpUseSessionBlockSunOpen\":" + (InpUseSessionBlockSunOpen ? "true" : "false") + ",";
      j += "\"InpUseSessionWhitelistLdnNy\":" + (InpUseSessionWhitelistLdnNy ? "true" : "false") + ",";
      j += "\"InpBaseLot\":" + DoubleToString(InpBaseLot, 2) + ",";
      j += "\"InpMagicNumber\":" + IntegerToString((long)InpMagicNumber) + ",";
      j += "\"InpReadPauseNewFlag\":" + (InpReadPauseNewFlag ? "true" : "false") + ",";
      j += "\"InpUseAiEventLog\":" + (InpUseAiEventLog ? "true" : "false") + ",";
      j += "\"InpUseAiTepGate\":" + (InpUseAiTepGate ? "true" : "false") + ",";
      j += "\"InpAiTepGateFile\":\"" + JsonEsc(InpAiTepGateFile) + "\",";
      j += "\"InpUseAiMidWarn\":" + (InpUseAiMidWarn ? "true" : "false") + ",";
      j += "\"InpAiMidGateFile\":\"" + JsonEsc(InpAiMidGateFile) + "\",";
      j += "\"InpUseAiMidEarlyBsl\":" + (InpUseAiMidEarlyBsl ? "true" : "false") + ",";
      j += "\"InpUseAiRegimeGate\":" + (InpUseAiRegimeGate ? "true" : "false") + ",";
      j += "\"InpAiRegimeGateFile\":\"" + JsonEsc(InpAiRegimeGateFile) + "\"";
      j += "}\r\n";
      return j;
     }

   bool              ParsePauseFlagBody(const string body) const
     {
      // Accept: "1", "true", "pause_new=1", JSON-ish "pause_new": true
      string t = body;
      StringTrimLeft(t);
      StringTrimRight(t);
      StringToLower(t);
      if(t == "1" || t == "true" || t == "yes" || t == "pause")
         return true;
      if(StringFind(t, "pause_new=1") >= 0 || StringFind(t, "pause_new=true") >= 0)
         return true;
      if(StringFind(t, "\"pause_new\": true") >= 0 || StringFind(t, "\"pause_new\":true") >= 0)
         return true;
      if(StringFind(t, "pause_new=0") >= 0 || StringFind(t, "pause_new=false") >= 0)
         return false;
      return false;
     }

   bool              ReadPauseFlagFile(const int common_flag) const
     {
      const string path = InpPauseNewFlagFile;
      if(!FileIsExist(path, common_flag))
         return false;
      const int h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI|common_flag);
      if(h == INVALID_HANDLE)
         return false;
      string body = "";
      while(!FileIsEnding(h))
         body += FileReadString(h);
      FileClose(h);
      return ParsePauseFlagBody(body);
     }

   void              RefreshPauseNewFlag()
     {
      if(!InpReadPauseNewFlag)
        {
         if(m_pause_new_active)
           {
            m_pause_new_active = false;
            m_ai_log.LogLifecycle("RESUME", "PAUSE_FLAG_DISABLED");
            m_logger.LogInfo("Pause-new wire disabled — new baskets allowed");
           }
         return;
        }

      const bool want = ReadPauseFlagFile(FILE_COMMON) || ReadPauseFlagFile(0);
      if(want == m_pause_new_active)
         return;
      m_pause_new_active = want;
      if(want)
        {
         m_ai_log.LogLifecycle("PAUSE_NEW", "FLAG_FILE");
         m_logger.LogWarn("EL6 pause-new ACTIVE (flag file) — no new baskets; manage open only");
        }
      else
        {
         m_ai_log.LogLifecycle("RESUME", "PAUSE_FLAG_CLEARED");
         m_logger.LogInfo("EL6 pause-new cleared — new baskets allowed");
        }
     }

   void              SyncBasketIfFlat(const bool apply_sl_cooldown = false)
     {
      if(m_basket.HasOpenPositions())
         return;
      if(m_basket.BasketStartBarTime() <= 0)
         return;

      m_ai_log.OnBasketAborted();
      m_basket.OnBasketClosed();
      m_exit.ResetTrailState();
      m_grid.ResetFiredFlags();

      if(apply_sl_cooldown)
        {
         m_filters.StartCooldownAfterSl();
         m_state.StartCooldown(iTime(_Symbol, _Period, 0));
        }
     }

   void              DetectPerTradeSlClose()
     {
      const int count = m_exposure.CountOpenPositions();
      if(count < m_prev_position_count && m_prev_position_count > 0)
        {
         m_logger.LogInfo("Position closed externally (per-trade SL): " +
                          IntegerToString(m_prev_position_count) + " -> " + IntegerToString(count));
         if(count == 0)
            SyncBasketIfFlat(true);
         else
            m_filters.StartCooldownAfterTp();
        }
      m_prev_position_count = count;
     }

   void              UpdateStateFromPositions()
     {
      if(m_state.GetState() == FEMA_STATE_SUSPENDED)
        {
         // Manual suspend stays sticky. Auto-suspend (exec failures) resumes when tradeable.
         if(InpManualSuspend)
            return;
         if(FemaMarketTradeable(_Symbol))
           {
            m_logger.LogInfo("Auto-resume from SUSPENDED (market tradeable again)");
            m_ai_log.LogLifecycle("RESUME", "MARKET_TRADEABLE");
            m_state.SetReady();
           }
         else
            return;
        }

      if(InpManualSuspend)
        {
         m_state.SetSuspended();
         return;
        }

      if(m_exposure.HasOpenPositions())
        {
         if(m_state.GetState() != FEMA_STATE_BASKET_MANAGEMENT &&
            m_state.GetState() != FEMA_STATE_IN_TRADE)
            m_state.SetBasketManagement();
         return;
        }

      if(m_state.GetState() == FEMA_STATE_COOLDOWN)
        {
         if(m_filters.CooldownExpired(m_state))
            m_state.SetReady();
         return;
        }

      if(m_state.GetState() == FEMA_STATE_IDLE)
         m_state.SetReady();
      else if(m_state.GetState() == FEMA_STATE_IN_TRADE ||
              m_state.GetState() == FEMA_STATE_BASKET_MANAGEMENT)
         m_state.SetReady();
     }

   void              ProcessExit()
     {
      if(!m_basket.HasOpenPositions())
         return;

      const double profit = m_basket.FloatingProfit();
      m_ai_log.UpdatePath(profit);

      m_logger.LogBasket(m_basket.BasketId(),
                         profit,
                         m_basket.PositionCount(),
                         m_state.GetState());

      m_exit.UpdateTrail(profit);

      const double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      const double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      const ENUM_FEMA_EXIT_REASON reason = m_exit.GetCloseReason(m_basket,
                                                                 m_exposure.PrimaryDirection(),
                                                                 m_indicators.EmaFast(),
                                                                 bid,
                                                                 ask);
      if(reason == FEMA_EXIT_NONE)
         return;

      const int age_bars = m_basket.AgeBars();
      if(m_exit.CloseBasket(m_basket, m_execution, reason))
         FinalizeBasketClose(profit, reason, age_bars);
     }

   void              FinalizeBasketClose(const double profit,
                                         const ENUM_FEMA_EXIT_REASON reason,
                                         const int age_bars)
     {
      SFemaAiFeatures closed_open;
      ENUM_FEMA_DIRECTION closed_dir = FEMA_DIR_NONE;
      const bool had_open = m_ai_log.CopyActiveOpenFeatures(closed_open, closed_dir);
      m_ai_log.OnBasketClosed(profit, reason, age_bars);
      if(had_open && InpUseAiTepGate && m_tep_gate.Loaded())
         m_tep_gate.OnBasketClosed(closed_open, closed_dir, m_tep_pending_consec);
      if(had_open && InpUseAiRegimeGate && m_regime_gate.Loaded())
         m_regime_gate.OnBasketClosed(closed_open, closed_dir, m_regime_pending_consec);
      if(had_open && (InpUseAiMidWarn || InpUseAiMidEarlyBsl) && m_mid_warn.Loaded())
         m_mid_warn.OnBasketClosed(closed_open, closed_dir);
      m_basket.OnBasketClosed();
      m_grid.ResetFiredFlags();

      if(reason == FEMA_EXIT_BASKET_SL || reason == FEMA_EXIT_MID_WARN)
         m_filters.StartCooldownAfterSl();
      else
         m_filters.StartCooldownAfterTp();

      m_state.StartCooldown(iTime(_Symbol, _Period, 0));
     }

   void              ProcessEntry()
     {
      if(!m_state.CanEnter())
         return;

      // Detect candidate touch before risk filters so AI0 can log skips.
      SFemaSignal signal;
      if(!m_entry.Evaluate(m_grid, m_indicators, m_htf, signal))
         return;

      const int pos_count = m_exposure.CountOpenPositions();
      const bool is_new_basket = (pos_count == 0);
      SFemaAiFeatures features;
      m_ai_log.BuildFeatures(signal, m_indicators, m_regime, m_grid,
                             pos_count, m_basket.BasketId(), features);
      m_ai_log.LogCandidate(features);

      string filter_reason = "";
      if(!m_filters.AllowEntry(m_state, m_exposure, filter_reason))
        {
         m_ai_log.LogSkip(features, filter_reason == "" ? "filter" : filter_reason);
         if(filter_reason != "" && m_logger.IsDetailed())
            m_logger.LogInfo("Entry blocked: " + filter_reason);
         return;
        }

      // Regime gates filter new basket opens only — grid add-ons must complete.
      if(is_new_basket)
        {
         if(m_pause_new_active)
           {
            m_ai_log.LogSkip(features, "pause_new_flag");
            if(m_logger.IsDetailed())
               m_logger.LogInfo("Entry blocked: pause_new_flag");
            return;
           }

         string regime_reason = "";
         if(!m_regime.AllowsDirection(signal.direction, m_indicators, regime_reason))
           {
            m_ai_log.LogSkip(features, regime_reason == "" ? "regime" : regime_reason);
            if(regime_reason != "" && m_logger.IsDetailed())
               m_logger.LogInfo("Entry blocked: " + regime_reason);
            return;
           }

         if(InpUseAiTepGate && m_tep_gate.Loaded())
           {
            double tep_proba = 0.0;
            if(m_tep_gate.ShouldSkip(features, tep_proba))
              {
               const string tep_reason = "tep_gate;p=" + DoubleToString(tep_proba, 4);
               m_ai_log.LogSkip(features, tep_reason);
               if(m_logger.IsDetailed())
                  m_logger.LogInfo("Entry blocked: " + tep_reason);
               return;
              }
            m_tep_pending_consec = m_tep_gate.LastConsecutive();
           }

         if(InpUseAiRegimeGate && m_regime_gate.Loaded())
           {
            string reg_name = "";
            if(m_regime_gate.ShouldSkip(features, reg_name))
              {
               const string reg_reason = "regime_gate;" + reg_name;
               m_ai_log.LogSkip(features, reg_reason);
               if(m_logger.IsDetailed())
                  m_logger.LogInfo("Entry blocked: " + reg_reason);
               return;
              }
            m_regime_pending_consec = m_regime_gate.LastConsecutive();
           }
        }

      string session_reason = "";
      if(!m_session.AllowsEntry(is_new_basket, session_reason))
        {
         m_ai_log.LogSkip(features, session_reason == "" ? "session" : session_reason);
         if(session_reason != "" && m_logger.IsDetailed())
            m_logger.LogInfo("Entry blocked: " + session_reason);
         return;
        }

      const int spread = CFemaHelpers::SpreadPoints(_Symbol);
      m_logger.LogSignal(signal, spread);

      const double lots = m_lot_sizing.CalculateLots(m_symbol_info);

      double sl_price = 0.0;
      if(InpUsePerTradeSl)
        {
         bool sl_ok = false;
         if(InpSlUseGridStructure)
            sl_ok = CFemaHelpers::CalcGridStructureStopPrice(_Symbol,
                                                             signal.direction,
                                                             signal.trigger_price,
                                                             m_indicators.Atr(),
                                                             InpSlAtrMultiplier,
                                                             InpAtrMultiplier,
                                                             signal.level_index,
                                                             InpGridLevels,
                                                             m_symbol_info.StopsLevel(),
                                                             sl_price);
         else
            sl_ok = CFemaHelpers::CalcAtrStopPrice(_Symbol,
                                                  signal.direction,
                                                  signal.trigger_price,
                                                  m_indicators.Atr(),
                                                  InpSlAtrMultiplier,
                                                  m_symbol_info.StopsLevel(),
                                                  sl_price);
         if(!sl_ok)
           {
            m_ai_log.LogSkip(features, "sl_calc_failed");
            m_logger.LogWarn("Failed to calculate per-trade SL");
            return;
           }
        }

      string validation_reason = "";
      if(!m_validation.Validate(m_symbol_info, signal.direction, lots, sl_price, validation_reason))
        {
         m_ai_log.LogSkip(features, validation_reason == "" ? "validation" : validation_reason);
         m_logger.LogWarn("Validation failed: " + validation_reason);
         return;
        }

      const string comment = CFemaTradeManager::BuildComment(signal.level_index, signal.direction);
      int retcode = 0;
      const bool ok = m_execution.OpenMarket(signal.direction, lots, sl_price, comment, retcode);

      if(ok)
        {
         if(m_exposure.CountOpenPositions() == 1)
           {
            m_exit.ResetTrailState();
            m_basket.OnBasketStart(iTime(_Symbol, _Period, 0));
            features.basket_id = m_basket.BasketId();
            m_ai_log.OnBasketOpened(m_basket.BasketId(), features);
            if((InpUseAiMidWarn || InpUseAiMidEarlyBsl) && m_mid_warn.Loaded())
               m_mid_warn.OnBasketOpened(features);
           }

         m_ai_log.OnLegFilled(signal.level_index);
         m_ai_log.LogFill(features, !is_new_basket);

         m_logger.LogOrderResult(m_basket.BasketId(),
                                 signal.direction,
                                 signal.level_index,
                                 signal.trigger_price,
                                 lots,
                                 ok,
                                 retcode,
                                 comment);

         const int level_index = m_entry.FindLevelArrayIndex(m_grid, signal);
         if(level_index >= 0)
            m_grid.MarkFired(level_index);

         m_filters.RegisterEntry();
         m_state.RegisterExecutionSuccess();

         if((InpUseAiMidWarn || InpUseAiMidEarlyBsl) && m_mid_warn.Loaded() && signal.level_index >= 2)
           {
            double mid_p = 0.0;
            if(m_mid_warn.ShouldWarn(signal.level_index, mid_p))
              {
               const string mid_detail = "p=" + DoubleToString(mid_p, 4) +
                                         ";depth=" + IntegerToString(signal.level_index);
               m_ai_log.LogLifecycle("mid_warn", mid_detail);

               if(InpUseAiMidEarlyBsl)
                 {
                  const double mid_profit = m_basket.FloatingProfit();
                  const int mid_age = m_basket.AgeBars();
                  m_ai_log.LogLifecycle("mid_early_bsl", mid_detail);
                  if(m_logger.IsDetailed())
                     m_logger.LogInfo("Mid Mode B early close: " + mid_detail +
                                      " profit=" + DoubleToString(mid_profit, 2));
                  if(m_exit.CloseBasket(m_basket, m_execution, FEMA_EXIT_MID_WARN))
                    {
                     FinalizeBasketClose(mid_profit, FEMA_EXIT_MID_WARN, mid_age);
                     return;
                    }
                  m_logger.LogWarn("Mid Mode B close incomplete — basket still open");
                 }
               else if(m_logger.IsDetailed())
                  m_logger.LogInfo("Mid-warn (log only): " + mid_detail);
              }
           }

         if(m_exposure.CountOpenPositions() <= 1)
            m_state.SetInTrade();
         else
            m_state.SetBasketManagement();
        }
      else
        {
         m_ai_log.LogOrderFail(features, retcode, FemaIsTransientOrderFail(retcode), comment);
         m_logger.LogOrderResult(m_basket.BasketId(),
                                 signal.direction,
                                 signal.level_index,
                                 signal.trigger_price,
                                 lots,
                                 ok,
                                 retcode,
                                 comment);
         // Do not count market-closed / transient rejects toward permanent SUSPEND.
         if(!FemaIsTransientOrderFail(retcode))
           {
            m_state.RegisterExecutionFailure(FEMA_EXECUTION_FAILURE_LIMIT);
            if(m_state.GetState() == FEMA_STATE_SUSPENDED)
               m_ai_log.LogLifecycle("SUSPEND", "EXEC_FAIL_LIMIT;retcode=" + IntegerToString(retcode));
           }
         else
            m_logger.LogInfo("Transient order fail retcode=" + IntegerToString(retcode) +
                             " — not counted toward SUSPEND");
        }
     }

public:
                     CFemaEngine() : m_prev_position_count(0), m_pause_new_active(false),
                                     m_tep_pending_consec(1), m_regime_pending_consec(1) {}

   int               OnInit()
     {
      const string symbol = _Symbol;
      const ENUM_TIMEFRAMES timeframe = _Period;

      m_logger.Init(InpLogMode, symbol);
      WireLoggers();

      if(InpEmaFastPeriod < 2 || InpEmaTrendPeriod < 2 || InpAtrPeriod < 1)
        {
         m_logger.LogError("Invalid indicator periods");
         return INIT_PARAMETERS_INCORRECT;
        }

      if(InpGridLevels < 1 || InpMaxOpenTrades < 1)
        {
         m_logger.LogError("Invalid grid or trade limits");
         return INIT_PARAMETERS_INCORRECT;
        }

      m_helpers.Init(symbol, timeframe);

      if(!m_symbol_info.Init(symbol))
        {
         m_logger.LogError("Failed to initialize symbol info");
         return INIT_FAILED;
        }

      if(!m_indicators.Init(symbol, timeframe, InpEmaFastPeriod, InpEmaTrendPeriod, InpAtrPeriod,
                            InpUseRsiExhaustionFilter, InpRsiPeriod, InpRsiBuyMax, InpRsiSellMin))
        {
         m_logger.LogError("Failed to initialize indicators");
         return INIT_FAILED;
        }

      if(!m_htf.Init(symbol, InpUseHtfFilter, InpHtfTimeframe, InpHtfEmaPeriod, InpHtfRequireSlope))
        {
         m_logger.LogError("Failed to initialize HTF filter");
         return INIT_FAILED;
        }

      if(!m_regime.Init(symbol, timeframe,
                        InpUseAdxGate, InpAdxMax, InpAdxPeriod,
                        InpUseAtrPercentileGate, InpAtrPercentileMax, InpAtrPercentileLookback,
                        InpUseEmaSepGate, InpEmaSepAtrMult,
                        InpUseEmaSlopeGate,
                        InpUseBreakoutSuspend, InpBreakoutAtrMult,
                        InpUseAiEventLog))
        {
         m_logger.LogError("Failed to initialize regime filter");
         return INIT_FAILED;
        }

      m_grid.Init(symbol, InpGridLevels, InpAtrMultiplier, InpGridRebuildAtr);
      m_grid.BuildInitial(m_indicators);

      m_entry.Init(symbol, timeframe, InpTradePermission, InpMaxEntryDepth, InpUseCandleConfirm);
      m_exposure.Init(symbol, InpMagicNumber);
      m_trade_manager.Init(symbol, InpMagicNumber);
      m_basket.Init(symbol, timeframe, m_exposure, m_trade_manager);
      m_filters.Init(symbol, timeframe, InpSpreadFilter, InpMaxSpreadPoints,
                     InpCooldownBars, InpCooldownBarsAfterSl,
                     InpMaxOpenTrades, InpMinEquity);
      m_session.Init(InpUseSessionBlockNo23, InpUseSessionBlockFriClose,
                     InpUseSessionBlockSunOpen, InpUseSessionWhitelistLdnNy);
      m_lot_sizing.Init(InpBaseLot, InpRiskPercent);
      m_execution.Init(symbol, InpMagicNumber, InpSlippagePoints, m_symbol_info);
      m_exit.Init(InpBasketTp, InpUseBasketSl, InpBasketSl, InpMaxBasketBars,
                  InpUseExitRte, InpRteMinProfit,
                  InpUseBasketTrail, InpBasketTrailActivatePct, InpBasketTrailGivebackPct);
      if(!m_ai_log.Init(InpUseAiEventLog, symbol, InpMagicNumber,
                         FEMA_VERSION, "PRODUCTION", InpUseAdxGate, InpBasketSl))
         m_logger.LogWarn("AI event log failed to open — continuing without AI CSV");
      else
         m_ai_log.WriteRunConfigJson(BuildRunConfigJson());

      if(!m_tep_gate.Init(InpUseAiTepGate, InpAiTepGateFile) && InpUseAiTepGate)
         m_logger.LogWarn("TEP guardrail gate disabled — check gate file export");
      if(!m_mid_warn.Init(InpUseAiMidWarn || InpUseAiMidEarlyBsl, InpAiMidGateFile) &&
         (InpUseAiMidWarn || InpUseAiMidEarlyBsl))
         m_logger.LogWarn("Mid-warn/Mode B disabled — check mid_gate_v1.txt export");
      if(InpUseAiMidEarlyBsl && !InpUseAiMidWarn)
         m_logger.LogInfo("Mode B early BSL on — mid gate loaded for scoring (warn log optional)");
      if(!m_regime_gate.Init(InpUseAiRegimeGate, InpAiRegimeGateFile) && InpUseAiRegimeGate)
         m_logger.LogWarn("Regime gate disabled — check regime_gate_v1.txt export");

      m_pause_new_active = false;
      RefreshPauseNewFlag();

      if(!m_regime.Update(m_indicators))
        {
         m_logger.LogWarn("Regime filter update failed on init");
         return INIT_FAILED;
        }

      m_prev_position_count = m_exposure.CountOpenPositions();

      if(InpManualSuspend)
         m_state.SetSuspended();
      else
         m_state.SetReady();

      string entry_summary = "";
      if(InpUseCandleConfirm)
         entry_summary = "candle";
      if(InpUseRsiExhaustionFilter)
         entry_summary += (entry_summary == "" ? "" : "+") + "rsi";
      if(entry_summary == "")
         entry_summary = "off";

      m_logger.LogInfo("Init v" + FEMA_VERSION + " symbol=" + symbol + " tf=" + EnumToString(timeframe) +
                       " bsl=" + DoubleToString(InpBasketSl, 0) +
                       " adx_gate=" + (InpUseAdxGate ? "on" : "off") +
                       " atr_gate=" + (InpUseAtrPercentileGate ? "on" : "off") +
                       " ses=" + m_session.ActiveSummary() +
                       " exit=" + m_exit.ActiveSummary() +
                       " entry=" + entry_summary +
                       " ai_log=" + (InpUseAiEventLog ? "on" : "off") +
                       (InpUseAiEventLog ? (" run_id=" + m_ai_log.RunId()) : "") +
                       " tep_gate=" + (InpUseAiTepGate ? (m_tep_gate.Loaded() ? "on" : "missing") : "off") +
                       " mid_warn=" + ((InpUseAiMidWarn || InpUseAiMidEarlyBsl) ? (m_mid_warn.Loaded() ? "on" : "missing") : "off") +
                       " mid_bsl=" + (InpUseAiMidEarlyBsl ? "on" : "off") +
                       " regime_gate=" + (InpUseAiRegimeGate ? (m_regime_gate.Loaded() ? "on" : "missing") : "off") +
                       " pause_flag=" + (InpReadPauseNewFlag ? (m_pause_new_active ? "ON" : "armed") : "off") +
                       (InpUseHtfFilter ? " HTF=" + EnumToString(InpHtfTimeframe) : ""));
      m_logger.LogBarSummary(m_state.GetState(),
                             m_indicators.EmaFast(),
                             m_indicators.EmaTrend(),
                             m_indicators.Atr(),
                             m_indicators.Trend(),
                             m_grid.Center());
      return INIT_SUCCEEDED;
     }

   void              OnDeinit(const int reason)
     {
      m_ai_log.Close();
      m_regime.Release();
      m_htf.Release();
      m_indicators.Release();
      m_logger.LogInfo("FEMA deinitialized reason=" + IntegerToString(reason));
     }

   void              OnTick()
     {
      if(InpManualSuspend && m_state.GetState() != FEMA_STATE_SUSPENDED)
         m_state.SetSuspended();

      if(m_helpers.IsNewBar())
        {
         RefreshPauseNewFlag();
         if(!m_indicators.Update())
           {
            m_logger.LogWarn("Indicator update failed on new bar");
            return;
           }
         if(!m_htf.Update())
           {
            m_logger.LogWarn("HTF filter update failed on new bar");
            return;
           }
         if(!m_regime.Update(m_indicators))
            m_logger.LogWarn("Regime filter update failed on new bar — using last threshold");
         m_grid.RebuildIfNeeded(m_indicators, m_basket.HasOpenPositions());
         m_logger.LogBarSummary(m_state.GetState(),
                                m_indicators.EmaFast(),
                                m_indicators.EmaTrend(),
                                m_indicators.Atr(),
                                m_indicators.Trend(),
                                m_grid.Center());
        }

      UpdateStateFromPositions();
      DetectPerTradeSlClose();
      SyncBasketIfFlat();
      ProcessExit();
      ProcessEntry();
      UpdateStateFromPositions();
      DetectPerTradeSlClose();
      SyncBasketIfFlat();

      m_logger.LogTickMinimal(m_state.GetState(), m_basket.FloatingProfit());
     }
  };

#endif
