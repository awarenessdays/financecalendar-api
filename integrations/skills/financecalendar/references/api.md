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

[Versioned beta packages and checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-history-2026-11-14) work without npm/PyPI registry publication. [Full CLI/SDK reference](https://www.financecalendar.com/api/cli/) includes every command and option. Node requires 20+; Python requires 3.10+. Both CLIs use `financecalendar`; choose the appropriate environment.

```sh
financecalendar next in-cpi --json
financecalendar calendar --country KR --from YYYY-MM-DD --to YYYY-MM-DD --json
```

Python `Client.iter_calendar` handles window chunking, pagination and stable-ID deduplication. Node/CLI commands expose individual pages; use explicit limits and offsets for a full export. `/week` and human overview output do not guarantee every matching record. Source installation and per-client configuration are documented in the public repository.

REST and local clients use your private API key; hosted MCP supports a configured API key or approved OAuth account linking. Public sample, product-offer and OpenAPI inspection routes are separate public resources. Use X-API-Key or Bearer authorization in a header; never place credentials in a URL. Free Developer requires verified email and one active account key; 100 successful responses per UTC month and at most 10/day, ongoing with no card. It covers schedule-only JSON GET /calendar and /today, UTC today through today+6, up to 20 records, no pagination, country (up to 3) and impact filters. Forecasts/results, history, other formats/routes, hosted MCP and browser tools require paid access. Existing enrolled trials keep original budgets/clocks. Starter is US$9.99/year with 1,000 requests/day and 25,000 per UTC calendar month; Build includes 100,000/day and Scale 1,000,000/day. Linked paid keys and hosted MCP calls share the paid account allowance; existing paid subscriptions retain their applicable terms. Configure FC_API_KEY in your client environment. The shipped key-based manifest requires environment-expanded custom headers. Compatible chat clients may use hosted OAuth account linking instead; local stdio reads FC_API_KEY. Inspect your usage response for the actual limit. Public inspection and recorded series availability do not establish guaranteed delivery latency or universal coverage.

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
