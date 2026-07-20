//+------------------------------------------------------------------+
//| AiRegimeGate.mqh — ASI-P8 regime filter (skip caution/skip)      |
//+------------------------------------------------------------------+
#ifndef FEMA_AIREGIMEGATE_MQH
#define FEMA_AIREGIMEGATE_MQH

#include "AiTypes.mqh"
#include "../Utils/Logger.mqh"

#define FEMA_REGIME_GATE_SCHEMA "fema_regime_gate_v1"
#define FEMA_REGIME_MAX_FILTER  16

class CFemaAiRegimeGate
  {
private:
   bool              m_enabled;
   bool              m_loaded;
   int               m_n_filter;
   string            m_filter[FEMA_REGIME_MAX_FILTER];
   string            m_last_regime;

   double            m_impulse_score_hi;
   double            m_atr_expand_hi;
   double            m_atr_expand_lo;
   double            m_adx_hi;
   double            m_adx_mid;
   double            m_adx_lo;
   double            m_adx_accel_hi;
   double            m_adx_accel_lo;
   double            m_dist_hi;
   double            m_dist_mid;
   double            m_dist_lo;
   double            m_spread_hi;
   double            m_slope_hi;
   double            m_slope_lo;
   double            m_consec_hi;
   double            m_thin_hour_end;

   CFemaLogger      *m_log;
   bool              m_has_prev;
   SFemaAiFeatures   m_prev_open;
   ENUM_FEMA_DIRECTION m_prev_dir;
   int               m_prev_consecutive;
   int               m_last_consecutive;

   bool              SplitCols(const string line, string &parts[], const int expect)
     {
      const int n = StringSplit(line, '\t', parts);
      return (n >= expect);
     }

   bool              IsFiltered(const string regime) const
     {
      for(int i = 0; i < m_n_filter; i++)
        {
         if(m_filter[i] == regime)
            return true;
        }
      return false;
     }

   string            Classify(const SFemaAiFeatures &f,
                              const double atr_expansion_rate,
                              const double adx_accel,
                              const int consecutive_same_dir,
                              const double impulse_score) const
     {
      const double adx = f.adx;
      const double dist = MathAbs(f.dist_ema_trend_atr);
      const double spread = (double)f.spread_points;
      const double hour = (double)f.hour;
      const double slope_abs = MathAbs(f.ema_slope);

      if(hour < m_thin_hour_end || spread >= m_spread_hi)
         return "liquidity_vacuum";
      if(impulse_score >= m_impulse_score_hi &&
         (adx_accel >= m_adx_accel_hi || atr_expansion_rate >= m_atr_expand_hi))
         return "impulse";
      if(atr_expansion_rate >= m_atr_expand_hi && adx >= m_adx_mid)
         return "expansion";
      if(adx >= m_adx_hi && adx_accel <= m_adx_accel_lo &&
         (double)consecutive_same_dir >= m_consec_hi)
         return "exhaustion";
      if(dist >= m_dist_hi && adx <= m_adx_mid && adx_accel <= 0.0)
         return "false_breakout";
      if(atr_expansion_rate <= m_atr_expand_lo && adx <= m_adx_mid)
         return "compression";
      if(adx >= m_adx_lo && adx <= m_adx_hi &&
         slope_abs <= m_slope_hi && dist <= m_dist_mid)
         return "grind";
      if(adx >= m_adx_lo && adx <= m_adx_hi &&
         dist >= m_dist_lo && dist <= m_dist_hi &&
         slope_abs >= m_slope_lo)
         return "pullback_trend";
      if(adx < m_adx_lo)
         return "rotation";
      return "pullback_trend";
     }

public:
                     CFemaAiRegimeGate() :
                     m_enabled(false),
                     m_loaded(false),
                     m_n_filter(0),
                     m_last_regime(""),
                     m_impulse_score_hi(22.0),
                     m_atr_expand_hi(0.56),
                     m_atr_expand_lo(-0.37),
                     m_adx_hi(27.0),
                     m_adx_mid(23.7),
                     m_adx_lo(21.0),
                     m_adx_accel_hi(4.0),
                     m_adx_accel_lo(-4.0),
                     m_dist_hi(4.0),
                     m_dist_mid(2.0),
                     m_dist_lo(1.2),
                     m_spread_hi(8.0),
                     m_slope_hi(3e-5),
                     m_slope_lo(1.5e-5),
                     m_consec_hi(4.0),
                     m_thin_hour_end(7.0),
                     m_log(NULL),
                     m_has_prev(false),
                     m_prev_dir(FEMA_DIR_NONE),
                     m_prev_consecutive(1),
                     m_last_consecutive(1)
     {
      FemaAiFeaturesReset(m_prev_open);
     }

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }
   bool              Loaded() const { return m_loaded; }
   string            LastRegime() const { return m_last_regime; }
   int               LastConsecutive() const { return m_last_consecutive; }

   bool              Init(const bool enabled, const string rel_path)
     {
      m_enabled = enabled;
      m_loaded = false;
      m_n_filter = 0;
      if(!m_enabled)
         return true;

      string path = rel_path;
      if(path == "")
         path = "FEMA_AI\\regime_gate_v1.txt";

      int h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON);
      if(h == INVALID_HANDLE)
         h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI);
      if(h == INVALID_HANDLE)
        {
         if(m_log != NULL)
            m_log.LogWarn("Regime gate file missing: " + path + " — gate disabled");
         m_enabled = false;
         return false;
        }

      string parts[];
      string header = FileReadString(h);
      if(header != FEMA_REGIME_GATE_SCHEMA)
        {
         FileClose(h);
         if(m_log != NULL)
            m_log.LogWarn("Regime gate schema mismatch: " + header);
         m_enabled = false;
         return false;
        }

      while(!FileIsEnding(h))
        {
         const string line = FileReadString(h);
         if(line == "" || StringFind(line, "#") == 0)
            continue;
         if(!SplitCols(line, parts, 2))
            continue;

         if(parts[0] == "filter" && m_n_filter < FEMA_REGIME_MAX_FILTER)
           {
            m_filter[m_n_filter++] = parts[1];
           }
         else if(parts[0] == "thr.impulse_score_hi")
            m_impulse_score_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.atr_expand_hi")
            m_atr_expand_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.atr_expand_lo")
            m_atr_expand_lo = StringToDouble(parts[1]);
         else if(parts[0] == "thr.adx_hi")
            m_adx_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.adx_mid")
            m_adx_mid = StringToDouble(parts[1]);
         else if(parts[0] == "thr.adx_lo")
            m_adx_lo = StringToDouble(parts[1]);
         else if(parts[0] == "thr.adx_accel_hi")
            m_adx_accel_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.adx_accel_lo")
            m_adx_accel_lo = StringToDouble(parts[1]);
         else if(parts[0] == "thr.dist_hi")
            m_dist_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.dist_mid")
            m_dist_mid = StringToDouble(parts[1]);
         else if(parts[0] == "thr.dist_lo")
            m_dist_lo = StringToDouble(parts[1]);
         else if(parts[0] == "thr.spread_hi")
            m_spread_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.slope_hi")
            m_slope_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.slope_lo")
            m_slope_lo = StringToDouble(parts[1]);
         else if(parts[0] == "thr.consec_hi")
            m_consec_hi = StringToDouble(parts[1]);
         else if(parts[0] == "thr.thin_hour_end")
            m_thin_hour_end = StringToDouble(parts[1]);
        }
      FileClose(h);

      if(m_n_filter <= 0)
        {
         if(m_log != NULL)
            m_log.LogWarn("Regime gate: no filter regimes — nothing to skip");
         m_enabled = false;
         return false;
        }

      m_loaded = true;
      if(m_log != NULL)
        {
         string flist = "";
         for(int i = 0; i < m_n_filter; i++)
           {
            if(i > 0) flist += ",";
            flist += m_filter[i];
           }
         m_log.LogInfo("Regime gate loaded filters=[" + flist + "] file=" + path);
        }
      return true;
     }

   void              OnBasketClosed(const SFemaAiFeatures &open_features,
                                    const ENUM_FEMA_DIRECTION dir,
                                    const int consec_at_open)
     {
      m_prev_open = open_features;
      m_prev_dir = dir;
      m_prev_consecutive = consec_at_open;
      m_has_prev = true;
     }

   bool              ClassifyOpen(const SFemaAiFeatures &f, string &regime)
     {
      regime = "";
      if(!m_enabled || !m_loaded)
         return false;

      double ema_slope_accel = 0.0;
      double adx_accel = 0.0;
      double atr_expansion_rate = 0.0;
      int consecutive_same_dir = 1;
      if(m_has_prev)
        {
         ema_slope_accel = f.ema_slope - m_prev_open.ema_slope;
         adx_accel = f.adx - m_prev_open.adx;
         const double prev_atr = m_prev_open.atr;
         if(MathAbs(prev_atr) > 1e-12)
            atr_expansion_rate = (f.atr - prev_atr) / prev_atr;
         if(m_prev_dir == f.direction && f.direction != FEMA_DIR_NONE)
            consecutive_same_dir = m_prev_consecutive + 1;
        }
      m_last_consecutive = consecutive_same_dir;

      const double dist_ema_abs = MathAbs(f.dist_ema_trend_atr);
      const double impulse_score =
         MathAbs(ema_slope_accel) * 10000.0
         + MathMax(0.0, adx_accel) * 2.0
         + MathMax(0.0, atr_expansion_rate) * 10.0
         + (double)consecutive_same_dir * 0.5
         + dist_ema_abs * 0.25;

      regime = Classify(f, atr_expansion_rate, adx_accel, consecutive_same_dir, impulse_score);
      m_last_regime = regime;
      return true;
     }

   bool              ShouldSkip(const SFemaAiFeatures &f, string &regime)
     {
      if(!ClassifyOpen(f, regime))
         return false;
      return IsFiltered(regime);
     }
  };

#endif
