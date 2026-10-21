# financecalendar

Python client and CLI for the free [financecalendar.com API](https://www.financecalendar.com/api/): scheduled economic releases (CPI, jobs report, GDP, PCE...), central bank decisions (Fed, ECB, BoE, BoJ...) and exchange holidays. Availability varies by series: check each event's `status` and `source_url`; consensus and actual results are included where available.

No API key needed. A free key raises the daily limit from 2,000 to 10,000 requests.

## Install

```sh
pip install financecalendar            # client + CLI
pip install "financecalendar[pandas]"  # adds the DataFrame helper
```

Requires Python 3.10 or newer. The only runtime dependency is `httpx` (plus `tzdata` on Windows for timezone names).

## Quick start

```python
from financecalendar import Client

fc = Client()                                  # reads FC_API_KEY and FC_API_BASE if set
nxt = fc.next("fomc")["next"]
print(nxt["date"], nxt["time_et"], nxt["consensus"], nxt["url"])

week = fc.week(country="us", impact="high", tz="Europe/London")
for e in week["events"]:
    print(e["date"], e["time_local"], e["name"], e["consensus"])
```

Every method returns the API's JSON as plain dicts and lists.

| Method | Endpoint |
|---|---|
| `calendar(**params)` | `GET /calendar` (from_, to, country, impact, category, series, include_holidays, status, tz, limit, offset) |
| `calendar_csv(**params)` | `GET /calendar?format=csv`, returns the CSV text |
| `iter_calendar(from_, to, **params)` | yields every event over any span: pages with offset/limit and splits ranges longer than 92 days |
| `today(country=None, tz=None)` | `GET /today` |
| `week(which="this", **params)` | `GET /week` |
| `next(series, country=None, tz=None)` | `GET /next` |
| `series(**params)` | `GET /series` |
| `series_detail(code, tz=None)` | `GET /series/{code}` |
| `history(series, **params)` | `GET /history` |
| `holidays(exchange="nyse", year=None)` | `GET /holidays` |
| `market_status(exchange="nyse")` | `GET /market-status` |
| `changes(since=None, **params)` | `GET /changes` |
| `countries()` | `GET /countries` |
| `status()` | `GET /status` |
| `openapi()` | `GET /openapi` |

### Long ranges and paging

```python
from datetime import date

rows = list(fc.iter_calendar(date(2026, 1, 1), date(2026, 12, 31), country="us,gb", impact="high"))
```

### Errors

Any 4xx or 5xx raises `FinanceCalendarError` with the API's message:

```python
from financecalendar import Client, FinanceCalendarError

try:
    Client().calendar(tz="Mars/Olympus")
except FinanceCalendarError as exc:
    print(exc.status, exc.message, exc.retry_after)   # 400, "tz must be an IANA timezone...", None
```

On a 429 the `retry_after` attribute holds the `Retry-After` seconds.

### pandas

```python
from financecalendar import Client, to_dataframe

df = to_dataframe(Client().history("us-cpi", limit=24))
print(df[["date", "consensus", "actual"]])
```

`to_dataframe` accepts a list of event rows or a whole calendar/history response and parses `date` and `release_at_utc` to datetimes. pandas is imported only when you call it.

### Configuration

| Setting | Constructor | Environment variable |
|---|---|---|
| Base URL | `Client(base_url=...)` | `FC_API_BASE` (default `https://www.financecalendar.com/wp-json/fc/v1`; an edge mirror at `https://api.financecalendar.com/v1` is planned) |
| API key | `Client(api_key=...)` | `FC_API_KEY`, sent as `X-API-Key` |
| Timeout | `Client(timeout=20)` | |

`Client` is also a context manager and has `close()`.

## CLI

```sh
financecalendar next fomc
financecalendar next cpi --country uk --tz Europe/London
financecalendar today
financecalendar week --next --impact high
financecalendar calendar --from 2026-11-01 --to 2026-11-30 --country us,gb --holidays
financecalendar calendar --from 2026-11-01 --to 2026-11-30 --csv > november.csv
financecalendar series --country gb
financecalendar show boe
financecalendar history us-cpi --limit 12
financecalendar holidays lse 2027
financecalendar status hkex
financecalendar changes --since 2026-10-18T00:00:00Z
financecalendar countries
financecalendar health
```

Add `--json` to any command for the raw response. Global options (accepted before or after the command): `--json`, `--tz ZONE`, `--api-key KEY`, `--base-url URL` and `--version`. `health` prints the API's own `/status` (snapshot age and counts). Times are shown in your local zone unless you pass `--tz`:

```
$ financecalendar --tz America/New_York next fomc
Wed 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold
https://www.financecalendar.com/event/fomc-rate-decision-october-2026/
```

## Data terms

Free for any use, commercial included, with attribution: a visible link to [financecalendar.com](https://www.financecalendar.com) wherever the data appears. Earnings dates are not included. Full terms, rate limits and the changelog: [financecalendar.com/api](https://www.financecalendar.com/api/).

## Source and issues

[Client source and tests](https://github.com/awarenessdays/financecalendar-api/tree/main/clients/python) · [Report an issue](https://github.com/awarenessdays/financecalendar-api/issues).

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/python -m pytest -q        # offline: every request is answered by httpx.MockTransport fixtures
.venv/bin/python -m build            # wheel + sdist into dist/
```

Licence: MIT, Awareness Days Ltd / financecalendar.com.
