//+------------------------------------------------------------------+
//| BasketManager.mqh — basket grouping and floating P/L             |
//+------------------------------------------------------------------+
#ifndef FEMA_BASKETMANAGER_MQH
#define FEMA_BASKETMANAGER_MQH

#include "../Risk/Exposure.mqh"
#include "../Trading/TradeManager.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

class CFemaBasketManager
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_timeframe;
   ulong             m_basket_id;
   datetime          m_basket_start_bar_time;
   CFemaExposure    *m_exposure;
   CFemaTradeManager *m_trade_manager;
   CFemaLogger      *m_log;

public:
                     CFemaBasketManager() :
                     m_symbol(""),
                     m_timeframe(PERIOD_CURRENT),
                     m_basket_id(0),
                     m_basket_start_bar_time(0),
                     m_exposure(NULL),
                     m_trade_manager(NULL),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const string symbol,
                          const ENUM_TIMEFRAMES timeframe,
                          CFemaExposure &exposure,
                          CFemaTradeManager &trade_manager)
     {
      m_symbol = symbol;
      m_timeframe = timeframe;
      m_exposure = GetPointer(exposure);
      m_trade_manager = GetPointer(trade_manager);
      m_basket_id = 0;
      m_basket_start_bar_time = 0;
     }

   ulong             BasketId() const { return m_basket_id; }
   datetime          BasketStartBarTime() const { return m_basket_start_bar_time; }

   void              OnBasketStart(const datetime bar_time)
     {
      if(m_basket_id == 0)
         m_basket_id = 1;
      else
         m_basket_id++;
      m_basket_start_bar_time = bar_time;
     }

   void              OnBasketClosed()
     {
      m_basket_id = 0;
      m_basket_start_bar_time = 0;
     }

   int               AgeBars() const
     {
      if(m_basket_start_bar_time <= 0)
         return 0;
      return CFemaHelpers::BarsSince(m_symbol, m_timeframe, m_basket_start_bar_time);
     }

   bool              HasOpenPositions() const
     {
      return m_exposure != NULL && m_exposure.HasOpenPositions();
     }

   int               PositionCount() const
     {
      return m_exposure != NULL ? m_exposure.CountOpenPositions() : 0;
     }

   double            FloatingProfit() const
     {
      return m_exposure != NULL ? m_exposure.FloatingProfit() : 0.0;
     }

   bool              CollectTickets(ulong &tickets[]) const
     {
      if(m_trade_manager == NULL)
         return false;
      m_trade_manager.CollectTickets(tickets);
      return ArraySize(tickets) > 0;
     }
  };

#endif
