# Finance Calendar API

Build release watchlists, compare recorded consensus forecasts with published results, and query economic schedules as JSON, CSV and ICS. Provider consensus now spans **12 selected US headline release series**, alongside source-linked actual/prior values. The calendar also covers central bank decisions, selected crypto events and exchange holidays. Records retain their metric, reference period, source verification, timing precision and freshness metadata. Snapshot builds run hourly; source freshness is reported separately.

- **Docs:** https://www.financecalendar.com/api/
- **Base URL:** `https://www.financecalendar.com/wp-json/fc/v1`
- **OpenAPI 3.1:** [`openapi.json`](openapi.json) (also served live at `/openapi`)
- **Full dataset export:** [Scale account download](https://www.financecalendar.com/account/#fc-account-full-export). Active Scale subscription required; full snapshots and capture history are not distributed in this source repository.
- **ChatGPT and Claude connector:** [Hosted MCP setup](https://www.financecalendar.com/api/mcp/) — authenticated HTTPS for clients supporting API-key headers.
- **Codex and Claude Code:** [Plugin and portable Agent Skill](integrations/README.md)
- **MCP server and CLI:** [Node source and installation](clients/node/README.md)
- **Python client and CLI:** [Python source and installation](clients/python/README.md)
- **Trading tools and bots:** [Runnable Python/Node watchlists and a MetaTrader source example](integrations/examples/trading-tools/README.md)
- **Measured coverage:** https://www.financecalendar.com/api/coverage/

The API and [tested beta client downloads](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-2026-11-03) accept a configured API key. The existing archives are unchanged; use current source for the updated setup and missing-key errors. npm/PyPI registry publication remains pending.

The [public calendar is free to browse](https://www.financecalendar.com/events/). Programmatic API access requires an active paid plan and API key, including status and OpenAPI. [Choose a plan](https://www.financecalendar.com/pricing/), register and verify your email, complete payment, then create a key in your workspace. Creating an account does not charge you. Anonymous `POST /keys` creation is retired.

Starter costs **US$9.99/year** and includes **1,000 requests per UTC day and 25,000 per UTC calendar month**. Build includes **100,000 requests per day** and Scale **1,000,000 per day**. All account keys share the applicable allowance. Daily usage resets at 00:00 UTC; monthly usage resets at 00:00 UTC on the first day of the next calendar month. Existing paid customers retain their contracted prices and applicable allowances; check your account or `/keys/me` for effective limits. See [current plans](https://www.financecalendar.com/pricing/) for billing options and complete snapshot downloads.

Daily and monthly quota usage counts admitted requests, not successful responses. Requests refused with HTTP 429 do not consume more allowance; a request that passes the quota check can still consume allowance if it later returns an error. Retained per-key request history remains a separate attempt diagnostic and can include rejected requests.

The [Data explorer](https://www.financecalendar.com/data/) provides search/filter,
saved views, source evidence and matching/selected CSV or JSON exports within its
displayed limits. It uses your verified account sign-in rather than an API key.
Active Starter, Build and Scale subscriptions include the Data explorer. Complete current snapshot downloads require Scale. See [current plans](https://www.financecalendar.com/pricing/) for billing options and allowances.

## Hosted connector

Use Streamable HTTP with your own key on **every** request:

```text
https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
X-API-Key: fc_live_YOUR_ACTUAL_KEY
```

`Authorization: Bearer fc_live_YOUR_ACTUAL_KEY` is also accepted. Use an actual
key in private client settings. Hosted data calls consume the same account
allowance as direct REST; protocol initialization/discovery validates the key
without consuming a data request. There is no shared anonymous MCP allowance.

The server does not implement OAuth. Use a header-capable MCP client; a platform
that only offers no authentication or OAuth cannot use this hosted setup. The
[local stdio server](clients/node/README.md) accepts `FC_API_KEY` instead.
[Setup and full reference](https://www.financecalendar.com/api/mcp/). Existing
platform smoke results predate this authentication change and do not establish
current ChatGPT or Claude.ai account-level setup or directory approval.

## Quick start

```bash
export FC_API_KEY='fc_live_YOUR_ACTUAL_KEY'
B=https://www.financecalendar.com/wp-json/fc/v1

# Next Fed decision
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=fomc"

# Next UK CPI release
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/next?series=uk-cpi"

# High-impact releases in London time
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/calendar?impact=high&tz=Europe/London"

# This week as CSV; ICS downloads require the same credential header.
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/week?format=csv" -o week.csv

# What changed in the retained window
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" "$B/changes"

```

## Endpoints

| Endpoint | What it returns |
|---|---|
| `GET /calendar` | Events in a date range (max 92 days): `from`, `to`, `country`, `impact`, `category`, `asset`, `series`, `status`, `include=holidays`, `tz`, `limit`, `offset`, `format=json\|csv\|ics` |
| `GET /today` | Today's releases, live NYSE status and any exchange closures |
| `GET /week` | This week or next (`which=next`) |
| `GET /next` | Next occurrence of a series (`series=fomc`, `cpi`, `uk-cpi`, `japan-gdp`...; `country=` override) |
| `GET /series` | Every series with code, aliases, country, tier and next date |
| `GET /series/{code}` | One series: next, last, upcoming, history, verified dataset where published |
| `GET /history` | Past releases of a series, with consensus, prior and actual where available |
| `GET /holidays` | Exchange holidays and early closes for 12 exchanges (`exchange=nyse\|sifma\|cme\|lse\|tsx\|asx\|hkex\|euronext\|jpx\|six\|xetra\|nse\|all`) |
| `GET /market-status` | Is the exchange open right now (session, breaks, early closes, holidays) |
| `GET /changes` | Lossless cursor-paginated change log for the last 30 days (`since=`, `limit=`, `cursor=`); restart the original checkpoint on snapshot-change HTTP 409 |
| `GET /countries` | Countries covered with counts |
| `GET /status` | Snapshot age/counts and publisher-source health |
| `GET /keys/me` | Key and shared-account usage; create keys in your verified account |
| `GET /account/full-export` | Complete current JSON dataset; active Scale subscription and Scale API key header required |

Missing or invalid keys return HTTP 401; revoked keys or disallowed accounts return 403. Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`. Send credentials in headers rather than URLs, and do not expose them in browser code.

## Key usage

`GET /keys/me` requires an active key and is uncounted, even after the daily cap. `used_today` and `retained_requests` count rate-gate attempts, including 429 responses. `usage_window` explicitly covers 90 UTC dates including today; lifetime `requests_total` is null because the legacy counter was cache-throttled and is not reliable as a request total. `legacy_activity_samples` is diagnostic only. Successful origin responses are a separate metric. [Complete usage fields](https://www.financecalendar.com/api/reference/#schema-keyusage).

Keys created or linked in your [verified account](https://www.financecalendar.com/account/) share one daily account allowance. For those keys, `quota_scope: "account"`, `used_today` and `remaining_today` cover every account key, including revoked keys. `key_used_today` describes the presented key; `retained_requests_scope: "key"` keeps retained history per key. Key rotation does not reset usage. Data responses include `X-RateLimit-Scope: account`. Existing unclaimed keys keep their previous per-key limits.

## Examples

- [`examples/python.py`](examples/python.py)
- [`examples/javascript.js`](examples/javascript.js)
- [`examples/google-sheets.md`](examples/google-sheets.md)
- [`examples/curl.md`](examples/curl.md)
- [`widget/`](widget/): server-side integration guidance; the legacy anonymous embed is retired

## Numerical evidence

Provider consensus coverage now spans **12 selected US headline release series**: US headline CPI, nonfarm payrolls, PPI, retail sales, PCE, ISM Manufacturing, industrial production, Conference Board Consumer Confidence, JOLTS, ADP employment, ISM Services PMI and goods-and-services Trade Balance. Actual and prior values combine validated official observations with matched provider data; validated official values retain precedence. Compare values with their metric, reference period, unit and source evidence. The existing `/calendar`, `/history` and series endpoints return the expanded records without new request paths.

Check the [current coverage and source evidence](https://www.financecalendar.com/api/coverage/) or authenticated `/quality` report for recorded availability. Preserve `null` when a value has no recorded evidence. BLS payroll values are already in jobs, while `source_value` retains thousands of jobs and the exact conversion factor. Publisher-reported revisions, engine-observed revisions and original first prints are distinct. See the [complete reference](https://www.financecalendar.com/api/reference/) for document manifests and occurrence bindings.

## Data

The complete current JSON export includes the loaded calendar window, series registry, exchange table, source evidence and 30-day change log. Full dataset downloads require an active Scale subscription and are served through the authenticated account or full-export endpoint. This public repository contains developer tools, API schemas and small test fixtures, not full snapshots or their history.

Direct schedule connectors currently read BLS, ONS, BEA, Census, Federal
Reserve G.17, DOL jobless claims, EIA energy releases, Treasury auctions,
Eurostat, Japan e-Stat, China NBS, Malaysia DOSM, Australia ABS, South Korea MODS, Bank of Korea statistics and India MoSPI. Publisher horizons differ; a rolling window does not mean every
source has announced dates through its end. Check `/status` and the coverage page
for current availability.

Event JSON includes `period`, nullable `release_stage`, `source_id`, `native_id`,
`time_precision`, `last_verified_at` and `data_stale`. Nullable
`time_window_start`/`time_window_end` preserve announced publication windows;
`time_role` identifies auction bidding deadlines, and `auction` contains
security identifiers and official results where published. China NBS calendar
dates and pending Treasury announcements retain estimated status. GDP estimates and separate
catch-up periods remain distinct releases. A changed date retains the release's
public ID; last-good data is marked stale when a source is unavailable. Source
verification refers to a calendar fetch, independently of numerical result
availability. Treasury results are imported from the official auctioned-securities
feed. Explicit ONS, DOL and BLS mappings add selected numerical observations with
reference periods, units and source-vintage evidence. Other calendar connectors
add schedules without inventing macro results or consensus.

```python
import json, os, urllib.request
request = urllib.request.Request(
    "https://www.financecalendar.com/wp-json/fc/v1/account/full-export",
    headers={"X-API-Key": os.environ["FC_API_KEY"]},  # active Scale account
)
with urllib.request.urlopen(request, timeout=30) as response:
    cal = json.load(response)
print(cal["generated_at"], cal["counts"])
```

## Terms

Access to complete dataset downloads requires Scale. Reuse of lawfully obtained data remains permitted subject to applicable source terms and credits, with a visible link to https://www.financecalendar.com wherever the data appears (or on your app's credits page). Earnings dates are not included. See [DATA-TERMS.md](DATA-TERMS.md) and the current [API service terms](https://www.financecalendar.com/api/terms/).

## Issues

Wrong date? Missing series? Open an issue here. The engine reads official calendars, so tell us the official source and we will add it.

## Selected crypto events

Use `category=crypto&asset=ethereum` with `/calendar`, `/week` or `/today`.
Discover canonical asset IDs through `/series?category=crypto`; symbols such as
ETH are display labels. Coverage includes selected network upgrades, token unlock
schedules, public DAO voting deadlines and labelled supply projections. A declared
asset or series does not guarantee an upcoming record.

Global crypto has `country=null`; `impact` may be null. Inspect `crypto.event_type`,
source evidence and `verification_method`. Schedules are not proof of observed
activation or token transfer. Month/quarter/year targets retain both
`date_window_start` and `date_window_end`; `date` is their lower-bound index.
Supply projections are not confirmed cliff unlocks; voting deadlines are not
proposal outcomes. Provider-reported evidence remains labelled as such.

Keep `source_license` credits, `attribution_url`, licence links, adaptation notices
and `source_rights` factual-source notices when redistributing records. Licensed
PatternPlus rows require [Data: PatternPlus](https://pattern.plus) linked credit
under CC BY 4.0. A discovery URL is separate from primary verification evidence.
The MIT software licence does not relicense upstream data.

See the [crypto calendar](https://www.financecalendar.com/crypto/) and
[full REST reference](https://www.financecalendar.com/api/reference/).

Korean calendars use `country=KR` and `kr-` series codes. They retain explicit
period/stage identities and raw `source_clock` evidence. Where a clock timezone
has not been independently verified, exact UTC/local time remains null and
`all_day=false`; `release_tz` records calendar jurisdiction, not permission to
convert the raw clock. Check the published horizon and per-source health.

MoSPI dates use `country=IN` and `in-` series codes. Its latest fiscal-year
calendar is discovered from the official manifest. Planned dates remain
estimated; explicitly recorded publication dates take precedence. No holiday
move, publication clock or missing measured period is inferred. Combined GDP
publications retain their original component description and are not a single
headline observation. Source health exposes held reference-year and identity
ambiguities.

## Build a working dashboard

Start with the [economic calendar dashboard example](integrations/examples/economic-calendar-dashboard/README.md): a complete Node backend and responsive browser calendar. Preview the labelled demo without a key, then connect your verified account. Source details, missing-value handling and a shared 30-minute cache are included, along with a prompt for your coding assistant.
