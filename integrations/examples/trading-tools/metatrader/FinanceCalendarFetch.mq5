#property strict
#property script_show_inputs
// Manual download example. Source reviewed; not compiled with MetaEditor here.
// Add https://www.financecalendar.com to Tools > Options > Expert Advisors
// > Allow WebRequest for listed URL. Run as a script, not an indicator/tester.
input string InputAPIKey = "";

string UTCDate(datetime when)
{
   string value = TimeToString(when, TIME_DATE);
   StringReplace(value, ".", "-");
   return value;
}

bool ValidKey(string key)
{
   if(StringLen(key) != 40 || StringSubstr(key, 0, 8) != "fc_live_") return false;
   for(int i = 8; i < 40; i++)
   {
      ushort c = StringGetCharacter(key, i);
      if(!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
   }
   return true;
}

string RetryAfter(string headers)
{
   string lines[];
   int count = StringSplit(headers, '\n', lines);
   for(int i = 0; i < count; i++)
   {
      string line = lines[i];
      string lower = line;
      StringToLower(lower);
      if(StringFind(lower, "retry-after:") != 0) continue;
      string value = StringSubstr(line, 12);
      StringTrimLeft(value);
      StringTrimRight(value);
      // Only this standard response field is displayed; never log all headers.
      if(StringLen(value) > 80) return "present: inspect allowance before rerunning";
      return value;
   }
   return "absent: wait at least 15 minutes and inspect your allowance";
}

void OnStart()
{
   if(!ValidKey(InputAPIKey))
   {
      Print("Set InputAPIKey locally. Get a key: https://www.financecalendar.com/account/");
      return;
   }
   datetime now = TimeGMT();
   string url = "https://www.financecalendar.com/wp-json/fc/v1/calendar?from="
      + UTCDate(now) + "&to=" + UTCDate(now + 6 * 86400)
      + "&impact=high&status=confirmed%2Cestimated%2Crescheduled&limit=500&offset=0";
   string headers = "X-API-Key: " + InputAPIKey + "\r\nAccept: application/json\r\n";
   char request[];
   char response[];
   string response_headers;
   ArrayResize(request, 0);
   ResetLastError();
   // Official seven-argument custom-header overload in MQL4 and MQL5.
   int status = WebRequest("GET", url, headers, 12000, request, response, response_headers);
   if(status == -1)
   {
      Print("WebRequest failed. Error ", GetLastError(),
         ". Check connection and the https://www.financecalendar.com URL allowlist.");
      return;
   }
   if(status == 401 || status == 402 || status == 403)
   {
      Print("HTTP ", status, ": stop. Check key/account: https://www.financecalendar.com/account/");
      return;
   }
   if(status == 429)
   {
      Print("HTTP 429. Retry-After: ", RetryAfter(response_headers),
         ". No automatic retry. Do not rerun before that delay.");
      return;
   }
   if(status != 200)
   {
      Print("HTTP ", status, ": request stopped; no response body logged.");
      return;
   }
   int size = ArraySize(response);
   if(size <= 0 || size > 4 * 1024 * 1024)
   {
      Print("Response was empty or exceeded the 4 MiB file bound; nothing saved.");
      return;
   }
   // Terminal-local MQL4/Files or MQL5/Files sandbox; never save the API key.
   // This demonstrates one page only: inspect count/total before using the data.
   int file = FileOpen("FinanceCalendar-calendar.json", FILE_WRITE | FILE_BIN);
   if(file == INVALID_HANDLE)
   {
      Print("Could not open the terminal-local calendar file. Error ", GetLastError());
      return;
   }
   uint written = FileWriteArray(file, response, 0, size);
   FileClose(file);
   if(written != (uint)size)
   {
      FileDelete("FinanceCalendar-calendar.json");
      Print("Incomplete file removed; request stopped.");
      return;
   }
   Print("Saved ", size, " bytes to terminal Files/FinanceCalendar-calendar.json. ",
      "Single-page JSON: retain attribution/source_rights and inspect count/total. No orders placed.");
}
