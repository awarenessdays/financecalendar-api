# Finance Calendar API

Economic releases, central bank decisions, selected crypto events and exchange holidays as JSON, CSV and ICS. The database combines direct official publisher feeds, checked-in schedules and explicitly licensed crypto data. Source verification, estimates and stale data are identified per record; consensus, prior and actual values are included where available. Snapshot updates run hourly, with coverage varying by source and series.

- **Docs:** https://www.financecalendar.com/api/
- **Base URL:** `https://www.financecalendar.com/wp-json/fc/v1`
- **OpenAPI 3.1:** [`openapi.json`](openapi.json) (also served live at `/openapi`)
- **Full dataset:** [`data/calendar.json`](data/calendar.json), refreshed hourly by the engine (also at https://www.financecalendar.com/wp-content/uploads/fc/calendar.json)
- **ChatGPT and Claude connector:** [Hosted MCP setup](https://www.financecalendar.com/api/mcp/) — public beta, no local installation.
- **Codex and Claude Code:** [Plugin and portable Agent Skill](integrations/README.md)
- **MCP server and CLI:** [Node source and installation](clients/node/README.md)
- **Python client and CLI:** [Python source and installation](clients/python/README.md)
- **Measured coverage:** https://www.financecalendar.com/api/coverage/

The API and [tested beta client downloads](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-2026-10-22) work now. npm/PyPI registry publication is pending; use those downloads or the source installation instructions linked above.

No API key is needed. A free key raises the daily limit from 2,000 to 10,000 requests and identifies your app: `POST /keys {"email": "you@example.com"}` or use the form on the docs page.

## Hosted connector

Add this Streamable HTTP endpoint as a custom connector in ChatGPT or Claude, with no authentication:

```text
https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
```

[Setup and full tool reference](https://www.financecalendar.com/api/mcp/). The public beta provides 12 read-only tools and shares the keyless per-IP daily allowance; platform proxy IPs may be shared by several users. The local server remains available with a personal API key. A real Claude Messages API call has been verified against the hosted MCP endpoint. ChatGPT and Claude.ai account-level setup checks, plus directory listings, remain pending.

## Quick start

```bash
# Next Fed decision
curl "https://www.financecalendar.com/wp-json/fc/v1/next?series=fomc"

# Next UK CPI print
curl "https://www.financecalendar.com/wp-json/fc/v1/next?series=uk-cpi"

# Every high-impact release in the next two weeks, in London time
curl "https://www.financecalendar.com/wp-json/fc/v1/calendar?impact=high&tz=Europe/London"

# This week as a CSV
curl -o week.csv "https://www.financecalendar.com/wp-json/fc/v1/week?format=csv"

# Subscribe in a calendar app (ICS)
https://www.financecalendar.com/wp-json/fc/v1/calendar?series=fomc,us-cpi,us-nfp&format=ics

# What changed in the last 24 hours (new dates, moved dates, consensus, actuals)
curl "https://www.financecalendar.com/wp-json/fc/v1/changes"
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
| `POST /keys`, `GET /keys/me` | Free key signup and usage |

Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`.

## Key usage

`GET /keys/me` requires an active key and is uncounted, even after the daily cap. `used_today` and `retained_requests` count rate-gate attempts, including 429 responses. `usage_window` explicitly covers 90 UTC dates including today; lifetime `requests_total` is null because the legacy counter was cache-throttled and is not reliable as a request total. `legacy_activity_samples` is diagnostic only. Successful origin responses are a separate metric. [Complete usage fields](https://www.financecalendar.com/api/reference/#schema-keyusage).

Keys created or linked in your [verified account](https://www.financecalendar.com/account/) share one daily account allowance. For those keys, `quota_scope: "account"`, `used_today` and `remaining_today` cover every account key, including revoked keys. `key_used_today` describes the presented key; `retained_requests_scope: "key"` keeps retained history per key. Key rotation does not reset usage. Data responses include `X-RateLimit-Scope: account`. Existing unclaimed keys keep their previous per-key limits.

## Examples

- [`examples/python.py`](examples/python.py)
- [`examples/javascript.js`](examples/javascript.js)
- [`examples/google-sheets.md`](examples/google-sheets.md)
- [`examples/curl.md`](examples/curl.md)
- [`widget/`](widget/): drop-in calendar widget for any site

## Numerical evidence

Current `actual` and `prior` fields require supported official observation evidence or an exact structured Treasury result summary; article metadata is not a fallback. Consensus estimates are not currently collected and remain null. Check reference periods, measurement units, source vintages and stale flags. BLS payroll values are already in jobs, while `source_value` retains thousands of jobs and the exact conversion factor. Publisher-reported revisions, engine-observed revisions and original first prints are distinct. See the [complete reference](https://www.financecalendar.com/api/reference/) for document manifests and occurrence bindings.

## Data

`data/calendar.json` contains the current database in a rolling window from
12 months back to 400 days ahead, the series registry, exchange table and
30-day change log. Commit history records published snapshots.

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
import json, urllib.request
cal = json.load(urllib.request.urlopen("https://raw.githubusercontent.com/awarenessdays/financecalendar-api/main/data/calendar.json"))
print(cal["generated_at"], cal["counts"])
```

## Terms

Free for commercial use subject to applicable source terms and credits, with a visible link to https://www.financecalendar.com wherever the data appears (or on your app's credits page). Earnings dates are not included. See [DATA-TERMS.md](DATA-TERMS.md).

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
