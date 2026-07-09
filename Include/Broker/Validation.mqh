//+------------------------------------------------------------------+
//| Validation.mqh — pre-trade broker checks                         |
//+------------------------------------------------------------------+
#ifndef FEMA_VALIDATION_MQH
#define FEMA_VALIDATION_MQH

#include "../Broker/SymbolInfo.mqh"
#include "../Core/Types.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

class CFemaValidation
  {
private:
   CFemaLogger      *m_log;

public:
                     CFemaValidation() : m_log(NULL) {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Validate(const CFemaSymbolInfo &symbol_info,
                              const ENUM_FEMA_DIRECTION direction,
                              const double lots,
                              const double sl,
                              string &reason) const
     {
      reason = "";
      const string symbol = symbol_info.Symbol();

      if(!symbol_info.IsTradeAllowed())
        {
         reason = "Symbol trade mode disabled";
         return false;
        }

      if(lots < symbol_info.VolumeMin() - 0.0000001 || lots > symbol_info.VolumeMax() + 0.0000001)
        {
         reason = "Lot size out of broker bounds";
         return false;
        }

      const double step = symbol_info.VolumeStep();
      if(step > 0.0)
        {
         const double normalized = CFemaHelpers::NormalizeVolume(symbol, lots);
         if(MathAbs(normalized - lots) > step * 0.1)
           {
            reason = "Lot size not aligned to volume step";
            return false;
           }
        }

      const double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      const double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      const double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
      const int freeze = symbol_info.FreezeLevel();
      const int stops_level = symbol_info.StopsLevel();
      const double min_stop_dist = (stops_level > 0 && point > 0.0) ? stops_level * point : 0.0;

      if(direction == FEMA_DIR_BUY)
        {
         if(ask <= 0.0)
           {
            reason = "Invalid ask price";
            return false;
           }
         if(sl > 0.0)
           {
            if(sl >= ask)
              {
               reason = "Buy SL must be below entry";
               return false;
              }
            if(min_stop_dist > 0.0 && ask - sl < min_stop_dist)
              {
               reason = "Buy SL inside stops level";
               return false;
              }
           }
         if(freeze > 0 && point > 0.0)
           {
            const double distance_points = MathAbs(ask - bid) / point;
            if(distance_points <= freeze)
              {
               reason = "Inside freeze level";
               return false;
              }
           }
        }
      else if(direction == FEMA_DIR_SELL)
        {
         if(bid <= 0.0)
           {
            reason = "Invalid bid price";
            return false;
           }
         if(sl > 0.0)
           {
            if(sl <= bid)
              {
               reason = "Sell SL must be above entry";
               return false;
              }
            if(min_stop_dist > 0.0 && sl - bid < min_stop_dist)
              {
               reason = "Sell SL inside stops level";
               return false;
              }
           }
        }
      else
        {
         reason = "Invalid direction";
         return false;
        }

      return true;
     }
  };

#endif
