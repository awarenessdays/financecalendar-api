---
name: financecalendar
description: Use Finance Calendar to find scheduled economic releases, central-bank decisions, exchange holidays, covered crypto events and historical economic observations, or build calendar integrations with its API, MCP tools, SDKs and CLI. Use for financial-event dates and source-backed release data, not personal calendar management.
license: MIT
---

# Finance Calendar

Use the connected Finance Calendar tools for release schedules and available official observations. Discover covered countries and series instead of assuming a fixed country list or that a familiar series name means the US release. A country filter excludes global crypto rows; use canonical asset IDs for asset queries.

## Find and explain events

For a paid-plan or hosted-MCP current-data question, first call `feed_status` once, then query the requested events. For Free Developer schedule JSON, query `/calendar` or `/today` directly within UTC today through today+6, at most 20 records, no pagination: `/status`, `/next` and hosted MCP are outside that scope. For paid responses, inspect each returned record’s `last_verified_at` and `data_stale`. Free Developer omits numerical and freshness evidence; cite its schedule/source fields without inferring feed-wide freshness. Production data requests require the caller's API key; public OpenAPI, product-offer and fixed-sample inspection do not. For paid access, if that tool is unavailable, first use `GET https://www.financecalendar.com/wp-json/fc/v1/status` with the `X-API-Key` header read from private `FC_API_KEY` configuration. Never put a key in a URL or output. If health cannot be checked, say so and do not describe the feed as fresh. Fresh snapshot generation is separate from each source's successful verification and observation freshness.

With paid access, use the request's country, date range, series and timezone. Free Developer supports country/impact filters and dates narrowed within its seven-date UTC window; do not add paid-only series or timezone parameters. Generic `cpi`/`gdp` names normally default to the US: pass a country or an exact discovered series code for another country. Show dates, source links and the user's requested detail. Link to the existing Finance Calendar event page when returned; otherwise cite the original publisher. Attribute Finance Calendar with a link to https://www.financecalendar.com and preserve record-specific source attribution and licence/rights requirements.

Treat these distinctions as part of the answer:

- A null number is unknown, while a recorded zero is a value. Provider consensus is recorded for 12 selected US headline series where evidence is available; a missing consensus remains unknown. Paid responses also carry `forecasts`: a Finance Calendar blend of market forecasts for headline measures across 10 economies, each with its measure, unit, `as_of` time and `source_families` count. Present it as a blended market forecast, quote the measure it belongs to, and keep it separate from consensus. Describe a missing value as unavailable in the feed; do not promise it will appear after release. Do not fill missing actuals or priors from article prose, estimates or another period.
- `release_at_utc=null` means no verified instant. A raw `source_clock` with unknown timezone cannot be converted using `release_tz`, which can identify only the calendar jurisdiction. `all_day=false` with date precision means unknown exact timing. Exchange closures can be all-day events.
- Keep publication date separate from the measured `period` / `source_reference_period`. An Indian fiscal publication slot is not the measured month. Some GDP publications bundle several periods/stages and do not identify one headline metric.
- Use `status`, `last_verified_at`, `data_stale` and `observation_status`. An estimated date is tentative; a retained stale record keeps its original verification. Calendar health and numerical health are separate. Missing future dates can reflect an unpublished publisher horizon.
- Current-vintage observations, publisher-reported revisions, engine-observed revisions and original first prints differ. Calendar history and the change log are not a first-print backtesting dataset. BLS payroll `value` is already in jobs; `source_value` preserves thousands and its conversion factor. Do not multiply the canonical value again.
- Distinguish an auction bidding deadline from result publication. For crypto, distinguish mainnet from testnet, scheduled activation from observed activation, voting deadline from outcome, and issuer supply projection from a confirmed unlock. Preserve complete approximate date windows rather than reporting their lower-bound index as an exact date.

If an answer depends on a missing or unverified field, state that limitation with the relevant event; continue with the verified facts.

## Retrieve complete results

Inspect `count`, `total`, continuation and truncation metadata. The hosted MCP server returns at most 50 rows per call, with lower defaults and bounded overview arrays. Recover partial week/today/series results with `calendar` using the returned dates and filters, then `limit`/`offset`. Local MCP and REST limits differ. A single `history` call is not an exhaustive export.

The complete-results instructions in this section apply to paid access. Free Developer returns at most 20 schedule records per response within its seven-date UTC window and does not support pagination or complete exports. Already-enrolled finite evaluations retain their separate original ten-record response limit and 25-request/48-hour grant. Paid REST calendar windows are at most 92 days. For larger exports, chunk the requested dates, paginate every chunk, and deduplicate stable event IDs. Preserve full unknown/range timing and nested provenance when exporting JSON/CSV; human CLI output is a summary. Respect rate-limit errors and `Retry-After` instead of repeatedly retrying.

## Research historical data

For long-run observations or past publications, discover actual stored depth
with `/history/coverage` before choosing dates. Use `/history/observations` by
measured reference-period start, or `/history/releases` by publication date.
The local stdio tools `history_coverage`, `historic_observations` and
`historic_releases` are available in client 0.2.4; the hosted catalogue is
unchanged. If they are absent, use authenticated REST or the Python/CLI archive
methods described in [the history recipes](references/api.md#historical-archive).

Keep exact decimal strings, derived-input evidence and nulls. Follow every
`next_cursor` with unchanged filters and limit. A 409 invalidates the partial
export; restart rather than reporting it complete. Current-vintage backfills
do not establish original prints or old market forecasts. `as_of` uses FC's
durable evidence receipt bound; it cannot make a new import known years ago.

## Build an integration

Read [API and client recipes](references/api.md) when choosing a transport, exporting data or following change cursors. Prefer the existing client/tool interfaces and the current OpenAPI document over guessed endpoints. Use the user's chosen language and environment. Every production data request requires a key. Ongoing Free Developer at https://www.financecalendar.com/account/?free=1 requires verified email and one account key; it provides 100 successful JSON schedule responses per UTC month, at most 10/day, with no card or expiry. GET /calendar and /today cover UTC today through today+6 with at most 20 records, up to 3 country codes and impact filters. Free omits forecasts/results, numerical evidence, history, other formats, hosted MCP and browser tools. Starter US$9.99/year adds these richer capabilities. Existing enrolled trials and paid/legacy grants remain intact. Keep the key in `X-API-Key` or the client's private environment configuration, not generated source or shared URLs.

The shipped hosted plugin manifest is read-only and uses a configured API key with paid access. OAuth-capable clients can connect separately through the hosted account-linking setup. Account signup, email verification and key creation are separate actions; do not create accounts or keys as a side effect of a read request.
