//+------------------------------------------------------------------+
//| ExitEngine.mqh — basket TP / SL / RTE / trail exits              |
//+------------------------------------------------------------------+
#ifndef FEMA_EXITENGINE_MQH
#define FEMA_EXITENGINE_MQH

#include "../Core/Types.mqh"
#include "../Broker/Execution.mqh"
#include "../Trading/BasketManager.mqh"
#include "../Utils/Logger.mqh"

class CFemaExitEngine
  {
private:
   double            m_basket_tp;
   double            m_basket_sl;
   bool              m_use_basket_sl;
   int               m_max_basket_bars;
   bool              m_use_exit_rte;
   double            m_rte_min_profit;
   bool              m_use_basket_trail;
   double            m_trail_activate_pct;
   double            m_trail_giveback_pct;
   bool              m_trail_armed;
   double            m_trail_peak;
   CFemaLogger      *m_log;

   bool              IsRteExit(const ENUM_FEMA_DIRECTION direction,
                                 const double ema_fast,
                                 const double bid,
                                 const double ask,
                                 const double profit) const
     {
      if(!m_use_exit_rte || direction == FEMA_DIR_NONE || ema_fast <= 0.0)
         return false;
      if(profit < m_rte_min_profit)
         return false;

      if(direction == FEMA_DIR_BUY)
         return bid >= ema_fast;
      if(direction == FEMA_DIR_SELL)
         return ask <= ema_fast;
      return false;
     }

   bool              IsTrailExit(const double profit) const
     {
      if(!m_use_basket_trail || !m_trail_armed || m_trail_peak <= 0.0)
         return false;

      const double floor = m_trail_peak * (1.0 - m_trail_giveback_pct / 100.0);
      return profit <= floor;
     }

public:
                     CFemaExitEngine() :
                     m_basket_tp(10.0),
                     m_basket_sl(20.0),
                     m_use_basket_sl(true),
                     m_max_basket_bars(0),
                     m_use_exit_rte(false),
                     m_rte_min_profit(0.0),
                     m_use_basket_trail(false),
                     m_trail_activate_pct(50.0),
                     m_trail_giveback_pct(50.0),
                     m_trail_armed(false),
                     m_trail_peak(0.0),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const double basket_tp,
                          const bool use_basket_sl,
                          const double basket_sl,
                          const int max_basket_bars,
                          const bool use_exit_rte,
                          const double rte_min_profit,
                          const bool use_basket_trail,
                          const double trail_activate_pct,
                          const double trail_giveback_pct)
     {
      m_basket_tp = basket_tp;
      m_use_basket_sl = use_basket_sl;
      m_basket_sl = basket_sl;
      m_max_basket_bars = max_basket_bars;
      m_use_exit_rte = use_exit_rte;
      m_rte_min_profit = rte_min_profit;
      m_use_basket_trail = use_basket_trail;
      m_trail_activate_pct = trail_activate_pct;
      m_trail_giveback_pct = trail_giveback_pct;
      ResetTrailState();
     }

   void              ResetTrailState()
     {
      m_trail_armed = false;
      m_trail_peak = 0.0;
     }

   void              UpdateTrail(const double profit)
     {
      if(!m_use_basket_trail || m_basket_tp <= 0.0)
         return;

      const double activate_level = m_basket_tp * m_trail_activate_pct / 100.0;
      if(!m_trail_armed)
        {
         if(profit >= activate_level)
           {
            m_trail_armed = true;
            m_trail_peak = profit;
           }
         return;
        }

      if(profit > m_trail_peak)
         m_trail_peak = profit;
     }

   string            ActiveSummary() const
     {
      if(m_use_exit_rte)
         return "rte";
      if(m_use_basket_trail)
         return "trail" + DoubleToString(m_trail_activate_pct, 0);
      return "btp";
     }

   ENUM_FEMA_EXIT_REASON GetCloseReason(const CFemaBasketManager &basket,
                                        const ENUM_FEMA_DIRECTION direction,
                                        const double ema_fast,
                                        const double bid,
                                        const double ask) const
     {
      if(!basket.HasOpenPositions())
         return FEMA_EXIT_NONE;

      const double profit = basket.FloatingProfit();

      if(m_use_basket_sl && m_basket_sl > 0.0 && profit <= -m_basket_sl)
         return FEMA_EXIT_BASKET_SL;

      if(m_max_basket_bars > 0 && basket.AgeBars() >= m_max_basket_bars)
         return FEMA_EXIT_BASKET_TIME;

      if(IsRteExit(direction, ema_fast, bid, ask, profit))
         return FEMA_EXIT_RTE;

      if(IsTrailExit(profit))
         return FEMA_EXIT_BASKET_TRAIL;

      if(m_basket_tp > 0.0 && profit >= m_basket_tp)
         return FEMA_EXIT_BASKET_TP;

      return FEMA_EXIT_NONE;
     }

   bool              CloseBasket(CFemaBasketManager &basket,
                                 CFemaExecution &execution,
                                 const ENUM_FEMA_EXIT_REASON reason)
     {
      ulong tickets[];
      if(!basket.CollectTickets(tickets))
         return false;

      bool all_closed = true;
      for(int i = 0; i < ArraySize(tickets); i++)
        {
         int retcode = 0;
         if(!execution.ClosePosition(tickets[i], retcode))
            all_closed = false;
        }

      if(all_closed)
         ResetTrailState();

      if(m_log != NULL)
        {
         if(all_closed)
            m_log.LogInfo("Basket closed: " + FemaExitReasonToString(reason) +
                          " profit=" + DoubleToString(basket.FloatingProfit(), 2));
         else
            m_log.LogWarn("Basket close incomplete: " + FemaExitReasonToString(reason));
        }
      return all_closed;
     }
  };

#endif
