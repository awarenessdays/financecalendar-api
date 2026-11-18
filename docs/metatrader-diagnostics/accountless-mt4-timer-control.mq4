// Dated diagnostic only: isolated accountless MT4 timer control, not product code.
// Temporary minimal MT4 timer control: no Finance Calendar include, parser or data.
// Accountless and order-free. Distinct timer_probe_only receipts cannot satisfy
// the full integration gate (zero fixture checks are intentionally reported).
#property strict
int g_timer_calls = 0;
bool g_timer_set = false;
int g_timer_error = 0;
void Receipt(const string stage)
{
   string body="{\"timer_probe_only\":true,\"stage\":\""+stage+"\",\"timer_calls\":"+IntegerToString(g_timer_calls)
      +",\"program_type\":"+IntegerToString(MQLInfoInteger(MQL_PROGRAM_TYPE))
      +",\"tester\":"+IntegerToString(MQLInfoInteger(MQL_TESTER))
      +",\"terminal_trade_allowed\":"+IntegerToString(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      +",\"program_trade_allowed\":"+IntegerToString(MQLInfoInteger(MQL_TRADE_ALLOWED))
      +",\"terminal_connected\":"+IntegerToString(TerminalInfoInteger(TERMINAL_CONNECTED))
      +",\"timer_set_returned\":"+IntegerToString(g_timer_set?1:0)+",\"timer_set_error\":"+IntegerToString(g_timer_error)
      +",\"fixture_checks\":0,\"fixture_failures\":0,\"public_sample_http_status\":0,\"public_sample_bytes\":0,\"paid_key_tested\":false,\"broker_account_tested\":false}";
   string name=stage=="callbacks"?"FinanceCalendar-native-4.json":"FinanceCalendar-timer-control-"+stage+".json";
   int file=FileOpen(name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(file!=INVALID_HANDLE){FileWriteString(file,body);FileFlush(file);FileClose(file);}
   if(stage=="before") Print("plain timer control before creation: ",body);
}
int OnInit()
{
   Receipt("before");
   ResetLastError();
   g_timer_set=EventSetMillisecondTimer(1000);
   g_timer_error=GetLastError();
   Receipt("after");
   Receipt("on-init-returning");
   return g_timer_set?INIT_SUCCEEDED:INIT_FAILED;
}
void OnTimer()
{
   g_timer_calls++;
   if(g_timer_calls<2){Receipt("callback-one");return;}
   Receipt("callbacks");
   EventKillTimer();
   TerminalClose(0);
}
void OnTick(){}
void OnDeinit(const int reason){EventKillTimer();}
