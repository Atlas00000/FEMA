//+------------------------------------------------------------------+
//| Helpers.mqh — bar detection and price normalization              |
//+------------------------------------------------------------------+
#ifndef FEMA_HELPERS_MQH
#define FEMA_HELPERS_MQH

#include "../Core/Types.mqh"

class CFemaHelpers
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_timeframe;
   datetime          m_last_bar_time;

public:
                     CFemaHelpers() : m_symbol(""), m_timeframe(PERIOD_CURRENT), m_last_bar_time(0) {}

   void              Init(const string symbol, const ENUM_TIMEFRAMES timeframe)
     {
      m_symbol = symbol;
      m_timeframe = timeframe;
      m_last_bar_time = iTime(m_symbol, m_timeframe, 0);
     }

   string            Symbol() const { return m_symbol; }
   ENUM_TIMEFRAMES   Timeframe() const { return m_timeframe; }

   bool              IsNewBar()
     {
      const datetime bar_time = iTime(m_symbol, m_timeframe, 0);
      if(bar_time == 0)
         return false;
      if(bar_time != m_last_bar_time)
        {
         m_last_bar_time = bar_time;
         return true;
        }
      return false;
     }

   static double     NormalizePrice(const string symbol, const double price)
     {
      const int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      return NormalizeDouble(price, digits);
     }

   static double     NormalizeVolume(const string symbol, const double volume)
     {
      const double min_vol  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
      const double max_vol  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
      const double step     = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
      if(step <= 0.0)
         return volume;

      double lots = MathFloor(volume / step + 0.0000001) * step;
      lots = MathMax(min_vol, lots);
      lots = MathMin(max_vol, lots);
      return NormalizeDouble(lots, 2);
     }

   static int        SpreadPoints(const string symbol)
     {
      const double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      const double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      const double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      if(point <= 0.0)
         return 0;
      return (int)MathRound((ask - bid) / point);
     }

   static int        BarsSince(const string symbol, const ENUM_TIMEFRAMES timeframe, const datetime from_time)
     {
      if(from_time <= 0)
         return INT_MAX;
      const int shift = iBarShift(symbol, timeframe, from_time, true);
      if(shift < 0)
         return INT_MAX;
      return shift;
     }

   static bool       CalcAtrStopPrice(const string symbol,
                                      const ENUM_FEMA_DIRECTION direction,
                                      const double entry_price,
                                      const double atr,
                                      const double atr_multiplier,
                                      const int stops_level,
                                      double &sl_price)
     {
      sl_price = 0.0;
      if(entry_price <= 0.0 || atr <= 0.0 || atr_multiplier <= 0.0)
         return false;

      const double sl_distance = atr * atr_multiplier;
      return ApplyStopDistance(symbol, direction, entry_price, sl_distance, stops_level, sl_price);
     }

   static bool       CalcGridStructureStopPrice(const string symbol,
                                                const ENUM_FEMA_DIRECTION direction,
                                                const double entry_price,
                                                const double atr,
                                                const double atr_multiplier,
                                                const double grid_atr_multiplier,
                                                const int level_index,
                                                const int grid_levels,
                                                const int stops_level,
                                                double &sl_price)
     {
      sl_price = 0.0;
      if(entry_price <= 0.0 || atr <= 0.0 || level_index < 1 || grid_levels < 1)
         return false;

      const double spacing = atr * grid_atr_multiplier;
      const int levels_to_bottom = grid_levels - level_index + 1;
      const double sl_distance = levels_to_bottom * spacing + atr * atr_multiplier * 0.25;
      return ApplyStopDistance(symbol, direction, entry_price, sl_distance, stops_level, sl_price);
     }

   static bool       ApplyStopDistance(const string symbol,
                                       const ENUM_FEMA_DIRECTION direction,
                                       const double entry_price,
                                       const double sl_distance,
                                       const int stops_level,
                                       double &sl_price)
     {
      sl_price = 0.0;
      if(entry_price <= 0.0 || sl_distance <= 0.0)
         return false;

      const double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      const double min_dist = (stops_level > 0 && point > 0.0) ? stops_level * point : point;
      double distance = MathMax(sl_distance, min_dist);

      if(direction == FEMA_DIR_BUY)
         sl_price = entry_price - distance;
      else if(direction == FEMA_DIR_SELL)
         sl_price = entry_price + distance;
      else
         return false;

      sl_price = NormalizePrice(symbol, sl_price);
      return sl_price > 0.0;
     }
  };

#endif
