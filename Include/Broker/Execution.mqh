//+------------------------------------------------------------------+
//| Execution.mqh — market order execution with retry                |
//+------------------------------------------------------------------+
#ifndef FEMA_EXECUTION_MQH
#define FEMA_EXECUTION_MQH

#include <Trade\Trade.mqh>
#include "../Broker/SymbolInfo.mqh"
#include "../Core/Types.mqh"
#include "../Utils/Logger.mqh"

class CFemaExecution
  {
private:
   string            m_symbol;
   ulong             m_magic;
   int               m_slippage_points;
   int               m_max_retries;
   ENUM_ORDER_TYPE_FILLING m_filling;
   CTrade            m_trade;
   CFemaLogger      *m_log;

   bool              SendMarket(const ENUM_FEMA_DIRECTION direction,
                                const double lots,
                                const double sl,
                                const string comment,
                                int &retcode)
     {
      m_trade.SetExpertMagicNumber(m_magic);
      m_trade.SetDeviationInPoints(m_slippage_points);
      m_trade.SetTypeFilling(m_filling);

      bool ok = false;
      if(direction == FEMA_DIR_BUY)
         ok = m_trade.Buy(lots, m_symbol, 0.0, sl, 0.0, comment);
      else if(direction == FEMA_DIR_SELL)
         ok = m_trade.Sell(lots, m_symbol, 0.0, sl, 0.0, comment);

      retcode = (int)m_trade.ResultRetcode();
      if(!ok && m_log != NULL)
         m_log.LogError("Order failed retcode=" + IntegerToString(retcode) +
                        " desc=" + m_trade.ResultRetcodeDescription());
      return ok;
     }

public:
                     CFemaExecution() :
                     m_symbol(""),
                     m_magic(0),
                     m_slippage_points(5),
                     m_max_retries(3),
                     m_filling(ORDER_FILLING_IOC),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Init(const string symbol,
                          const ulong magic,
                          const int slippage_points,
                          const CFemaSymbolInfo &symbol_info)
     {
      m_symbol = symbol;
      m_magic = magic;
      m_slippage_points = slippage_points;
      m_filling = symbol_info.FillingMode();
      m_trade.SetExpertMagicNumber(m_magic);
      m_trade.SetDeviationInPoints(m_slippage_points);
      m_trade.SetTypeFilling(m_filling);
      return true;
     }

   bool              OpenMarket(const ENUM_FEMA_DIRECTION direction,
                                 const double lots,
                                 const double sl,
                                 const string comment,
                                 int &retcode)
     {
      int deviation = m_slippage_points;
      for(int attempt = 1; attempt <= m_max_retries; attempt++)
        {
         m_trade.SetDeviationInPoints(deviation);
         if(SendMarket(direction, lots, sl, comment, retcode))
            return true;

         if(retcode == TRADE_RETCODE_REQUOTE || retcode == TRADE_RETCODE_PRICE_OFF)
            deviation += m_slippage_points;
        }
      return false;
     }

   bool              ClosePosition(const ulong ticket, int &retcode)
     {
      m_trade.SetExpertMagicNumber(m_magic);
      m_trade.SetDeviationInPoints(m_slippage_points);
      const bool ok = m_trade.PositionClose(ticket);
      retcode = (int)m_trade.ResultRetcode();
      if(!ok && m_log != NULL)
         m_log.LogError("Close failed ticket=" + IntegerToString((int)ticket) +
                        " retcode=" + IntegerToString(retcode));
      return ok;
     }
  };

#endif
