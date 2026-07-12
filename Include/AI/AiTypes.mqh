//+------------------------------------------------------------------+
//| AiTypes.mqh — AI feature / event structures (schema-versioned)   |
//+------------------------------------------------------------------+
#ifndef FEMA_AITYPES_MQH
#define FEMA_AITYPES_MQH

#include "../Core/Types.mqh"

#define FEMA_AI_BASKETS_SCHEMA  "fema_baskets_v2"
#define FEMA_AI_EVENTS_SCHEMA   "fema_events_v2"

enum ENUM_FEMA_AI_EVENT
  {
   FEMA_AI_CANDIDATE   = 0,
   FEMA_AI_SKIP        = 1,
   FEMA_AI_FILL        = 2,
   FEMA_AI_ADD         = 3,
   FEMA_AI_BASKET_OPEN = 4,
   FEMA_AI_BASKET_CLOSE= 5,
   FEMA_AI_ORDER_FAIL  = 6,
   FEMA_AI_LIFECYCLE   = 7
  };

struct SFemaAiFeatures
  {
   datetime             time;
   ulong                basket_id;
   ENUM_FEMA_DIRECTION  direction;
   int                  level_index;
   double               level_price;
   double               trigger_price;
   double               ema_fast;
   double               ema_trend;
   double               ema_sep;
   double               ema_sep_atr;
   double               ema_slope;
   double               atr;
   double               adx;
   double               grid_center;
   double               dist_ema_trend_atr;
   int                  spread_points;
   int                  hour;
   int                  dow;
   int                  pos_count;
   bool                 is_new_basket;
   double               roll_wr;
   double               roll_pf;
   int                  roll_n;
  };

struct SFemaAiBasketTrack
  {
   bool                 active;
   ulong                basket_id;
   datetime             open_time;
   ENUM_FEMA_DIRECTION  direction;
   int                  open_level;
   int                  max_depth;
   double               mae;
   double               mfe;
   SFemaAiFeatures      open_features;
  };

struct SFemaAiFingerprint
  {
   string               ea_build;
   string               preset_id;
   bool                 adx_gate;
   double               bsl;
   ulong                magic;
  };

string FemaAiEventToString(const ENUM_FEMA_AI_EVENT ev)
  {
   switch(ev)
     {
      case FEMA_AI_CANDIDATE:    return "CANDIDATE";
      case FEMA_AI_SKIP:         return "SKIP";
      case FEMA_AI_FILL:         return "FILL";
      case FEMA_AI_ADD:          return "ADD";
      case FEMA_AI_BASKET_OPEN:  return "BASKET_OPEN";
      case FEMA_AI_BASKET_CLOSE: return "BASKET_CLOSE";
      case FEMA_AI_ORDER_FAIL:   return "ORDER_FAIL";
      case FEMA_AI_LIFECYCLE:    return "LIFECYCLE";
     }
   return "UNKNOWN";
  }

string FemaAiRejectClass(const int retcode, const bool transient)
  {
   if(retcode == 0)
      return "ok";
   if(transient)
      return "transient";
   if(retcode == TRADE_RETCODE_NO_MONEY)
      return "no_money";
   if(retcode == TRADE_RETCODE_REJECT ||
      retcode == TRADE_RETCODE_INVALID ||
      retcode == TRADE_RETCODE_INVALID_VOLUME ||
      retcode == TRADE_RETCODE_INVALID_PRICE ||
      retcode == TRADE_RETCODE_INVALID_STOPS ||
      retcode == TRADE_RETCODE_TRADE_DISABLED)
      return "reject";
   return "other";
  }

void FemaAiFeaturesReset(SFemaAiFeatures &f)
  {
   f.time = 0;
   f.basket_id = 0;
   f.direction = FEMA_DIR_NONE;
   f.level_index = 0;
   f.level_price = 0.0;
   f.trigger_price = 0.0;
   f.ema_fast = 0.0;
   f.ema_trend = 0.0;
   f.ema_sep = 0.0;
   f.ema_sep_atr = 0.0;
   f.ema_slope = 0.0;
   f.atr = 0.0;
   f.adx = 0.0;
   f.grid_center = 0.0;
   f.dist_ema_trend_atr = 0.0;
   f.spread_points = 0;
   f.hour = 0;
   f.dow = 0;
   f.pos_count = 0;
   f.is_new_basket = false;
   f.roll_wr = 0.0;
   f.roll_pf = 0.0;
   f.roll_n = 0;
  }

#endif
