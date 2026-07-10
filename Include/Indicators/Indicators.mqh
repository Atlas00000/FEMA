//+------------------------------------------------------------------+
//| Indicators.mqh — EMA fast/trend and ATR                          |
//+------------------------------------------------------------------+
#ifndef FEMA_INDICATORS_MQH
#define FEMA_INDICATORS_MQH

#include "../Core/Types.mqh"
#include "../Utils/Logger.mqh"

class CFemaIndicators
  {
private:
   string            m_symbol;
   ENUM_TIMEFRAMES   m_timeframe;
   int               m_ema_fast_period;
   int               m_ema_trend_period;
   int               m_atr_period;
   int               m_handle_ema_fast;
   int               m_handle_ema_trend;
   int               m_handle_atr;
   int               m_handle_rsi;
   int               m_rsi_period;
   bool              m_use_rsi;
   double            m_rsi_buy_max;
   double            m_rsi_sell_min;
   double            m_ema_fast;
   double            m_ema_trend;
   double            m_atr;
   ENUM_FEMA_TREND   m_trend;
   CFemaLogger      *m_log;

   bool              ReadValue(const int handle, const int shift, double &value) const
     {
      double buffer[];
      ArraySetAsSeries(buffer, true);
      if(CopyBuffer(handle, 0, shift, 1, buffer) != 1)
         return false;
      value = buffer[0];
      return MathIsValidNumber(value);
     }

   bool              ReadValue(const int handle, double &value) const
     {
      return ReadValue(handle, 0, value);
     }

   void              UpdateTrend()
     {
      if(m_ema_fast > m_ema_trend)
         m_trend = FEMA_TREND_UP;
      else if(m_ema_fast < m_ema_trend)
         m_trend = FEMA_TREND_DOWN;
      else
         m_trend = FEMA_TREND_NONE;
     }

public:
                     CFemaIndicators() :
                     m_symbol(""),
                     m_timeframe(PERIOD_CURRENT),
                     m_ema_fast_period(20),
                     m_ema_trend_period(100),
                     m_atr_period(14),
                     m_handle_ema_fast(INVALID_HANDLE),
                     m_handle_ema_trend(INVALID_HANDLE),
                     m_handle_atr(INVALID_HANDLE),
                     m_handle_rsi(INVALID_HANDLE),
                     m_rsi_period(14),
                     m_use_rsi(false),
                     m_rsi_buy_max(70.0),
                     m_rsi_sell_min(30.0),
                     m_ema_fast(0.0),
                     m_ema_trend(0.0),
                     m_atr(0.0),
                     m_trend(FEMA_TREND_NONE),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Init(const string symbol,
                          const ENUM_TIMEFRAMES timeframe,
                          const int ema_fast_period,
                          const int ema_trend_period,
                          const int atr_period,
                          const bool use_rsi = false,
                          const int rsi_period = 14,
                          const double rsi_buy_max = 70.0,
                          const double rsi_sell_min = 30.0)
     {
      m_symbol = symbol;
      m_timeframe = timeframe;
      m_ema_fast_period = ema_fast_period;
      m_ema_trend_period = ema_trend_period;
      m_atr_period = atr_period;
      m_use_rsi = use_rsi;
      m_rsi_period = MathMax(2, rsi_period);
      m_rsi_buy_max = rsi_buy_max;
      m_rsi_sell_min = rsi_sell_min;

      m_handle_ema_fast = iMA(m_symbol, m_timeframe, m_ema_fast_period, 0, MODE_EMA, PRICE_CLOSE);
      m_handle_ema_trend = iMA(m_symbol, m_timeframe, m_ema_trend_period, 0, MODE_EMA, PRICE_CLOSE);
      m_handle_atr = iATR(m_symbol, m_timeframe, m_atr_period);
      m_handle_rsi = INVALID_HANDLE;
      if(m_use_rsi)
        {
         m_handle_rsi = iRSI(m_symbol, m_timeframe, m_rsi_period, PRICE_CLOSE);
         if(m_handle_rsi == INVALID_HANDLE)
           {
            if(m_log != NULL)
               m_log.LogError("Failed to create RSI handle");
            return false;
           }
        }

      if(m_handle_ema_fast == INVALID_HANDLE ||
         m_handle_ema_trend == INVALID_HANDLE ||
         m_handle_atr == INVALID_HANDLE)
        {
         if(m_log != NULL)
            m_log.LogError("Failed to create indicator handles");
         return false;
        }
      return Update();
     }

   void              Release()
     {
      if(m_handle_ema_fast != INVALID_HANDLE)
         IndicatorRelease(m_handle_ema_fast);
      if(m_handle_ema_trend != INVALID_HANDLE)
         IndicatorRelease(m_handle_ema_trend);
      if(m_handle_atr != INVALID_HANDLE)
         IndicatorRelease(m_handle_atr);
      if(m_handle_rsi != INVALID_HANDLE)
         IndicatorRelease(m_handle_rsi);
      m_handle_ema_fast = INVALID_HANDLE;
      m_handle_ema_trend = INVALID_HANDLE;
      m_handle_atr = INVALID_HANDLE;
      m_handle_rsi = INVALID_HANDLE;
     }

   bool              Update()
     {
      if(!ReadValue(m_handle_ema_fast, m_ema_fast))
         return false;
      if(!ReadValue(m_handle_ema_trend, m_ema_trend))
         return false;
      if(!ReadValue(m_handle_atr, m_atr))
         return false;
      if(m_atr <= 0.0)
         return false;
      UpdateTrend();
      return true;
     }

   double            EmaFast() const { return m_ema_fast; }
   double            EmaTrend() const { return m_ema_trend; }
   double            Atr() const { return m_atr; }
   ENUM_FEMA_TREND   Trend() const { return m_trend; }

   bool              RsiAllowsDirection(const ENUM_FEMA_DIRECTION dir) const
     {
      if(!m_use_rsi || m_handle_rsi == INVALID_HANDLE)
         return true;

      double rsi = 0.0;
      if(!ReadValue(m_handle_rsi, rsi))
         return true;

      if(dir == FEMA_DIR_BUY && rsi > m_rsi_buy_max)
         return false;
      if(dir == FEMA_DIR_SELL && rsi < m_rsi_sell_min)
         return false;
      return true;
     }

   bool              ReadEmaFastAt(const int shift, double &value) const
     {
      return ReadValue(m_handle_ema_fast, shift, value);
     }

   bool              ReadAtrAt(const int shift, double &value) const
     {
      return ReadValue(m_handle_atr, shift, value);
     }

   int               AtrHandle() const { return m_handle_atr; }
  };

#endif
