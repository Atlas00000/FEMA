//+------------------------------------------------------------------+
//| Exposure.mqh — open position count by magic                      |
//+------------------------------------------------------------------+
#ifndef FEMA_EXPOSURE_MQH
#define FEMA_EXPOSURE_MQH

#include <Trade\PositionInfo.mqh>
#include "../Core/Types.mqh"

class CFemaExposure
  {
private:
   string            m_symbol;
   ulong             m_magic;

public:
                     CFemaExposure() : m_symbol(""), m_magic(0) {}

   void              Init(const string symbol, const ulong magic)
     {
      m_symbol = symbol;
      m_magic = magic;
     }

   int               CountOpenPositions() const
     {
      int count = 0;
      CPositionInfo position;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(!position.SelectByIndex(i))
            continue;
         if(position.Symbol() != m_symbol)
            continue;
         if(position.Magic() != m_magic)
            continue;
         count++;
        }
      return count;
     }

   double            FloatingProfit() const
     {
      double profit = 0.0;
      CPositionInfo position;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(!position.SelectByIndex(i))
            continue;
         if(position.Symbol() != m_symbol)
            continue;
         if(position.Magic() != m_magic)
            continue;
         profit += position.Profit() + position.Swap() + position.Commission();
        }
      return profit;
     }

   bool              HasOpenPositions() const
     {
      return CountOpenPositions() > 0;
     }

   ENUM_FEMA_DIRECTION PrimaryDirection() const
     {
      CPositionInfo position;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(!position.SelectByIndex(i))
            continue;
         if(position.Symbol() != m_symbol)
            continue;
         if(position.Magic() != m_magic)
            continue;
         if(position.PositionType() == POSITION_TYPE_BUY)
            return FEMA_DIR_BUY;
         if(position.PositionType() == POSITION_TYPE_SELL)
            return FEMA_DIR_SELL;
        }
      return FEMA_DIR_NONE;
     }
  };

#endif
