# curl cheat sheet

[Paid API plans](https://www.financecalendar.com/pricing/) start at **US$9.99/year** for Starter (**1,000 requests/UTC day and 25,000/UTC calendar month**). Build is **US$9.99/month or US$95.90/year** for **100,000/day**. Scale is **US$29/month or US$278.40/year** for **1,000,000/day** and the complete current dataset download. [Inspect the public sample](https://www.financecalendar.com/api/sample/) before choosing a plan.

[Free Developer](https://www.financecalendar.com/account/?free=1) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one active key, no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit consensus, actual/prior figures and numerical evidence; Starter adds these recorded fields, wider dates/history, formats, hosted MCP and browser tools.

Starter is **US$9.99/year** for **1,000 requests per UTC day and 25,000 per UTC calendar month**; Build includes **100,000/day** and Scale **1,000,000/day**. Account keys share their paid allowance. Check [current plans](https://www.financecalendar.com/pricing/) and your account for effective prices and limits.

Set `FC_API_KEY` privately and keep it out of URLs. This first request works within Free Developer scope:

```sh
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "https://www.financecalendar.com/wp-json/fc/v1/calendar?limit=10"

# Today’s UTC schedule is also within Free Developer scope.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "https://www.financecalendar.com/wp-json/fc/v1/today"

# Inspect account usage without consuming a schedule allowance.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "https://www.financecalendar.com/wp-json/fc/v1/keys/me"

# The OpenAPI contract is public and requires no key.
curl --fail-with-body "https://www.financecalendar.com/wp-json/fc/v1/openapi"
```

The following wider-date, non-calendar and export examples require the corresponding paid plan:

```bash
export FC_API_KEY='fc_live_YOUR_ACTUAL_KEY'
B=https://www.financecalendar.com/wp-json/fc/v1

curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=fomc"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=cpi&country=uk"
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

# Complete snapshot file: active Scale subscription required.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/account/full-export" -o financecalendar-full.json
```

ICS downloads require the same header. A calendar application that cannot attach
an API-key header cannot subscribe through the anonymous URLs shown in older guides.
Do not work around that by exposing a secret in a subscription URL. A server you
control can fetch authenticated data and publish an appropriately restricted feed.

Use the [Data explorer](https://www.financecalendar.com/data/) for browser research
and matching/selected CSV or JSON exports. It is included with active
Starter, Build and Scale subscriptions and uses a verified account session rather than an API key. Free Developer does not include the Data explorer.

## Historical observations and publication dates

The new archive includes one year on Starter, ten years on Build and all
available history on Scale. Existing `/history` and curated rights are unchanged.
These archive routes have independent measured coverage. Start with coverage, then follow every `next_cursor` using identical filters and limit:

```sh
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/history/coverage?metric_id=gb-cpi-all-items-yoy&limit=100"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/history/observations?metric_id=gb-cpi-all-items-yoy&limit=100"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/history/releases?metric_id=gb-gdp-monthly-mom-sa&limit=100"
```

Observations filter measured reference-period starts; releases filter publisher
dates. A changed revision returns 409: discard the partial export and restart.
Current-vintage history does not imply original prints or old forecast cutoffs.
See the [complete history workflow](../docs/history.md).
