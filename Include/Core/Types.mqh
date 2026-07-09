//+------------------------------------------------------------------+
//| Types.mqh — shared enums and structures                          |
//+------------------------------------------------------------------+
#ifndef FEMA_TYPES_MQH
#define FEMA_TYPES_MQH

enum ENUM_FEMA_STATE
  {
   FEMA_STATE_IDLE              = 0,
   FEMA_STATE_READY             = 1,
   FEMA_STATE_IN_TRADE          = 2,
   FEMA_STATE_BASKET_MANAGEMENT = 3,
   FEMA_STATE_COOLDOWN          = 4,
   FEMA_STATE_SUSPENDED         = 5
  };

enum ENUM_FEMA_DIRECTION
  {
   FEMA_DIR_NONE = 0,
   FEMA_DIR_BUY  = 1,
   FEMA_DIR_SELL = 2
  };

enum ENUM_FEMA_TREND
  {
   FEMA_TREND_NONE = 0,
   FEMA_TREND_UP   = 1,
   FEMA_TREND_DOWN = 2
  };

enum ENUM_FEMA_LOG_MODE
  {
   FEMA_LOG_DETAILED = 0,
   FEMA_LOG_MINIMAL  = 1
  };

enum ENUM_FEMA_TRADE_PERMISSION
  {
   FEMA_PERM_BOTH      = 0,
   FEMA_PERM_BUY_ONLY  = 1,
   FEMA_PERM_SELL_ONLY = 2
  };

enum ENUM_FEMA_EXIT_REASON
  {
   FEMA_EXIT_NONE        = 0,
   FEMA_EXIT_BASKET_TP   = 1,
   FEMA_EXIT_BASKET_SL   = 2,
   FEMA_EXIT_BASKET_TIME = 3
  };

struct SFemaGridLevel
  {
   int                  index;
   ENUM_FEMA_DIRECTION  direction;
   double               price;
   bool                 fired;
  };

struct SFemaSignal
  {
   bool                 valid;
   ENUM_FEMA_DIRECTION  direction;
   int                  level_index;
   double               level_price;
   double               trigger_price;
  };

string FemaStateToString(const ENUM_FEMA_STATE state)
  {
   switch(state)
     {
      case FEMA_STATE_IDLE:              return "IDLE";
      case FEMA_STATE_READY:             return "READY";
      case FEMA_STATE_IN_TRADE:          return "IN_TRADE";
      case FEMA_STATE_BASKET_MANAGEMENT: return "BASKET_MANAGEMENT";
      case FEMA_STATE_COOLDOWN:          return "COOLDOWN";
      case FEMA_STATE_SUSPENDED:         return "SUSPENDED";
     }
   return "UNKNOWN";
  }

string FemaDirectionToString(const ENUM_FEMA_DIRECTION dir)
  {
   switch(dir)
     {
      case FEMA_DIR_BUY:  return "BUY";
      case FEMA_DIR_SELL: return "SELL";
     }
   return "NONE";
  }

string FemaTrendToString(const ENUM_FEMA_TREND trend)
  {
   switch(trend)
     {
      case FEMA_TREND_UP:   return "UP";
      case FEMA_TREND_DOWN: return "DOWN";
     }
   return "NONE";
  }

string FemaExitReasonToString(const ENUM_FEMA_EXIT_REASON reason)
  {
   switch(reason)
     {
      case FEMA_EXIT_BASKET_TP:   return "BASKET_TP";
      case FEMA_EXIT_BASKET_SL:   return "BASKET_SL";
      case FEMA_EXIT_BASKET_TIME: return "BASKET_TIME";
     }
   return "NONE";
  }

#endif
