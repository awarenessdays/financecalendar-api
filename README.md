# Finance Calendar API

Economic releases, central bank decisions, selected crypto events and exchange holidays as JSON, CSV and ICS. The database combines direct official publisher feeds with checked-in schedules. Source verification, estimates and stale data are identified per record; consensus, prior and actual values are included where available. Snapshot updates run hourly, with coverage varying by source and series.

- **Docs:** https://www.financecalendar.com/api/
- **Base URL:** `https://www.financecalendar.com/wp-json/fc/v1`
- **OpenAPI 3.1:** [`openapi.json`](openapi.json) (also served live at `/openapi`)
- **Full dataset:** [`data/calendar.json`](data/calendar.json), refreshed hourly by the engine (also at https://www.financecalendar.com/wp-content/uploads/fc/calendar.json)
- **MCP server and CLI:** [Node source and installation](clients/node/README.md)
- **Python client and CLI:** [Python source and installation](clients/python/README.md)
- **Measured coverage:** https://www.financecalendar.com/api/coverage/

The API and source installations work now. npm/PyPI publication is pending;
use the source installation instructions linked above.

No API key is needed. A free key raises the daily limit from 2,000 to 10,000 requests and identifies your app: `POST /keys {"email": "you@example.com"}` or use the form on the docs page.

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
| `GET /changes` | Field-level change log for the last 30 days (`since=`) |
| `GET /countries` | Countries covered with counts |
| `GET /status` | Snapshot age/counts and publisher-source health |
| `POST /keys`, `GET /keys/me` | Free key signup and usage |

Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`.

## Examples

- [`examples/python.py`](examples/python.py)
- [`examples/javascript.js`](examples/javascript.js)
- [`examples/google-sheets.md`](examples/google-sheets.md)
- [`examples/curl.md`](examples/curl.md)
- [`widget/`](widget/): drop-in calendar widget for any site

## Data

`data/calendar.json` contains the current database in a rolling window from
12 months back to 400 days ahead, the series registry, exchange table and
30-day change log. Commit history records published snapshots.

Direct schedule connectors currently read BLS, ONS, BEA, Census, Federal
Reserve G.17, DOL jobless claims, EIA energy releases, Treasury auctions,
Eurostat, Japan e-Stat and China NBS. Publisher horizons differ; a rolling window does not mean every
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
feed. Other new connectors add schedules, without inventing macro results or consensus.

```python
import json, urllib.request
cal = json.load(urllib.request.urlopen("https://raw.githubusercontent.com/awarenessdays/financecalendar-api/main/data/calendar.json"))
print(cal["generated_at"], cal["counts"])
```

## Terms

Free for any use, commercial included, with one condition: a visible link to https://www.financecalendar.com wherever the data appears (or on your app's credits page). Earnings dates are not included. See [DATA-TERMS.md](DATA-TERMS.md).

## Issues

Wrong date? Missing series? Open an issue here. The engine reads official calendars, so tell us the official source and we will add it.

## Selected crypto events

Use `category=crypto&asset=ethereum` with `/calendar`, `/week` or `/today`.
Discover canonical asset IDs through `/series?category=crypto`; symbols such as
ETH are display labels. Initial public coverage is selected Ethereum mainnet
and testnet upgrade schedules, not every coin or token unlock.

Global crypto has `country=null`; `impact` may be null. Check
`crypto.environment`, `crypto.activation_status` and `verification_method`.
Scheduled activation is not observed activation. Month/quarter/year targets
retain `date_window_start` and `date_window_end`; `date` is only a lower-bound
index. Calendar filters include overlapping windows. Keep `source_license`
credit, licence links, adaptation information and notices when reusing records.

See the [crypto calendar](https://www.financecalendar.com/crypto/) and
[full REST reference](https://www.financecalendar.com/api/reference/).
