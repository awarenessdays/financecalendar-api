static void verify(bool ok, const char *message) { if(!ok) { printf("FAILED: %s\n", message); exit(1); } }
static const char *KEY = "fc_live_0123456789abcdef0123456789abcdef";
static void fresh_terminal() { t_globals.clear(); t_files.clear(); t_log.clear(); t_requests = 0; t_status = 200; t_headers = ""; t_error = 0; }
int main() {
   FcFixtureRun();
   for(auto &l : t_log) printf("%s\n", l.c_str());
   verify(g_fixture_failed == 0, "shared native MQL fixture checks");
   t_now = FcParseUtc("2026-11-17T13:00:00Z");
   t_symbols = {{"EURUSD", {"EUR", "USD"}}, {"EURUSD.a", {"EUR", "USD"}}, {"XAUUSD", {"XAU", "USD"}}, {"BTCUSD", {"BTC", "USD"}}, {"NOPE", {"ZZZ", "YYY"}}};
   verify(FcSymbolCountries("EURUSD.a") == "EU,DE,US", "broker metadata maps suffix symbols");
   verify(FcSymbolCountries("GBP/JPY") == "GB,JP", "explicit slash pair maps without broker metadata");
   verify(FcSymbolCountries("BTCUSD") == "" && FcSymbolCountries("XAUUSD") == "US", "unsupported bases not silently mapped");
   fresh_terminal(); t_body = FcFixtureCalendar(FcFixtureRow());
   verify(FcNewsInit(KEY), "valid key accepted"); FcNewsRefresh();
   verify(t_url == "https://www.financecalendar.com/wp-json/fc/v1/calendar?from=2026-11-16&to=2026-11-23&country=US,EU,DE,GB,JP,CA,AU,NZ,CH,CN,IN,KR,MY,HK,NO,SE&impact=high&limit=500", "paid range includes yesterday");
   verify(t_request_headers.find(KEY) != string::npos && t_url.find(KEY) == string::npos, "key only in header");
   verify(FcNewsReady(), "complete fetched schedule ready");
   string reason; verify(FcNewsBlocked("EURUSD", 30, 30, reason), "quiet compatibility blocks");
   string file = FcFileName(), scope = g_fc_scope; int requests = t_requests;
   verify(file.find(KEY) == string::npos, "file name contains no key");
   FcNewsInit(KEY); verify(FcNewsReady(), "same-key chart shares cache"); FcNewsRefresh();
   verify(t_requests == requests, "shared chart makes no extra request");
   FcNewsInit("fc_live_1123456789abcdef0123456789abcdef");
   verify(!FcNewsReady() && g_fc_scope != scope && FcFileName() != file, "different key cannot read cache");
   verify(FcNewsBlocked("EURUSD",30,30,reason), "missing schedule compatibility blocks");
   FcNewsInit(KEY); t_now += 180*60; t_status=503; FcNewsRefresh();
   verify(!FcNewsReady() && FcNewsBlocked("EURUSD",30,30,reason), "failed refresh cannot advertise old calendar");
   // Simulate a sibling chart retaining its previous in-memory fields: shared failure
   // must invalidate decisions even before that chart's next timer/network refresh.
   g_fc_complete=true;verify(FcNewsState("EURUSD",30,30,reason)==FC_NEWS_UNKNOWN,"shared failure invalidates peer decisions");
   fresh_terminal(); FcNewsInit(KEY); t_status=429;t_headers="Retry-After: 7200\r\n";FcNewsRefresh();
   t_now += 7199; FcNewsRefresh(); verify(t_requests==1,"429 Retry-After respected"); t_now++;t_status=200;FcNewsRefresh();verify(t_requests==2,"429 resumes exactly after Retry-After despite normal refresh interval");
   t_now=FcParseUtc("2026-11-17T15:00:00Z");
   verify(FcRetryAfterSeconds("Retry-After: Tue, 17 Nov 2026 17:00:00 GMT\r\n") == 7200, "HTTP-date retry delay");
   verify(FcRetryAfterSeconds("Retry-After: 99999999999999999999\r\n") == -1, "oversized retry delay is not shortened");
   fresh_terminal(); FcNewsInit(KEY);t_status=503;FcNewsRefresh();t_now+=899;FcNewsRefresh();verify(t_requests==1,"transport failure pause respected");t_now++;t_status=200;FcNewsRefresh();verify(t_requests==2,"transport retry at 15min not 180min");
   for(int status : {401,402,403}) { fresh_terminal();FcNewsInit(KEY);t_status=status;FcNewsRefresh();t_now+=86400;FcNewsRefresh();verify(t_requests==1 && !FcNewsReady(),"access rejection stops refresh"); FcNewsInit(KEY);FcNewsRefresh();verify(t_requests==1,"auth stop survives sibling init"); FcNewsResumeAfterAccessFix();t_status=200;FcNewsRefresh();verify(t_requests==2,"explicit access repair resumes calls"); }
   fresh_terminal(); t_now=FcParseUtc("2026-11-17T13:00:00Z");t_body=FcFixtureCalendar(FcFixtureRow());InpApiKey=KEY;_Symbol="EURUSD";
   OnInit();verify(t_globals["FC_NEWS_BLOCK_EURUSD"]==1,"EA adapter publishes quiet");
   t_now+=3601;OnTimer();verify(t_globals["FC_NEWS_BLOCK_EURUSD"]==0,"timer updates clear");
   g_fc_complete=false;OnTimer();verify(t_globals["FC_NEWS_BLOCK_EURUSD"]==-1,"timer publishes unknown");
   OnDeinit(0);verify(!t_globals.count("FC_NEWS_BLOCK_EURUSD"),"EA cleanup removes published state");
   printf("MetaTrader: %d shared MQL fixtures + 23 transport/cache/EA checks passed in C++ stand-in (not native terminal).\n",g_fixture_checks);
}
