//+------------------------------------------------------------------+
//| AiTypes.mqh — AI0 feature / event structures (logging only)      |
//+------------------------------------------------------------------+
#ifndef FEMA_AITYPES_MQH
#define FEMA_AITYPES_MQH

#include "../Core/Types.mqh"

enum ENUM_FEMA_AI_EVENT
  {
   FEMA_AI_CANDIDATE   = 0,
   FEMA_AI_SKIP        = 1,
   FEMA_AI_FILL        = 2,
   FEMA_AI_ADD         = 3,
   FEMA_AI_BASKET_OPEN = 4,
   FEMA_AI_BASKET_CLOSE= 5
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
     }
   return "UNKNOWN";
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
