//+------------------------------------------------------------------+
//| TradeManager.mqh — comment format and ticket helpers             |
//+------------------------------------------------------------------+
#ifndef FEMA_TRADEMANAGER_MQH
#define FEMA_TRADEMANAGER_MQH

#include <Trade\PositionInfo.mqh>
#include "../Core/Types.mqh"

class CFemaTradeManager
  {
private:
   string            m_symbol;
   ulong             m_magic;

public:
                     CFemaTradeManager() : m_symbol(""), m_magic(0) {}

   void              Init(const string symbol, const ulong magic)
     {
      m_symbol = symbol;
      m_magic = magic;
     }

   static string     BuildComment(const int level_index, const ENUM_FEMA_DIRECTION direction)
     {
      return "FEG_L" + IntegerToString(level_index) + "_" + FemaDirectionToString(direction);
     }

   void              CollectTickets(ulong &tickets[]) const
     {
      ArrayResize(tickets, 0);
      CPositionInfo position;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(!position.SelectByIndex(i))
            continue;
         if(position.Symbol() != m_symbol)
            continue;
         if(position.Magic() != m_magic)
            continue;
         const int size = ArraySize(tickets);
         ArrayResize(tickets, size + 1);
         tickets[size] = position.Ticket();
        }
     }
  };

#endif
