# Finance Calendar API

Economic releases, central bank decisions and exchange holidays as JSON, CSV and ICS. Every row is verified against the official calendar, carries consensus, prior and actual figures, and is refreshed within the hour of a print.

- **Docs:** https://www.financecalendar.com/api/
- **Base URL:** `https://www.financecalendar.com/wp-json/fc/v1`
- **OpenAPI 3.1:** [`openapi.json`](openapi.json) (also served live at `/openapi.json`)
- **Full dataset:** [`data/calendar.json`](data/calendar.json), refreshed hourly by the engine (also at https://www.financecalendar.com/wp-content/uploads/fc/calendar.json)
- **MCP server and CLI:** `npx financecalendar-mcp` and `npx financecalendar` (package `financecalendar-mcp`)
- **Python:** `pip install financecalendar`

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
| `GET /calendar` | Events in a date range (max 92 days): `from`, `to`, `country`, `impact`, `category`, `series`, `status`, `include=holidays`, `tz`, `limit`, `offset`, `format=json\|csv\|ics` |
| `GET /today` | Today's releases, live NYSE status and any exchange closures |
| `GET /week` | This week or next (`which=next`) |
| `GET /next` | Next occurrence of a series (`series=fomc`, `cpi`, `uk-cpi`, `japan-gdp`...; `country=` override) |
| `GET /series` | Every series with code, aliases, country, tier and next date |
| `GET /series/{code}` | One series: next, last, upcoming, history, verified dataset where published |
| `GET /history` | Past releases of a series with consensus, prior and actual |
| `GET /holidays` | Exchange holidays and early closes for 12 exchanges (`exchange=nyse\|sifma\|cme\|lse\|tsx\|asx\|hkex\|euronext\|jpx\|six\|xetra\|nse\|all`) |
| `GET /market-status` | Is the exchange open right now (session, breaks, early closes, holidays) |
| `GET /changes` | Field-level change log for the last 30 days (`since=`) |
| `GET /countries` | Countries covered with counts |
| `GET /status` | Health: snapshot age and counts |
| `POST /keys`, `GET /keys/me` | Free key signup and usage |

Invalid parameters return HTTP 400 with an `error` message. Daily limits return HTTP 429 with `Retry-After`.

## Examples

- [`examples/python.py`](examples/python.py)
- [`examples/javascript.js`](examples/javascript.js)
- [`examples/google-sheets.md`](examples/google-sheets.md)
- [`examples/curl.md`](examples/curl.md)
- [`widget/`](widget/): drop-in calendar widget for any site

## Data

`data/calendar.json` is the whole dataset the API serves: every event from 12 months back to 400 days ahead, every series, the exchange table and the 30-day change log. Commit history is the audit trail.

```python
import json, urllib.request
cal = json.load(urllib.request.urlopen("https://raw.githubusercontent.com/awarenessdays/financecalendar-api/main/data/calendar.json"))
print(cal["generated_at"], cal["counts"])
```

## Terms

Free for any use, commercial included, with one condition: a visible link to https://www.financecalendar.com wherever the data appears (or on your app's credits page). Earnings dates are not included. See [DATA-TERMS.md](DATA-TERMS.md).

## Issues

Wrong date? Missing series? Open an issue here. The engine reads official calendars, so tell us the official source and we will add it.
