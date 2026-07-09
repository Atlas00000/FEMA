//+------------------------------------------------------------------+
//| ExitEngine.mqh — basket TP / SL / time exits                     |
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
   CFemaLogger      *m_log;

public:
                     CFemaExitEngine() :
                     m_basket_tp(10.0),
                     m_basket_sl(20.0),
                     m_use_basket_sl(true),
                     m_max_basket_bars(0),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const double basket_tp,
                          const bool use_basket_sl,
                          const double basket_sl,
                          const int max_basket_bars)
     {
      m_basket_tp = basket_tp;
      m_use_basket_sl = use_basket_sl;
      m_basket_sl = basket_sl;
      m_max_basket_bars = max_basket_bars;
     }

   ENUM_FEMA_EXIT_REASON GetCloseReason(const CFemaBasketManager &basket) const
     {
      if(!basket.HasOpenPositions())
         return FEMA_EXIT_NONE;

      const double profit = basket.FloatingProfit();

      if(m_use_basket_sl && m_basket_sl > 0.0 && profit <= -m_basket_sl)
         return FEMA_EXIT_BASKET_SL;

      if(m_max_basket_bars > 0 && basket.AgeBars() >= m_max_basket_bars)
         return FEMA_EXIT_BASKET_TIME;

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
