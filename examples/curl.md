# curl cheat sheet

```bash
B=https://www.financecalendar.com/wp-json/fc/v1

curl "$B/next?series=fomc"                      # next Fed decision
curl "$B/next?series=cpi&country=uk"            # next UK CPI (or series=uk-cpi)
curl "$B/today"                                 # today + NYSE status + closures
curl "$B/week?which=next&impact=high"           # next week's big releases
curl "$B/calendar?from=2026-11-01&to=2026-11-30&country=US,EU&tz=Europe/Berlin"
curl "$B/calendar?series=fomc,ecb,boe&format=ics" -o central-banks.ics
curl "$B/series?country=jp"                     # every Japanese series
curl "$B/series/us-nfp"                         # NFP: next, last, upcoming, history
curl "$B/history?series=us-cpi&limit=24"        # two years of CPI prints
curl "$B/holidays?exchange=hkex&year=2027"
curl "$B/market-status?exchange=lse"
curl "$B/changes?since=2026-10-18T00:00:00Z"    # what moved since yesterday
curl "$B/countries"
curl "$B/status"

# Free key (10,000/day)
curl -X POST "$B/keys" -H "Content-Type: application/json" -d '{"email":"you@example.com","use_case":"trading dashboard"}'
curl "$B/keys/me" -H "X-API-Key: fc_live_..."
```
