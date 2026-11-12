# financecalendar

Bring economic-release dates, consensus forecasts and published results into Python, pandas and terminal workflows with the [financecalendar.com API](https://www.financecalendar.com/api/). Provider consensus now spans **12 selected US headline release series**, with source-linked actual/prior values for covered records. The same API also supplies central bank decisions, exchange holidays and source-backed crypto events. Use each record’s metric, reference period and source evidence when comparing expectations with results.

[Paid API plans](https://www.financecalendar.com/pricing/) start at **US$9.99/year** for Starter (**1,000 requests/UTC day and 25,000/UTC calendar month**). Build is **US$9.99/month or US$95.90/year** for **100,000/day**. Scale is **US$29/month or US$278.40/year** for **1,000,000/day** and the complete current dataset download. [Inspect the public sample](https://www.financecalendar.com/api/sample/) before choosing a plan.

[Free Developer](https://www.financecalendar.com/account/?free=1) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one active key, no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit consensus, actual/prior figures and numerical evidence; Starter adds these recorded fields, wider dates/history, formats, hosted MCP and browser tools.

The [public calendar remains free to browse](https://www.financecalendar.com/events/). Hosted MCP, status and the wider data examples below require a paid plan. The public sample, product offer and OpenAPI document can be read directly without a key; SDK requests consistently use your configured account key. Set `FC_API_KEY` securely or pass `Client(api_key=...)`. Missing credentials fail before any network request.

Starter costs **US$9.99/year** and includes **1,000 requests per UTC day and 25,000 per UTC calendar month**. Build includes **100,000 requests per day** and Scale **1,000,000 per day**. All account keys share the applicable allowance. Daily usage resets at 00:00 UTC; monthly usage resets at 00:00 UTC on the first day of the next calendar month. Existing paid customers retain their contracted prices and applicable allowances; check your account or `/keys/me` for effective limits. See [current plans](https://www.financecalendar.com/pricing/) for billing options and complete snapshot downloads.

Free Developer counts successful committed HTTP 200 JSON schedule responses, including valid empty responses. Invalid or denied requests, quota errors and pre-commit server failures do not consume its allowance. Usage is shared by the account and survives key rotation; daily and monthly resets follow UTC. Already-enrolled evaluations retain their original 25-successful-request budget, 48-hour clock from first use and original scope. New trial enrolment is closed. Existing paid, legacy and custom access grants are preserved; no account is silently converted to Free Developer.

For paid plans, daily and monthly quota usage counts admitted requests, not successful responses. Requests refused with HTTP 429 do not consume more allowance; a request that passes the quota check can still consume allowance if it later returns an error. Retained per-key request history remains a separate attempt diagnostic and can include rejected requests.

```sh
export FC_API_KEY='fc_live_YOUR_ACTUAL_KEY'
```

Use your real key and keep it private; never include it in a shared notebook or URL.

## Install the tested beta download

[Download packages and SHA-256 checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-free-developer-2026-11-12). Use the direct package URL in your chosen environment:

```sh
python -m pip install https://github.com/awarenessdays/financecalendar-api/releases/download/clients-free-developer-2026-11-12/financecalendar-0.1.3-py3-none-any.whl
```

Registry publication remains pending. The GitHub release is a versioned, tested distribution; source installation is also available below.

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

The `financecalendar` name is not currently published on PyPI; use the tested wheel or source command above.

Requires Python 3.10 or newer. The only runtime dependency is `httpx` (plus `tzdata` on Windows for timezone names).

## Quick start

A first bounded request within free access:

```python
from financecalendar import Client

with Client() as fc:  # reads your private FC_API_KEY
    sample = fc.calendar(limit=10)
    print(sample["events"])
```

The following `/next` example and the wider methods below require a paid plan:

```python
from financecalendar import Client

fc = Client()                                  # requires FC_API_KEY; reads FC_API_BASE if set
nxt = fc.next("fomc")["next"]
print(nxt["date"], nxt["time_et"], nxt["consensus"], nxt["url"])

week = fc.week(country="us", impact="high", tz="Europe/London")
for e in week["events"]:
    print(e["date"], e["time_local"], e["name"], e["consensus"])
```

Every method returns the API's JSON as plain dicts and lists.

Paid event responses include nullable `period` and `release_stage` fields. Human CLI output
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
| `enrichment_history(series, **params)` | `GET /enrichment/history`; evidenced results with from_, to, limit, offset, ledger_cursor and publication_revision |
| `enrichment_editions(event_id, **params)` | `GET /enrichment/editions`; accepted editions with limit, offset and both pagination pins |
| `holidays(exchange="nyse", year=None)` | `GET /holidays` |
| `market_status(exchange="nyse")` | `GET /market-status` |
| `changes(since=None, **params)` | One page from `GET /changes`; accepts series, change, limit and cursor |
| `countries()` | `GET /countries` |
| `status()` | `GET /status` |
| `quality(**params)` | `GET /quality`, the current snapshot's quality and evidence-coverage report |
| `observations(**params)` | One page from `GET /observations`; accepts series, event_id, role, reference_period, limit, offset and snapshot_generated_at |
| `openapi()` | `GET /openapi` |

### Economic results and editions

```python
with Client() as fc:
    results = fc.enrichment_history("us-adp", from_="2026-01-01", limit=20)
    for release in results["releases"]:
        print(release["actual"], release["consensus"], release["selected_editions"])
        editions = fc.enrichment_editions(release["event_id"], limit=100)
```

These endpoints cover `us-jolts`, `us-adp`, `us-ism-services` and
`us-trade-balance` when the enrichment service is enabled and accepted evidence
is available. First pages return `ledger_cursor` and `publication_revision`.
Follow `next_offset` with the same filters and both pins; they are required
when offset is above zero. The ledger pin excludes later appends, while the
publication pin prevents combining different published views. On HTTP 409,
restart at offset zero without the old pins.
Values retain exact decimal strings, nulls, reference periods and provenance.
`available_at` describes recorded source availability; `received_at` records
Finance Calendar's receipt. A provider archive is labelled separately from an
engine capture. `as_of_supported` is false; these responses do not reconstruct
an original first print. Normal account authentication and quota rules apply.

### Long ranges and paging

```python
from datetime import date

rows = list(fc.iter_calendar(date(2026, 1, 1), date(2026, 12, 31), country="us,gb", impact="high"))
```

For changes, follow `next_cursor` until `has_more` is false, passing that cursor
alone to `fc.changes(cursor=...)`. Advance the `since` checkpoint only after all
pages finish. HTTP 409 means the snapshot changed: restart with the original
`since` and filters and deduplicate repeated changes. Reload the full snapshot
if the checkpoint is outside the 30-day retention window. The CLI accepts the
same continuation with `financecalendar changes --cursor ...`.

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

Free Developer provides the bounded schedule scope above; richer data and wider features require a paid plan. Use is subject to the current [API service terms](https://www.financecalendar.com/api/terms/) and applicable source terms and credits. Include a visible link to [financecalendar.com](https://www.financecalendar.com) wherever the data appears. Retain each record's `source_license` requirements, including `attribution_url`, source and licence links, full notices and adaptation labels; PatternPlus records require [Data: PatternPlus](https://pattern.plus). Preserve `source_rights` attribution, evidence, access basis and notice for independently normalised facts. This rights metadata does not assert a publisher copyright licence. Earnings dates are not included. Full terms, rate limits and the changelog: [financecalendar.com/api](https://www.financecalendar.com/api/).

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

## Official numerical observations

Where a result is explicitly mapped, responses retain `observations`,
`observation_status`, `observation_metric_id` and `observation_fields`. Each
observation identifies its value, unit, reference period, source, engine capture
time and any revisions. The previous value uses the previous reference period
at the current observed vintage; it is not a reconstructed original first print.
Numerical-source staleness is separate from calendar schedule staleness.
Text output explains this distinction and retains source credits; JSON and CSV
retain the available lineage. Unknown consensus stays absent. See the
[REST reference](https://www.financecalendar.com/api/reference/) for the contract.

Expanded US coverage brings consensus forecasts and release results together for
CPI, nonfarm payrolls, PPI, retail sales, headline PCE, ISM Manufacturing,
industrial production, Consumer Confidence, JOLTS, ADP employment, ISM Services
and goods-and-services Trade Balance. Inspect each value's source, reference
period and recorded edition through its numerical evidence. Official observations
retain priority for mapped actual/prior values.
BLS payroll `value` is already converted to jobs. `source_value` remains in
`source_unit` thousands of jobs with `conversion_factor="1000"`; do not multiply
the canonical value again. `publisher_reported_revisions` retains publisher units
and is separate from engine-observed `revision_history`. Neither establishes
original first prints. Preserve document manifests, occurrence bindings and
record-level source credits when reusing data.

### Query quality and observation evidence

These methods are available in the current source checkout. The older versioned
beta wheel above may predate these additions; no new registry release is implied.

```python
with Client() as fc:
    quality = fc.quality()
    evidence = fc.observations(series="us-cpi", role="actual", limit=100)
    for row in evidence["observations"]:
        print(row["event_id"], row["observation"])
```

Both methods use the same API key, quotas and `FinanceCalendarError` handling as
the calendar. They return unmodified nested JSON, including source lineage,
engine-observed revision history, null values and recorded zeros. `quality()`
reports the current engine snapshot; `observations()` returns validated evidence
per event and role, including retained stale observations where endorsed by the
engine contract. Missing evidence does not establish that a release has no result.

For observation paging, pass `offset=page["next_offset"]` together with
`snapshot_generated_at=page["snapshot_generated_at"]` and the identical filters
while `has_more` is true. On HTTP 409, restart at offset zero against the current
snapshot. An `observation_id` can occur in several event/role entries.

These are **engine-observed current vintages**. They do not reconstruct original
first prints or arbitrary historical knowledge. The API rejects `as_of`; the
client passes it through so callers receive the server's normal HTTP 400 error.

## Korean official calendars

Filter with `country=KR` (aliases `korea` and `south korea`) or a `kr-` series
code. MODS and BOK schedules retain explicit reference periods and release
stages; unsupported or ambiguous identities are withheld. Coverage ends at the
publisher's verified horizon: a year selector does not establish published dates.

These records currently have date precision and `all_day=false`. BOK's raw
media-publication clock is carried in `source_clock`, distinct from ECOS
availability. Its timezone has not been explicitly verified, so `release_at_utc`
and local display time remain null. `release_tz=Asia/Seoul` identifies the calendar
jurisdiction; do not use it to manufacture an instant. Numerical results and
consensus remain null until separately verified by an implemented result source.

## Indian official release dates

MoSPI dates use `country=IN` and `in-` series codes. Publisher-planned dates remain
estimated, with no computed holiday adjustment or clock. The source's explicitly
recorded publication dates take precedence. A publication month is not the
measured month: `period` and `source_reference_period` stay null where omitted.
GDP publications may bundle multiple quarterly/annual estimate components;
these retain their original description and do not imply one headline result.
Reference-year conflicts and indistinguishable release identities are held for
review. Inspect per-source health and the verified fiscal-year horizon.
