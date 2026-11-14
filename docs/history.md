# Historical economic data

Use long-run economic observations for charts, research and reproducible data
exports. Start with authenticated coverage, select the exact metric you need,
then page its observations or dated release records. Existing paid API access
covers these routes; the [current plans](https://www.financecalendar.com/pricing/)
state allowances and source terms.

```sh
B=https://www.financecalendar.com/wp-json/fc/v1
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" \
  "$B/history/coverage?metric_id=gb-cpi-all-items-yoy&limit=100"
curl --fail-with-body -H "X-API-Key: $FC_API_KEY" \
  "$B/history/observations?metric_id=gb-cpi-all-items-yoy&from=2006-01-01&limit=100"
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

**Coverage** returns actual stored counts, populated values and earliest/latest
periods for each source/metric/kind. It is paginated. A null expected count or gap
list means no authoritative full publisher inventory was asserted. Configured
start dates and raw row totals do not establish complete event coverage.

The initial roster covers 21 exact metrics from six official agencies across the
US, UK, euro area, Canada and Australia. Most observation series reach into 2006.
The selected Canadian retail vector and US hourly-earnings series start later;
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
        from_="2006-01-01", limit=100,
    ))
print(len(rows), rows[0]["reference_period"], rows[-1]["reference_period"])
```

The installed Python or Node CLI buffers a complete pinned traversal with `--all`:

```sh
financecalendar history-coverage --all
financecalendar archive-observations --metric-id gb-cpi-all-items-yoy --from 2006-01-01 --limit 100 --all
financecalendar archive-releases --series-code gb-cpi --from 2018-01-01 --limit 100 --all
```

These commands emit JSON, preserve exact values and fail rather than report a
partial traversal as a complete export. The runnable
[Python export example](../examples/history.py) writes the rows with a count and
SHA-256 manifest. New archive tools are available in local stdio MCP. The hosted
MCP catalogue remains unchanged.

## Source and capture meaning

Initial collectors admit `vintage_basis=current_vintage`. They capture the
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

Retain Finance Calendar attribution and each row's `source_license` credits.
Source response fingerprints and mapping/parser versions support inspection.
Original public agency payloads are retained in the private operational archive;
this public source repository distributes client code, schemas and small test
fixtures. No new third-party supplier licence or universal twenty-year
calendar/forecast archive is implied.

See the [OpenAPI schema](../openapi.json), [Python client](../clients/python/README.md)
and [Node CLI/local MCP](../clients/node/README.md). Obtain a key through your
[Finance Calendar account](https://www.financecalendar.com/account/).
