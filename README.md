# Finance Calendar API

Build release watchlists, compare Finance Calendar's consensus with published results, and query economic schedules as JSON, CSV and ICS. **Consensus is Finance Calendar's own record of the market's expected figure**: the middle value across independent sources, recorded before each release and frozen at release time, so a surprise calculated afterwards never moves. Paid plans carry the headline consensus, previous figure and result for **15 selected US headline releases**, including ISM, Conference Board and ADP, with a year of history; the headline consensus for releases in the UK, euro area, Germany, Canada and Australia; and consensus by measure for **60 mapped measures across 10 economies** in the `forecasts` field, labelled with update time and source count. Coverage varies by release; the mapped total is not the number with a live figure at any moment. The calendar also covers central bank decisions, selected crypto events and exchange holidays. Records retain their metric, reference period, source verification, timing precision and freshness metadata. Snapshot builds run hourly; source freshness is reported separately.

Building a **US CPI and FOMC watchlist with an AI agent**? Read the [public recorded sample and briefing](https://www.financecalendar.com/api/sample/) without an account, then use the [agent setup guide](docs/agent-setup.md) to prepare an owner-approved connection to live paid data. An agent that cannot send API requests can offer the [browser preparation page](https://www.financecalendar.com/api/sample/?setup_client=chatgpt#prepare-owner-setup), where a person or browser-capable agent selects **Prepare setup link** to create a genuine owner link.

## Affordable API access

The [public economic calendar is free to browse](https://www.financecalendar.com/events/). Start with Starter for recorded consensus, results and integration tools. A secondary ongoing Free Developer option supplies schedule JSON:

| Plan | Price | Shared account allowance | Included access |
|---|---|---|---|
| Starter | [Live price](https://www.financecalendar.com/pricing/#starter) | **250 requests/UTC day; 5,000/UTC calendar month** | REST, MCP, CLI, Python, Data explorer and filtered CSV/JSON exports |
| Build | **US$9.99/month** or **US$95.90/year** | **100,000 requests/UTC day** | Higher API capacity and the same recorded fields and tools |
| Scale | **US$29/month** or **US$278.40/year** | **1,000,000 requests/UTC day** | Complete current dataset JSON download and larger integrations |
| Free Developer | **US$0, ongoing** | **100 successful JSON responses/UTC month; at most 10/UTC day** | Schedule-only `/calendar` and `/today`, 7 UTC dates, 20 records, one approved API key |

Prices include applicable tax. Paid plans renew at the selected interval until cancelled; access continues to the end of the paid period. Existing contracts and effective account allowances are preserved. [Compare current plans](https://www.financecalendar.com/pricing/) or [choose Starter](https://www.financecalendar.com/account/?plan=starter&billing_interval=year). Creating an account does not charge you.

Starter, Build and Scale can power customer-facing websites and apps, including paid products, within plan limits and applicable source terms. Free Developer also permits personal or customer-facing projects within its limited schedule scope; its data and capacity limits define the upgrade path.

### What each plan includes

<!-- fc-plan-comparison:start -->
| Feature | Free Developer | Starter | Build | Scale |
| --- | --- | --- | --- | --- |
| Price | US$0; No card | [Live price](https://www.financecalendar.com/pricing/#starter) | US$9.99/month; or US$95.90/year | US$29.00/month; or US$278.40/year |
| Requests / UTC day | 10 | 250 | 100,000 | 1,000,000 |
| Requests / UTC month | 100 | 5,000 | No monthly cap | No monthly cap |
| Calendar records / response | Up to 20; No pagination | Up to 500; With pagination | Up to 500; With pagination | Up to 500; With pagination |
| Release schedules | Today through +6; UTC | Full calendar | Full calendar | Full calendar |
| Calendar categories | Economic releases; and central banks | All categories | All categories | All categories |
| Consensus across 10 economies | No | Yes | Yes | Yes |
| Consensus, previous and result | No | Yes | Yes | Yes |
| Release history | No | Yes | Yes | Yes |
| Official observation archive | No | 1 year | 10 years | All available |
| Change feed and webhooks | No | Yes | Yes | Yes |
| News window | No | No | Yes | Yes |
| Market closures by currency | No | No | Yes | Yes |
| Formats | JSON | JSON, CSV, ICS | JSON, CSV, ICS | JSON, CSV, ICS |
| REST, CLI and Python | Yes | Yes | Yes | Yes |
| Hosted MCP and Data explorer | No | Yes | Yes | Yes |
| Complete dataset download | No | No | No | Yes |
| Customer-facing apps | No | No | Yes | Yes |

Price: Annual prices are charged upfront. Paid plans renew at the selected interval until cancelled. Applicable tax included.

Requests / UTC month: Free Developer counts successful schedule JSON responses. Paid plans count admitted requests; linked keys share the account allowance.

Calendar records / response: Record limits and pagination apply to calendar list responses; other routes use their documented limits.

Release schedules: Dates, times and status. Paid date ranges follow the current snapshot coverage.

Calendar categories: Paid categories include central bank speeches, exchange holidays and selected crypto events.

Consensus across 10 economies: Consensus coverage maps 60 measures across the US, UK, euro area, Germany, Canada, Australia, New Zealand, Japan, Switzerland and China. A figure typically appears in the week before a release and is frozen at release time.

Consensus, previous and result: Schedule rows mark figures available on paid plans. The headline consensus, previous figure and result for 15 US releases, with a year of history, and the headline consensus for releases in the UK, euro area, Germany, Canada and Australia.

Release history: Retained release records and curated datasets vary by series; see coverage for their date ranges.

Official observation archive: Plan windows use rolling UTC calendar years. Each measure lists its stored and accessible dates. Existing release history and curated datasets are separate.

Change feed and webhooks: Signed webhooks notify your integration when calendar updates are published.

News window: Build and Scale answer blocked, clear or unknown for a pair and window in one request.

Market closures by currency: Build and Scale group exchange and bond-market closures by currency, with whether there is a closure today.

REST, CLI and Python: Free Developer uses /calendar and /today through REST and local clients. Routes and response fields follow the active plan.

Complete dataset download: Scale includes the complete current snapshot as one JSON download.

Customer-facing apps: Choose Build or Scale to show Finance Calendar data to users of your app, website or service. Free Developer and Starter cover personal use, internal tools and private development. Existing grants continue under their agreed terms. Retain Finance Calendar attribution and publisher credits.
<!-- fc-plan-comparison:end -->

This comparison is generated from the canonical offer with `python3 scripts/sync-plan-comparison.py`; run it with `--check` to reject drift. Consult the [machine-readable offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) and the [pricing page](https://www.financecalendar.com/pricing/#plan-comparison) for the current Starter charge and complete offer.

### Inspect a public sample

Read a published US CPI result and scheduled CPI and FOMC decision examples before registering. The [sample guide](https://www.financecalendar.com/api/sample/) presents the records in HTML with the capture time, event times and official source links. The same fixed records are available as JSON:

```sh
curl --fail-with-body "https://www.financecalendar.com/wp-json/fc/v1/sample"
```

Read `sample.captured_at` before briefing the data: it is a recorded example, not a current watchlist. Use the `completed_release`, `scheduled_release` and `scheduled_decision` roles to distinguish the published result from future schedules. Cite `actual_evidence.edition_url` for the CPI result and each record's `source_url` for its schedule. Keep missing values as `null`; a passed release time does not establish that a result was captured.

If a connected hosted MCP client cannot fetch the public page or JSON, call `feed_status` and read `structuredContent.recorded_public_sample`. It carries the same fixed sample, including its capture time, record roles and official source evidence. Keep that recorded example separate from the tool's live status fields. Hosted MCP still requires eligible account access and authentication.

The public sample contains at most three publisher-selected records, with no configurable filters, dates, pagination or full export. Use the canonical URL above without filter parameters. It does not grant ongoing production API access. [Sample guide and owner setup](https://www.financecalendar.com/api/sample/) · [Machine-readable offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer)

### Set up live access for an account owner

An agent can prepare a next-US-CPI setup without an API key by sending `POST https://www.financecalendar.com/wp-json/fc-handoff/v1/setup` with `{"recipe":"next-us-cpi","client":"claude","plan":"starter","billing_interval":"year","timezone":"America/New_York"}`. Use `chatgpt`, `cursor`, `rest` or `cli` for the corresponding client. Check the [current offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) for available plans and billing intervals.

If the agent cannot make outbound API requests, use the [browser preparation page](https://www.financecalendar.com/api/sample/?setup_client=chatgpt#prepare-owner-setup). Opening the page only displays the form; selecting **Prepare setup link** sends the POST and displays the genuine `owner_url` returned by the server. The preparation page URL is not an `owner_url`, and offering or opening it does not create a setup. This fallback needs no existing paid connector; the owner still approves account linking and any payment.

Share only the returned `owner_url`. The owner signs in with a verified account, approves **Link this setup to my account**, then reviews and pays through Stripe if needed. Keep `status_token` in private tool state and send it in the `X-FC-Handoff-Token` header to `status_url`, respecting `poll_after_seconds` and `expires_at`. When the status is `ready`, follow `resume` to connect the account and run the first query. Setup and readiness do not supply a data credential or authorize payment on the owner's behalf.

Read the [complete agent setup and resume guide](docs/agent-setup.md) for the request, readiness states, owner approvals and CPI/FOMC query examples. The initial setup recipe supports the next US CPI release; query FOMC separately after connecting the paid account.

### Ongoing Free Developer schedules

**Developer access review: 7 days**

Allow up to 7 days for review. Your API key is issued after approval. We email you when access is ready.

[Free Developer](https://www.financecalendar.com/pricing/#plan-comparison) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one API key issued after approval (allow up to 7 days for review), no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit consensus, actual/prior figures and numerical evidence; Starter adds these recorded fields, wider dates/history, formats, hosted MCP and browser tools.

Already-enrolled evaluations retain their original budget, first-use clock and scope. New trial enrolment is closed. Existing paid, legacy and custom access grants are preserved; no account is silently converted to Free Developer.

Keep your key private, then make an authenticated request:

```sh
curl --fail-with-body \
  -H "X-API-Key: $FC_API_KEY" \
  "https://www.financecalendar.com/wp-json/fc/v1/calendar?limit=10"
```

### Currency filters, impact ratings and coverage

For news filters and watchlists, `/calendar`, `/today` and `/week` accept `currency=USD,EUR` (fifteen currencies), `pair=EURUSD` for one pair and `pair=XAUUSD` for gold. Use one of `currency`, `pair` or `country` in a request, and combine it with `impact=high`.

Build and Scale also include `/news-window`, which answers the question a news filter asks: is a relevant release inside my window now? It returns `blocked`, `clear` or `unknown`, the releases inside the window and the next release. They also include `/currency-holidays?currency=USD,GBP`, which groups exchange and bond-market closures by currency. The hosted MCP connector exposes both as the `news_window` and `currency_holidays` tools, and its `calendar`, `today` and `week` tools accept `pair` and `currency`.

```bash
curl --fail-with-body \
  -H "X-API-Key: $FC_API_KEY" \
  "https://www.financecalendar.com/wp-json/fc/v1/news-window?pair=EURUSD&before=30&after=30"
```

```sh
curl --fail-with-body \
  "https://www.financecalendar.com/wp-json/fc/v1/calendar?currency=USD,EUR&impact=high&limit=100" \
  -H "X-API-Key: $FC_API_KEY"
```

- **High-impact coverage** includes rate decisions from the Fed, ECB, Bank of England, Bank of Japan, RBA, Bank of Canada, RBNZ and SNB; inflation, jobs, GDP and retail sales for the major economies; US ISM, JOLTS, ADP and jobless claims; and flash and final PMI release times. Impact ratings are set by Finance Calendar.
- **Countries** include the US, euro area, Germany, France, Italy, Spain, the UK, Japan, Canada, Australia, New Zealand and Switzerland. France, Italy and Spain carry national inflation, GDP and unemployment releases with release times (series such as `fr-cpi-flash`, `it-gdp` and `es-unemployment`). `GET /countries` lists current coverage.
- **Coverage object:** each calendar response includes `coverage`, which says whether events were recorded for the query and lists any source whose latest collection did not complete. An empty result means no matching event is recorded; it is not a guarantee that nothing is scheduled.
- **Series names:** rate decisions can be requested by bank or by country, for example `series=boc` or `series=ca-rate-decision`.
- **Holiday rows** carry `estimated`, `source_url` and `last_verified_at`. SIFMA fixed-income close recommendations are available for the US, UK and Japan (`exchange=sifma`, `sifma-uk`, `sifma-jp`).

### Forex pair filters and MetaTrader

Choose a pair to include scheduled economic releases for both currencies:

```sh
curl --fail-with-body \
  -H "X-API-Key: $FC_API_KEY" \
  "https://www.financecalendar.com/wp-json/fc/v1/calendar?pair=EURUSD&impact=high&limit=100"
```

The paid API supports one `pair` on `/calendar`, `/today` and `/week`. Use `EURUSD` or `EUR/USD`; case is ignored and surrounding whitespace is removed. EUR/USD includes euro area, German and US releases (from 29 November 2026 also French, Italian and Spanish releases, matching `currency=EUR`); GBP/JPY includes UK and Japanese releases; XAU/USD includes US releases for gold’s dollar side. Use `pair` or `country` in a request, not both. Multiple pairs and broker suffixes are not accepted. This selects economic-calendar context, not quotes, order execution or price predictions. Pair filtering does not extend Free Developer or retained evaluation scope. Inspect pagination and source freshness before treating a result as complete.

[Download the MT4/MT5 source package](https://github.com/awarenessdays/financecalendar-api/releases/download/metatrader-0.2.0/financecalendar-metatrader.zip), follow the [MetaTrader setup guide](docs/metatrader.md), or try the [pair request builder](https://www.financecalendar.com/api/forex-calendar/). The filter returns **quiet**, **clear** or **unknown**, with configurable windows and explicit stale/incomplete-data handling. It supplies schedule context to your own EA and places no orders. Consult the release’s acceptance evidence for the compiler/runtime checks performed; test live broker connectivity and your EA’s behaviour in a demo terminal.

- **Docs:** https://www.financecalendar.com/api/
- **Base URL:** `https://www.financecalendar.com/wp-json/fc/v1`
- **OpenAPI 3.1:** [`openapi.json`](openapi.json) (also served live at `/openapi`)
- **Full dataset export:** [Scale account download](https://www.financecalendar.com/account/#fc-account-full-export). Active Scale subscription required; full snapshots and capture history are not distributed in this source repository.
- **ChatGPT and Claude connector:** [Hosted MCP setup](https://www.financecalendar.com/api/mcp/) — authenticated HTTPS for clients supporting API-key headers.
- **Codex and Claude Code:** [Plugin and portable Agent Skill](integrations/README.md)
- **MCP server and CLI:** [Node source and installation](clients/node/README.md)
- **Python client and CLI:** [Python source and installation](clients/python/README.md)
- **Trading tools and bots:** [Runnable Python/Node watchlists and the MetaTrader news filter](integrations/examples/trading-tools/README.md)
- **Measured coverage:** https://www.financecalendar.com/api/coverage/

Install the Node CLI and local MCP server with `npm install --global financecalendar-mcp` when its [npm release](https://www.npmjs.com/package/financecalendar-mcp) is available. Install the Python SDK and CLI with `python -m pip install financecalendar` when its [PyPI release](https://pypi.org/project/financecalendar/) is available. The [earlier GitHub beta packages and checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-annual-restored-2026-11-15) remain available for version-pinned installs. Configure a private API key for data requests. Use the [live offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) for pricing and access.

Programmatic data access requires a verified account and API key. Choose Starter for richer recorded data and tools or explicitly enrol in Free Developer for the bounded schedule scope above. Public sample, product-offer and OpenAPI routes are separate inspection resources. Creating an account does not charge you. Anonymous `POST /keys` creation remains unavailable.

Starter is billed monthly or annually and includes **250 requests per UTC day and 5,000 per UTC calendar month** for new accounts. Build includes **100,000 requests per day** and Scale **1,000,000 per day**. All account keys share the applicable allowance. Daily usage resets at 00:00 UTC; monthly usage resets at 00:00 UTC on the first day of the next calendar month. Existing paid customers retain their contracted prices and applicable allowances; check your account or `/keys/me` for effective limits. See [current plans](https://www.financecalendar.com/pricing/) for billing options and complete snapshot downloads.

Free Developer counts successful committed HTTP 200 JSON responses, including valid empty results. Invalid/denied requests, quota errors and pre-commit failures do not count. Its account ledger survives key rotation, with UTC day/month resets. `GET /keys/me` is uncounted and reports a distinct `free_developer` usage object. Existing enrolled trials keep their separate original budgets and clocks.

For paid plans, daily and monthly quota usage counts admitted requests, not successful responses. Requests refused with HTTP 429 do not consume more allowance; a request that passes the quota check can still consume allowance if it later returns an error. Retained per-key request history remains a separate attempt diagnostic and can include rejected requests.

The [Data explorer](https://www.financecalendar.com/data/) provides search/filter,
saved views, source evidence and matching/selected CSV or JSON exports within its
displayed limits. It uses your verified account sign-in rather than an API key.
Active Starter, Build and Scale subscriptions include the Data explorer. Complete current snapshot downloads require Scale. See [current plans](https://www.financecalendar.com/pricing/) for billing options and allowances.

## Hosted connector

Find the read-only hosted connector as `io.github.awarenessdays/financecalendar` in the [official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.awarenessdays%2Ffinancecalendar/versions/latest). Its [manifest](server.json) records the endpoint. See the [setup guide](https://www.financecalendar.com/api/mcp/) for account linking and supported clients.

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

The MetaTrader package has verified MT5 native parser, timer and public HTTPS checks. MT4 is a source preview with native compiler/parser checks; connected-demo callbacks and HTTPS remain pending. Read the [verification scope](docs/metatrader-acceptance.json).

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
| `GET /history/editions` | Named numerical source editions by publication day, with qualified initial/revision/correction status |
| `GET /history/forecasts` | Typed public survey aggregates by issue-period start index, with separate target and horizon |
| `GET /history/vintage-coverage` | Measured edition/forecast scopes, clocks and plan-accessible ranges |
| `GET /holidays` | Exchange holidays and early closes for 12 exchanges plus SIFMA UK and Japan recommendations (`exchange=nyse\|sifma\|sifma-uk\|sifma-jp\|cme\|lse\|tsx\|asx\|hkex\|euronext\|jpx\|six\|xetra\|nse\|all`) |
| `GET /market-status` | Is the exchange open right now (session, breaks, early closes, holidays) |
| `GET /changes` | Lossless cursor-paginated change log for the last 30 days (`since=`, `limit=`, `cursor=`); restart the original checkpoint on snapshot-change HTTP 409 |
| `GET /countries` | Countries covered with counts |
| `GET /status` | Snapshot age/counts and publisher-source health |
| `GET /health` | Service state, data freshness, source collection results and measured availability (API key required) |
| `GET /keys/me` | Key and shared-account usage; create keys in your verified account |
| `GET /account/full-export` | Complete current JSON dataset; active Scale subscription and Scale API key header required |

Missing or invalid keys return HTTP 401; revoked keys or disallowed accounts return 403. Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`. Send credentials in headers rather than URLs, and do not expose them in browser code.

## Key usage

`GET /keys/me` requires an active key and is uncounted. Free Developer returns `{ "free_developer": { ... } }` with UTC daily/monthly successful-response usage and its schedule window. An already-enrolled evaluation key returns a distinct `{ "trial": { ... } }` usage object with its 25-request total budget, first-use clock and expiry; the status request does not start the clock or consume a data request. Paid and retained keys keep the existing flat `KeyUsage` response described below, available even after the daily cap. `used_today` and `retained_requests` count rate-gate attempts, including 429 responses. `usage_window` explicitly covers 90 UTC dates including today; lifetime `requests_total` is null because the legacy counter was cache-throttled and is not reliable as a request total. `legacy_activity_samples` is diagnostic only. Successful origin responses are a separate metric. [Complete usage fields](https://www.financecalendar.com/api/reference/#schema-keyusage).

Keys created or linked in your [verified account](https://www.financecalendar.com/account/) share one daily account allowance. For those keys, `quota_scope: "account"`, `used_today` and `remaining_today` cover every account key, including revoked keys. `key_used_today` describes the presented key; `retained_requests_scope: "key"` keeps retained history per key. Key rotation does not reset usage. Data responses include `X-RateLimit-Scope: account`. Existing unclaimed keys keep their previous per-key limits.

## Historical economic data

Explore long-run inflation, employment and growth observations alongside evidenced
publication dates. The new archive includes **one year with Starter**, **ten
years with Build**, and **all available history with Scale**. Existing `/history`
and curated datasets keep their current access; explicit prior licences remain
applicable. [Check measured coverage](https://www.financecalendar.com/api/coverage/) and start
with `GET /history/coverage` to choose an exact metric and available period.

The initial official-source roster contains 21 metrics from BLS, ONS, ECB,
Eurostat, Statistics Canada and ABS. In the all-available Scale scope, many
observation series extend into 2006; available depth and latest periods vary. Dated ONS publication records are supplied
separately, with values left unknown when an original result was not collected.
Source editions and historical survey forecasts use their own numerical routes.
`/history/editions` retains native release stages and qualified initial/correction
status; `/history/forecasts` retains survey type, aggregation, issue period and
separate target. Discover actual scope with `/history/vintage-coverage`.
Starter includes one year, Build ten years and Scale all available, using
publication-day filters plus an in-window measured reference-period start for
edition eligibility, and issue-period start index for forecasts.
Survey aggregates are distinct from event-matched market consensus. Exact
`available_before` cutoffs exclude unknown/date-only clocks and may return no rows.
Local MCP now has 19 tools; hosted keeps 14. Preserve source credits, including
the ECB free-source notice.

Use the [history guide](docs/history.md) for the measured definitions, paging,
source credits and complete export examples.

- `GET /history/observations`: exact decimal values by measured reference-period
  start date; `metric_id` or `series_code` required.
- `GET /history/releases`: evidenced publication records by publisher release
  date, with unknown clocks and results preserved as null.
- `GET /history/coverage`: paginated counts and actual earliest/latest periods
  for each source, metric and record kind.

Omit `from` for the server-authorized plan window, or select dates within the
returned access scope. Repeat the original filters and limit with `next_cursor`
to retrieve every permitted page. A changed archive revision returns 409; discard the partial export and restart.
`as_of` selects evidence held by Finance Calendar by its server receipt bound;
it does not turn a newly imported historical value into knowledge FC held years
ago. Current-vintage backfills are labelled and do not establish original prints
or historical forecast cutoffs.

[Python and CLI downloads](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-annual-restored-2026-11-15)
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

Consensus coverage spans **15 selected US headline release series**: US headline CPI, nonfarm payrolls, PPI, retail sales, PCE, ISM Manufacturing, industrial production, Conference Board Consumer Confidence, JOLTS, ADP employment, ISM Services PMI, goods-and-services Trade Balance, core CPI, core PPI and University of Michigan consumer sentiment. Actual and prior values combine validated official observations with recorded release figures; validated official values retain precedence. Compare values with their metric, reference period, unit and source evidence. The existing `/calendar`, `/history` and series endpoints return the expanded records without new request paths.

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
