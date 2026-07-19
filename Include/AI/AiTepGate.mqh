//+------------------------------------------------------------------+
//| AiTepGate.mqh — ASI-P4 offline TEP guardrail (skip new basket)   |
//+------------------------------------------------------------------+
#ifndef FEMA_AITEPGATE_MQH
#define FEMA_AITEPGATE_MQH

#include "AiTypes.mqh"
#include "../Utils/Logger.mqh"

#define FEMA_TEP_GATE_SCHEMA "fema_tep_gate_v1"
#define FEMA_TEP_MAX_FEATURES 32

class CFemaAiTepGate
  {
private:
   bool              m_enabled;
   bool              m_loaded;
   double            m_threshold;
   double            m_intercept;
   int               m_n_features;
   string            m_feature_names[FEMA_TEP_MAX_FEATURES];
   double            m_mean[FEMA_TEP_MAX_FEATURES];
   double            m_scale[FEMA_TEP_MAX_FEATURES];
   double            m_coef[FEMA_TEP_MAX_FEATURES];
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

   double            FeatureValue(const string name, const SFemaAiFeatures &f,
                                  const double ema_slope_accel,
                                  const double adx_accel,
                                  const double atr_expansion_rate,
                                  const int consecutive_same_dir,
                                  const double dist_ema_abs,
                                  const double impulse_score,
                                  const double adx_x_atr_expand,
                                  const double slope_x_consec,
                                  const double impulse_x_dist) const
     {
      if(name == "ema_sep_atr") return f.ema_sep_atr;
      if(name == "ema_slope") return f.ema_slope;
      if(name == "atr") return f.atr;
      if(name == "adx") return f.adx;
      if(name == "dist_ema_trend_atr") return f.dist_ema_trend_atr;
      if(name == "spread_points") return (double)f.spread_points;
      if(name == "hour") return (double)f.hour;
      if(name == "dow") return (double)f.dow;
      if(name == "roll_wr") return f.roll_wr;
      // Cap sentinel PF=99 (no losses yet) — otherwise z-score explodes and P≈1 forever
      if(name == "roll_pf") return MathMin(f.roll_pf, 5.0);
      if(name == "roll_n") return (double)f.roll_n;
      if(name == "ema_slope_accel") return ema_slope_accel;
      if(name == "adx_accel") return adx_accel;
      if(name == "atr_expansion_rate") return atr_expansion_rate;
      if(name == "consecutive_same_dir") return (double)consecutive_same_dir;
      if(name == "dist_ema_abs") return dist_ema_abs;
      if(name == "impulse_score") return impulse_score;
      if(name == "adx_x_atr_expand") return adx_x_atr_expand;
      if(name == "slope_x_consec") return slope_x_consec;
      if(name == "impulse_x_dist") return impulse_x_dist;
      if(name == "is_sell") return (f.direction == FEMA_DIR_SELL ? 1.0 : 0.0);
      return 0.0;
     }

public:
                     CFemaAiTepGate() :
                     m_enabled(false),
                     m_loaded(false),
                     m_threshold(1.0),
                     m_intercept(0.0),
                     m_n_features(0),
                     m_log(NULL),
                     m_has_prev(false),
                     m_prev_dir(FEMA_DIR_NONE),
                     m_prev_consecutive(1),
                     m_last_consecutive(1)
     {
      FemaAiFeaturesReset(m_prev_open);
      ArrayInitialize(m_mean, 0.0);
      ArrayInitialize(m_scale, 1.0);
      ArrayInitialize(m_coef, 0.0);
     }

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   bool              Loaded() const { return m_loaded; }
   double            Threshold() const { return m_threshold; }
   int               LastConsecutive() const { return m_last_consecutive; }

   bool              Init(const bool enabled, const string rel_path)
     {
      m_enabled = enabled;
      m_loaded = false;
      if(!m_enabled)
         return true;

      string path = rel_path;
      if(path == "")
         path = "FEMA_AI\\tep_gate_v1.txt";

      int h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON);
      if(h == INVALID_HANDLE)
         h = FileOpen(path, FILE_READ|FILE_TXT|FILE_ANSI);
      if(h == INVALID_HANDLE)
        {
         if(m_log != NULL)
            m_log.LogWarn("TEP gate file missing: " + path + " — gate disabled");
         m_enabled = false;
         return false;
        }

      string parts[];
      string header = FileReadString(h);
      if(header != FEMA_TEP_GATE_SCHEMA)
        {
         FileClose(h);
         if(m_log != NULL)
            m_log.LogWarn("TEP gate schema mismatch: " + header);
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
         else if(parts[0] == "feature")
            continue;
         else if(m_n_features < FEMA_TEP_MAX_FEATURES && ArraySize(parts) >= 4)
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
            m_log.LogWarn("TEP gate: no features loaded");
         m_enabled = false;
         return false;
        }

      m_loaded = true;
      if(m_log != NULL)
         m_log.LogInfo("TEP gate loaded n=" + IntegerToString(m_n_features) +
                       " thr=" + DoubleToString(m_threshold, 4) +
                       " file=" + path);
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

   bool              ScoreProba(const SFemaAiFeatures &f, double &proba)
     {
      proba = 0.0;
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
      const double adx_x_atr_expand = MathMax(0.0, adx_accel) * MathMax(0.0, atr_expansion_rate);
      const double slope_x_consec = MathAbs(ema_slope_accel) * 10000.0 * (double)consecutive_same_dir;
      const double impulse_x_dist = impulse_score * dist_ema_abs;

      double logit = m_intercept;
      for(int i = 0; i < m_n_features; i++)
        {
         double x = FeatureValue(m_feature_names[i], f,
                                   ema_slope_accel, adx_accel, atr_expansion_rate,
                                   consecutive_same_dir, dist_ema_abs, impulse_score,
                                   adx_x_atr_expand, slope_x_consec, impulse_x_dist);
         if(MathAbs(m_scale[i]) > 1e-12)
            x = (x - m_mean[i]) / m_scale[i];
         // Defensive clip — prevents one wild feature (e.g. roll_pf=99) locking P≈1
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

   bool              ShouldSkip(const SFemaAiFeatures &f, double &proba)
     {
      if(!ScoreProba(f, proba))
         return false;
      return (proba >= m_threshold - 1e-9);
     }
  };

#endif
