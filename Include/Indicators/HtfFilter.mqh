//+------------------------------------------------------------------+
//| HtfFilter.mqh — higher-timeframe EMA bias (Phase 2B)             |
//+------------------------------------------------------------------+
#ifndef FEMA_HTFFILTER_MQH
#define FEMA_HTFFILTER_MQH

#include "../Core/Types.mqh"
#include "../Utils/Logger.mqh"

class CFemaHtfFilter
  {
private:
   string            m_symbol;
   bool              m_enabled;
   ENUM_TIMEFRAMES   m_timeframe;
   int               m_ema_period;
   bool              m_require_slope;
   int               m_handle_ema;
   double            m_close;
   double            m_ema;
   double            m_ema_prev;
   bool              m_ready;
   CFemaLogger      *m_log;

   bool              ReadBar(const int shift, double &ema, double &close) const
     {
      if(m_handle_ema == INVALID_HANDLE)
         return false;

      double ema_buf[];
      double close_buf[];
      ArraySetAsSeries(ema_buf, true);
      ArraySetAsSeries(close_buf, true);

      if(CopyBuffer(m_handle_ema, 0, shift, 1, ema_buf) != 1)
         return false;
      if(CopyClose(m_symbol, m_timeframe, shift, 1, close_buf) != 1)
         return false;

      ema = ema_buf[0];
      close = close_buf[0];
      return MathIsValidNumber(ema) && MathIsValidNumber(close);
     }

public:
                     CFemaHtfFilter() :
                     m_symbol(""),
                     m_enabled(false),
                     m_timeframe(PERIOD_H1),
                     m_ema_period(200),
                     m_require_slope(false),
                     m_handle_ema(INVALID_HANDLE),
                     m_close(0.0),
                     m_ema(0.0),
                     m_ema_prev(0.0),
                     m_ready(false),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Init(const string symbol,
                          const bool enabled,
                          const ENUM_TIMEFRAMES timeframe,
                          const int ema_period,
                          const bool require_slope)
     {
      m_symbol = symbol;
      m_enabled = enabled;
      m_timeframe = timeframe;
      m_ema_period = MathMax(2, ema_period);
      m_require_slope = require_slope;
      m_ready = false;

      if(!m_enabled)
         return true;

      m_handle_ema = iMA(m_symbol, m_timeframe, m_ema_period, 0, MODE_EMA, PRICE_CLOSE);
      if(m_handle_ema == INVALID_HANDLE)
        {
         if(m_log != NULL)
            m_log.LogError("Failed to create HTF EMA handle");
         return false;
        }

      return Update();
     }

   void              Release()
     {
      if(m_handle_ema != INVALID_HANDLE)
         IndicatorRelease(m_handle_ema);
      m_handle_ema = INVALID_HANDLE;
      m_ready = false;
     }

   bool              Update()
     {
      if(!m_enabled)
        {
         m_ready = true;
         return true;
        }

      double ema_bar1 = 0.0;
      double close_bar1 = 0.0;
      double ema_bar2 = 0.0;
      double close_bar2 = 0.0;

      if(!ReadBar(1, ema_bar1, close_bar1))
         return false;
      if(m_require_slope && !ReadBar(2, ema_bar2, close_bar2))
         return false;

      m_ema = ema_bar1;
      m_close = close_bar1;
      m_ema_prev = ema_bar2;
      m_ready = true;
      return true;
     }

   bool              IsEnabled() const { return m_enabled; }
   bool              IsReady() const { return !m_enabled || m_ready; }

   bool              Allows(const ENUM_FEMA_DIRECTION dir) const
     {
      if(!m_enabled || !m_ready)
         return true;

      if(dir == FEMA_DIR_BUY)
        {
         if(m_close <= m_ema)
            return false;
         if(m_require_slope && m_ema <= m_ema_prev)
            return false;
         return true;
        }

      if(dir == FEMA_DIR_SELL)
        {
         if(m_close >= m_ema)
            return false;
         if(m_require_slope && m_ema >= m_ema_prev)
            return false;
         return true;
        }

      return false;
     }
  };

#endif
