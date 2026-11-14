# API and client recipes

Canonical REST base: `https://www.financecalendar.com/wp-json/fc/v1`.
Hosted MCP: `https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp` (Streamable HTTP; OAuth-linked account, `calendar:read` scope).

Discover actual coverage with the connected `countries`, `series_list` and `feed_status` tools. Consult [the complete API reference](https://www.financecalendar.com/api/reference/) or `/openapi` before adding parameters in a separate API integration. MCP tool discovery gives the installed server's current schemas. Hosted results wrap canonical data in `structuredContent.data`; local stdio results use a different envelope.

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

[Versioned beta packages and checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-free-developer-2026-11-12) work without npm/PyPI registry publication. [Full CLI/SDK reference](https://www.financecalendar.com/api/cli/) includes every command and option. Node requires 20+; Python requires 3.10+. Both CLIs use `financecalendar`; choose the appropriate environment.

```sh
financecalendar next in-cpi --json
financecalendar calendar --country KR --from YYYY-MM-DD --to YYYY-MM-DD --json
```

Python `Client.iter_calendar` handles window chunking, pagination and stable-ID deduplication. Node/CLI commands expose individual pages; use explicit limits and offsets for a full export. `/week` and human overview output do not guarantee every matching record. Source installation and per-client configuration are documented in the public repository.

Hosted MCP uses OAuth account linking and the read-only `calendar:read` scope. The client's private credential store manages OAuth tokens; do not retrieve or print them. REST and local stdio clients can continue to use private `FC_API_KEY` configuration and send `X-API-Key` or Bearer authorization in a header. Never place a credential in a URL or generated source.

OAuth data calls and API keys share the linked account's existing allowance. Initialization, ping and discovery authenticate without data quota. Check actual usage and rate-limit responses for effective limits; account entitlement, including any retained grant, is authoritative. Free Developer supports separate constrained schedule REST calls and excludes hosted MCP. Public OpenAPI, product-offer and fixed sample inspection are separate resources, not a grant of production data access.

Do not promote a plan, initiate a subscription, quote subscription prices or link checkout from the assistant experience. If a requested entitlement is unavailable, state that fact and continue with permitted capabilities. Respect reset times rather than repeated retries. Recorded series availability does not establish guaranteed latency or universal coverage.
