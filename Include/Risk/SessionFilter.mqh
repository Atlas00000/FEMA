//+------------------------------------------------------------------+
//| SessionFilter.mqh — Phase 2D session / time gates               |
//+------------------------------------------------------------------+
#ifndef FEMA_SESSIONFILTER_MQH
#define FEMA_SESSIONFILTER_MQH

#include "../Core/Types.mqh"

class CFemaSessionFilter
  {
private:
   bool              m_block_no23;
   bool              m_block_fri_close;
   bool              m_block_sun_open;
   bool              m_whitelist_ldn_ny;

   static void       BrokerTimeParts(int &hour, int &day_of_week)
     {
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      hour = dt.hour;
      day_of_week = dt.day_of_week;
     }

   bool              IsActive() const
     {
      return m_block_no23 || m_block_fri_close || m_block_sun_open || m_whitelist_ldn_ny;
     }

   bool              InRolloverWindow(const int hour) const
     {
      return hour >= 22 || hour == 0;
     }

   bool              InLondonNyWindow(const int hour) const
     {
      return (hour >= 8 && hour < 12) || (hour >= 13 && hour < 18);
     }

public:
                     CFemaSessionFilter() :
                     m_block_no23(false),
                     m_block_fri_close(false),
                     m_block_sun_open(false),
                     m_whitelist_ldn_ny(false)
     {}

   void              Init(const bool block_no23,
                          const bool block_fri_close,
                          const bool block_sun_open,
                          const bool whitelist_ldn_ny)
     {
      m_block_no23 = block_no23;
      m_block_fri_close = block_fri_close;
      m_block_sun_open = block_sun_open;
      m_whitelist_ldn_ny = whitelist_ldn_ny;
     }

   bool              AllowsEntry(const bool is_new_basket, string &reason) const
     {
      reason = "";
      if(!IsActive())
         return true;

      int hour = 0;
      int dow = 0;
      BrokerTimeParts(hour, dow);

      if(m_block_no23 && InRolloverWindow(hour))
        {
         reason = "Session block: rollover window (hour " + IntegerToString(hour) + ")";
         return false;
        }

      if(m_block_sun_open && dow == 0 && hour < 2)
        {
         reason = "Session block: Sunday open (hour " + IntegerToString(hour) + ")";
         return false;
        }

      if(m_block_fri_close && is_new_basket && dow == 5 && hour >= 20)
        {
         reason = "Session block: Friday close (hour " + IntegerToString(hour) + ")";
         return false;
        }

      if(m_whitelist_ldn_ny && !InLondonNyWindow(hour))
        {
         reason = "Session block: outside London/NY window (hour " + IntegerToString(hour) + ")";
         return false;
        }

      return true;
     }

   string            ActiveSummary() const
     {
      if(!IsActive())
         return "off";
      string s = "";
      if(m_block_no23)
         s += (s == "" ? "" : "+") + "no23";
      if(m_block_fri_close)
         s += (s == "" ? "" : "+") + "nofri";
      if(m_block_sun_open)
         s += (s == "" ? "" : "+") + "nosun";
      if(m_whitelist_ldn_ny)
         s += (s == "" ? "" : "+") + "ldnny";
      return s;
     }
  };

#endif
