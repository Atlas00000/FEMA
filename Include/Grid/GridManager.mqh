//+------------------------------------------------------------------+
//| GridManager.mqh — floating grid around EMA fast                  |
//+------------------------------------------------------------------+
#ifndef FEMA_GRIDMANAGER_MQH
#define FEMA_GRIDMANAGER_MQH

#include "../Core/Types.mqh"
#include "../Indicators/Indicators.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

class CFemaGridManager
  {
private:
   string            m_symbol;
   int               m_grid_levels;
   double            m_atr_multiplier;
   double            m_rebuild_atr_factor;
   double            m_center;
   double            m_last_center;
   SFemaGridLevel    m_levels[];
   CFemaLogger      *m_log;

   void              ClearLevels()
     {
      ArrayResize(m_levels, 0);
     }

   void              BuildLevels(const CFemaIndicators &indicators)
     {
      ClearLevels();
      m_center = indicators.EmaFast();
      m_last_center = m_center;
      const double spacing = indicators.Atr() * m_atr_multiplier;
      const ENUM_FEMA_TREND trend = indicators.Trend();

      int count = 0;
      if(trend == FEMA_TREND_UP)
        {
         for(int i = 1; i <= m_grid_levels; i++)
           {
            ArrayResize(m_levels, count + 1);
            m_levels[count].index = i;
            m_levels[count].direction = FEMA_DIR_BUY;
            m_levels[count].price = CFemaHelpers::NormalizePrice(m_symbol, m_center - i * spacing);
            m_levels[count].fired = false;
            count++;
           }
        }
      else if(trend == FEMA_TREND_DOWN)
        {
         for(int i = 1; i <= m_grid_levels; i++)
           {
            ArrayResize(m_levels, count + 1);
            m_levels[count].index = i;
            m_levels[count].direction = FEMA_DIR_SELL;
            m_levels[count].price = CFemaHelpers::NormalizePrice(m_symbol, m_center + i * spacing);
            m_levels[count].fired = false;
            count++;
           }
        }
     }

   void              LogLevels() const
     {
      if(m_log == NULL)
         return;
      for(int i = 0; i < ArraySize(m_levels); i++)
         m_log.LogGridLevel(m_levels[i].index, m_levels[i].direction, m_levels[i].price, m_levels[i].fired);
     }

public:
                     CFemaGridManager() :
                     m_symbol(""),
                     m_grid_levels(5),
                     m_atr_multiplier(1.0),
                     m_rebuild_atr_factor(0.25),
                     m_center(0.0),
                     m_last_center(0.0),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const string symbol,
                          const int grid_levels,
                          const double atr_multiplier,
                          const double rebuild_atr_factor)
     {
      m_symbol = symbol;
      m_grid_levels = MathMax(1, grid_levels);
      m_atr_multiplier = atr_multiplier;
      m_rebuild_atr_factor = rebuild_atr_factor;
     }

   void              BuildInitial(const CFemaIndicators &indicators)
     {
      BuildLevels(indicators);
      LogLevels();
     }

   void              RebuildIfNeeded(const CFemaIndicators &indicators,
                                      const bool defer_while_basket_open = false)
     {
      if(defer_while_basket_open && ArraySize(m_levels) > 0)
         return;

      const double new_center = indicators.EmaFast();
      const double shift = MathAbs(new_center - m_last_center);
      const double threshold = indicators.Atr() * m_rebuild_atr_factor;

      if(ArraySize(m_levels) == 0)
        {
         BuildLevels(indicators);
         LogLevels();
         return;
        }

      if(shift < threshold)
         return;

      if(m_log != NULL)
         m_log.LogInfo("Grid rebuild: center shift " + DoubleToString(shift, _Digits) +
                       " >= threshold " + DoubleToString(threshold, _Digits));

      BuildLevels(indicators);
      LogLevels();
     }

   double            Center() const { return m_center; }

   int               LevelCount() const { return ArraySize(m_levels); }

   bool              GetLevel(const int index, SFemaGridLevel &level) const
     {
      if(index < 0 || index >= ArraySize(m_levels))
         return false;
      level = m_levels[index];
      return true;
     }

   void              MarkFired(const int index)
     {
      if(index < 0 || index >= ArraySize(m_levels))
         return;
      m_levels[index].fired = true;
     }

   void              ResetFiredFlags()
     {
      for(int i = 0; i < ArraySize(m_levels); i++)
         m_levels[i].fired = false;
     }
  };

#endif
