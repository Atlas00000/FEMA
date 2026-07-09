//+------------------------------------------------------------------+
//| SymbolInfo.mqh — cached broker symbol constraints                |
//+------------------------------------------------------------------+
#ifndef FEMA_SYMBOLINFO_MQH
#define FEMA_SYMBOLINFO_MQH

#include <Trade\SymbolInfo.mqh>

class CFemaSymbolInfo
  {
private:
   string            m_symbol;
   CSymbolInfo       m_info;
   int               m_stops_level;
   int               m_freeze_level;
   double            m_volume_min;
   double            m_volume_max;
   double            m_volume_step;
   ENUM_SYMBOL_TRADE_MODE m_trade_mode;
   ENUM_ACCOUNT_MARGIN_MODE m_margin_mode;

   ENUM_ORDER_TYPE_FILLING ResolveFilling() const
     {
      const long filling = SymbolInfoInteger(m_symbol, SYMBOL_FILLING_MODE);
      if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
         return ORDER_FILLING_FOK;
      if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
         return ORDER_FILLING_IOC;
      return ORDER_FILLING_RETURN;
     }

public:
                     CFemaSymbolInfo() :
                     m_symbol(""),
                     m_stops_level(0),
                     m_freeze_level(0),
                     m_volume_min(0.0),
                     m_volume_max(0.0),
                     m_volume_step(0.0),
                     m_trade_mode(SYMBOL_TRADE_MODE_DISABLED),
                     m_margin_mode(ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
     {}

   bool              Init(const string symbol)
     {
      m_symbol = symbol;
      if(!m_info.Name(m_symbol))
         return false;

      m_stops_level = (int)SymbolInfoInteger(m_symbol, SYMBOL_TRADE_STOPS_LEVEL);
      m_freeze_level = (int)SymbolInfoInteger(m_symbol, SYMBOL_TRADE_FREEZE_LEVEL);
      m_volume_min = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MIN);
      m_volume_max = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_MAX);
      m_volume_step = SymbolInfoDouble(m_symbol, SYMBOL_VOLUME_STEP);
      m_trade_mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(m_symbol, SYMBOL_TRADE_MODE);
      m_margin_mode = (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
      return true;
     }

   string            Symbol() const { return m_symbol; }
   int               StopsLevel() const { return m_stops_level; }
   int               FreezeLevel() const { return m_freeze_level; }
   double            VolumeMin() const { return m_volume_min; }
   double            VolumeMax() const { return m_volume_max; }
   double            VolumeStep() const { return m_volume_step; }
   ENUM_SYMBOL_TRADE_MODE TradeMode() const { return m_trade_mode; }
   ENUM_ACCOUNT_MARGIN_MODE MarginMode() const { return m_margin_mode; }
   ENUM_ORDER_TYPE_FILLING FillingMode() const { return ResolveFilling(); }

   bool              IsTradeAllowed() const
     {
      return m_trade_mode == SYMBOL_TRADE_MODE_FULL;
     }
  };

#endif
