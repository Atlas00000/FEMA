//+------------------------------------------------------------------+
//| EntryEngine.mqh — grid level touch + trend filter                |
//+------------------------------------------------------------------+
#ifndef FEMA_ENTRYENGINE_MQH
#define FEMA_ENTRYENGINE_MQH

#include "../Core/Config.mqh"
#include "../Core/Types.mqh"
#include "../Grid/GridManager.mqh"
#include "../Indicators/Indicators.mqh"
#include "../Indicators/HtfFilter.mqh"
#include "../Utils/Helpers.mqh"

class CFemaEntryEngine
  {
private:
   string            m_symbol;
   ENUM_FEMA_TRADE_PERMISSION m_permission;
   int               m_max_entry_depth;

   bool              DirectionAllowed(const ENUM_FEMA_DIRECTION dir) const
     {
      if(dir == FEMA_DIR_BUY)
         return m_permission == FEMA_PERM_BOTH || m_permission == FEMA_PERM_BUY_ONLY;
      if(dir == FEMA_DIR_SELL)
         return m_permission == FEMA_PERM_BOTH || m_permission == FEMA_PERM_SELL_ONLY;
      return false;
     }

   bool              TrendAllows(const ENUM_FEMA_DIRECTION dir, const ENUM_FEMA_TREND trend) const
     {
      if(trend == FEMA_TREND_UP)
         return dir == FEMA_DIR_BUY;
      if(trend == FEMA_TREND_DOWN)
         return dir == FEMA_DIR_SELL;
      return false;
     }

   bool              IsLevelTouched(const SFemaGridLevel &level) const
     {
      const double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      const double ask = SymbolInfoDouble(m_symbol, SYMBOL_ASK);
      if(level.direction == FEMA_DIR_BUY)
         return ask <= level.price;
      if(level.direction == FEMA_DIR_SELL)
         return bid >= level.price;
      return false;
     }

public:
                     CFemaEntryEngine() : m_symbol(""), m_permission(FEMA_PERM_BOTH), m_max_entry_depth(5) {}

   void              Init(const string symbol,
                          const ENUM_FEMA_TRADE_PERMISSION permission,
                          const int max_entry_depth)
     {
      m_symbol = symbol;
      m_permission = permission;
      m_max_entry_depth = MathMax(1, max_entry_depth);
     }

   bool              Evaluate(CFemaGridManager &grid,
                              const CFemaIndicators &indicators,
                              const CFemaHtfFilter &htf,
                              SFemaSignal &signal) const
     {
      signal.valid = false;
      signal.direction = FEMA_DIR_NONE;
      signal.level_index = 0;
      signal.level_price = 0.0;
      signal.trigger_price = 0.0;

      if(htf.IsEnabled() && !htf.IsReady())
         return false;

      const ENUM_FEMA_TREND trend = indicators.Trend();
      if(trend == FEMA_TREND_NONE)
         return false;

      for(int i = 0; i < grid.LevelCount(); i++)
        {
         SFemaGridLevel level;
         if(!grid.GetLevel(i, level))
            continue;
         if(level.fired)
            continue;
         if(level.index > m_max_entry_depth)
            continue;
         if(!TrendAllows(level.direction, trend))
            continue;
         if(!DirectionAllowed(level.direction))
            continue;
         if(!htf.Allows(level.direction))
            continue;
         if(!IsLevelTouched(level))
            continue;

         signal.valid = true;
         signal.direction = level.direction;
         signal.level_index = level.index;
         signal.level_price = level.price;
         signal.trigger_price = (level.direction == FEMA_DIR_BUY) ?
                                SymbolInfoDouble(m_symbol, SYMBOL_ASK) :
                                SymbolInfoDouble(m_symbol, SYMBOL_BID);
         return true;
        }
      return false;
     }

   int               FindLevelArrayIndex(CFemaGridManager &grid, const SFemaSignal &signal) const
     {
      for(int i = 0; i < grid.LevelCount(); i++)
        {
         SFemaGridLevel level;
         if(!grid.GetLevel(i, level))
            continue;
         if(level.index == signal.level_index && level.direction == signal.direction)
            return i;
        }
      return -1;
     }
  };

#endif
