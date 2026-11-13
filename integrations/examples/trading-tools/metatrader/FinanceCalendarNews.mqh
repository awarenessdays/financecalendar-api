//+------------------------------------------------------------------+
//| FinanceCalendarNews.mqh                                          |
//| Economic-release news filter for MetaTrader 4 and 5.             |
//| Data: Finance Calendar API, https://www.financecalendar.com/api/ |
//+------------------------------------------------------------------+
// Compiles in MetaEditor for MQL4 and MQL5; not run on a trading terminal by the publisher.
// Test it on a demo account before relying on it.
//
// What it does: downloads the upcoming release schedule a few times a day, keeps it in
// memory and in a terminal-local file, and answers one question for your own code:
// "is this symbol inside a quiet window around a scheduled release right now?"
// It places, changes and closes no orders.
//
// Setup: Tools > Options > Expert Advisors > Allow WebRequest for listed URL:
//    https://www.financecalendar.com
// WebRequest is not available in indicators or in the Strategy Tester.
//
// Requests: one GET per refresh. The default refresh is every 180 minutes, which is
// 8 requests a day and fits the Free Developer allowance (10 successful responses a
// day, 100 a month, today through today+6 UTC, up to 20 records). All charts in one
// terminal share the same schedule, so several charts still make one request.
#property strict

#define FC_NEWS_MAX_BYTES  4194304
#define FC_NEWS_STALE_SECS 93600   // 26 hours: an older schedule is treated as no data

const string FC_NEWS_URL     = "https://www.financecalendar.com/wp-json/fc/v1/calendar";
const string FC_NEWS_ACCOUNT = "https://www.financecalendar.com/account/";

struct FcNewsEvent
{
   datetime when_utc;   // 0 when the release has no published time
   string   country;    // two-letter code used by the API, for example US, EU, GB
   string   impact;     // high, medium or low
   string   name;
};

FcNewsEvent g_fc_events[];
int      g_fc_count        = 0;
datetime g_fc_loaded_utc   = 0;     // when the schedule in memory was fetched
datetime g_fc_stop_until   = 0;     // no request before this UTC time
bool     g_fc_stopped      = false; // access problem: no further requests until restart
string   g_fc_key          = "";
string   g_fc_impact       = "high";
int      g_fc_refresh_min  = 180;
int      g_fc_max_events   = 20;
string   g_fc_message      = "Not started";

//--- small helpers that behave the same in MQL4 and MQL5 ---------------------------

string FcTrim(const string text)
{
   int a = 0, b = StringLen(text) - 1;
   while(a <= b && StringGetCharacter(text, a) <= ' ') a++;
   while(b >= a && StringGetCharacter(text, b) <= ' ') b--;
   return (b < a) ? "" : StringSubstr(text, a, b - a + 1);
}

string FcUpper(const string text)
{
   string out = text;
   StringToUpper(out);
   return out;
}

string FcUtcDate(const datetime when)
{
   string value = TimeToString(when, TIME_DATE);
   StringReplace(value, ".", "-");
   return value;
}

bool FcNewsValidKey(const string key)
{
   if(StringLen(key) != 40 || StringSubstr(key, 0, 8) != "fc_live_") return false;
   for(int i = 8; i < 40; i++)
   {
      ushort c = StringGetCharacter(key, i);
      if(!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
   }
   return true;
}

// Terminal-wide values, so every chart shares one schedule and one request budget.
string FcGvName(const string what) { return "FC_NEWS_" + what + "_" + g_fc_impact + "_" + IntegerToString(g_fc_max_events); }
string FcFileName()                { return "FinanceCalendarNews-" + g_fc_impact + "-" + IntegerToString(g_fc_max_events) + ".json"; }

//--- minimal JSON reading -----------------------------------------------------------
// Only what the schedule needs: top-level fields of an object, and the items of an array.

int FcJsonSkipSpace(const string &text, int i)
{
   int n = StringLen(text);
   while(i < n && StringGetCharacter(text, i) <= ' ') i++;
   return i;
}

// Index of the closing quote of the string that opens at 'start', or -1.
int FcJsonStringEnd(const string &text, const int start)
{
   int n = StringLen(text);
   for(int i = start + 1; i < n; i++)
   {
      ushort c = StringGetCharacter(text, i);
      if(c == '\\') { i++; continue; }
      if(c == '"') return i;
   }
   return -1;
}

// Index just past the JSON value that starts at 'start', or -1.
int FcJsonValueEnd(const string &text, const int start)
{
   int n = StringLen(text);
   if(start >= n) return -1;
   ushort first = StringGetCharacter(text, start);
   if(first == '"')
   {
      int end = FcJsonStringEnd(text, start);
      return (end < 0) ? -1 : end + 1;
   }
   if(first == '{' || first == '[')
   {
      int depth = 0;
      for(int i = start; i < n; i++)
      {
         ushort c = StringGetCharacter(text, i);
         if(c == '"')
         {
            i = FcJsonStringEnd(text, i);
            if(i < 0) return -1;
            continue;
         }
         if(c == '{' || c == '[') depth++;
         else if(c == '}' || c == ']')
         {
            depth--;
            if(depth == 0) return i + 1;
         }
      }
      return -1;
   }
   int j = start;
   while(j < n)
   {
      ushort c = StringGetCharacter(text, j);
      if(c == ',' || c == '}' || c == ']' || c <= ' ') break;
      j++;
   }
   return j;
}

// Raw value of a top-level key of the object in 'object_text'. False when the key is absent.
bool FcJsonTop(const string &object_text, const string key, string &value)
{
   int n = StringLen(object_text);
   int i = FcJsonSkipSpace(object_text, 0);
   if(i >= n || StringGetCharacter(object_text, i) != '{') return false;
   i++;
   while(i < n)
   {
      i = FcJsonSkipSpace(object_text, i);
      if(i >= n) return false;
      ushort c = StringGetCharacter(object_text, i);
      if(c == '}') return false;
      if(c == ',') { i++; continue; }
      if(c != '"') return false;
      int name_end = FcJsonStringEnd(object_text, i);
      if(name_end < 0) return false;
      string name = StringSubstr(object_text, i + 1, name_end - i - 1);
      int colon = FcJsonSkipSpace(object_text, name_end + 1);
      if(colon >= n || StringGetCharacter(object_text, colon) != ':') return false;
      int start = FcJsonSkipSpace(object_text, colon + 1);
      int stop = FcJsonValueEnd(object_text, start);
      if(stop < 0) return false;
      if(name == key)
      {
         value = StringSubstr(object_text, start, stop - start);
         return true;
      }
      i = stop;
   }
   return false;
}

// Text of a JSON string value; "" for null, numbers, objects and anything else.
string FcJsonText(const string raw)
{
   int n = StringLen(raw);
   if(n < 2 || StringGetCharacter(raw, 0) != '"') return "";
   string out = StringSubstr(raw, 1, n - 2);
   StringReplace(out, "\\/", "/");
   StringReplace(out, "\\\"", "\"");
   StringReplace(out, "\\\\", "\\");
   return out;
}

// "2026-11-16T02:00:00+00:00" or "...Z" to a UTC datetime; 0 when absent or not UTC.
datetime FcParseUtc(const string iso)
{
   int n = StringLen(iso);
   if(n < 17) return 0;
   string zone = StringSubstr(iso, n - 1) == "Z" ? "Z" : StringSubstr(iso, n - 6);
   if(zone != "Z" && zone != "+00:00") return 0;
   string value = StringSubstr(iso, 0, 10) + " " + StringSubstr(iso, 11, 5);
   StringReplace(value, "-", ".");
   return StringToTime(value);
}

//--- schedule -----------------------------------------------------------------------

// Reads the "events" array of a calendar response into memory. False when it is not a schedule.
bool FcNewsParse(const string &body, const datetime fetched_utc)
{
   string events;
   if(!FcJsonTop(body, "events", events)) return false;
   int n = StringLen(events);
   int i = FcJsonSkipSpace(events, 0);
   if(i >= n || StringGetCharacter(events, i) != '[') return false;
   i++;
   FcNewsEvent parsed[];
   int count = 0;
   while(i < n)
   {
      i = FcJsonSkipSpace(events, i);
      if(i >= n) return false;
      ushort c = StringGetCharacter(events, i);
      if(c == ']') break;
      if(c == ',') { i++; continue; }
      int stop = FcJsonValueEnd(events, i);
      if(stop < 0) return false;
      if(c == '{')
      {
         string item = StringSubstr(events, i, stop - i);
         string raw;
         // A row marked as a notice is a message from the API, never a release.
         bool notice = FcJsonTop(item, "notice", raw) && raw == "true";
         string status = FcJsonTop(item, "status", raw) ? FcJsonText(raw) : "";
         string country = FcJsonTop(item, "country", raw) ? FcJsonText(raw) : "";
         if(!notice && status != "cancelled" && status != "notice" && StringLen(country) == 2)
         {
            ArrayResize(parsed, count + 1, 64);
            parsed[count].country = country;
            parsed[count].impact = FcJsonTop(item, "impact", raw) ? FcJsonText(raw) : "";
            parsed[count].name = FcJsonTop(item, "name", raw) ? FcJsonText(raw) : "";
            if(parsed[count].name == "" && FcJsonTop(item, "title", raw)) parsed[count].name = FcJsonText(raw);
            parsed[count].when_utc = FcJsonTop(item, "release_at_utc", raw) ? FcParseUtc(FcJsonText(raw)) : 0;
            count++;
         }
      }
      i = stop;
   }
   ArrayResize(g_fc_events, count);
   for(int k = 0; k < count; k++) g_fc_events[k] = parsed[k];
   g_fc_count = count;
   g_fc_loaded_utc = fetched_utc;
   string raw_total, raw_count;
   if(FcJsonTop(body, "total", raw_total) && FcJsonTop(body, "count", raw_count)
      && StringToInteger(raw_total) > StringToInteger(raw_count))
      Print("Finance Calendar: the schedule was cut at ", raw_count, " of ", raw_total,
         " releases. The nearest ones are kept. Use fewer impact levels, or a paid plan with a higher event limit.");
   return true;
}

bool FcNewsLoadFile()
{
   if(!GlobalVariableCheck(FcGvName("FETCHED"))) return false;
   datetime fetched = (datetime)GlobalVariableGet(FcGvName("FETCHED"));
   if(fetched <= g_fc_loaded_utc) return false;
   int file = FileOpen(FcFileName(), FILE_READ | FILE_BIN | FILE_SHARE_READ);
   if(file == INVALID_HANDLE) return false;
   uchar bytes[];
   int size = (int)FileSize(file);
   bool ok = size > 0 && size <= FC_NEWS_MAX_BYTES && FileReadArray(file, bytes, 0, size) == (uint)size;
   FileClose(file);
   if(!ok) return false;
   string body = CharArrayToString(bytes, 0, size, CP_UTF8);
   return FcNewsParse(body, fetched);
}

void FcNewsPause(const int seconds, const string message)
{
   g_fc_stop_until = TimeGMT() + seconds;
   GlobalVariableSet(FcGvName("STOP"), (double)g_fc_stop_until);
   g_fc_message = message;
   Print("Finance Calendar: ", message);
}

int FcRetryAfterSeconds(const string headers)
{
   string lines[];
   int count = StringSplit(headers, '\n', lines);
   for(int i = 0; i < count; i++)
   {
      string line = FcTrim(lines[i]);
      if(FcUpper(StringSubstr(line, 0, 12)) != "RETRY-AFTER:") continue;
      int seconds = (int)StringToInteger(FcTrim(StringSubstr(line, 12)));
      if(seconds < 900) seconds = 900;
      if(seconds > 172800) seconds = 172800;
      return seconds;
   }
   return 900;
}

bool FcNewsFetch()
{
   datetime now = TimeGMT();
   // Only parameters every plan accepts, including Free Developer.
   string url = FC_NEWS_URL + "?from=" + FcUtcDate(now) + "&to=" + FcUtcDate(now + 6 * 86400)
      + "&impact=" + g_fc_impact + "&limit=" + IntegerToString(g_fc_max_events);
   string headers = "X-API-Key: " + g_fc_key + "\r\nAccept: application/json\r\n";
   char request[];
   char response[];
   string response_headers;
   ArrayResize(request, 0);
   ResetLastError();
   int status = WebRequest("GET", url, headers, 12000, request, response, response_headers);
   // Claim the slot whatever happens, so several charts never repeat a failing request.
   GlobalVariableSet(FcGvName("TRIED"), (double)now);
   if(status == -1)
   {
      FcNewsPause(900, "WebRequest failed (error " + IntegerToString(GetLastError())
         + "). Allow https://www.financecalendar.com under Tools > Options > Expert Advisors. Next try in 15 minutes.");
      return false;
   }
   if(status == 401 || status == 402 || status == 403)
   {
      g_fc_stopped = true;
      g_fc_message = "HTTP " + IntegerToString(status) + ": the API key or plan needs attention at " + FC_NEWS_ACCOUNT
         + " . No more requests until this program is restarted.";
      Print("Finance Calendar: ", g_fc_message);
      return false;
   }
   if(status == 429)
   {
      int wait = FcRetryAfterSeconds(response_headers);
      FcNewsPause(wait, "Allowance reached (HTTP 429). Next request in about " + IntegerToString(wait / 60)
         + " minutes. Check your allowance at " + FC_NEWS_ACCOUNT);
      return false;
   }
   int size = ArraySize(response);
   if(status != 200 || size <= 0 || size > FC_NEWS_MAX_BYTES)
   {
      FcNewsPause(900, "Unexpected answer (HTTP " + IntegerToString(status) + "). Next try in 15 minutes.");
      return false;
   }
   string body = CharArrayToString(response, 0, size, CP_UTF8);
   string raw;
   if(FcJsonTop(body, "notice", raw) && StringGetCharacter(raw, 0) == '{')
   {
      g_fc_stopped = true;
      g_fc_message = "The API answered with a notice instead of data: an API key is needed. Get one at " + FC_NEWS_ACCOUNT;
      Print("Finance Calendar: ", g_fc_message);
      return false;
   }
   if(!FcNewsParse(body, now))
   {
      FcNewsPause(900, "The answer was not a schedule. Next try in 15 minutes.");
      return false;
   }
   // Terminal-local MQL4/Files or MQL5/Files sandbox. Schedule only; the key is never saved.
   int file = FileOpen(FcFileName(), FILE_WRITE | FILE_BIN);
   if(file != INVALID_HANDLE)
   {
      uint written = FileWriteArray(file, response, 0, size);
      FileClose(file);
      if(written == (uint)size) GlobalVariableSet(FcGvName("FETCHED"), (double)now);
      else FileDelete(FcFileName());
   }
   g_fc_message = "Schedule loaded: " + IntegerToString(g_fc_count) + " releases";
   return true;
}

//--- public functions ---------------------------------------------------------------

// Call once from OnInit. impact: "high", or "high,medium". refresh_minutes: 15 or more.
// max_events: 20 on Free Developer; paid plans accept up to 500.
bool FcNewsInit(const string api_key, const string impact = "high", const int refresh_minutes = 180, const int max_events = 20)
{
   g_fc_key = FcTrim(api_key);
   string levels = impact;
   StringToLower(levels);
   StringReplace(levels, " ", "");
   if(levels != "high" && levels != "high,medium" && levels != "high,medium,low" && levels != "medium" && levels != "medium,low" && levels != "low")
      levels = "high";
   g_fc_impact = levels;
   g_fc_refresh_min = (refresh_minutes < 15) ? 15 : refresh_minutes;
   g_fc_max_events = (max_events < 1) ? 1 : ((max_events > 500) ? 500 : max_events);
   g_fc_stopped = false;
   g_fc_count = 0;
   g_fc_loaded_utc = 0;
   ArrayResize(g_fc_events, 0);
   if(!FcNewsValidKey(g_fc_key))
   {
      g_fc_stopped = true;
      g_fc_message = "Enter your Finance Calendar API key. Free Developer and paid keys: " + FC_NEWS_ACCOUNT;
      Print("Finance Calendar: ", g_fc_message);
      return false;
   }
   g_fc_stop_until = GlobalVariableCheck(FcGvName("STOP")) ? (datetime)GlobalVariableGet(FcGvName("STOP")) : 0;
   g_fc_message = "Waiting for the first schedule";
   FcNewsLoadFile();
   return true;
}

// Call from OnTimer (every 30 to 60 seconds is plenty). Makes a request only when one is due.
void FcNewsRefresh()
{
   if(g_fc_stopped) return;
   // Another chart may have refreshed the shared schedule.
   if(FcNewsLoadFile()) g_fc_message = "Schedule loaded: " + IntegerToString(g_fc_count) + " releases";
   datetime now = TimeGMT();
   if(GlobalVariableCheck(FcGvName("STOP"))) g_fc_stop_until = (datetime)GlobalVariableGet(FcGvName("STOP"));
   if(now < g_fc_stop_until) return;
   datetime tried = GlobalVariableCheck(FcGvName("TRIED")) ? (datetime)GlobalVariableGet(FcGvName("TRIED")) : 0;
   if(tried > 0 && now - tried < g_fc_refresh_min * 60) return;
   FcNewsFetch();
}

// True when a usable schedule is in memory (fetched within the last 26 hours).
bool FcNewsReady()
{
   return g_fc_loaded_utc > 0 && TimeGMT() - g_fc_loaded_utc <= FC_NEWS_STALE_SECS;
}

string FcNewsStatus() { return g_fc_message; }

// Countries whose releases matter for a currency code.
string FcCurrencyCountries(const string currency)
{
   string c = FcUpper(currency);
   if(c == "USD") return "US";
   if(c == "EUR") return "EU,DE";
   if(c == "GBP") return "GB";
   if(c == "JPY") return "JP";
   if(c == "CAD") return "CA";
   if(c == "AUD") return "AU";
   if(c == "NZD") return "NZ";
   if(c == "CHF") return "CH";
   if(c == "CNY" || c == "CNH") return "CN";
   if(c == "INR") return "IN";
   if(c == "KRW") return "KR";
   if(c == "MYR") return "MY";
   if(c == "HKD") return "HK";
   if(c == "NOK") return "NO";
   if(c == "SEK") return "SE";
   return "";
}

// Comma-separated country codes for a symbol, from its base and quote currencies.
// XAUUSD gives US; EURUSD gives EU,DE,US. Empty when neither currency is covered.
string FcSymbolCountries(const string symbol)
{
   string a = FcCurrencyCountries(SymbolInfoString(symbol, SYMBOL_CURRENCY_BASE));
   string b = FcCurrencyCountries(SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT));
   if(a == "" || a == b) return b == "" ? a : b;
   return b == "" ? a : a + "," + b;
}

bool FcCountryListed(const string countries, const string country)
{
   return StringFind("," + countries + ",", "," + country + ",") >= 0;
}

// Is 'symbol' inside the quiet window of a scheduled release right now?
// minutes_before / minutes_after: size of the window around the release time.
// 'reason' receives the release name when the answer is true.
// Releases without a published time are ignored. With no usable schedule the answer is
// false: check FcNewsReady() if you would rather stand aside when the schedule is missing.
bool FcNewsBlocked(const string symbol, const int minutes_before, const int minutes_after, string &reason)
{
   reason = "";
   if(!FcNewsReady()) return false;
   string countries = FcSymbolCountries(symbol);
   if(countries == "") return false;
   datetime now = TimeGMT();
   for(int i = 0; i < g_fc_count; i++)
   {
      if(g_fc_events[i].when_utc == 0 || !FcCountryListed(countries, g_fc_events[i].country)) continue;
      if(now >= g_fc_events[i].when_utc - minutes_before * 60 && now <= g_fc_events[i].when_utc + minutes_after * 60)
      {
         reason = g_fc_events[i].name;
         return true;
      }
   }
   return false;
}

// The next scheduled release for 'symbol'. False when none is in the loaded schedule.
bool FcNewsNext(const string symbol, datetime &when_utc, string &name)
{
   when_utc = 0;
   name = "";
   if(!FcNewsReady()) return false;
   string countries = FcSymbolCountries(symbol);
   datetime now = TimeGMT();
   for(int i = 0; i < g_fc_count; i++)
   {
      if(g_fc_events[i].when_utc <= now || !FcCountryListed(countries, g_fc_events[i].country)) continue;
      if(when_utc == 0 || g_fc_events[i].when_utc < when_utc)
      {
         when_utc = g_fc_events[i].when_utc;
         name = g_fc_events[i].name;
      }
   }
   return when_utc > 0;
}
