# Finance Calendar API

Build release watchlists, compare recorded consensus forecasts with published results, and query economic schedules as JSON, CSV and ICS. Paid plans support **release forecasts for 60 mapped headline measures across 10 economies**. Available values appear in the `forecasts` field, refreshed hourly and labelled with their update time and source count. Coverage varies by release; the mapped total is not the number with a live forecast at any moment. Provider consensus spans **12 selected US headline release series**, alongside source-linked actual/prior values. The calendar also covers central bank decisions, selected crypto events and exchange holidays. Records retain their metric, reference period, source verification, timing precision and freshness metadata. Snapshot builds run hourly; source freshness is reported separately.

## Affordable API access

The [public economic calendar is free to browse](https://www.financecalendar.com/events/). Start with Starter for recorded forecasts, results and integration tools. A secondary ongoing Free Developer option supplies schedule JSON:

| Plan | Price | Shared account allowance | Included access |
|---|---|---|---|
| Starter | **US$9.99/year**, paid yearly | **1,000 requests/UTC day; 25,000/UTC calendar month** | REST, MCP, CLI, Python, Data explorer and filtered CSV/JSON exports |
| Build | **US$9.99/month** or **US$95.90/year** | **100,000 requests/UTC day** | Higher API capacity and the same recorded fields and tools |
| Scale | **US$29/month** or **US$278.40/year** | **1,000,000 requests/UTC day** | Complete current dataset JSON download and larger integrations |
| Free Developer | **US$0, ongoing** | **100 successful JSON responses/UTC month; at most 10/UTC day** | Schedule-only `/calendar` and `/today`, 7 UTC dates, 20 records, one key |

Prices include applicable tax. Paid plans renew at the selected interval until cancelled; access continues to the end of the paid period. Existing contracts and effective account allowances are preserved. [Compare current plans](https://www.financecalendar.com/pricing/) or [choose Starter](https://www.financecalendar.com/account/?plan=starter&billing_interval=year). Creating an account does not charge you.

Starter, Build and Scale can power customer-facing websites and apps, including paid products, within plan limits and applicable source terms. Free Developer also permits personal or customer-facing projects within its limited schedule scope; its data and capacity limits define the upgrade path.

### What each plan includes

<!-- fc-plan-comparison:start -->
| Feature | Free Developer | Starter | Build | Scale |
| --- | --- | --- | --- | --- |
| Price | US$0; No card | US$9.99/year | US$9.99/month; or US$95.90/year | US$29.00/month; or US$278.40/year |
| Requests / UTC day | 10 | 1,000 | 100,000 | 1,000,000 |
| Requests / UTC month | 100 | 25,000 | No monthly cap | No monthly cap |
| Calendar records / response | Up to 20; No pagination | Up to 500; With pagination | Up to 500; With pagination | Up to 500; With pagination |
| Release schedules | Today through +6; UTC | Full calendar | Full calendar | Full calendar |
| Calendar categories | Economic releases; and central banks | All categories | All categories | All categories |
| Release forecasts | No | Yes | Yes | Yes |
| Consensus, prior and actual | No | Yes | Yes | Yes |
| Release history | No | Yes | Yes | Yes |
| Change feed and webhooks | No | Yes | Yes | Yes |
| Formats | JSON | JSON, CSV, ICS | JSON, CSV, ICS | JSON, CSV, ICS |
| REST, CLI and Python | Yes | Yes | Yes | Yes |
| Hosted MCP and Data explorer | No | Yes | Yes | Yes |
| Complete dataset download | No | No | No | Yes |
| Customer-facing apps | Yes | Yes | Yes | Yes |

Price: Annual prices are charged upfront. Paid plans renew at the selected interval until cancelled. Applicable tax included.

Requests / UTC month: Free Developer counts successful schedule JSON responses. Paid plans count admitted requests; linked keys share the account allowance.

Calendar records / response: Record limits and pagination apply to calendar list responses; other routes use their documented limits.

Release schedules: Dates, times and status. Paid date ranges follow the current snapshot coverage.

Calendar categories: Paid categories include central bank speeches, exchange holidays and selected crypto events.

Release forecasts: Forecast coverage maps 60 headline measures across 10 economies. A forecast appears when a matched pre-release value is available; coverage varies by release.

Consensus, prior and actual: Schedule rows mark figures available on paid plans. Recorded figures vary by series and release; missing values stay null.

Release history: Retained release records and curated datasets vary by series; see coverage for their date ranges.

Change feed and webhooks: Signed webhooks notify your integration when calendar updates are published.

REST, CLI and Python: Free Developer uses /calendar and /today through REST and local clients. Routes and response fields follow the active plan.

Complete dataset download: Scale includes the complete current snapshot as one JSON download.

Customer-facing apps: Personal and customer-facing products are allowed within each plan’s scope, request limits and applicable source terms. Retain Finance Calendar attribution and publisher credits.
<!-- fc-plan-comparison:end -->

This comparison is generated from the canonical offer with `python3 scripts/sync-plan-comparison.py`; run it with `--check` to reject drift. Prices and limits are the current offer at the time of writing. The [machine-readable offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) and the [pricing page](https://www.financecalendar.com/pricing/#plan-comparison) are always current.

### Inspect a public sample

Read the response fields, recorded values and source credits before registering:

```sh
curl --fail-with-body "https://www.financecalendar.com/wp-json/fc/v1/sample"
```

The public sample contains at most three publisher-selected records. It is a fixed technical example, with no arbitrary filters, dates, pagination or full export. It does not grant ongoing production API access. [Sample guide](https://www.financecalendar.com/api/sample/) · [Machine-readable offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer)

### Ongoing Free Developer schedules

[Free Developer](https://www.financecalendar.com/account/?free=1) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one active key, no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit consensus, actual/prior figures and numerical evidence; Starter adds these recorded fields, wider dates/history, formats, hosted MCP and browser tools.

Already-enrolled evaluations retain their original 25-successful-request budget, 48-hour clock from first use and original scope. New trial enrolment is closed. Existing paid, legacy and custom access grants are preserved; no account is silently converted to Free Developer.

Keep your key private, then make an authenticated request:

```sh
curl --fail-with-body \
  -H "X-API-Key: $FC_API_KEY" \
  "https://www.financecalendar.com/wp-json/fc/v1/calendar?limit=10"
```

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

The API and [tested beta client downloads](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-history-2026-11-14) accept a configured API key. These archives include authenticated setup, historical archive traversal and the current pricing/access guide. npm/PyPI registry publication remains pending.

Programmatic data access requires a verified account and API key. Choose Starter for richer recorded data and tools or explicitly enrol in Free Developer for the bounded schedule scope above. Public sample, product-offer and OpenAPI routes are separate inspection resources. Creating an account does not charge you. Anonymous `POST /keys` creation remains unavailable.

Starter costs **US$9.99/year** and includes **1,000 requests per UTC day and 25,000 per UTC calendar month**. Build includes **100,000 requests per day** and Scale **1,000,000 per day**. All account keys share the applicable allowance. Daily usage resets at 00:00 UTC; monthly usage resets at 00:00 UTC on the first day of the next calendar month. Existing paid customers retain their contracted prices and applicable allowances; check your account or `/keys/me` for effective limits. See [current plans](https://www.financecalendar.com/pricing/) for billing options and complete snapshot downloads.

Free Developer counts successful committed HTTP 200 JSON responses, including valid empty results. Invalid/denied requests, quota errors and pre-commit failures do not count. Its account ledger survives key rotation, with UTC day/month resets. `GET /keys/me` is uncounted and reports a distinct `free_developer` usage object. Existing enrolled trials keep their separate original budgets and clocks.

For paid plans, daily and monthly quota usage counts admitted requests, not successful responses. Requests refused with HTTP 429 do not consume more allowance; a request that passes the quota check can still consume allowance if it later returns an error. Retained per-key request history remains a separate attempt diagnostic and can include rejected requests.

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
key in private client settings. Hosted MCP requires paid access or an applicable retained grant. A custom local wrapper can use Free Developer’s permitted REST routes; installing a wrapper does not expand scope. Hosted data calls consume the same account
allowance as direct REST; protocol initialization/discovery validates the key
without consuming a data request. There is no shared anonymous MCP allowance.

Compatible Claude, ChatGPT and other Streamable HTTP clients can use OAuth
account linking. Sign in on financecalendar.com and approve read-only
`calendar:read` access; optional `offline_access` permits token renewal. Revoke
access in [connected-assistant settings](https://www.financecalendar.com/?fc_oauth_connections=1).
Header-capable clients can use their own API-key or bearer header instead. The
[local stdio server](clients/node/README.md) reads `FC_API_KEY`.
[Setup and full reference](https://www.financecalendar.com/api/mcp/). Platform
policies and directory listings remain separate from endpoint support.

## Quick start

The examples below use paid-plan routes and formats. For Free Developer, use the authenticated JSON calendar example above.

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

This table describes paid-plan capabilities. Free Developer is limited to schedule-only JSON `/calendar` and `/today` within the 100/month, 10/day allowance and seven-date window above. It excludes figures, market status, holidays, crypto, history and the other data routes.

| Endpoint | What it returns |
|---|---|
| `GET /calendar` | Events in a date range (max 92 days): `from`, `to`, `country`, `impact`, `category`, `asset`, `series`, `status`, `include=holidays`, `tz`, `limit`, `offset`, `format=json\|csv\|ics` |
| `GET /today` | Today's releases, live NYSE status and any exchange closures |
| `GET /week` | This week or next (`which=next`) |
| `GET /next` | Next occurrence of a series (`series=fomc`, `cpi`, `uk-cpi`, `japan-gdp`...; `country=` override) |
| `GET /series` | Every series with code, aliases, country, tier and next date |
| `GET /series/{code}` | One series: next, last, upcoming, history, verified dataset where published |
| `GET /history` | Past releases of a series, with consensus, prior and actual where available |
| `GET /history/observations` | Exact archived observations by measured reference-period start date; paginated, source-linked and version pinned |
| `GET /history/releases` | Evidenced dated publications; original values and clocks remain null when unknown |
| `GET /history/coverage` | Actual per-source/metric counts and period bounds; paginated |
| `GET /holidays` | Exchange holidays and early closes for 12 exchanges (`exchange=nyse\|sifma\|cme\|lse\|tsx\|asx\|hkex\|euronext\|jpx\|six\|xetra\|nse\|all`) |
| `GET /market-status` | Is the exchange open right now (session, breaks, early closes, holidays) |
| `GET /changes` | Lossless cursor-paginated change log for the last 30 days (`since=`, `limit=`, `cursor=`); restart the original checkpoint on snapshot-change HTTP 409 |
| `GET /countries` | Countries covered with counts |
| `GET /status` | Snapshot age/counts and publisher-source health |
| `GET /keys/me` | Key and shared-account usage; create keys in your verified account |
| `GET /account/full-export` | Complete current JSON dataset; active Scale subscription and Scale API key header required |

Missing or invalid keys return HTTP 401; revoked keys or disallowed accounts return 403. Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`. Send credentials in headers rather than URLs, and do not expose them in browser code.

## Key usage

`GET /keys/me` requires an active key and is uncounted. Free Developer returns `{ "free_developer": { ... } }` with UTC daily/monthly successful-response usage and its schedule window. An already-enrolled evaluation key returns a distinct `{ "trial": { ... } }` usage object with its 25-request total budget, first-use clock and expiry; the status request does not start the clock or consume a data request. Paid and retained keys keep the existing flat `KeyUsage` response described below, available even after the daily cap. `used_today` and `retained_requests` count rate-gate attempts, including 429 responses. `usage_window` explicitly covers 90 UTC dates including today; lifetime `requests_total` is null because the legacy counter was cache-throttled and is not reliable as a request total. `legacy_activity_samples` is diagnostic only. Successful origin responses are a separate metric. [Complete usage fields](https://www.financecalendar.com/api/reference/#schema-keyusage).

Keys created or linked in your [verified account](https://www.financecalendar.com/account/) share one daily account allowance. For those keys, `quota_scope: "account"`, `used_today` and `remaining_today` cover every account key, including revoked keys. `key_used_today` describes the presented key; `retained_requests_scope: "key"` keeps retained history per key. Key rotation does not reset usage. Data responses include `X-RateLimit-Scope: account`. Existing unclaimed keys keep their previous per-key limits.

## Historical economic data

Explore long-run inflation, employment and growth observations alongside evidenced
publication dates. Paid API access includes the separate historical archive;
[check measured coverage](https://www.financecalendar.com/api/coverage/) and start
with `GET /history/coverage` to choose an exact metric and available period.

The initial official-source roster contains 21 metrics from BLS, ONS, ECB,
Eurostat, Statistics Canada and ABS. Many observation series extend into 2006;
coverage and latest periods vary. Dated ONS publication records are supplied
separately, with values left unknown when an original result was not collected.
Use the [history guide](docs/history.md) for the measured definitions, paging,
source credits and complete export examples.

- `GET /history/observations`: exact decimal values by measured reference-period
  start date; `metric_id` or `series_code` required.
- `GET /history/releases`: evidenced publication records by publisher release
  date, with unknown clocks and results preserved as null.
- `GET /history/coverage`: paginated counts and actual earliest/latest periods
  for each source, metric and record kind.

Repeat the original filters and limit with `next_cursor` to retrieve every page.
A changed archive revision returns 409; discard the partial export and restart.
`as_of` selects evidence held by Finance Calendar by its server receipt bound;
it does not turn a newly imported historical value into knowledge FC held years
ago. Current-vintage backfills are labelled and do not establish original prints
or historical forecast cutoffs.

[Python and CLI downloads](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-history-2026-11-14)
include archive methods and complete traversal. The Node package adds three local
stdio MCP tools. The hosted MCP tool catalogue is unchanged; call these archive
routes through REST, Python, the CLI or local MCP.

## Examples

- [`examples/python.py`](examples/python.py)
- [`examples/javascript.js`](examples/javascript.js)
- [`examples/google-sheets.md`](examples/google-sheets.md)
- [`examples/curl.md`](examples/curl.md)
- [`widget/`](widget/): server-side integration guidance; the legacy anonymous embed is retired

## Numerical evidence

Release forecast coverage maps 60 headline measures across the US, UK, euro area, Germany, Canada, Australia, New Zealand, Japan, Switzerland and China: inflation, jobs, GDP, retail sales, business surveys and central bank rate decisions, with separate forecasts for headline and core measures. A forecast appears when a matched pre-release market value is available. Each is a Finance Calendar blend of market forecasts, frozen at release time, with its `as_of` time and `source_families` count. See the [coverage guide](https://www.financecalendar.com/api/coverage/#release-forecasts).

Provider consensus coverage spans **12 selected US headline release series**: US headline CPI, nonfarm payrolls, PPI, retail sales, PCE, ISM Manufacturing, industrial production, Conference Board Consumer Confidence, JOLTS, ADP employment, ISM Services PMI and goods-and-services Trade Balance. Actual and prior values combine validated official observations with matched provider data; validated official values retain precedence. Compare values with their metric, reference period, unit and source evidence. The existing `/calendar`, `/history` and series endpoints return the expanded records without new request paths.

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
