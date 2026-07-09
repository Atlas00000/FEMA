//+------------------------------------------------------------------+
//| StateMachine.mqh — execution lifecycle states                    |
//+------------------------------------------------------------------+
#ifndef FEMA_STATEMACHINE_MQH
#define FEMA_STATEMACHINE_MQH

#include "Types.mqh"
#include "../Utils/Logger.mqh"

class CFemaStateMachine
  {
private:
   ENUM_FEMA_STATE   m_state;
   datetime          m_cooldown_bar_time;
   int               m_consecutive_failures;
   CFemaLogger      *m_log;

   void              SetStateInternal(const ENUM_FEMA_STATE state)
     {
      if(m_state == state)
         return;
      if(m_log != NULL)
         m_log.LogInfo("State " + FemaStateToString(m_state) + " -> " + FemaStateToString(state));
      m_state = state;
     }

public:
                     CFemaStateMachine() :
                     m_state(FEMA_STATE_IDLE),
                     m_cooldown_bar_time(0),
                     m_consecutive_failures(0),
                     m_log(NULL)
     {}

   void              SetLogger(CFemaLogger &log) { m_log = GetPointer(log); }

   ENUM_FEMA_STATE   GetState() const { return m_state; }
   datetime          GetCooldownBarTime() const { return m_cooldown_bar_time; }
   int               GetConsecutiveFailures() const { return m_consecutive_failures; }

   void              SetReady()
     {
      m_consecutive_failures = 0;
      SetStateInternal(FEMA_STATE_READY);
     }

   void              SetInTrade()
     {
      SetStateInternal(FEMA_STATE_IN_TRADE);
     }

   void              SetBasketManagement()
     {
      SetStateInternal(FEMA_STATE_BASKET_MANAGEMENT);
     }

   void              StartCooldown(const datetime bar_time)
     {
      m_cooldown_bar_time = bar_time;
      SetStateInternal(FEMA_STATE_COOLDOWN);
     }

   void              SetSuspended()
     {
      SetStateInternal(FEMA_STATE_SUSPENDED);
     }

   void              RegisterExecutionSuccess()
     {
      m_consecutive_failures = 0;
     }

   void              RegisterExecutionFailure(const int max_failures)
     {
      m_consecutive_failures++;
      if(m_consecutive_failures >= max_failures)
        {
         if(m_log != NULL)
            m_log.LogError("Execution failures reached limit; entering SUSPENDED");
         SetSuspended();
        }
     }

   bool              IsTradingAllowed() const
     {
      return m_state == FEMA_STATE_READY ||
             m_state == FEMA_STATE_IN_TRADE ||
             m_state == FEMA_STATE_BASKET_MANAGEMENT;
     }

   bool              CanEnter() const
     {
      return m_state == FEMA_STATE_READY ||
             m_state == FEMA_STATE_IN_TRADE ||
             m_state == FEMA_STATE_BASKET_MANAGEMENT;
     }
  };

#endif
