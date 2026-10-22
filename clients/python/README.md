# financecalendar

Python client and CLI for the free [financecalendar.com API](https://www.financecalendar.com/api/): scheduled economic releases (CPI, jobs report, GDP, PCE...), central bank decisions (Fed, ECB, BoE, BoJ...) exchange holidays and source-backed crypto events. Availability varies by series: check each event's `status` and `source_url`; consensus and actual results are included where available.

No API key needed. A free key raises the daily limit from 2,000 to 10,000 requests.

## Install from source

Registry publication is pending. Install the current version from the public
source repository:

```sh
git clone https://github.com/awarenessdays/financecalendar-api.git
cd financecalendar-api/clients/python
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/financecalendar --help
```

Use `.venv\Scripts\python` and `.venv\Scripts\financecalendar` on Windows.
Install `".[pandas]"` instead of `.` for the optional DataFrame helper.

After publication:

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

Events include nullable `period` and `release_stage` fields. Human CLI output
shows these details when provided, labels unknown economic release times
`time unknown`, and retains `all day` for exchange holidays.

| Method | Endpoint |
|---|---|
| `calendar(**params)` | `GET /calendar` (from_, to, country, impact, category, asset, series, include_holidays, status, tz, limit, offset) |
| `crypto_calendar(asset=None, **params)` | `GET /calendar` with `category=crypto` forced; canonical asset IDs |
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

## Crypto coverage

```python
from financecalendar import Client, to_dataframe

with Client() as fc:
    series = fc.series(category="crypto")  # discover canonical series and assets
    calendar = fc.crypto_calendar(asset="ethereum")
    nxt = fc.next("ethereum-network-upgrades", asset="ethereum")
    rows = list(fc.iter_calendar("2026-10-01", "2027-03-01", category="crypto", asset="ethereum"))
```

`asset` passes through `calendar`, `calendar_csv`, `iter_calendar`, `today`,
`week`, `next`, `series`, `series_detail` and `history`. Asset IDs are canonical
names such as `ethereum`, not ticker symbols such as ETH. Crypto rows have
`country=None` and may have `impact=None`. A country filter excludes global rows.

Estimated month/quarter/year windows retain `date_window_start/end`; `date` is
only their lower-bound index. Range queries include overlapping windows, and
`iter_calendar` deduplicates stable IDs across chunks. A scheduled testnet fork
is distinct from mainnet and is not proof of an observed activation. Inspect
`crypto.environment`, `crypto.activation_status`, `verification_url`,
`verification_method`, `manually_reviewed_at`, `last_verified_at` and `data_stale`.

`to_dataframe` retains nested `assets`, `crypto`, `source_license` and
`source_rights` plus the optional `discovery_url`, parses
estimated date-window bounds, and adds `asset_ids`, `asset_symbols`,
`crypto_event_type`, `crypto_network`, `crypto_exchange`, `crypto_environment`
and `crypto_activation_status`. It preserves null countries and recorded zeros.

```sh
financecalendar series --category crypto
financecalendar calendar --category crypto --asset ethereum --json
financecalendar next ethereum-network-upgrades --asset ethereum --tz UTC
```

Coverage includes network schedules, vesting installments, governance voting
deadlines and issuer supply projections. The `crypto` object retains source
metadata:

- Unlocks: `schedule_id`, `installment`, `beneficiaries`, `unlock_status`, `date_basis`, `token_amount` and `token_amount_basis` when supplied. Scheduled or upper-bound quantities do not prove transfer or sale.
- Governance: `dao`, `space_id`, `proposal_id`, optional `proposal_title`, `voting_start`, `voting_end`, `voting_state`, `voting_type` and `choice_count`. A voting deadline is not approval, rejection or execution.
- Supply projections: `projection_status`, `projected_circulating_supply`, `projected_monthly_supply_change` and `date_basis`. Issuer estimates are not confirmed unlocks or observed circulating supply; decimal strings retain source precision.

Public records combine licensed feeds and independently normalised factual
records. `source_license` carries actual upstream licensing requirements;
`source_rights` carries factual provenance, access basis, review time,
attribution and notice without asserting a publisher copyright licence. Either
may be null. An optional `discovery_url` is a discovery-page link, potentially
from an aggregator, and is separate from primary `source_url` and verification
evidence. CoinMarketCal internal API evaluation payloads are excluded. Coverage
varies by asset and source; empty results do not establish comprehensive coverage.

Raw JSON, `calendar_csv` and CLI `--csv` retain these fields; CSV stores nested
objects as JSON cells. Preserve record-level rights and licence metadata when
sharing data. PatternPlus records require the linked credit
[Data: PatternPlus](https://pattern.plus), carried in
`source_license.attribution` and `source_license.attribution_url`, alongside the
licence link and adaptation notice. Human CLI output includes source credits,
attribution links and factual notices, but remains a summary; use JSON/CSV to
retain every metadata field when redistributing.

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

API access is currently free, including for commercial applications, subject to applicable source terms and credits. Include a visible link to [financecalendar.com](https://www.financecalendar.com) wherever the data appears. Retain each record's `source_license` requirements, including `attribution_url`, source and licence links, full notices and adaptation labels; PatternPlus records require [Data: PatternPlus](https://pattern.plus). Preserve `source_rights` attribution, evidence, access basis and notice for independently normalised facts. This rights metadata does not assert a publisher copyright licence. Earnings dates are not included. Full terms, rate limits and the changelog: [financecalendar.com/api](https://www.financecalendar.com/api/).

## Source and issues

[Client source and tests](https://github.com/awarenessdays/financecalendar-api/tree/main/clients/python) · [Report an issue](https://github.com/awarenessdays/financecalendar-api/issues).

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"
.venv/bin/python -m pytest -q        # offline: every request is answered by httpx.MockTransport fixtures
.venv/bin/python -m build            # wheel + sdist into dist/
```

Client source code: MIT, Awareness Days Ltd / financecalendar.com. The code licence does not license upstream data; data terms and record-level rights metadata apply separately.
