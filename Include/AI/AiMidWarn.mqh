//+------------------------------------------------------------------+
//| AiMidWarn.mqh — ASI-P5 mid-basket steamroller warn (log only)    |
//+------------------------------------------------------------------+
#ifndef FEMA_AIMIDWARN_MQH
#define FEMA_AIMIDWARN_MQH

#include "AiTypes.mqh"
#include "../Utils/Logger.mqh"

#define FEMA_MID_GATE_SCHEMA "fema_mid_gate_v1"
#define FEMA_MID_MAX_FEATURES 32

class CFemaAiMidWarn
  {
private:
   bool              m_enabled;
   bool              m_loaded;
   double            m_threshold;
   double            m_intercept;
   int               m_n_features;
   string            m_feature_names[FEMA_MID_MAX_FEATURES];
   double            m_mean[FEMA_MID_MAX_FEATURES];
   double            m_scale[FEMA_MID_MAX_FEATURES];
   double            m_coef[FEMA_MID_MAX_FEATURES];
   CFemaLogger      *m_log;

   bool              m_has_prev;
   SFemaAiFeatures   m_prev_open;
   ENUM_FEMA_DIRECTION m_prev_dir;
   int               m_prev_consecutive;

   bool              m_basket_active;
   SFemaAiFeatures   m_open_snap;
   double            m_ema_slope_accel;
   double            m_adx_accel;
   double            m_atr_expansion_rate;
   int               m_consecutive_same_dir;
   double            m_dist_ema_abs;
   double            m_impulse_score;
   int               m_last_warned_depth;

   bool              SplitCols(const string line, string &parts[], const int expect)
     {
      const int n = StringSplit(line, '\t', parts);
      return (n >= expect);
     }

   double            FeatureValue(const string name, const int warn_depth) const
     {
      const SFemaAiFeatures f = m_open_snap;
      if(name == "ema_sep_atr") return f.ema_sep_atr;
      if(name == "ema_slope") return f.ema_slope;
      if(name == "atr") return f.atr;
      if(name == "adx") return f.adx;
      if(name == "dist_ema_trend_atr") return f.dist_ema_trend_atr;
      if(name == "spread_points") return (double)f.spread_points;
      if(name == "hour") return (double)f.hour;
      if(name == "dow") return (double)f.dow;
      if(name == "roll_wr") return f.roll_wr;
      if(name == "roll_pf") return MathMin(f.roll_pf, 5.0);
      if(name == "roll_n") return (double)f.roll_n;
      if(name == "ema_slope_accel") return m_ema_slope_accel;
      if(name == "adx_accel") return m_adx_accel;
      if(name == "atr_expansion_rate") return m_atr_expansion_rate;
      if(name == "consecutive_same_dir") return (double)m_consecutive_same_dir;
      if(name == "dist_ema_abs") return m_dist_ema_abs;
      if(name == "impulse_score") return m_impulse_score;
      if(name == "warn_depth") return (double)warn_depth;
      if(name == "is_sell") return (f.direction == FEMA_DIR_SELL ? 1.0 : 0.0);
      return 0.0;
     }

   void              FreezeOpenDerived(const SFemaAiFeatures &f)
     {
      m_ema_slope_accel = 0.0;
      m_adx_accel = 0.0;
      m_atr_expansion_rate = 0.0;
      m_consecutive_same_dir = 1;
      if(m_has_prev)
        {
         m_ema_slope_accel = f.ema_slope - m_prev_open.ema_slope;
         m_adx_accel = f.adx - m_prev_open.adx;
         const double prev_atr = m_prev_open.atr;
         if(MathAbs(prev_atr) > 1e-12)
            m_atr_expansion_rate = (f.atr - prev_atr) / prev_atr;
         if(m_prev_dir == f.direction && f.direction != FEMA_DIR_NONE)
            m_consecutive_same_dir = m_prev_consecutive + 1;
        }
      m_dist_ema_abs = MathAbs(f.dist_ema_trend_atr);
      m_impulse_score =
         MathAbs(m_ema_slope_accel) * 10000.0
         + MathMax(0.0, m_adx_accel) * 2.0
         + MathMax(0.0, m_atr_expansion_rate) * 10.0
         + (double)m_consecutive_same_dir * 0.5
         + m_dist_ema_abs * 0.25;
     }

public:
                     CFemaAiMidWarn() :
                     m_enabled(false),
                     m_loaded(false),
                     m_threshold(1.0),
                     m_intercept(0.0),
                     m_n_features(0),
                     m_log(NULL),
                     m_has_prev(false),
                     m_prev_dir(FEMA_DIR_NONE),
                     m_prev_consecutive(1),
                     m_basket_active(false),
                     m_ema_slope_accel(0.0),
                     m_adx_accel(0.0),
                     m_atr_expansion_rate(0.0),
                     m_consecutive_same_dir(1),
                     m_dist_ema_abs(0.0),
                     m_impulse_score(0.0),
                     m_last_warned_depth(0)
     {
      FemaAiFeaturesReset(m_prev_open);
      FemaAiFeaturesReset(m_open_snap);
      ArrayInitialize(m_mean, 0.0);
      ArrayInitialize(m_scale, 1.0);
      ArrayInitialize(m_coef, 0.0);
     }

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }
   bool              Loaded() const { return m_loaded; }
   double            Threshold() const { return m_threshold; }

   bool              Init(const bool enabled, const string rel_path)
     {
      m_enabled = enabled;
      m_loaded = false;
      if(!m_enabled)
         return true;

      string path = rel_path;
      if(path == "")
         path = "FEMA_AI\\mid_gate_v1.txt";

      int h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON);
      if(h == INVALID_HANDLE)
         h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI);
      if(h == INVALID_HANDLE)
        {
         if(m_log != NULL)
            m_log.LogWarn("Mid-warn gate file missing: " + path + " — mid warn disabled");
         m_enabled = false;
         return false;
        }

      string parts[];
      string header = FileReadString(h);
      if(header != FEMA_MID_GATE_SCHEMA)
        {
         FileClose(h);
         if(m_log != NULL)
            m_log.LogWarn("Mid-warn schema mismatch: " + header);
         m_enabled = false;
         return false;
        }

      while(!FileIsEnding(h))
        {
         const string line = FileReadString(h);
         if(line == "" || StringFind(line, "feature\t") == 0)
            continue;
         if(!SplitCols(line, parts, 2))
            continue;
         if(parts[0] == "threshold")
            m_threshold = StringToDouble(parts[1]);
         else if(parts[0] == "intercept")
            m_intercept = StringToDouble(parts[1]);
         else if(parts[0] == "policy" || parts[0] == "exported_at")
            continue;
         else if(m_n_features < FEMA_MID_MAX_FEATURES && ArraySize(parts) >= 4)
           {
            m_feature_names[m_n_features] = parts[0];
            m_mean[m_n_features] = StringToDouble(parts[1]);
            m_scale[m_n_features] = StringToDouble(parts[2]);
            m_coef[m_n_features] = StringToDouble(parts[3]);
            m_n_features++;
           }
        }
      FileClose(h);

      if(m_n_features <= 0)
        {
         if(m_log != NULL)
            m_log.LogWarn("Mid-warn: no features loaded");
         m_enabled = false;
         return false;
        }

      m_loaded = true;
      if(m_log != NULL)
         m_log.LogInfo("Mid-warn loaded n=" + IntegerToString(m_n_features) +
                       " thr=" + DoubleToString(m_threshold, 4) +
                       " policy=warn_only file=" + path);
      return true;
     }

   void              OnBasketOpened(const SFemaAiFeatures &open_features)
     {
      if(!m_enabled || !m_loaded)
         return;
      m_open_snap = open_features;
      FreezeOpenDerived(open_features);
      m_basket_active = true;
      m_last_warned_depth = 0;
     }

   void              OnBasketClosed(const SFemaAiFeatures &open_features,
                                    const ENUM_FEMA_DIRECTION dir)
     {
      m_prev_open = open_features;
      m_prev_dir = dir;
      m_prev_consecutive = m_consecutive_same_dir;
      m_has_prev = true;
      m_basket_active = false;
      m_last_warned_depth = 0;
     }

   bool              ScoreProba(const int warn_depth, double &proba)
     {
      proba = 0.0;
      if(!m_enabled || !m_loaded || !m_basket_active)
         return false;
      if(warn_depth < 2)
         return false;

      double logit = m_intercept;
      for(int i = 0; i < m_n_features; i++)
        {
         double x = FeatureValue(m_feature_names[i], warn_depth);
         if(MathAbs(m_scale[i]) > 1e-12)
            x = (x - m_mean[i]) / m_scale[i];
         if(x > 6.0) x = 6.0;
         if(x < -6.0) x = -6.0;
         logit += m_coef[i] * x;
        }

      if(logit >= 0.0)
         proba = 1.0 / (1.0 + MathExp(-logit));
      else
        {
         const double e = MathExp(logit);
         proba = e / (1.0 + e);
        }
      return true;
     }

   // Returns true once per depth when P >= threshold. Never closes / stops adds.
   bool              ShouldWarn(const int warn_depth, double &proba)
     {
      proba = 0.0;
      if(warn_depth < 2 || warn_depth <= m_last_warned_depth)
         return false;
      if(!ScoreProba(warn_depth, proba))
         return false;
      if(proba < m_threshold - 1e-9)
         return false;
      m_last_warned_depth = warn_depth;
      return true;
     }
  };

#endif
