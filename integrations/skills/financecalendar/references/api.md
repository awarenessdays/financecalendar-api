# API and client recipes

Canonical REST base: `https://www.financecalendar.com/wp-json/fc/v1`.
Hosted MCP: `https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp` (Streamable HTTP; authenticated OAuth account linking or a private API-key header).

With paid access, discover actual coverage with `/countries`, `/series` and `/status`. For Free Developer, use schedule JSON `/calendar?limit=20` without a wider date or category filter; metadata routes are outside free scope. Consult [the complete API reference](https://www.financecalendar.com/api/reference/) or `/openapi` before adding parameters. MCP tool discovery gives the installed server's current schemas. Hosted results wrap canonical data in `structuredContent.data`; local stdio results use a different envelope.

The following wider-date, non-calendar and export queries require paid access:

```text
/next?series=cpi&country=IN
/next?series=kr-cpi&country=KR
/calendar?country=GB&from=YYYY-MM-DD&to=YYYY-MM-DD&limit=500&offset=0
/calendar?category=crypto&asset=ethereum&from=YYYY-MM-DD&to=YYYY-MM-DD
/calendar?series=fomc,us-cpi&format=ics
```

Replace placeholder dates with explicit requested dates, within 92 days per window. Calendar defaults omit holidays; use `include=holidays` for an export that needs them. Apply filters before pagination. Keep country null for global crypto, and use canonical asset IDs discovered from the service rather than ticker symbols.

For change polling, retain the original `since` checkpoint until all pages complete. Follow `next_cursor` without changing bound filters or resending conflicting defaults. A snapshot-change HTTP 409 means restart that checkpoint and deduplicate consumed changes. Advance the checkpoint only after the complete interval is processed.

Use `npm install --global financecalendar-mcp` for the [Node release](https://www.npmjs.com/package/financecalendar-mcp) or `python -m pip install financecalendar` for the [Python release](https://pypi.org/project/financecalendar/) when available. [Earlier GitHub archives and checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-annual-restored-2026-11-15) provide version-pinned downloads. [Full CLI/SDK reference](https://www.financecalendar.com/api/cli/) includes every command and option. Node requires 20+; Python requires 3.10+. Both CLIs use `financecalendar`; choose the appropriate environment.

```sh
financecalendar next in-cpi --json
financecalendar calendar --country KR --from YYYY-MM-DD --to YYYY-MM-DD --json
```

Python `Client.iter_calendar` handles window chunking, pagination and stable-ID deduplication. Node/CLI commands expose individual pages; use explicit limits and offsets for a full export. `/week` and human overview output do not guarantee every matching record. Source installation and per-client configuration are documented in the public repository.

REST and local clients use your private API key; hosted MCP supports a configured API key or approved OAuth account linking. Public sample, product-offer and OpenAPI inspection routes are separate public resources. Use X-API-Key or Bearer authorization in a header; never place credentials in a URL. Free Developer requires verified email and one API key issued after approval (allow up to 48 hours for review); 100 successful responses per UTC month and at most 10/day, ongoing with no card. It covers schedule-only JSON GET /calendar and /today, UTC today through today+6, up to 20 records, no pagination, country (up to 3) and impact filters. Forecasts/results, history, other formats/routes, hosted MCP and browser tools require paid access. The [live offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) is the source for current prices. Existing enrolled trials keep original budgets/clocks. [Annually billed Starter](https://www.financecalendar.com/pricing/#starter) includes 1,000 requests/day and 25,000 per UTC calendar month; Build includes 100,000/day and Scale 1,000,000/day. Linked paid keys and hosted MCP calls share the paid account allowance; existing paid subscriptions retain their applicable terms. Configure FC_API_KEY in your client environment. The shipped key-based manifest requires environment-expanded custom headers. Compatible chat clients may use hosted OAuth account linking instead; local stdio reads FC_API_KEY. Inspect your usage response for the actual limit. Public inspection and recorded series availability do not establish guaranteed delivery latency or universal coverage.

## Historical archive

Start with authenticated `/history/coverage`; inspect actual counts, populated
values, first/last periods and access metadata. The new archive grants Starter
one year, Build ten years and Scale all available history. Omit date bounds for
the permitted default; explicit bounds must fit the returned plan window.
Legacy `/history`, curated datasets and explicit prior licences are separate. Choose an exact metric, not a guessed release
family. Historical observations are separate from dated publication records:

```sh
financecalendar history-coverage --source-id ons --all
financecalendar archive-observations --metric-id gb-cpi-all-items-yoy --limit 100 --all
financecalendar archive-releases --metric-id gb-gdp-monthly-mom-sa --limit 100 --all
```

Python `Client.iter_history_coverage()` and `Client.iter_archive()` traverse all
pages. CLI `--all` buffers a complete consistent traversal before printing.
For individual REST/local MCP pages, repeat the original filters and limit with
`next_cursor`; a changed revision returns 409 and requires a fresh traversal.
Local archive MCP tools default to 20 records, maximum 50, and preserve whole
pages. They do not loop or trim them. These three tools are not in the hosted
catalogue, which retains its established fourteen tools.

Observation `from`/`to` bounds use measured period-start dates; release bounds use
publisher publication dates. Preserve strings/nulls, units, exact derivations
and source attribution. Initial current-vintage data is not a complete original
print or historical consensus archive. `as_of` selects FC's durable evidence
receipt bound (`fc_evidence_commit_observed_bound`), not past market availability.
Source capture, publication and vintage precision have separate meanings.
See the [maintained history guide](https://github.com/awarenessdays/financecalendar-api/blob/main/docs/history.md).

## Dated source editions and historical survey forecasts

Explore numerical values in named source editions with `/history/editions` and typed public survey aggregates with `/history/forecasts`. Start with `/history/vintage-coverage` to inspect each exact metric’s stored scope and your key’s `accessible_range`. **Starter includes one year, Build ten years, and Scale all available history**; omit date bounds to use your plan window. Depth varies by metric/source. Free Developer excludes these routes; existing legacy routes and agreements keep their established access.

Edition `from`/`to` filters use publication day; edition access also requires the measured reference-period start inside the plan window. A newly published edition does not grant older measured periods beyond your plan. Forecast filters use `issue_period_start`, an ordering index; `reference_period` describes the separate target. Preserve `forecast_type`, aggregation, target definition, native horizon, exact decimal strings, nulls, units, scale and source credits. Published survey aggregates are distinct from event-matched market consensus and FC blends. Historical survey databases may contain publisher corrections; they are not automatically unchanged original archived issues. Inspect `first_print_status`, `first_print_rule_id`, native stage and correction status for source editions.

`as_of` replays Finance Calendar’s durable receipt versions. `available_before` is a separate strict source-public-availability cutoff: provide exact UTC seconds ending in `Z`; unknown, date-only and coarse issue clocks are excluded. A valid query may return no rows. These source cutoffs test the selected FC capture version and do not silently fall back to a different earlier capture. Future/coarse/naive cutoffs are rejected. Follow `next_cursor` with the same original filters and limit; on 409 restart and discard partial results.

Use REST or the current local clients for these three V2 routes. Local tools `historic_editions`, `historic_forecasts` and `vintage_coverage` default to 20/max 50 rows; all six archive tools are local only. The hosted catalogue remains 14 tools. Python 0.1.6 methods are `archive_editions`, `archive_forecasts`, `vintage_coverage` and their `iter_archive_editions`, `iter_archive_forecasts`, `iter_vintage_coverage` iterators. Node 0.2.6 exports `archiveEditions`, `archiveForecasts`, `vintageCoverage` and buffered `collectArchive(kind, params)`.

```sh
financecalendar vintage-coverage --kind forecasts --all
financecalendar historic-editions --metric-id us-gdp-real-qoq-saar --all
financecalendar historic-forecasts --metric-id eu-spf-hicp-annual-mean-p12m --all
```

Retain every row’s `source_license`, including the ECB notice that its original data are freely available at source. A historical issue month/quarter is not a publication instant. Do not substitute an index date, midnight, submission deadline or FC receipt for unknown source availability. Official source editions can identify qualified initial releases for specific mappings; do not extend that claim to every series or treat all survey history as release consensus.
