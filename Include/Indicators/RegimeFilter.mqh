//+------------------------------------------------------------------+
//| RegimeFilter.mqh — ADX / ATR / EMA regime gates (Phase 2C)       |
//+------------------------------------------------------------------+
#ifndef FEMA_REGIMEFILTER_MQH
#define FEMA_REGIMEFILTER_MQH

#include "../Core/Types.mqh"
#include "../Indicators/Indicators.mqh"
#include "../Utils/Logger.mqh"

class CFemaRegimeFilter
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_timeframe;
   bool              m_use_adx_gate;
   double            m_adx_max;
   int               m_adx_period;
   bool              m_use_atr_pct_gate;
   double            m_atr_pct_max;
   int               m_atr_pct_lookback;
   bool              m_use_ema_sep_gate;
   double            m_ema_sep_atr_mult;
   bool              m_use_ema_slope_gate;
   bool              m_use_breakout_suspend;
   double            m_breakout_atr_mult;
   int               m_handle_adx;
   double            m_adx;
   double            m_atr_pct_threshold;
   bool              m_ready;
   CFemaLogger      *m_log;

   bool              IsActive() const
     {
      return m_use_adx_gate || m_use_atr_pct_gate || m_use_ema_sep_gate ||
             m_use_ema_slope_gate || m_use_breakout_suspend;
     }

   static double     PercentileValue(double &values[], const double pct)
     {
      const int n = ArraySize(values);
      if(n <= 0)
         return 0.0;
      ArraySort(values);
      const int idx = (int)MathFloor((pct / 100.0) * (n - 1));
      return values[MathMax(0, MathMin(n - 1, idx))];
     }

   bool              UpdateAtrPercentile(const CFemaIndicators &indicators)
     {
      if(!m_use_atr_pct_gate)
         return true;

      const int lookback = MathMax(10, m_atr_pct_lookback);
      double atr_buf[];
      ArraySetAsSeries(atr_buf, true);
      if(CopyBuffer(indicators.AtrHandle(), 0, 1, lookback, atr_buf) != lookback)
         return false;

      m_atr_pct_threshold = PercentileValue(atr_buf, m_atr_pct_max);
      return m_atr_pct_threshold > 0.0;
     }

public:
                     CFemaRegimeFilter() :
                     m_symbol(""),
                     m_timeframe(PERIOD_CURRENT),
                     m_use_adx_gate(false),
                     m_adx_max(25.0),
                     m_adx_period(14),
                     m_use_atr_pct_gate(false),
                     m_atr_pct_max(70.0),
                     m_atr_pct_lookback(100),
                     m_use_ema_sep_gate(false),
                     m_ema_sep_atr_mult(3.0),
                     m_use_ema_slope_gate(false),
                     m_use_breakout_suspend(false),
                     m_breakout_atr_mult(3.0),
                     m_handle_adx(INVALID_HANDLE),
                     m_adx(0.0),
                     m_atr_pct_threshold(0.0),
                     m_ready(false),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Init(const string symbol,
                          const ENUM_TIMEFRAMES timeframe,
                          const bool use_adx_gate,
                          const double adx_max,
                          const int adx_period,
                          const bool use_atr_pct_gate,
                          const double atr_pct_max,
                          const int atr_pct_lookback,
                          const bool use_ema_sep_gate,
                          const double ema_sep_atr_mult,
                          const bool use_ema_slope_gate,
                          const bool use_breakout_suspend,
                          const double breakout_atr_mult)
     {
      m_symbol = symbol;
      m_timeframe = timeframe;
      m_use_adx_gate = use_adx_gate;
      m_adx_max = adx_max;
      m_adx_period = MathMax(2, adx_period);
      m_use_atr_pct_gate = use_atr_pct_gate;
      m_atr_pct_max = MathMax(1.0, MathMin(99.0, atr_pct_max));
      m_atr_pct_lookback = MathMax(10, atr_pct_lookback);
      m_use_ema_sep_gate = use_ema_sep_gate;
      m_ema_sep_atr_mult = MathMax(0.1, ema_sep_atr_mult);
      m_use_ema_slope_gate = use_ema_slope_gate;
      m_use_breakout_suspend = use_breakout_suspend;
      m_breakout_atr_mult = MathMax(0.1, breakout_atr_mult);
      m_ready = false;

      if(!IsActive())
        {
         m_ready = true;
         return true;
        }

      if(m_use_adx_gate)
        {
         m_handle_adx = iADX(m_symbol, m_timeframe, m_adx_period);
         if(m_handle_adx == INVALID_HANDLE)
           {
            if(m_log != NULL)
               m_log.LogError("Failed to create ADX handle");
            return false;
           }
        }

      return true;
     }

   void              Release()
     {
      if(m_handle_adx != INVALID_HANDLE)
         IndicatorRelease(m_handle_adx);
      m_handle_adx = INVALID_HANDLE;
      m_ready = false;
     }

   bool              Update(const CFemaIndicators &indicators)
     {
      if(!IsActive())
        {
         m_ready = true;
         return true;
        }

      if(m_use_adx_gate)
        {
         double adx_buf[];
         ArraySetAsSeries(adx_buf, true);
         if(CopyBuffer(m_handle_adx, 0, 1, 1, adx_buf) != 1)
            return false;
         m_adx = adx_buf[0];
         if(!MathIsValidNumber(m_adx))
            return false;
        }

      if(!UpdateAtrPercentile(indicators))
         return false;

      m_ready = true;
      return true;
     }

   bool              IsReady() const { return !IsActive() || m_ready; }

   bool              AllowsDirection(const ENUM_FEMA_DIRECTION dir,
                                     const CFemaIndicators &indicators,
                                     string &reason) const
     {
      // Engine calls this only when flat (new basket). Grid add-ons skip regime gates.
      reason = "";
      if(!IsActive() || !m_ready)
         return true;

      if(m_use_adx_gate && m_adx > m_adx_max)
        {
         reason = "ADX too high: " + DoubleToString(m_adx, 1);
         return false;
        }

      if(m_use_atr_pct_gate)
        {
         double atr_now = 0.0;
         if(!indicators.ReadAtrAt(1, atr_now))
            return true;
         if(atr_now > m_atr_pct_threshold)
           {
            reason = "ATR above " + DoubleToString(m_atr_pct_max, 0) +
                      "th pct: " + DoubleToString(atr_now, 5);
            return false;
           }
        }

      const double ema_fast = indicators.EmaFast();
      const double ema_trend = indicators.EmaTrend();
      const double atr = indicators.Atr();

      if(m_use_ema_sep_gate && atr > 0.0)
        {
         if(MathAbs(ema_fast - ema_trend) > m_ema_sep_atr_mult * atr)
           {
            reason = "EMA separation > " + DoubleToString(m_ema_sep_atr_mult, 1) + "x ATR";
            return false;
           }
        }

      if(m_use_ema_slope_gate)
        {
         double ema_bar1 = 0.0;
         double ema_bar2 = 0.0;
         if(!indicators.ReadEmaFastAt(1, ema_bar1) || !indicators.ReadEmaFastAt(2, ema_bar2))
            return true;

         if(dir == FEMA_DIR_BUY && ema_bar1 <= ema_bar2)
           {
            reason = "EMA20 slope not rising for buy";
            return false;
           }
         if(dir == FEMA_DIR_SELL && ema_bar1 >= ema_bar2)
           {
            reason = "EMA20 slope not falling for sell";
            return false;
           }
        }

      if(m_use_breakout_suspend && atr > 0.0)
        {
         const double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
         const double dist = MathAbs(bid - ema_fast);
         if(dist > m_breakout_atr_mult * atr)
           {
            reason = "Breakout: price > " + DoubleToString(m_breakout_atr_mult, 1) +
                      "x ATR from EMA20";
            return false;
           }
        }

      return true;
     }
  };

#endif
