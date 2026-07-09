//+------------------------------------------------------------------+
//| LotSizing.mqh — fixed lot sizing (v1)                            |
//+------------------------------------------------------------------+
#ifndef FEMA_LOTSIZING_MQH
#define FEMA_LOTSIZING_MQH

#include "../Broker/SymbolInfo.mqh"
#include "../Utils/Helpers.mqh"
#include "../Utils/Logger.mqh"

class CFemaLotSizing
  {
private:
   double            m_base_lot;
   double            m_risk_percent;
   CFemaLogger      *m_log;

public:
                     CFemaLotSizing() : m_base_lot(0.01), m_risk_percent(0.0), m_log(NULL) {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   void              Init(const double base_lot, const double risk_percent)
     {
      m_base_lot = base_lot;
      m_risk_percent = risk_percent;
      if(m_risk_percent > 0.0 && m_log != NULL)
         m_log.LogWarn("Risk % input is inactive in Phase 1; using fixed lots");
     }

   double            CalculateLots(const CFemaSymbolInfo &symbol_info) const
     {
      return CFemaHelpers::NormalizeVolume(symbol_info.Symbol(), m_base_lot);
     }
  };

#endif
