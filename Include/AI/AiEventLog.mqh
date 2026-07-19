//+------------------------------------------------------------------+
//| AiEventLog.mqh — schema-versioned CSV event / basket logger      |
//+------------------------------------------------------------------+
#ifndef FEMA_AIEVENTLOG_MQH
#define FEMA_AIEVENTLOG_MQH

#include "AiTypes.mqh"
#include "../Indicators/Indicators.mqh"
#include "../Indicators/RegimeFilter.mqh"
#include "../Grid/GridManager.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

#define FEMA_AI_ROLL_WINDOW 50

class CFemaAiEventLog
  {
private:
   bool              m_enabled;
   string            m_symbol;
   ulong             m_magic;
   string            m_run_id;
   string            m_ea_build;
   string            m_preset_id;
   string            m_fingerprint;
   int               m_events_handle;
   int               m_baskets_handle;
   int               m_events_handle_local;
   int               m_baskets_handle_local;
   CFemaLogger      *m_log;
   SFemaAiBasketTrack m_track;
   double            m_roll_profits[FEMA_AI_ROLL_WINDOW];
   int               m_roll_count;
   int               m_roll_idx;

   string            Tag() const
     {
      return m_symbol + "_" + IntegerToString((long)m_magic);
     }

   string            Esc(const string s) const
     {
      string out = s;
      StringReplace(out, ",", ";");
      StringReplace(out, "\n", " ");
      return out;
     }

   void              WriteLine(const int h1, const int h2, const string line) const
     {
      if(h1 != INVALID_HANDLE)
        {
         FileWriteString(h1, line);
         FileFlush(h1);
        }
      if(h2 != INVALID_HANDLE)
        {
         FileWriteString(h2, line);
         FileFlush(h2);
        }
     }

   int               OpenCsv(const string path, const int common_flag) const
     {
      return FileOpen(path, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_REWRITE|common_flag);
     }

   void              WriteMetaBlock(const int h1, const int h2, const string schema) const
     {
      WriteLine(h1, h2, "# FEMA_META schema=" + schema + "\r\n");
      WriteLine(h1, h2, "# FEMA_META run_id=" + Esc(m_run_id) + "\r\n");
      WriteLine(h1, h2, "# FEMA_META magic=" + IntegerToString((long)m_magic) + "\r\n");
      WriteLine(h1, h2, "# FEMA_META ea_build=" + Esc(m_ea_build) + "\r\n");
      WriteLine(h1, h2, "# FEMA_META fingerprint=" + Esc(m_fingerprint) + "\r\n");
      WriteLine(h1, h2, "# FEMA_META created=" +
                TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\r\n");
     }

   void              WriteRunMetaFile() const
     {
      const string path = "FEMA_AI\\" + Tag() + "_run.meta.txt";
      const string body =
         "schema_baskets=" + FEMA_AI_BASKETS_SCHEMA + "\r\n" +
         "schema_events=" + FEMA_AI_EVENTS_SCHEMA + "\r\n" +
         "run_id=" + m_run_id + "\r\n" +
         "magic=" + IntegerToString((long)m_magic) + "\r\n" +
         "ea_build=" + m_ea_build + "\r\n" +
         "preset_id=" + m_preset_id + "\r\n" +
         "fingerprint=" + m_fingerprint + "\r\n" +
         "symbol=" + m_symbol + "\r\n" +
         "created=" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\r\n";

      int h = FileOpen(path, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_REWRITE|FILE_COMMON);
      if(h != INVALID_HANDLE)
        {
         FileWriteString(h, body);
         FileClose(h);
        }
      h = FileOpen(path, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_REWRITE);
      if(h != INVALID_HANDLE)
        {
         FileWriteString(h, body);
         FileClose(h);
        }
     }

   void              WriteEventsHeader()
     {
      WriteMetaBlock(m_events_handle, m_events_handle_local, FEMA_AI_EVENTS_SCHEMA);
      const string hdr =
         "event_time,event,basket_id,symbol,direction,level_index,"
         "level_price,trigger_price,profit,reason,"
         "ema_fast,ema_trend,ema_sep,ema_sep_atr,ema_slope,atr,adx,"
         "grid_center,dist_ema_trend_atr,spread_points,hour,dow,"
         "pos_count,is_new_basket,roll_wr,roll_pf,roll_n,"
         "retcode,reject_class,transient\r\n";
      WriteLine(m_events_handle, m_events_handle_local, hdr);
     }

   void              WriteBasketsHeader()
     {
      WriteMetaBlock(m_baskets_handle, m_baskets_handle_local, FEMA_AI_BASKETS_SCHEMA);
      const string hdr =
         "basket_id,open_time,close_time,symbol,direction,open_level,"
         "max_depth,profit,exit_reason,hit_tp,hit_bsl,mae,mfe,"
         "bars_alive,ema_fast,ema_trend,ema_sep,ema_sep_atr,ema_slope,"
         "atr,adx,grid_center,dist_ema_trend_atr,spread_points,hour,dow,"
         "roll_wr,roll_pf,roll_n\r\n";
      WriteLine(m_baskets_handle, m_baskets_handle_local, hdr);
     }

   void              WriteEventRow(const ENUM_FEMA_AI_EVENT ev,
                                   const SFemaAiFeatures &f,
                                   const double profit,
                                   const string reason,
                                   const int retcode,
                                   const string reject_class,
                                   const bool transient)
     {
      if(!m_enabled)
         return;
      if(m_events_handle == INVALID_HANDLE && m_events_handle_local == INVALID_HANDLE)
         return;
      const string line =
         TimeToString(f.time, TIME_DATE|TIME_SECONDS) + "," +
         FemaAiEventToString(ev) + "," +
         IntegerToString((int)f.basket_id) + "," +
         m_symbol + "," +
         FemaDirectionToString(f.direction) + "," +
         IntegerToString(f.level_index) + "," +
         DoubleToString(f.level_price, _Digits) + "," +
         DoubleToString(f.trigger_price, _Digits) + "," +
         DoubleToString(profit, 2) + "," +
         Esc(reason) + "," +
         DoubleToString(f.ema_fast, _Digits) + "," +
         DoubleToString(f.ema_trend, _Digits) + "," +
         DoubleToString(f.ema_sep, _Digits) + "," +
         DoubleToString(f.ema_sep_atr, 4) + "," +
         DoubleToString(f.ema_slope, _Digits) + "," +
         DoubleToString(f.atr, _Digits) + "," +
         DoubleToString(f.adx, 2) + "," +
         DoubleToString(f.grid_center, _Digits) + "," +
         DoubleToString(f.dist_ema_trend_atr, 4) + "," +
         IntegerToString(f.spread_points) + "," +
         IntegerToString(f.hour) + "," +
         IntegerToString(f.dow) + "," +
         IntegerToString(f.pos_count) + "," +
         (f.is_new_basket ? "1" : "0") + "," +
         DoubleToString(f.roll_wr, 4) + "," +
         DoubleToString(f.roll_pf, 4) + "," +
         IntegerToString(f.roll_n) + "," +
         IntegerToString(retcode) + "," +
         Esc(reject_class) + "," +
         (transient ? "1" : "0") + "\r\n";
      WriteLine(m_events_handle, m_events_handle_local, line);
     }

   void              ComputeRollStats(double &wr, double &pf, int &n) const
     {
      wr = 0.0;
      pf = 0.0;
      n = m_roll_count;
      if(n <= 0)
         return;

      double gross_win = 0.0;
      double gross_loss = 0.0;
      int wins = 0;
      for(int i = 0; i < n; i++)
        {
         const double p = m_roll_profits[i];
         if(p > 0.0)
           {
            wins++;
            gross_win += p;
           }
         else if(p < 0.0)
            gross_loss += -p;
        }
      wr = (double)wins / (double)n;
      if(gross_loss > 0.0)
         pf = gross_win / gross_loss;
      else
         pf = (gross_win > 0.0 ? 5.0 : 0.0);  // was 99 — caps TEP feature scale
      if(pf > 5.0)
         pf = 5.0;
     }

   void              PushRoll(const double profit)
     {
      if(m_roll_count < FEMA_AI_ROLL_WINDOW)
        {
         m_roll_profits[m_roll_count++] = profit;
         m_roll_idx = m_roll_count % FEMA_AI_ROLL_WINDOW;
         return;
        }
      m_roll_profits[m_roll_idx] = profit;
      m_roll_idx = (m_roll_idx + 1) % FEMA_AI_ROLL_WINDOW;
     }

public:
                     CFemaAiEventLog() :
                     m_enabled(false),
                     m_symbol(""),
                     m_magic(0),
                     m_run_id(""),
                     m_ea_build(""),
                     m_preset_id(""),
                     m_fingerprint(""),
                     m_events_handle(INVALID_HANDLE),
                     m_baskets_handle(INVALID_HANDLE),
                     m_events_handle_local(INVALID_HANDLE),
                     m_baskets_handle_local(INVALID_HANDLE),
                     m_log(NULL),
                     m_roll_count(0),
                     m_roll_idx(0)
     {
      m_track.active = false;
      m_track.basket_id = 0;
      m_track.open_time = 0;
      m_track.direction = FEMA_DIR_NONE;
      m_track.open_level = 0;
      m_track.max_depth = 0;
      m_track.mae = 0.0;
      m_track.mfe = 0.0;
      FemaAiFeaturesReset(m_track.open_features);
      ArrayInitialize(m_roll_profits, 0.0);
     }

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }
   bool              Enabled() const { return m_enabled; }
   string            RunId() const { return m_run_id; }

   // INF-EA: edge fingerprint JSON (Inp* that define the lock). Body built by Engine.
   void              WriteRunConfigJson(const string json_body) const
     {
      if(!m_enabled)
         return;
      const string path = "FEMA_AI\\" + Tag() + "_run_config.json";
      int h = FileOpen(path, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_REWRITE|FILE_COMMON);
      if(h != INVALID_HANDLE)
        {
         FileWriteString(h, json_body);
         FileClose(h);
        }
      h = FileOpen(path, FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_REWRITE);
      if(h != INVALID_HANDLE)
        {
         FileWriteString(h, json_body);
         FileClose(h);
        }
     }

   bool              Init(const bool enabled,
                          const string symbol,
                          const ulong magic,
                          const string ea_build,
                          const string preset_id,
                          const bool adx_gate,
                          const double bsl)
     {
      Close();
      m_enabled = enabled;
      m_symbol = symbol;
      m_magic = magic;
      m_ea_build = ea_build;
      m_preset_id = (preset_id == "" ? "PRODUCTION" : preset_id);
      m_fingerprint = "adx_gate=" + (adx_gate ? "on" : "off") +
                      ";bsl=" + DoubleToString(bsl, 0) +
                      ";preset=" + m_preset_id;
      m_run_id = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
      StringReplace(m_run_id, ".", "");
      StringReplace(m_run_id, ":", "");
      StringReplace(m_run_id, " ", "_");
      m_run_id = m_run_id + "_" + Tag();

      m_roll_count = 0;
      m_roll_idx = 0;
      m_track.active = false;
      if(!m_enabled)
         return true;

      FolderCreate("FEMA_AI", FILE_COMMON);
      FolderCreate("FEMA_AI");

      const string tag = Tag();
      const string events_path = "FEMA_AI\\" + tag + "_events.csv";
      const string baskets_path = "FEMA_AI\\" + tag + "_baskets.csv";

      m_events_handle = OpenCsv(events_path, FILE_COMMON);
      m_baskets_handle = OpenCsv(baskets_path, FILE_COMMON);
      m_events_handle_local = OpenCsv(events_path, 0);
      m_baskets_handle_local = OpenCsv(baskets_path, 0);

      const bool any_ok =
         (m_events_handle != INVALID_HANDLE && m_baskets_handle != INVALID_HANDLE) ||
         (m_events_handle_local != INVALID_HANDLE && m_baskets_handle_local != INVALID_HANDLE);

      if(!any_ok)
        {
         if(m_log != NULL)
            m_log.LogError("AI log open failed (common+local)");
         Close();
         m_enabled = false;
         return false;
        }

      WriteEventsHeader();
      WriteBasketsHeader();
      WriteRunMetaFile();
      if(m_log != NULL)
        {
         m_log.LogInfo("AI log " + FEMA_AI_BASKETS_SCHEMA + "/" + FEMA_AI_EVENTS_SCHEMA +
                       " run_id=" + m_run_id +
                       " fp=" + m_fingerprint +
                       " common_ok=" + IntegerToString(m_events_handle != INVALID_HANDLE) +
                       " local_ok=" + IntegerToString(m_events_handle_local != INVALID_HANDLE));
        }
      return true;
     }

   void              Close()
     {
      if(m_events_handle != INVALID_HANDLE)
        {
         FileClose(m_events_handle);
         m_events_handle = INVALID_HANDLE;
        }
      if(m_baskets_handle != INVALID_HANDLE)
        {
         FileClose(m_baskets_handle);
         m_baskets_handle = INVALID_HANDLE;
        }
      if(m_events_handle_local != INVALID_HANDLE)
        {
         FileClose(m_events_handle_local);
         m_events_handle_local = INVALID_HANDLE;
        }
      if(m_baskets_handle_local != INVALID_HANDLE)
        {
         FileClose(m_baskets_handle_local);
         m_baskets_handle_local = INVALID_HANDLE;
        }
     }

   void              BuildFeatures(const SFemaSignal &signal,
                                   const CFemaIndicators &indicators,
                                   const CFemaRegimeFilter &regime,
                                   const CFemaGridManager &grid,
                                   const int pos_count,
                                   const ulong basket_id,
                                   SFemaAiFeatures &f) const
     {
      FemaAiFeaturesReset(f);
      f.time = TimeCurrent();
      f.basket_id = basket_id;
      f.direction = signal.direction;
      f.level_index = signal.level_index;
      f.level_price = signal.level_price;
      f.trigger_price = signal.trigger_price;
      f.ema_fast = indicators.EmaFast();
      f.ema_trend = indicators.EmaTrend();
      f.atr = indicators.Atr();
      f.ema_sep = f.ema_fast - f.ema_trend;
      f.ema_sep_atr = (f.atr > 0.0 ? f.ema_sep / f.atr : 0.0);
      f.adx = regime.Adx();
      f.grid_center = grid.Center();
      f.pos_count = pos_count;
      f.is_new_basket = (pos_count == 0);
      f.spread_points = CFemaHelpers::SpreadPoints(m_symbol);

      MqlDateTime dt;
      TimeToStruct(f.time, dt);
      f.hour = dt.hour;
      f.dow = dt.day_of_week;

      const double bid = SymbolInfoDouble(m_symbol, SYMBOL_BID);
      f.dist_ema_trend_atr = (f.atr > 0.0 ? (bid - f.ema_trend) / f.atr : 0.0);

      double ema1 = 0.0;
      double ema2 = 0.0;
      if(indicators.ReadEmaFastAt(1, ema1) && indicators.ReadEmaFastAt(2, ema2))
         f.ema_slope = ema1 - ema2;

      ComputeRollStats(f.roll_wr, f.roll_pf, f.roll_n);
     }

   void              LogCandidate(const SFemaAiFeatures &f)
     {
      WriteEventRow(FEMA_AI_CANDIDATE, f, 0.0, "", 0, "ok", false);
     }

   void              LogSkip(const SFemaAiFeatures &f, const string reason)
     {
      WriteEventRow(FEMA_AI_SKIP, f, 0.0, reason, 0, "ok", false);
     }

   void              LogFill(const SFemaAiFeatures &f, const bool is_add)
     {
      WriteEventRow(is_add ? FEMA_AI_ADD : FEMA_AI_FILL, f, 0.0, "", 0, "ok", false);
     }

   void              LogOrderFail(const SFemaAiFeatures &f,
                                  const int retcode,
                                  const bool transient,
                                  const string detail)
     {
      const string cls = FemaAiRejectClass(retcode, transient);
      const string reason = "order_fail_" + IntegerToString(retcode) +
                            (detail == "" ? "" : ";" + detail);
      WriteEventRow(FEMA_AI_ORDER_FAIL, f, 0.0, reason, retcode, cls, transient);
      // Back-compat for older parsers that only look at SKIP
      WriteEventRow(FEMA_AI_SKIP, f, 0.0, "order_fail_" + IntegerToString(retcode),
                    retcode, cls, transient);
     }

   void              LogLifecycle(const string code, const string detail)
     {
      SFemaAiFeatures f;
      FemaAiFeaturesReset(f);
      f.time = TimeCurrent();
      f.spread_points = CFemaHelpers::SpreadPoints(m_symbol);
      MqlDateTime dt;
      TimeToStruct(f.time, dt);
      f.hour = dt.hour;
      f.dow = dt.day_of_week;
      WriteEventRow(FEMA_AI_LIFECYCLE, f, 0.0, Esc(code) + (detail == "" ? "" : ";" + Esc(detail)),
                    0, "ok", false);
     }

   void              OnBasketOpened(const ulong basket_id,
                                    const SFemaAiFeatures &f)
     {
      if(!m_enabled)
         return;
      m_track.active = true;
      m_track.basket_id = basket_id;
      m_track.open_time = f.time;
      m_track.direction = f.direction;
      m_track.open_level = f.level_index;
      m_track.max_depth = f.level_index;
      m_track.mae = 0.0;
      m_track.mfe = 0.0;
      m_track.open_features = f;
      m_track.open_features.basket_id = basket_id;
      WriteEventRow(FEMA_AI_BASKET_OPEN, m_track.open_features, 0.0, "", 0, "ok", false);
     }

   void              OnLegFilled(const int level_index)
     {
      if(!m_enabled || !m_track.active)
         return;
      if(level_index > m_track.max_depth)
         m_track.max_depth = level_index;
     }

   void              UpdatePath(const double floating_profit)
     {
      if(!m_enabled || !m_track.active)
         return;
      if(floating_profit < m_track.mae)
         m_track.mae = floating_profit;
      if(floating_profit > m_track.mfe)
         m_track.mfe = floating_profit;
     }

   void              OnBasketClosed(const double profit,
                                    const ENUM_FEMA_EXIT_REASON reason,
                                    const int bars_alive)
     {
      if(!m_enabled || !m_track.active)
         return;

      SFemaAiFeatures f = m_track.open_features;
      f.time = TimeCurrent();
      f.basket_id = m_track.basket_id;
      WriteEventRow(FEMA_AI_BASKET_CLOSE, f, profit, FemaExitReasonToString(reason), 0, "ok", false);

      if(m_baskets_handle != INVALID_HANDLE || m_baskets_handle_local != INVALID_HANDLE)
        {
         const int hit_tp = (reason == FEMA_EXIT_BASKET_TP ? 1 : 0);
         const int hit_bsl = (reason == FEMA_EXIT_BASKET_SL ? 1 : 0);
         const string line =
            IntegerToString((int)m_track.basket_id) + "," +
            TimeToString(m_track.open_time, TIME_DATE|TIME_SECONDS) + "," +
            TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "," +
            m_symbol + "," +
            FemaDirectionToString(m_track.direction) + "," +
            IntegerToString(m_track.open_level) + "," +
            IntegerToString(m_track.max_depth) + "," +
            DoubleToString(profit, 2) + "," +
            FemaExitReasonToString(reason) + "," +
            IntegerToString(hit_tp) + "," +
            IntegerToString(hit_bsl) + "," +
            DoubleToString(m_track.mae, 2) + "," +
            DoubleToString(m_track.mfe, 2) + "," +
            IntegerToString(bars_alive) + "," +
            DoubleToString(m_track.open_features.ema_fast, _Digits) + "," +
            DoubleToString(m_track.open_features.ema_trend, _Digits) + "," +
            DoubleToString(m_track.open_features.ema_sep, _Digits) + "," +
            DoubleToString(m_track.open_features.ema_sep_atr, 4) + "," +
            DoubleToString(m_track.open_features.ema_slope, _Digits) + "," +
            DoubleToString(m_track.open_features.atr, _Digits) + "," +
            DoubleToString(m_track.open_features.adx, 2) + "," +
            DoubleToString(m_track.open_features.grid_center, _Digits) + "," +
            DoubleToString(m_track.open_features.dist_ema_trend_atr, 4) + "," +
            IntegerToString(m_track.open_features.spread_points) + "," +
            IntegerToString(m_track.open_features.hour) + "," +
            IntegerToString(m_track.open_features.dow) + "," +
            DoubleToString(m_track.open_features.roll_wr, 4) + "," +
            DoubleToString(m_track.open_features.roll_pf, 4) + "," +
            IntegerToString(m_track.open_features.roll_n) + "\r\n";
         WriteLine(m_baskets_handle, m_baskets_handle_local, line);
        }

      PushRoll(profit);
      m_track.active = false;
     }

   bool              CopyActiveOpenFeatures(SFemaAiFeatures &out,
                                            ENUM_FEMA_DIRECTION &dir) const
     {
      if(!m_track.active)
         return false;
      out = m_track.open_features;
      dir = m_track.direction;
      return true;
     }

   void              OnBasketAborted()
     {
      m_track.active = false;
     }
  };

#endif
