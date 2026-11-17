// Native terminal fixture acceptance. No broker credentials and no order functions.
// Compile in the disposable portable terminal; never distributed as a trading EA.
#property strict
#include "FinanceCalendarNews.mqh"
#include "FixtureCases.mqh"
int g_native_timer_calls = 0;
int OnInit()
{
   FcFixtureRun();
   if(!EventSetTimer(1)) return INIT_FAILED;
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
   string report = "{\"platform\":\"MT" + platform + "\",\"fixture_checks\":" + IntegerToString(g_fixture_checks)
      + ",\"fixture_failures\":" + IntegerToString(g_fixture_failed) + ",\"timer_calls\":" + IntegerToString(g_native_timer_calls)
      + ",\"public_sample_http_status\":" + IntegerToString(status) + ",\"public_sample_mql_error\":" + IntegerToString(error)
      + ",\"public_sample_bytes\":" + IntegerToString(ArraySize(response))
      + ",\"paid_key_tested\":false,\"broker_account_tested\":false}";
   int file = FileOpen("FinanceCalendar-native-" + platform + ".json", FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(file != INVALID_HANDLE) { FileWriteString(file, report); FileFlush(file); FileClose(file); }
   Print("Finance Calendar native acceptance: ", report);
   TerminalClose(0);
}
void OnTick() {}
void OnDeinit(const int reason) { EventKillTimer(); }
