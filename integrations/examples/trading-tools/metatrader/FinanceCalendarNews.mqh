//+------------------------------------------------------------------+
//| FinanceCalendarNews.mqh                                          |
//| Economic-release news filter for MetaTrader 4 and 5.             |
//| Data: Finance Calendar API, https://www.financecalendar.com/api/ |
//+------------------------------------------------------------------+
// Release 0.2.0. See README for the exact compile/runtime acceptance evidence.
// Downloads scheduled releases and computes configurable news windows. No order operations.
// Allow https://www.financecalendar.com in Tools > Options > Expert Advisors.
// Run as an Expert Advisor or script; WebRequest is unavailable in indicators/Strategy Tester.
// Defaults use paid API access: yesterday through today+6, 500 rows, refresh every 3 hours.
// All charts using the same key/settings share a private terminal-local cache.
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
   string   date;
   string   last_verified_at;
   bool     uncertain;
   bool     freshness_unknown;
   string   uncertainty;
};

enum FcNewsWindowState { FC_NEWS_UNKNOWN = -1, FC_NEWS_CLEAR = 0, FC_NEWS_QUIET = 1 };

FcNewsEvent g_fc_events[];
int      g_fc_count        = 0;
datetime g_fc_loaded_utc   = 0;     // when the schedule in memory was fetched
datetime g_fc_stop_until   = 0;     // no request before this UTC time
bool     g_fc_stopped      = false; // access problem: no further requests until restart
string   g_fc_key          = "";
string   g_fc_impact       = "high";
int      g_fc_refresh_min  = 180;
int      g_fc_max_events   = 500;
bool     g_fc_complete     = false;
datetime g_fc_from_utc     = 0;
datetime g_fc_until_utc    = 0;
string   g_fc_scope        = "";
string   g_fc_quality      = "No usable schedule";
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

// Partition shared files/coordination by key and settings. The two non-credential
// identifiers below keep key material out of file names, globals and diagnostics.
string FcCacheScope(const string key)
{
   uint a = 2166136261, b = 5381;
   for(int i = 0; i < StringLen(key); i++)
   {
      a = (a ^ (uint)StringGetCharacter(key, i)) * 16777619;
      b = (b * 33) ^ (uint)StringGetCharacter(key, StringLen(key) - i - 1);
   }
   return IntegerToString((long)a) + "-" + IntegerToString((long)b);
}
string FcGvName(const string what) { return "FCN2_" + what + "_" + g_fc_scope + "_" + g_fc_impact + "_" + IntegerToString(g_fc_max_events); }
string FcFileName() { return "FinanceCalendarNews-v2-" + g_fc_scope + "-" + g_fc_impact + "-" + IntegerToString(g_fc_max_events) + ".json"; }

//--- minimal JSON reading -----------------------------------------------------------
// Only what the schedule needs: top-level fields of an object, and the items of an array.

int FcJsonSkipSpace(const string &text, int i)
{
   int n = StringLen(text);
   while(i < n && StringGetCharacter(text, i) <= ' ') i++;
   return i;
}

bool FcJsonDigit(const ushort c) { return c >= '0' && c <= '9'; }
bool FcJsonHex(const ushort c) { return FcJsonDigit(c) || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'); }

int FcJsonStringEnd(const string &text, const int start)
{
   int n = StringLen(text);
   if(start >= n || StringGetCharacter(text, start) != '"') return -1;
   for(int i = start + 1; i < n; i++)
   {
      ushort c = StringGetCharacter(text, i);
      if(c < 32) return -1;
      if(c == '"') return i;
      if(c == '\\')
      {
         if(++i >= n) return -1;
         c = StringGetCharacter(text, i);
         if(c == 'u')
         {
            for(int j = 0; j < 4; j++) if(++i >= n || !FcJsonHex(StringGetCharacter(text, i))) return -1;
         }
         else if(c != '"' && c != '\\' && c != '/' && c != 'b' && c != 'f' && c != 'n' && c != 'r' && c != 't') return -1;
      }
   }
   return -1;
}

// Strict recursive JSON scanner. A truncated suffix, malformed scalar, mismatched
// bracket or trailing comma must never turn into a usable empty schedule.
int FcJsonValueEnd(const string &text, const int start, const int depth = 0)
{
   int n = StringLen(text);
   if(start >= n || depth > 24) return -1;
   ushort first = StringGetCharacter(text, start);
   if(first == '"') { int stop = FcJsonStringEnd(text, start); return stop < 0 ? -1 : stop + 1; }
   if(first == '{' || first == '[')
   {
      ushort close = first == '{' ? '}' : ']';
      int i = FcJsonSkipSpace(text, start + 1);
      if(i < n && StringGetCharacter(text, i) == close) return i + 1;
      while(i < n)
      {
         if(first == '{')
         {
            int key_end = FcJsonStringEnd(text, i);
            if(key_end < 0) return -1;
            i = FcJsonSkipSpace(text, key_end + 1);
            if(i >= n || StringGetCharacter(text, i) != ':') return -1;
            i = FcJsonSkipSpace(text, i + 1);
         }
         i = FcJsonValueEnd(text, i, depth + 1);
         if(i < 0) return -1;
         i = FcJsonSkipSpace(text, i);
         if(i >= n) return -1;
         if(StringGetCharacter(text, i) == close) return i + 1;
         if(StringGetCharacter(text, i) != ',') return -1;
         i = FcJsonSkipSpace(text, i + 1);
         if(i >= n || StringGetCharacter(text, i) == close) return -1;
      }
      return -1;
   }
   for(int k = 0; k < 3; k++)
   {
      string literal = k == 0 ? "true" : (k == 1 ? "false" : "null");
      if(StringSubstr(text, start, StringLen(literal)) == literal) return start + StringLen(literal);
   }
   int i = start;
   if(StringGetCharacter(text, i) == '-') i++;
   if(i >= n || !FcJsonDigit(StringGetCharacter(text, i))) return -1;
   if(StringGetCharacter(text, i) == '0') i++;
   else while(i < n && FcJsonDigit(StringGetCharacter(text, i))) i++;
   if(i < n && StringGetCharacter(text, i) == '.')
   {
      i++;
      if(i >= n || !FcJsonDigit(StringGetCharacter(text, i))) return -1;
      while(i < n && FcJsonDigit(StringGetCharacter(text, i))) i++;
   }
   if(i < n && (StringGetCharacter(text, i) == 'e' || StringGetCharacter(text, i) == 'E'))
   {
      i++;
      if(i < n && (StringGetCharacter(text, i) == '+' || StringGetCharacter(text, i) == '-')) i++;
      if(i >= n || !FcJsonDigit(StringGetCharacter(text, i))) return -1;
      while(i < n && FcJsonDigit(StringGetCharacter(text, i))) i++;
   }
   return i;
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

// Strict UTC timestamp; invalid days, offsets and date-only values remain unknown.
datetime FcParseUtc(const string iso)
{
   int n = StringLen(iso);
   if(n != 20 && n != 25) return 0;
   if(StringSubstr(iso, 19) != "Z" && StringSubstr(iso, 19) != "+00:00") return 0;
   if(StringSubstr(iso, 4, 1) != "-" || StringSubstr(iso, 7, 1) != "-" || StringSubstr(iso, 10, 1) != "T"
      || StringSubstr(iso, 13, 1) != ":" || StringSubstr(iso, 16, 1) != ":") return 0;
   for(int i = 0; i < 19; i++)
   {
      if(i == 4 || i == 7 || i == 10 || i == 13 || i == 16) continue;
      if(!FcJsonDigit(StringGetCharacter(iso, i))) return 0;
   }
   string value = StringSubstr(iso, 0, 10) + " " + StringSubstr(iso, 11, 8);
   StringReplace(value, "-", ".");
   datetime out = StringToTime(value);
   return TimeToString(out, TIME_DATE | TIME_MINUTES | TIME_SECONDS) == value ? out : 0;
}
datetime FcParseDate(const string date) { return StringLen(date) == 10 ? FcParseUtc(date + "T00:00:00Z") : 0; }
bool FcJsonInteger(const string raw)
{
   if(StringLen(raw) < 1 || StringLen(raw) > 7) return false;
   for(int i = 0; i < StringLen(raw); i++) if(!FcJsonDigit(StringGetCharacter(raw, i))) return false;
   return StringLen(raw) == 1 || StringSubstr(raw, 0, 1) != "0";
}

// Only commit a fully parsed response. A failed refresh invalidates readiness;
// retained rows are never advertised as a fresh fallback.
bool FcNewsParse(const string &body, const datetime fetched_utc)
{
   g_fc_complete = false;
   g_fc_quality = "The API response is not a complete calendar";
   int root = FcJsonSkipSpace(body, 0), root_end = FcJsonValueEnd(body, root);
   if(root_end < 0 || FcJsonSkipSpace(body, root_end) != StringLen(body) || StringGetCharacter(body, root) != '{') return false;
   string raw, events, raw_count, raw_total;
   if(FcJsonTop(body, "notice", raw) || (FcJsonTop(body, "data_included", raw) && raw == "false")) return false;
   if(!FcJsonTop(body, "count", raw_count) || !FcJsonInteger(raw_count) || !FcJsonTop(body, "total", raw_total) || !FcJsonInteger(raw_total)) return false;
   datetime from = FcJsonTop(body, "from", raw) ? FcParseDate(FcJsonText(raw)) : 0;
   datetime to = FcJsonTop(body, "to", raw) ? FcParseDate(FcJsonText(raw)) : 0;
   if(from == 0 || to < from || to - from > 92 * 86400) return false;
   if(!FcJsonTop(body, "events", events) || StringGetCharacter(events, 0) != '[') return false;
   int n = StringLen(events), i = 1, count = 0, rows = 0;
   bool incomplete = StringToInteger(raw_total) > StringToInteger(raw_count) || FcJsonTop(body, "free_developer", raw);
   if(FcJsonTop(body, "truncated", raw))
   {
      if(raw != "true" && raw != "false") return false;
      if(raw == "true") incomplete = true;
   }
   FcNewsEvent parsed[];
   while(i < n)
   {
      i = FcJsonSkipSpace(events, i);
      if(StringGetCharacter(events, i) == ']') break;
      if(StringGetCharacter(events, i) != '{') return false;
      int stop = FcJsonValueEnd(events, i);
      if(stop < 0) return false;
      string item = StringSubstr(events, i, stop - i);
      rows++;
      if(rows > 500) return false;
      if(FcJsonTop(item, "notice", raw)) return false;
      string status = FcJsonTop(item, "status", raw) ? FcJsonText(raw) : "";
      string country = FcJsonTop(item, "country", raw) ? FcJsonText(raw) : "";
      string category = FcJsonTop(item, "category", raw) ? FcJsonText(raw) : "";
      bool unrelated_crypto = category == "crypto" || category == "crypto-events";
      if(status == "notice" || (!unrelated_crypto && (StringLen(country) != 2 || FcUpper(country) != country))) return false;
      if(status != "cancelled" && !unrelated_crypto)
      {
         ArrayResize(parsed, count + 1, 64);
         parsed[count].country = country;
         parsed[count].impact = FcJsonTop(item, "impact", raw) ? FcJsonText(raw) : "";
         parsed[count].name = FcJsonTop(item, "name", raw) ? FcJsonText(raw) : "";
         if(parsed[count].name == "" && FcJsonTop(item, "title", raw)) parsed[count].name = FcJsonText(raw);
         parsed[count].date = FcJsonTop(item, "date", raw) ? FcJsonText(raw) : "";
         parsed[count].when_utc = FcJsonTop(item, "release_at_utc", raw) ? FcParseUtc(FcJsonText(raw)) : 0;
         parsed[count].last_verified_at = FcJsonTop(item, "last_verified_at", raw) ? FcJsonText(raw) : "";
         string precision = FcJsonTop(item, "time_precision", raw) ? FcJsonText(raw) : "";
         bool fresh = FcJsonTop(item, "data_stale", raw) && raw == "false";
         bool timed = parsed[count].when_utc > 0 && (precision == "minute" || precision == "second" || precision == "exact" || precision == "instant");
         bool confirmed = status == "confirmed" || status == "rescheduled" || status == "released";
         parsed[count].freshness_unknown = !fresh;
         parsed[count].uncertain = !fresh || !timed || !confirmed;
         parsed[count].uncertainty = !fresh ? "Source freshness is stale or unavailable" : (!timed ? "The release time is unknown or imprecise" : (!confirmed ? "The release schedule is estimated" : ""));
         if(FcParseDate(parsed[count].date) == 0) { parsed[count].uncertain = true; parsed[count].uncertainty = "The release date is unavailable"; }
         count++;
      }
      i = FcJsonSkipSpace(events, stop);
      if(StringGetCharacter(events, i) == ',') i++;
      else if(StringGetCharacter(events, i) != ']') return false;
   }
   if(rows != (int)StringToInteger(raw_count) || StringToInteger(raw_total) < rows) return false;
   ArrayResize(g_fc_events, count);
   for(int k = 0; k < count; k++) g_fc_events[k] = parsed[k];
   g_fc_count = count;
   g_fc_loaded_utc = fetched_utc;
   g_fc_from_utc = from;
   g_fc_until_utc = to + 86400;
   g_fc_complete = !incomplete;
   g_fc_quality = incomplete ? "The calendar is truncated; increase the event limit or narrow the query" : "";
   return true;
}

bool FcNewsSharedInvalid()
{
   return (GlobalVariableCheck(FcGvName("FAILED")) && GlobalVariableGet(FcGvName("FAILED")) > 0)
      || (GlobalVariableCheck(FcGvName("LATEST")) && GlobalVariableGet(FcGvName("LATEST")) > (double)g_fc_loaded_utc);
}
bool FcNewsSharedStopped()
{
   return GlobalVariableCheck(FcGvName("ACCESS")) && GlobalVariableGet(FcGvName("ACCESS")) > 0;
}

bool FcNewsLoadFile()
{
   if(FcNewsSharedStopped()) { g_fc_stopped = true; g_fc_complete = false; return false; }
   if(GlobalVariableCheck(FcGvName("FAILED")) && GlobalVariableGet(FcGvName("FAILED")) > 0) { g_fc_complete = false; return false; }
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

datetime FcHttpDate(const string text)
{
   // Standard IMF-fixdate: Tue, 17 Nov 2026 13:30:00 GMT.
   if(StringLen(text) != 29 || StringSubstr(text, 3, 2) != ", " || StringSubstr(text, 25) != " GMT") return 0;
   string months = "JanFebMarAprMayJunJulAugSepOctNovDec";
   int month_at = StringFind(months, StringSubstr(text, 8, 3));
   if(month_at < 0 || month_at % 3 != 0) return 0;
   string month = IntegerToString(month_at / 3 + 1);
   if(StringLen(month) == 1) month = "0" + month;
   return FcParseUtc(StringSubstr(text, 12, 4) + "-" + month + "-" + StringSubstr(text, 5, 2) + "T" + StringSubstr(text, 17, 8) + "Z");
}
int FcRetryAfterSeconds(const string headers)
{
   string lines[];
   int count = StringSplit(headers, '\n', lines);
   for(int i = 0; i < count; i++)
   {
      string line = FcTrim(lines[i]);
      if(FcUpper(StringSubstr(line, 0, 12)) != "RETRY-AFTER:") continue;
      string value = FcTrim(StringSubstr(line, 12));
      bool numeric = StringLen(value) > 0;
      for(int j = 0; j < StringLen(value); j++) if(!FcJsonDigit(StringGetCharacter(value, j))) numeric = false;
      long seconds = 900;
      if(numeric)
      {
         if(StringLen(value) > 10) return -1;
         seconds = StringToInteger(value);
      }
      else
      {
         datetime at = FcHttpDate(value);
         if(at > 0) seconds = (long)(at - TimeGMT());
      }
      if(seconds > 2147483647) return -1; // manual review; never shorten a server-directed delay
      return seconds < 900 ? 900 : (int)seconds;
   }
   return 900;
}

bool FcNewsFetch()
{
   datetime now = TimeGMT();
   g_fc_complete = false;
   GlobalVariableSet(FcGvName("FAILED"), (double)now);
   g_fc_quality = "The latest calendar refresh did not succeed";
   // Paid calendar window includes yesterday so after-release windows survive UTC midnight.
   string url = FC_NEWS_URL + "?from=" + FcUtcDate(now - 86400) + "&to=" + FcUtcDate(now + 6 * 86400)
      + "&country=US,EU,DE,GB,JP,CA,AU,NZ,CH,CN,IN,KR,MY,HK,NO,SE&impact=" + g_fc_impact + "&limit=" + IntegerToString(g_fc_max_events);
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
      GlobalVariableSet(FcGvName("ACCESS"), (double)now);
      g_fc_message = "HTTP " + IntegerToString(status) + ": the API key or plan needs attention at " + FC_NEWS_ACCOUNT
         + " . Requests stopped; repair the account/key and explicitly resume.";
      Print("Finance Calendar: ", g_fc_message);
      return false;
   }
   if(status == 429)
   {
      int wait = FcRetryAfterSeconds(response_headers);
      if(wait < 0)
      {
         g_fc_stopped = true;
         GlobalVariableSet(FcGvName("ACCESS"), (double)now);
         g_fc_message = "Retry-After requires manual review; requests stopped";
         return false;
      }
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
      GlobalVariableSet(FcGvName("ACCESS"), (double)now);
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
   GlobalVariableSet(FcGvName("LATEST"), (double)now);
   GlobalVariableSet(FcGvName("FAILED"), 0.0);
   g_fc_message = "Schedule loaded: " + IntegerToString(g_fc_count) + " releases";
   return true;
}

//--- public functions ---------------------------------------------------------------

// Call once from OnInit. impact: "high", or "high,medium". refresh_minutes: 15 or more.
// Paid plan required for yesterday and up to 500 records. Check live plans for allowances.
bool FcNewsInit(const string api_key, const string impact = "high", const int refresh_minutes = 180, const int max_events = 500)
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
   g_fc_scope = FcCacheScope(g_fc_key);
   g_fc_stopped = FcNewsSharedStopped();
   g_fc_complete = false;
   g_fc_quality = "No usable schedule";
   g_fc_count = 0;
   g_fc_loaded_utc = 0;
   ArrayResize(g_fc_events, 0);
   if(!FcNewsValidKey(g_fc_key))
   {
      g_fc_stopped = true;
      g_fc_message = "Enter your paid Finance Calendar API key: " + FC_NEWS_ACCOUNT;
      Print("Finance Calendar: ", g_fc_message);
      return false;
   }
   g_fc_stop_until = GlobalVariableCheck(FcGvName("STOP")) ? (datetime)GlobalVariableGet(FcGvName("STOP")) : 0;
   g_fc_message = "Waiting for the first schedule";
   FcNewsLoadFile();
   return true;
}

// After repairing a 401/402/403 account/key issue, call once explicitly, then
// refresh. This clears only this key/settings access stop, never Retry-After.
void FcNewsResumeAfterAccessFix()
{
   GlobalVariableSet(FcGvName("ACCESS"), 0.0);
   GlobalVariableSet(FcGvName("TRIED"), 0.0);
   g_fc_stopped = false;
   g_fc_complete = false;
}

// Call from OnTimer (every 30 to 60 seconds is plenty). Makes a request only when one is due.
void FcNewsRefresh()
{
   if(g_fc_stopped || FcNewsSharedStopped()) { g_fc_stopped = true; g_fc_complete = false; return; }
   // Another chart may have refreshed the shared schedule.
   if(FcNewsLoadFile()) g_fc_message = "Schedule loaded: " + IntegerToString(g_fc_count) + " releases";
   datetime now = TimeGMT();
   if(GlobalVariableCheck(FcGvName("STOP"))) g_fc_stop_until = (datetime)GlobalVariableGet(FcGvName("STOP"));
   if(now < g_fc_stop_until) return;
   datetime tried = GlobalVariableCheck(FcGvName("TRIED")) ? (datetime)GlobalVariableGet(FcGvName("TRIED")) : 0;
   bool retrying = GlobalVariableCheck(FcGvName("FAILED")) && GlobalVariableGet(FcGvName("FAILED")) > 0;
   if(!retrying && tried > 0 && now - tried < g_fc_refresh_min * 60) return;
   // Atomic terminal-wide lease: simultaneous cold charts share one request.
   string lock = FcGvName("LOCK");
   GlobalVariableTemp(lock);
   double lease = GlobalVariableGet(lock);
   if(lease > (double)now || !GlobalVariableSetOnCondition(lock, (double)(now + 60), lease)) return;
   // Recheck after acquiring: a peer may have fetched since our first check.
   tried = GlobalVariableCheck(FcGvName("TRIED")) ? (datetime)GlobalVariableGet(FcGvName("TRIED")) : 0;
   retrying = GlobalVariableCheck(FcGvName("FAILED")) && GlobalVariableGet(FcGvName("FAILED")) > 0;
   datetime current_stop = GlobalVariableCheck(FcGvName("STOP")) ? (datetime)GlobalVariableGet(FcGvName("STOP")) : 0;
   if(TimeGMT() < current_stop || FcNewsSharedStopped() || (!retrying && tried > 0 && now - tried < g_fc_refresh_min * 60))
   { GlobalVariableSetOnCondition(lock, 0.0, (double)(now + 60)); return; }
   GlobalVariableSet(FcGvName("TRIED"), (double)now);
   FcNewsFetch();
   GlobalVariableSetOnCondition(lock, 0.0, (double)(now + 60));
}

// Readiness means a fully parsed, untruncated, recently fetched calendar. Each
// symbol can still be unknown because of source freshness or imprecise release times.
bool FcNewsReady()
{
   datetime now = TimeGMT();
   return !g_fc_stopped && !FcNewsSharedStopped() && !FcNewsSharedInvalid() && g_fc_complete && g_fc_loaded_utc > 0 && now >= g_fc_loaded_utc
      && now - g_fc_loaded_utc <= FC_NEWS_STALE_SECS && now >= g_fc_from_utc && now < g_fc_until_utc;
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
   string base = FcUpper(SymbolInfoString(symbol, SYMBOL_CURRENCY_BASE));
   string quote = FcUpper(SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT));
   // Explicit six-letter names also work for offline fixtures. Broker prefixes and
   // suffixes rely on broker currency metadata, never substring guesses.
   string normalized = FcUpper(symbol);
   StringReplace(normalized, "/", "");
   if(base == "" && quote == "" && StringLen(normalized) == 6)
   { base = StringSubstr(normalized, 0, 3); quote = StringSubstr(normalized, 3, 3); }
   string a = FcCurrencyCountries(base), b = FcCurrencyCountries(quote);
   if(base == "XAU" && b != "") return b;
   if(a == "" || b == "") return "";
   return a == b ? a : a + "," + b;
}

bool FcCountryListed(const string countries, const string country)
{
   return StringFind("," + countries + ",", "," + country + ",") >= 0;
}

// Explicit clock/country seam used by the native fixture harness as well as
// the live symbol wrapper. It performs no network calls and no order operations.
int FcNewsStateAt(const string countries, const datetime now, const int minutes_before, const int minutes_after, string &reason)
{
   reason = "";
   if(countries == "") { reason = "This symbol has no supported currency mapping"; return FC_NEWS_UNKNOWN; }
   if(minutes_before < 0 || minutes_after < 0 || minutes_before > 1440 || minutes_after > 1440)
   { reason = "News windows must be between 0 and 1440 minutes"; return FC_NEWS_UNKNOWN; }
   if(g_fc_stopped || FcNewsSharedStopped() || FcNewsSharedInvalid() || !g_fc_complete || g_fc_loaded_utc <= 0 || now < g_fc_loaded_utc || now - g_fc_loaded_utc > FC_NEWS_STALE_SECS)
   { reason = g_fc_quality != "" ? g_fc_quality : "No current complete calendar is loaded"; return FC_NEWS_UNKNOWN; }
   if(now - minutes_after * 60 < g_fc_from_utc || now + minutes_before * 60 >= g_fc_until_utc)
   { reason = "The configured window extends beyond the loaded calendar dates"; return FC_NEWS_UNKNOWN; }
   string uncertainty = "";
   for(int i = 0; i < g_fc_count; i++)
   {
      if(!FcCountryListed(countries, g_fc_events[i].country)) continue;
      if(g_fc_events[i].uncertain)
      {
         datetime day = FcParseDate(g_fc_events[i].date);
         if(g_fc_events[i].freshness_unknown || day == 0
            || (now + minutes_before * 60 >= day - 86400 && now - minutes_after * 60 < day + 2 * 86400))
            // Publisher dates are local. Pad by a day on each side rather than
            // invent an IANA-zone conversion or miss Tokyo/Sydney date boundaries.
            uncertainty = g_fc_events[i].uncertainty + ": " + g_fc_events[i].name;
         continue;
      }
      if(now >= g_fc_events[i].when_utc - minutes_before * 60 && now <= g_fc_events[i].when_utc + minutes_after * 60)
      { reason = g_fc_events[i].name; return FC_NEWS_QUIET; }
   }
   if(uncertainty != "") { reason = uncertainty; return FC_NEWS_UNKNOWN; }
   return FC_NEWS_CLEAR;
}

// 1=inside the configured news window, 0=outside it, -1=unknown.
// Outside the window is a schedule state, not a trading recommendation.
int FcNewsState(const string symbol, const int minutes_before, const int minutes_after, string &reason)
{
   return FcNewsStateAt(FcSymbolCountries(symbol), TimeGMT(), minutes_before, minutes_after, reason);
}

// Conservative compatibility: unknown blocks entry as well as a quiet window.
// Call FcNewsState() to distinguish why the Boolean is true.
bool FcNewsBlocked(const string symbol, const int minutes_before, const int minutes_after, string &reason)
{
   return FcNewsState(symbol, minutes_before, minutes_after, reason) != FC_NEWS_CLEAR;
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
      if(g_fc_events[i].uncertain || g_fc_events[i].when_utc <= now || !FcCountryListed(countries, g_fc_events[i].country)) continue;
      if(when_utc == 0 || g_fc_events[i].when_utc < when_utc)
      {
         when_utc = g_fc_events[i].when_utc;
         name = g_fc_events[i].name;
      }
   }
   return when_utc > 0;
}
