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

#define FEMA_EXECUTION_FAILURE_LIMIT 3

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
   int                   m_prev_position_count;

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
     }

   void              SyncBasketIfFlat(const bool apply_sl_cooldown = false)
     {
      if(m_basket.HasOpenPositions())
         return;
      if(m_basket.BasketStartBarTime() <= 0)
         return;

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
         return;

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

      m_logger.LogBasket(m_basket.BasketId(),
                         m_basket.FloatingProfit(),
                         m_basket.PositionCount(),
                         m_state.GetState());

      const double profit = m_basket.FloatingProfit();
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

      if(m_exit.CloseBasket(m_basket, m_execution, reason))
        {
         m_basket.OnBasketClosed();
         m_grid.ResetFiredFlags();

         if(reason == FEMA_EXIT_BASKET_SL)
            m_filters.StartCooldownAfterSl();
         else
            m_filters.StartCooldownAfterTp();

         m_state.StartCooldown(iTime(_Symbol, _Period, 0));
        }
     }

   void              ProcessEntry()
     {
      if(!m_state.CanEnter())
         return;

      string filter_reason = "";
      if(!m_filters.AllowEntry(m_state, m_exposure, filter_reason))
        {
         if(filter_reason != "" && m_logger.IsDetailed())
            m_logger.LogInfo("Entry blocked: " + filter_reason);
         return;
        }

      SFemaSignal signal;
      if(!m_entry.Evaluate(m_grid, m_indicators, m_htf, signal))
         return;

      // Regime gates filter new basket opens only — grid add-ons must complete.
      const bool is_new_basket = (m_exposure.CountOpenPositions() == 0);
      if(is_new_basket)
        {
         string regime_reason = "";
         if(!m_regime.AllowsDirection(signal.direction, m_indicators, regime_reason))
           {
            if(regime_reason != "" && m_logger.IsDetailed())
               m_logger.LogInfo("Entry blocked: " + regime_reason);
            return;
           }
        }

      string session_reason = "";
      if(!m_session.AllowsEntry(is_new_basket, session_reason))
        {
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
            m_logger.LogWarn("Failed to calculate per-trade SL");
            return;
           }
        }

      string validation_reason = "";
      if(!m_validation.Validate(m_symbol_info, signal.direction, lots, sl_price, validation_reason))
        {
         m_logger.LogWarn("Validation failed: " + validation_reason);
         return;
        }

      const string comment = CFemaTradeManager::BuildComment(signal.level_index, signal.direction);
      int retcode = 0;
      const bool ok = m_execution.OpenMarket(signal.direction, lots, sl_price, comment, retcode);
      m_logger.LogOrderResult(m_basket.BasketId(),
                              signal.direction,
                              signal.level_index,
                              signal.trigger_price,
                              lots,
                              ok,
                              retcode,
                              comment);

      if(ok)
        {
         if(m_exposure.CountOpenPositions() == 1)
           {
            m_exit.ResetTrailState();
            m_basket.OnBasketStart(iTime(_Symbol, _Period, 0));
           }

         const int level_index = m_entry.FindLevelArrayIndex(m_grid, signal);
         if(level_index >= 0)
            m_grid.MarkFired(level_index);

         m_filters.RegisterEntry();
         m_state.RegisterExecutionSuccess();

         if(m_exposure.CountOpenPositions() <= 1)
            m_state.SetInTrade();
         else
            m_state.SetBasketManagement();
        }
      else
        {
         m_state.RegisterExecutionFailure(FEMA_EXECUTION_FAILURE_LIMIT);
        }
     }

public:
                     CFemaEngine() : m_prev_position_count(0) {}

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
                        InpUseBreakoutSuspend, InpBreakoutAtrMult))
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
