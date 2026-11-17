// The same MQL fixture cases run in MetaTrader and the offline C++ stand-in.
int g_fixture_checks = 0;
int g_fixture_failed = 0;
string g_fixture_failures = "";
void FcFixtureCheck(const bool ok, const string name)
{
   g_fixture_checks++;
   if(!ok) { g_fixture_failed++; g_fixture_failures += name + "; "; Print("FAILED: ", name); }
}
string FcFixtureRow()
{
   return "{\"id\":\"fixture-us\",\"name\":\"US fixture release\",\"country\":\"US\",\"impact\":\"high\",\"date\":\"2026-11-17\",\"release_at_utc\":\"2026-11-17T13:30:00Z\",\"time_precision\":\"minute\",\"data_stale\":false,\"last_verified_at\":\"2026-11-17T12:00:00Z\",\"status\":\"confirmed\",\"actual\":0,\"consensus\":null}";
}
string FcFixtureCalendar(const string events, const int count = 1, const int total = 1)
{
   return "{\"from\":\"2026-11-16\",\"to\":\"2026-11-23\",\"count\":" + IntegerToString(count)
      + ",\"total\":" + IntegerToString(total) + ",\"events\":[" + events + "]}";
}
void FcFixtureRun()
{
   g_fixture_checks = 0; g_fixture_failed = 0; g_fixture_failures = "";
   datetime now = FcParseUtc("2026-11-17T13:00:00Z");
   g_fc_stopped = false;
   string row = FcFixtureRow(), body = FcFixtureCalendar(row), reason;
   FcFixtureCheck(FcParseUtc("2026-11-17T13:30:42+00:00") == FcParseUtc("2026-11-17T13:30:42Z"), "UTC offsets and seconds");
   FcFixtureCheck(FcParseUtc("2026-11-17T00:00:00Z") > 0, "midnight is a real timestamp");
   FcFixtureCheck(FcParseUtc("2026-02-30T13:30:00Z") == 0 && FcParseUtc("2026-11-17T25:00:00Z") == 0, "invalid date/hour rejected");
   FcFixtureCheck(FcParseUtc("2026-11-17") == 0 && FcParseUtc("2026-11-17T13:30:00+01:00") == 0, "date-only/non-UTC not invented");
   FcFixtureCheck(FcNewsParse(body, now - 60), "valid paid JSON with numeric zero and null");
   FcFixtureCheck(FcNewsStateAt("EU,DE,US", now - 1, 30, 30, reason) == FC_NEWS_CLEAR, "31 seconds outside boundary");
   FcFixtureCheck(FcNewsStateAt("EU,DE,US", now, 30, 30, reason) == FC_NEWS_QUIET && reason == "US fixture release", "inclusive before boundary");
   FcFixtureCheck(FcNewsStateAt("US", now + 3600, 30, 30, reason) == FC_NEWS_QUIET, "inclusive after boundary");
   FcFixtureCheck(FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_CLEAR, "one second after boundary");
   FcFixtureCheck(FcNewsStateAt("GB,JP", now, 30, 30, reason) == FC_NEWS_CLEAR, "both pair legs filtered");
   FcFixtureCheck(FcNewsStateAt("", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "unsupported symbol is unknown");
   FcFixtureCheck(FcNewsStateAt("US", now, -1, 30, reason) == FC_NEWS_UNKNOWN && FcNewsStateAt("US", now, 30, 1441, reason) == FC_NEWS_UNKNOWN, "invalid window is unknown");
   FcFixtureCheck(FcNewsStateAt("US", now + FC_NEWS_STALE_SECS, 30, 30, reason) == FC_NEWS_UNKNOWN, "old local fetch unknown");
   FcFixtureCheck(FcNewsStateAt("US", now - 120, 30, 30, reason) == FC_NEWS_UNKNOWN, "future local fetch unknown");
   FcFixtureCheck(FcNewsStateAt("US", FcParseDate("2026-11-16"), 30, 30, reason) == FC_NEWS_UNKNOWN, "window outside queried dates unknown");
   body = FcFixtureCalendar(row, 1, 2);
   FcFixtureCheck(FcNewsParse(body, now) && !g_fc_complete && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "truncated count never clear");
   body = FcFixtureCalendar(row); StringReplace(body, "\"events\":", "\"truncated\":true,\"events\":");
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "explicit truncation never clear");
   body = FcFixtureCalendar(row, 0, 0);
   FcFixtureCheck(!FcNewsParse(body, now), "count mismatch invalid");
   body = FcFixtureCalendar("", 0, 0);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_CLEAR, "explicit complete empty calendar");
   row = FcFixtureRow(); StringReplace(row, "\"data_stale\":false", "\"data_stale\":true"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "stale source unknown");
   FcFixtureCheck(FcNewsStateAt("GB,JP", now, 30, 30, reason) == FC_NEWS_CLEAR, "unrelated stale source does not affect pair");
   row = FcFixtureRow(); StringReplace(row, "\"data_stale\":false,", ""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "unavailable source freshness unknown");
   row = FcFixtureRow(); StringReplace(row, "\"minute\"", "\"date\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "date-only precision does not invent time");
   row = FcFixtureRow(); StringReplace(row, "\"2026-11-17T13:30:00Z\"", "null"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "missing clock makes current day unknown");
   row = FcFixtureRow(); StringReplace(row, "\"2026-11-17\"", "\"2026-11-20\""); StringReplace(row, "\"2026-11-17T13:30:00Z\"", "null"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_CLEAR, "future date-only release does not block today");
   row = FcFixtureRow(); StringReplace(row, "\"confirmed\"", "\"estimated\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "estimated schedule unknown");
   row = FcFixtureRow(); StringReplace(row, "\"confirmed\"", "\"cancelled\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && g_fc_count == 0 && FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_CLEAR, "cancelled release excluded");
   row = FcFixtureRow(); StringReplace(row, "\"confirmed\"", "\"released\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 2100, 30, 30, reason) == FC_NEWS_QUIET, "released event retains after window");
   row = FcFixtureRow(); StringReplace(row, "\"name\":\"US fixture release\"", "\"source\":{\"name\":\"Wrong nested title\"},\"name\":\"US fixture release\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && g_fc_events[0].name == "US fixture release", "nested fields do not replace event fields");
   body = FcFixtureCalendar(FcFixtureRow());
   string bad_body = StringSubstr(body, 0, StringLen(body) - 1);
   FcFixtureCheck(!FcNewsParse(bad_body, now), "truncated root rejected");
   bad_body = body + "garbage";
   FcFixtureCheck(!FcNewsParse(bad_body, now), "trailing garbage rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"data_stale\":false", "\"data_stale\":falsehood");
   FcFixtureCheck(!FcNewsParse(body, now), "malformed scalar rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"actual\":0", "\"actual\":01");
   FcFixtureCheck(!FcNewsParse(body, now), "invalid leading zero rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"actual\":0", "\"actual\":0,");
   FcFixtureCheck(!FcNewsParse(body, now), "consecutive comma rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"actual\":0", "\"actual\":\"bad\\x\"");
   FcFixtureCheck(!FcNewsParse(body, now), "invalid string escape rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"events\":[", "\"notice\":{},\"events\":[");
   FcFixtureCheck(!FcNewsParse(body, now), "key-required notice rejected");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"country\":\"US\"", "\"country\":null");
   FcFixtureCheck(!FcNewsParse(body, now), "missing country invalidates response");
   FcFixtureCheck(FcNewsStateAt("US", now, 30, 30, reason) == FC_NEWS_UNKNOWN, "parse failures invalidate readiness");
   row = FcFixtureRow(); StringReplace(row, "\"country\":\"US\"", "\"country\":\"JP\""); StringReplace(row, "\"2026-11-17\"", "\"2026-11-18\""); StringReplace(row, "\"2026-11-17T13:30:00Z\"", "null"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("JP", FcParseUtc("2026-11-17T16:00:00Z"), 30, 30, reason) == FC_NEWS_UNKNOWN, "publisher day may already be tomorrow in Tokyo");
   row = FcFixtureRow(); StringReplace(row, "\"country\":\"US\"", "\"country\":null,\"category\":\"crypto\""); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && g_fc_count == 0, "clearly unrelated countryless crypto excluded");
   body = FcFixtureCalendar(FcFixtureRow()); StringReplace(body, "\"events\":[", "\"free_developer\":{},\"events\":[");
   FcFixtureCheck(FcNewsParse(body, now) && !g_fc_complete, "schedule-only Free response cannot claim paid completeness");
   row = FcFixtureRow(); StringReplace(row, "\"2026-11-17T12:00:00Z\"", "null"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_UNKNOWN, "editorial row without verification is unknown even with stale=false");
   row = FcFixtureRow(); StringReplace(row, "2026-11-17T12:00:00Z", "2026-11-17T14:00:00Z"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_UNKNOWN, "future verification clock is unknown");
   row = FcFixtureRow(); StringReplace(row, "2026-11-17T12:00:00Z", "2026-11-17T12:00:00.164125+00:00"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_CLEAR, "real API microsecond verification clock accepted");
   row = FcFixtureRow(); StringReplace(row, "2026-11-17T12:00:00Z", "2026-11-17T13:00:00.000001Z"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_UNKNOWN, "future subsecond verification is not truncated into current evidence");
   row = FcFixtureRow(); StringReplace(row, "2026-11-17T12:00:00Z", "2026-11-17T13:00:00.000000Z"); body = FcFixtureCalendar(row);
   FcFixtureCheck(FcNewsParse(body, now) && FcNewsStateAt("US", now + 3601, 30, 30, reason) == FC_NEWS_CLEAR, "exact equal zero-fraction verification accepted");
   body = FcFixtureCalendar(FcFixtureRow());
   datetime interior = FcParseDate("2026-11-17");
   FcNewsParse(body, interior - 60);
   FcFixtureCheck(FcNewsStateAt("GB", interior + 1799, 30, 30, reason) == FC_NEWS_UNKNOWN, "publisher-local query dates require an interior UTC lower bound");
   FcFixtureCheck(FcNewsStateAt("GB", interior + 1800, 30, 30, reason) == FC_NEWS_CLEAR, "exact interior UTC coverage boundary is included");
   // Restore a useful fixture for adapter/timer checks.
   body = FcFixtureCalendar(FcFixtureRow()); FcNewsParse(body, now - 60);
}
