//+------------------------------------------------------------------+
//| Logger.mqh — structured logging                                  |
//+------------------------------------------------------------------+
#ifndef FEMA_LOGGER_MQH
#define FEMA_LOGGER_MQH

#include "../Core/Types.mqh"

class CFemaLogger
  {
private:
   ENUM_FEMA_LOG_MODE m_mode;
   string             m_prefix;

   void              Write(const string level, const string message) const
     {
      Print(m_prefix, "[", level, "] ", message);
     }

public:
                     CFemaLogger() : m_mode(FEMA_LOG_DETAILED), m_prefix("FEMA|") {}

   void              Init(const ENUM_FEMA_LOG_MODE mode, const string symbol)
     {
      m_mode = mode;
      m_prefix = "FEMA|" + symbol + "|";
     }

   bool              IsDetailed() const { return m_mode == FEMA_LOG_DETAILED; }

   void              LogInfo(const string message) const
     {
      Write("INFO", message);
     }

   void              LogWarn(const string message) const
     {
      Write("WARN", message);
     }

   void              LogError(const string message) const
     {
      Write("ERROR", message);
     }

   void              LogBarSummary(const ENUM_FEMA_STATE state,
                                     const double ema_fast,
                                     const double ema_trend,
                                     const double atr,
                                     const ENUM_FEMA_TREND trend,
                                     const double grid_center) const
     {
      if(!IsDetailed())
         return;
      Write("BAR",
            "state=" + FemaStateToString(state) +
            " ema_fast=" + DoubleToString(ema_fast, _Digits) +
            " ema_trend=" + DoubleToString(ema_trend, _Digits) +
            " atr=" + DoubleToString(atr, _Digits) +
            " trend=" + FemaTrendToString(trend) +
            " center=" + DoubleToString(grid_center, _Digits));
     }

   void              LogGridLevel(const int index,
                                  const ENUM_FEMA_DIRECTION dir,
                                  const double price,
                                  const bool fired) const
     {
      if(!IsDetailed())
         return;
      Write("GRID",
            "L" + IntegerToString(index) + " " + FemaDirectionToString(dir) +
            " price=" + DoubleToString(price, _Digits) +
            " fired=" + (fired ? "yes" : "no"));
     }

   void              LogSignal(const SFemaSignal &signal, const int spread_points) const
     {
      if(!IsDetailed())
         return;
      if(!signal.valid)
         return;
      Write("SIGNAL",
            FemaDirectionToString(signal.direction) +
            " L" + IntegerToString(signal.level_index) +
            " level=" + DoubleToString(signal.level_price, _Digits) +
            " trigger=" + DoubleToString(signal.trigger_price, _Digits) +
            " spread=" + IntegerToString(spread_points));
     }

   void              LogOrderResult(const ulong basket_id,
                                    const ENUM_FEMA_DIRECTION dir,
                                    const int level_index,
                                    const double price,
                                    const double lots,
                                    const bool success,
                                    const int retcode,
                                    const string comment) const
     {
      const string msg =
         "basket=" + IntegerToString((int)basket_id) +
         " " + FemaDirectionToString(dir) +
         " L" + IntegerToString(level_index) +
         " price=" + DoubleToString(price, _Digits) +
         " lots=" + DoubleToString(lots, 2) +
         " ok=" + (success ? "yes" : "no") +
         " retcode=" + IntegerToString(retcode) +
         " comment=" + comment;
      if(success)
         LogInfo(msg);
      else
         LogError(msg);
     }

   void              LogBasket(const ulong basket_id,
                               const double profit,
                               const int positions,
                               const ENUM_FEMA_STATE state) const
     {
      const string msg =
         "basket=" + IntegerToString((int)basket_id) +
         " profit=" + DoubleToString(profit, 2) +
         " positions=" + IntegerToString(positions) +
         " state=" + FemaStateToString(state);
      if(IsDetailed())
         LogInfo(msg);
     }

   void              LogTickMinimal(const ENUM_FEMA_STATE state, const double basket_profit) const
     {
      if(IsDetailed())
         return;
      Write("TICK", FemaStateToString(state) + " basket_pl=" + DoubleToString(basket_profit, 2));
     }
  };

#endif
