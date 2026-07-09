//+------------------------------------------------------------------+
//| Filters.mqh — spread, cooldown, max trades, equity               |
//+------------------------------------------------------------------+
#ifndef FEMA_FILTERS_MQH
#define FEMA_FILTERS_MQH

#include "../Core/StateMachine.mqh"
#include "../Risk/Exposure.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

class CFemaFilters
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_timeframe;
   bool              m_spread_filter;
   int               m_max_spread_points;
   int               m_cooldown_bars;
   int               m_cooldown_bars_after_sl;
   int               m_max_open_trades;
   double            m_min_equity;
   datetime          m_cooldown_anchor_bar_time;
   int               m_active_cooldown_bars;
   CFemaLogger      *m_log;

public:
                     CFemaFilters() :
                     m_symbol(""),
                     m_timeframe(PERIOD_CURRENT),
                     m_spread_filter(true),
                     m_max_spread_points(30),
                     m_cooldown_bars(1),
                     m_cooldown_bars_after_sl(10),
                     m_max_open_trades(5),
                     m_min_equity(0.0),
                     m_cooldown_anchor_bar_time(0),
                     m_active_cooldown_bars(0),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const string symbol,
                          const ENUM_TIMEFRAMES timeframe,
                          const bool spread_filter,
                          const int max_spread_points,
                          const int cooldown_bars,
                          const int cooldown_bars_after_sl,
                          const int max_open_trades,
                          const double min_equity)
     {
      m_symbol = symbol;
      m_timeframe = timeframe;
      m_spread_filter = spread_filter;
      m_max_spread_points = max_spread_points;
      m_cooldown_bars = cooldown_bars;
      m_cooldown_bars_after_sl = cooldown_bars_after_sl;
      m_max_open_trades = max_open_trades;
      m_min_equity = min_equity;
     }

   void              RegisterEntry()
     {
      // Entry timestamp reserved for future bar-based entry spacing.
     }

   void              StartCooldownAfterTp()
     {
      m_cooldown_anchor_bar_time = iTime(m_symbol, m_timeframe, 0);
      m_active_cooldown_bars = m_cooldown_bars;
     }

   void              StartCooldownAfterSl()
     {
      m_cooldown_anchor_bar_time = iTime(m_symbol, m_timeframe, 0);
      m_active_cooldown_bars = MathMax(m_cooldown_bars, m_cooldown_bars_after_sl);
      if(m_log != NULL)
         m_log.LogInfo("SL/time cooldown for " + IntegerToString(m_active_cooldown_bars) + " bars");
     }

   bool              CooldownExpired(const CFemaStateMachine &state) const
     {
      if(state.GetState() != FEMA_STATE_COOLDOWN)
         return true;
      if(m_active_cooldown_bars <= 0)
         return true;
      if(m_cooldown_anchor_bar_time <= 0)
         return true;
      const int bars_since = CFemaHelpers::BarsSince(m_symbol, m_timeframe, m_cooldown_anchor_bar_time);
      return bars_since >= m_active_cooldown_bars;
     }

   bool              AllowEntry(const CFemaStateMachine &state,
                                const CFemaExposure &exposure,
                                string &reason) const
     {
      reason = "";

      if(state.GetState() == FEMA_STATE_SUSPENDED)
        {
         reason = "EA suspended";
         return false;
        }

      if(state.GetState() == FEMA_STATE_COOLDOWN)
        {
         if(!CooldownExpired(state))
           {
            reason = "Cooldown active";
            return false;
           }
        }

      if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
        {
         reason = "Terminal trading disabled";
         return false;
        }

      if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
        {
         reason = "EA trading disabled";
         return false;
        }

      if(m_min_equity > 0.0 && AccountInfoDouble(ACCOUNT_EQUITY) < m_min_equity)
        {
         reason = "Equity below minimum";
         return false;
        }

      const int spread = CFemaHelpers::SpreadPoints(m_symbol);
      if(m_spread_filter && spread > m_max_spread_points)
        {
         reason = "Spread too high: " + IntegerToString(spread);
         return false;
        }

      if(exposure.CountOpenPositions() >= m_max_open_trades)
        {
         reason = "Max open trades reached";
         return false;
        }

      return true;
     }
  };

#endif
