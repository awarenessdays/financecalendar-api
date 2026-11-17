// Native terminal fixture acceptance. No broker credentials and no order functions.
// Compile in the disposable portable terminal; never distributed as a trading EA.
#property strict
#include "FinanceCalendarNews.mqh"
#include "FixtureCases.mqh"
int g_native_timer_calls = 0;
string NativeContext()
{
   string context = "\"program_type\":" + IntegerToString(MQLInfoInteger(MQL_PROGRAM_TYPE))
      + ",\"program_is_expert\":" + IntegerToString(MQLInfoInteger(MQL_PROGRAM_TYPE) == PROGRAM_EXPERT ? 1 : 0)
      + ",\"tester\":" + IntegerToString(MQLInfoInteger(MQL_TESTER))
      + ",\"terminal_trade_allowed\":" + IntegerToString(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
      + ",\"program_trade_allowed\":" + IntegerToString(MQLInfoInteger(MQL_TRADE_ALLOWED))
      + ",\"dll_allowed\":" + IntegerToString(MQLInfoInteger(MQL_DLLS_ALLOWED))
      + ",\"terminal_connected\":" + IntegerToString(TerminalInfoInteger(TERMINAL_CONNECTED));
#ifdef __MQL5__
   context += ",\"started_from_config\":" + IntegerToString(MQLInfoInteger(MQL_STARTED_FROM_CONFIG));
#endif
   return context;
}
string NativePlatform()
{
#ifdef __MQL5__
   return "5";
#else
   return "4";
#endif
}
void NativeWrite(const string name, const string report)
{
   int file = FileOpen(name, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(file != INVALID_HANDLE) { FileWriteString(file, report); FileFlush(file); FileClose(file); }
}
int OnInit()
{
   Print("Finance Calendar native OnInit entered: ", NativeContext());
   NativeWrite("FinanceCalendar-native-start-" + NativePlatform() + ".json", "{" + NativeContext() + ",\"on_init_entered\":true}");
   FcFixtureRun();
   ResetLastError();
   bool timer_set = EventSetTimer(1);
   Print("Finance Calendar native timer set: ", timer_set, "; error: ", GetLastError());
   if(!timer_set) return INIT_FAILED;
   return INIT_SUCCEEDED;
}
void OnTimer()
{
   g_native_timer_calls++;
   string reason;
   FcFixtureCheck(FcNewsStateAt("EU,DE,US", FcParseUtc("2026-11-17T13:00:00Z"), 30, 30, reason) == FC_NEWS_QUIET, "native timer executes real state code");
   if(g_native_timer_calls < 2) return;
   EventKillTimer();
   // Separately record real terminal HTTPS transport against the public fixed sample.
   // No account key is used; this does not establish paid-key or broker acceptance.
   char request[], response[];
   string headers;
   ResetLastError();
   int status = WebRequest("GET", "https://www.financecalendar.com/wp-json/fc/v1/sample", "Accept: application/json\r\n", 12000, request, response, headers);
   int error = GetLastError();
#ifdef __MQL5__
   string platform = "5";
#else
   string platform = "4";
#endif
   string report = "{" + NativeContext() + ",\"platform\":\"MT" + platform + "\",\"fixture_checks\":" + IntegerToString(g_fixture_checks)
      + ",\"fixture_failures\":" + IntegerToString(g_fixture_failed) + ",\"timer_calls\":" + IntegerToString(g_native_timer_calls)
      + ",\"public_sample_http_status\":" + IntegerToString(status) + ",\"public_sample_mql_error\":" + IntegerToString(error)
      + ",\"public_sample_bytes\":" + IntegerToString(ArraySize(response))
      + ",\"paid_key_tested\":false,\"broker_account_tested\":false}";
   NativeWrite("FinanceCalendar-native-" + platform + ".json", report);
   Print("Finance Calendar native acceptance: ", report);
   TerminalClose(0);
}
void OnTick() {}
void OnDeinit(const int reason) { EventKillTimer(); }
