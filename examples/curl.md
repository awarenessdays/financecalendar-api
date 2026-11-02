# curl cheat sheet

Create and verify a [Free account](https://www.financecalendar.com/account/?mode=register),
then create an API key in your workspace. Every API request requires a valid key,
including status and OpenAPI. Set your real key privately; never put it in a URL.
New Free accounts include 1,000 daily requests, Pro 100,000 and Business 1,000,000,
shared across account keys. Existing accounts and keys retain their effective allowance.

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

# Complete snapshot file: active Business subscription required.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/account/full-export" -o financecalendar-full.json
```

ICS downloads require the same header. A calendar application that cannot attach
an API-key header cannot subscribe through the anonymous URLs shown in older guides.
Do not work around that by exposing a secret in a subscription URL. A server you
control can fetch authenticated data and publish an appropriately restricted feed.

Use the [Data explorer](https://www.financecalendar.com/data/) for browser research
and matching/selected CSV or JSON exports. It is included with every verified
Free, Pro or Business account and does not require an API key or payment.
