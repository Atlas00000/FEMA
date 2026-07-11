//+------------------------------------------------------------------+
//|                                                         FEMA.mq5 |
//|                                  Floating EMA Grid — Phase 1       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, FEMA"
#property link      "https://www.mql5.com"
#property version   "1.21"

#define FEMA_VERSION "1.21"

#include "Include/Core/Engine.mqh"

CFemaEngine g_engine;

//+------------------------------------------------------------------+
int OnInit()
  {
   return g_engine.OnInit();
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   g_engine.OnDeinit(reason);
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   g_engine.OnTick();
  }
//+------------------------------------------------------------------+
