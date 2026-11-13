// Offline cases for the news filter. Appended after the translated MQL source.
static int checks = 0;
static void verify(bool ok, const char *message) {
   checks++;
   if(!ok) { printf("FAILED: %s\n", message); for(auto &l : t_log) printf("  log: %s\n", l.c_str()); exit(1); }
}
static datetime at(const char *when) { return StringToTime(when); }
static void fresh_terminal() { t_globals.clear(); t_files.clear(); t_log.clear(); t_requests = 0; t_status = 200; t_headers = ""; t_error = 0; }
static bool logged(const char *text) { for(auto &l : t_log) if(l.find(text) != string::npos) return true; return false; }
static const char *KEY = "fc_live_0123456789abcdef0123456789abcdef";

int main() {
   t_symbols = {{"EURUSD", {"EUR", "USD"}}, {"GBPJPY", {"GBP", "JPY"}}, {"XAUUSD", {"XAU", "USD"}}, {"AUDNZD", {"AUD", "NZD"}},
                {"BTCUSD", {"BTC", "USD"}}, {"USDCAD", {"USD", "CAD"}}, {"US500", {"USD", "USD"}}, {"NOPE", {"ZZZ", "YYY"}}};
   string reason, name; datetime when;

   // Keys
   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_body = FX_FREE_SCHEDULE;
   verify(!FcNewsInit("", "high") && !FcNewsInit("fc_live_short") && !FcNewsInit("fc_live_0123456789ABCDEF0123456789abcdef"), "Missing and malformed keys are refused.");
   FcNewsRefresh();
   verify(t_requests == 0 && !FcNewsReady(), "No request is made without a valid key.");

   // First load
   verify(FcNewsInit(string("  ") + KEY + " ", "High", 180, 20), "A valid key starts the filter.");
   FcNewsRefresh();
   verify(t_requests == 1, "The first refresh makes one request.");
   verify(t_url == "https://www.financecalendar.com/wp-json/fc/v1/calendar?from=2026-11-13&to=2026-11-19&impact=high&limit=20", "The request uses only parameters every plan accepts.");
   verify(t_request_headers == string("X-API-Key: ") + KEY + "\r\nAccept: application/json\r\n" && t_url.find("fc_live_") == string::npos, "The key travels in a header, never the URL.");
   verify(FcNewsReady() && g_fc_count == 7, "Seven scheduled releases are loaded.");
   verify(t_files.count("FinanceCalendarNews-high-20.json") == 1 && t_files["FinanceCalendarNews-high-20.json"].find("fc_live_") == string::npos, "The schedule file holds no key.");
   verify(g_fc_events[6].country == "AU" && g_fc_events[6].name == "Au Jobs", "A nested licence name does not replace the release name.");
   verify(g_fc_events[0].when_utc == at("2026.11.16 02:00"), "Release times are read as UTC.");

   // Symbols
   verify(FcSymbolCountries("EURUSD") == "EU,DE,US" && FcSymbolCountries("XAUUSD") == "US" && FcSymbolCountries("BTCUSD") == "US"
          && FcSymbolCountries("US500") == "US" && FcSymbolCountries("GBPJPY") == "GB,JP" && FcSymbolCountries("NOPE") == "", "Symbols map to the countries of their currencies.");

   // Next release
   verify(FcNewsNext("EURUSD", when, name) && when == at("2026.11.17 10:05") && name == "De Zew", "EURUSD: the next release is the German one.");
   verify(FcNewsNext("USDCAD", when, name) && when == at("2026.11.16 13:30") && name == "Ca Cpi", "USDCAD: the next release is Canadian CPI.");
   verify(!FcNewsNext("NOPE", when, name) && when == 0, "An uncovered symbol has no next release.");

   // Quiet window around US retail sales, 17 Nov 13:30 UTC (the timer keeps the schedule fresh)
   t_now = at("2026.11.17 12:59"); FcNewsRefresh(); verify(!FcNewsBlocked("EURUSD", 30, 30, reason) && reason == "", "31 minutes before: clear.");
   t_now = at("2026.11.17 13:00"); FcNewsRefresh(); verify(FcNewsBlocked("EURUSD", 30, 30, reason) && reason == "Us Retail Sales", "30 minutes before: quiet window.");
   t_now = at("2026.11.17 13:30"); FcNewsRefresh(); verify(FcNewsBlocked("XAUUSD", 30, 30, reason) && FcNewsBlocked("BTCUSD", 30, 30, reason), "At the release: gold and bitcoin against the dollar are in the window.");
   verify(!FcNewsBlocked("GBPJPY", 30, 30, reason) && !FcNewsBlocked("AUDNZD", 30, 30, reason) && !FcNewsBlocked("NOPE", 30, 30, reason), "Other currencies are not affected.");
   t_now = at("2026.11.17 14:00"); FcNewsRefresh(); verify(FcNewsBlocked("EURUSD", 30, 30, reason), "30 minutes after: still in the window.");
   t_now = at("2026.11.17 14:01"); FcNewsRefresh(); verify(!FcNewsBlocked("EURUSD", 30, 30, reason), "31 minutes after: clear.");
   t_now = at("2026.11.17 13:35"); FcNewsRefresh(); verify(!FcNewsBlocked("EURUSD", 30, 0, reason) && FcNewsBlocked("EURUSD", 0, 10, reason), "Before and after sizes apply separately.");
   t_now = at("2026.11.19 00:20"); FcNewsRefresh(); verify(FcNewsBlocked("AUDNZD", 15, 15, reason) && reason == "Au Jobs", "AUDNZD: Australian jobs opens a window.");

   // Request budget
   fresh_terminal(); t_now = at("2026.11.13 12:00"); FcNewsInit(KEY); FcNewsRefresh();
   for(int i = 1; i <= 179; i++) { t_now += 60; FcNewsRefresh(); }
   verify(t_requests == 1, "No second request inside the refresh interval.");
   t_now += 60; FcNewsRefresh();
   verify(t_requests == 2, "The next request comes when the interval has passed.");
   int before = t_requests; datetime start = t_now;
   while(t_now < start + 86400) { t_now += 30; FcNewsRefresh(); }
   verify(t_requests - before == 8, "A full day of 30-second timer calls makes 8 requests.");

   // A second chart in the same terminal shares the schedule
   int shared = t_requests;
   FcNewsInit(KEY);
   verify(FcNewsReady() && g_fc_count == 7 && t_requests == shared, "A second chart loads the shared schedule without a request.");
   FcNewsRefresh();
   verify(t_requests == shared, "And it does not refresh early.");
   FcNewsInit(KEY, "high,medium");
   verify(!FcNewsReady(), "A different impact setting keeps its own schedule.");

   // Failures
   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_status = -1; t_error = 4014; FcNewsInit(KEY); FcNewsRefresh();
   verify(t_requests == 1 && !FcNewsReady() && logged("Allow https://www.financecalendar.com"), "A blocked WebRequest explains the allow-list.");
   verify(!FcNewsBlocked("EURUSD", 30, 30, reason), "With no schedule the answer is false.");
   t_now += 899; FcNewsRefresh(); verify(t_requests == 1, "No retry inside 15 minutes.");

   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_status = 429; t_headers = "Content-Type: application/json\r\nretry-after: 7200\r\n"; FcNewsInit(KEY); FcNewsRefresh();
   t_status = 200; t_now += 7199; FcNewsRefresh();
   verify(t_requests == 1, "Retry-After is honoured.");
   t_now += 3600 + 2; FcNewsRefresh();
   verify(t_requests == 2 && FcNewsReady(), "Requests resume after the pause and the refresh interval.");

   for(int status : {401, 402, 403}) {
      fresh_terminal(); t_now = at("2026.11.13 12:00"); t_status = status; FcNewsInit(KEY); FcNewsRefresh();
      t_status = 200; t_now += 86400; FcNewsRefresh();
      verify(t_requests == 1 && !FcNewsReady() && FcNewsStatus().find("financecalendar.com/account") != string::npos, "An access problem stops requests and points to the account.");
   }

   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_body = FX_KEYLESS_NOTICE; FcNewsInit(KEY); FcNewsRefresh();
   verify(!FcNewsReady() && g_fc_count == 0 && FcNewsStatus().find("API key is needed") != string::npos, "A notice answer is never read as a release.");

   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_body = "<html>Just a moment</html>"; FcNewsInit(KEY); FcNewsRefresh();
   verify(!FcNewsReady() && logged("not a schedule"), "A page that is not JSON is rejected.");
   t_body = "{\"events\":[{\"country\":\"US\",\"release_at_utc\":\"2026-11-13T12:00"; t_now += 901; FcNewsRefresh();
   verify(!FcNewsReady(), "A cut-off answer is rejected.");

   // Stale schedule
   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_body = FX_FREE_SCHEDULE; FcNewsInit(KEY); FcNewsRefresh();
   t_status = -1; t_now = at("2026.11.17 13:30"); FcNewsRefresh();
   verify(!FcNewsReady() && !FcNewsBlocked("EURUSD", 30, 30, reason), "A schedule older than 26 hours is not used.");

   // Other shapes
   fresh_terminal(); t_now = at("2026.11.13 12:00"); t_body = FX_FREE_SCHEDULE_SPACED; FcNewsInit(KEY); FcNewsRefresh();
   verify(FcNewsReady() && g_fc_count == 7 && g_fc_events[4].name == "Us Retail Sales", "Indented JSON reads the same.");
   fresh_terminal(); t_now = at("2026.11.13 12:00");
   t_body = "{\"from\":\"2026-11-13\",\"count\":4,\"total\":9,\"events\":["
      "{\"id\":\"a\",\"name\":\"Fed \\\"Decision\\\" \\/ Statement\",\"title\":\"Paid title\",\"country\":\"US\",\"impact\":\"high\",\"release_at_utc\":\"2026-11-13T19:00:00Z\",\"status\":\"confirmed\",\"consensus\":\"3.5%\",\"auction\":{\"name\":\"x\",\"country\":\"JP\"},\"tags\":[\"a\",{\"country\":\"GB\"}]},"
      "{\"id\":\"b\",\"name\":\"Cancelled one\",\"country\":\"US\",\"impact\":\"high\",\"release_at_utc\":\"2026-11-13T12:10:00Z\",\"status\":\"cancelled\"},"
      "{\"id\":\"c\",\"name\":\"No time yet\",\"country\":\"US\",\"impact\":\"high\",\"release_at_utc\":null,\"status\":\"estimated\"},"
      "{\"id\":\"d\",\"title\":\"Title only\",\"country\":\"GB\",\"impact\":\"high\",\"release_at_utc\":\"2026-11-13T12:10:00+01:00\",\"status\":\"confirmed\"}]}";
   FcNewsInit(KEY); FcNewsRefresh();
   verify(g_fc_count == 3 && g_fc_events[0].name == "Fed \"Decision\" / Statement" && g_fc_events[0].country == "US", "Paid rows with nested values and escapes are read; cancelled rows are dropped.");
   verify(!FcNewsBlocked("EURUSD", 30, 30, reason) && g_fc_events[1].when_utc == 0 && g_fc_events[2].when_utc == 0 && g_fc_events[2].name == "Title only", "Releases without a UTC time never open a window.");
   verify(logged("cut at 4 of 9"), "A truncated schedule is reported.");

   // Example Expert Advisor
   fresh_terminal(); t_now = at("2026.11.17 13:20"); t_body = FX_FREE_SCHEDULE; _Symbol = "EURUSD";
   // The fixture window starts on 13 November; the API echoes whatever range is asked for.
   verify(OnInit() == INIT_SUCCEEDED && t_requests == 0 && t_globals["FC_NEWS_BLOCK_EURUSD"] == -1.0 && t_comment.find("Enter your Finance Calendar API key") != string::npos, "Without a key the example shows what to do and reports no schedule.");
   fresh_terminal(); InpApiKey = KEY; t_now = at("2026.11.17 13:20");
   verify(OnInit() == INIT_SUCCEEDED && t_requests == 1 && t_globals["FC_NEWS_BLOCK_EURUSD"] == 1.0, "With a key the example publishes the quiet-window state.");
   verify(t_comment.find("QUIET WINDOW: Us Retail Sales") != string::npos && t_comment.find("Next: Gb Cpi") == string::npos && t_comment.find("financecalendar.com") != string::npos, "The chart text names the release and the source.");
   t_now = at("2026.11.17 14:05"); OnTimer();
   verify(t_globals["FC_NEWS_BLOCK_EURUSD"] == 0.0 && t_comment.find("Clear") != string::npos && t_requests == 1, "After the window the state clears without another request.");
   _Symbol = "GBPJPY"; t_now = at("2026.11.17 14:06"); OnTimer();
   verify(t_comment.find("Next: Gb Cpi at 2026.11.18 07:00 UTC") != string::npos, "The chart text shows the next release for the symbol.");
   OnDeinit(0);
   verify(t_globals.count("FC_NEWS_BLOCK_GBPJPY") == 0 && t_comment == "", "Removing the example clears its state.");
   printf("MetaTrader news filter: %d offline checks passed (C++ stand-in runtime, not a MetaEditor compile)\n", checks);
   return 0;
}
