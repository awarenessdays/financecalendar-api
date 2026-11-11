# curl cheat sheet

[Free API access](https://www.financecalendar.com/account/?trial=1) includes **48 hours from your first successful data request and 25 successful requests in total**, with verified email, one API key and no card required. It returns JSON from `/calendar`, `/today` and `/week`, up to 10 economic releases or central bank decisions per response, from the previous seven days through the next two days in UTC. Real consensus, actual and prior values are included where recorded; missing values remain `null`. The allowance does not renew. Other routes, formats and wider access require a paid plan.

Starter is **US$9.99/year** for **1,000 requests per UTC day and 25,000 per UTC calendar month**; Build includes **100,000/day** and Scale **1,000,000/day**. Account keys share their paid allowance. Check [current plans](https://www.financecalendar.com/pricing/) and your account for effective prices and limits.

Set `FC_API_KEY` privately and keep it out of URLs. This first request works within free access:

```sh
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "https://www.financecalendar.com/wp-json/fc/v1/calendar?limit=10"
```

The following wider-date, non-calendar and export examples require the corresponding paid plan:

```bash
export FC_API_KEY='fc_live_YOUR_ACTUAL_KEY'
B=https://www.financecalendar.com/wp-json/fc/v1

curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=fomc"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=cpi&country=uk"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/today"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/week?which=next&impact=high"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/calendar?from=2026-11-01&to=2026-11-30&country=US,EU&tz=Europe/Berlin"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/calendar?series=fomc,ecb,boe&format=ics" -o central-banks.ics
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/series?country=jp"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/series/us-nfp"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/history?series=us-cpi&limit=24"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/holidays?exchange=hkex&year=2027"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/market-status?exchange=lse"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/changes?since=2026-10-18T00:00:00Z"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/countries"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/status"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/openapi"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/keys/me"

# Complete snapshot file: active Scale subscription required.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/account/full-export" -o financecalendar-full.json
```

ICS downloads require the same header. A calendar application that cannot attach
an API-key header cannot subscribe through the anonymous URLs shown in older guides.
Do not work around that by exposing a secret in a subscription URL. A server you
control can fetch authenticated data and publish an appropriately restricted feed.

Use the [Data explorer](https://www.financecalendar.com/data/) for browser research
and matching/selected CSV or JSON exports. It is included with active
Starter, Build and Scale subscriptions and uses a verified account session rather than an API key. Finite free API access does not include the Data explorer.
