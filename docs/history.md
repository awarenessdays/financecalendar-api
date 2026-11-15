# Historical economic data

Use long-run economic observations for charts, research and reproducible data
exports. Start with authenticated coverage, select the exact metric you need,
then page its observations or dated release records. The new archive supplies
one year with Starter, ten years with Build and all available history with Scale.
These windows apply to the new archive only: legacy `/history`, curated datasets
and explicit existing licence rights keep their applicable access. The [current plans](https://www.financecalendar.com/pricing/)
state allowances and source terms.

```sh
B=https://www.financecalendar.com/wp-json/fc/v1
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" \
  "$B/history/coverage?metric_id=gb-cpi-all-items-yoy&limit=100"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" \
  "$B/history/observations?metric_id=gb-cpi-all-items-yoy&limit=100"
```

`FC_API_KEY` must be your own paid or applicable retained key. No keys appear in
URLs. The free public calendar and bounded Free Developer schedule routes remain
available under their respective scopes.

## Choose the historical question

**Observations** use the start date of the measured reference period. A January
monthly observation has `period_start` 1 January and its own `period_end`. Its
publication time is not inferred from that month. Values are exact decimal
strings, including zero; a derived rate/change identifies its formula, exact
operands and source fingerprints.

**Releases** use the publisher's recorded calendar publication date. Exact UTC
clocks appear only where evidenced. Unknown clocks and numerical results remain
null. A current revised observation is not silently copied onto an old release.

**Source editions** use `/history/editions`, ordered by the source edition’s
publication day. Plan eligibility additionally requires the measured
reference-period start within the same window, so a recent edition cannot grant
older measured periods outside the plan. `access.date_basis` is
`edition_publication_and_reference_period_start`; `order_date_basis` stays
`edition_publication_date`. Inspect native `release_stage`, `first_print_status`,
`first_print_rule_id` and `correction_status` to identify qualified initial
releases separately from revisions, corrected editions or unverified source
vintages. A source edition is not automatically an original first print.

**Survey forecasts** use `/history/forecasts`. Date filters and plan access use
`issue_period_start`, an ordering index; `reference_period` is the separate
forecast target. Preserve forecast type, published aggregation, target basis
and native horizon. HMT panel aggregates and ECB SPF means are professional
surveys, distinct from event-matched market consensus or private FC blends.
These current historical databases can include publisher corrections. Unknown
publication dates remain unknown; HMT’s publication month is retained without
inventing a day, and an inferred ECB issue quarter is not publication evidence.

`/history/vintage-coverage` is the separate measured inventory for editions and
forecasts. Inspect each scope’s actual issue/publication bounds, qualified
initial counts, horizon scope, clock counts and plan-accessible range. Per-metric
starts vary; source-programme age does not establish uniform stored depth.

**Coverage** returns actual stored counts, populated values and earliest/latest
periods for each source/metric/kind. It is paginated. Inspect each row's
`accessible_range.from`, `accessible_range.to`, `accessible_range.record_count`
and `date_basis` alongside the global stored metadata. Top-level `access`
describes your effective rolling UTC calendar-year window. A global earliest
period is not permission to request data before your own plan floor. A null expected count or gap
list means no authoritative full publisher inventory was asserted. Configured
start dates and raw row totals do not establish complete event coverage.

The initial roster covers 21 exact metrics from six official agencies across the
US, UK, euro area, Canada and Australia. Within Scale's all-available scope,
most observation series reach into 2006. The selected Canadian retail vector and US hourly-earnings series start later;
the initial legacy euro-area HICP series stop in December 2025. Query coverage
for current bounds. Original source gaps and missing derivation operands are
retained rather than filled with incompatible measures. Dated ONS releases have
an independently shorter range than observation history.

## Complete traversal and export

Every successful page returns `rows`, `count`, `archive_revision`, `has_more` and
`next_cursor`. The opaque cursor binds the filters, sort order, page size,
revision and last stable key. Repeat all original filters and the same `limit`
when following it. Do not decode or modify the cursor. A changed query or cursor
fails explicitly; an intervening activated import returns 409. Restart and discard
partial results when that happens.

The Python client provides complete iterators:

```python
from financecalendar import Client

with Client() as fc:  # reads your private FC_API_KEY environment variable
    scopes = list(fc.iter_history_coverage(limit=100))
    rows = list(fc.iter_archive(
        kind="observations", metric_id="gb-cpi-all-items-yoy",
        limit=100,  # omit from_ for the authorized plan window
    ))
print(len(rows), rows[0]["reference_period"], rows[-1]["reference_period"])
```

The installed Python or Node CLI buffers a complete pinned traversal with `--all`:

```sh
financecalendar history-coverage --all
financecalendar archive-observations --metric-id gb-cpi-all-items-yoy --limit 100 --all
financecalendar archive-releases --series-code gb-cpi --limit 100 --all
```

Omit `from` to use the server-authorized window, inspect returned access metadata,
and keep explicit date bounds within that range. A request outside the plan
window fails explicitly. Complete pagination is available within every paid
plan's permitted history; Scale's all-available history is not a new bulk ZIP.
The existing Scale complete-current-snapshot download is a separate feature.

These commands emit JSON, preserve exact values and fail rather than report a
partial traversal as a complete export. The runnable
[Python export example](../examples/history.py) writes the rows with a count and
SHA-256 manifest. New archive tools are available in local stdio MCP. The hosted
MCP catalogue remains unchanged.

## Source and capture meaning

The observation/release collectors admit `vintage_basis=current_vintage`. They capture the
agency's presently available historical series, potentially revised. They do
not establish original first prints, historical consensus or what traders knew
at a past release. `historical_first_print` remains false and unverified
consensus/cutoff fields remain null.

`as_of` selects evidence using `fc_evidence_commit_observed_bound`: FC's server
receipt bound after the bytes were durably stored. `first_seen_at` and
`fc_observed_at` describe those receipt bounds. Collector `source_captured_at`
and source publication/vintage metadata retain their separate meanings and
precision. A newly backfilled 2006 observation is not made known to FC in 2006.
This is an evidence-receipt view, not a historical market-availability selector.

For V2 editions/forecasts, `available_before` separately requires an independently
qualified exact source-public-availability instant, in canonical UTC seconds
ending in `Z`. Date-only, month/quarter-only and unknown clocks are excluded;
a valid cutoff can return an empty page. The selected FC capture version is
checked without silently falling back to another capture. Do not use issue
indexes, submission deadlines, midnight or FC receipt as substitute source
availability clocks.

Retain Finance Calendar attribution and each row's `source_license` credits.
Source response fingerprints and mapping/parser versions support inspection.
Original public agency payloads are retained in the private operational archive;
this public source repository distributes client code, schemas and small test
fixtures. No new third-party supplier licence or universal twenty-year
calendar/forecast archive is implied.

See the [OpenAPI schema](../openapi.json), [Python client](../clients/python/README.md)
and [Node CLI/local MCP](../clients/node/README.md). Obtain a key through your
[Finance Calendar account](https://www.financecalendar.com/account/).

## Source-edition and survey exports

Python 0.1.5 provides `archive_editions`, `archive_forecasts`, `vintage_coverage`
and the complete `iter_archive_editions`, `iter_archive_forecasts`,
`iter_vintage_coverage` iterators. Values retain exact decimal strings, scale,
units, nulls and source licences. Buffer iterator output before committing an
export, because later errors make earlier yielded rows partial. Node 0.2.5 provides
`archiveEditions`, `archiveForecasts`, `vintageCoverage` and buffered
`collectArchive(kind, filters)`.

```sh
financecalendar vintage-coverage --kind forecasts --all
financecalendar historic-editions --metric-id us-gdp-real-qoq-saar --all
financecalendar historic-forecasts --metric-id eu-spf-hicp-annual-mean-p12m --all
python examples/history.py --kind forecasts --metric eu-spf-hicp-annual-mean-p12m
```

All six archive commands support one intact page or complete buffered `--all`
traversal, preserving original filters and limit with every cursor. Local tools
`historic_editions`, `historic_forecasts` and `vintage_coverage` bring the local
catalogue to 19; all six archive tools remain local only. Hosted retains 14 tools.
The same Starter 1 year / Build 10 years / Scale all available policy applies on the
route’s documented axes; edition eligibility checks both publication and measured-period start, while forecasts use issue-period start. Omitted bounds use the caller’s accessible window.
Retain every row’s source credit. ECB originals are freely available from the
ECB; paying users receive that notice before purchase and on each access.
