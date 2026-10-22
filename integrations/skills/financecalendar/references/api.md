# API and client recipes

Canonical REST base: `https://www.financecalendar.com/wp-json/fc/v1`.
Hosted MCP: `https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp` (Streamable HTTP, public no-auth beta).

Discover actual coverage with `/countries`, `/series` and `/status`. Consult [the complete API reference](https://www.financecalendar.com/api/reference/) or `/openapi` before adding parameters. MCP tool discovery gives the installed server's current schemas. Hosted results wrap canonical data in `structuredContent.data`; local stdio results use a different envelope.

Useful public GET queries:

```text
/next?series=cpi&country=IN
/next?series=kr-cpi&country=KR
/calendar?country=GB&from=YYYY-MM-DD&to=YYYY-MM-DD&limit=500&offset=0
/calendar?category=crypto&asset=ethereum&from=YYYY-MM-DD&to=YYYY-MM-DD
/calendar?series=fomc,us-cpi&format=ics
```

Replace placeholder dates with explicit requested dates, within 92 days per window. Calendar defaults omit holidays; use `include=holidays` for an export that needs them. Apply filters before pagination. Keep country null for global crypto, and use canonical asset IDs discovered from the service rather than ticker symbols.

For change polling, retain the original `since` checkpoint until all pages complete. Follow `next_cursor` without changing bound filters or resending conflicting defaults. A snapshot-change HTTP 409 means restart that checkpoint and deduplicate consumed changes. Advance the checkpoint only after the complete interval is processed.

[Versioned beta packages and checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-2026-10-22) work without npm/PyPI registry publication. [Full CLI/SDK reference](https://www.financecalendar.com/api/cli/) includes every command and option. Node requires 20+; Python requires 3.10+. Both CLIs use `financecalendar`; choose the appropriate environment.

```sh
financecalendar next in-cpi --json
financecalendar calendar --country KR --from YYYY-MM-DD --to YYYY-MM-DD --json
```

Python `Client.iter_calendar` handles window chunking, pagination and stable-ID deduplication. Node/CLI commands expose individual pages; use explicit limits and offsets for a full export. `/week` and human overview output do not guarantee every matching record. Source installation and per-client configuration are documented in the public repository.

Anonymous access currently has a shared per-IP allowance of 2,000 calls/day. A free personal REST/local-client key raises it to 10,000/day. The hosted no-auth connector does not forward personal credentials; platform proxy IPs may be shared. Inspect the response's transport/rate metadata. Public endpoint access and recorded series availability do not establish enterprise uptime or comprehensive worldwide coverage.
