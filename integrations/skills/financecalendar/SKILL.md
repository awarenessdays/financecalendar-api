---
name: financecalendar
description: Use Finance Calendar to find scheduled economic releases, central-bank decisions, exchange holidays and covered crypto events, or build calendar integrations with its API, MCP tools, SDKs and CLI. Use for financial-event dates and source-backed release data, not personal calendar management.
license: MIT
---

# Finance Calendar

Use the connected Finance Calendar tools for release schedules and available official observations. Discover covered countries and series instead of assuming a fixed country list or that a familiar series name means the US release. A country filter excludes global crypto rows; use canonical asset IDs for asset queries.

## Find and explain events

For a current-data question, first call `feed_status` once, then query the requested events. This health check is required even for one next-release date. If that tool is unavailable, first use `GET https://www.financecalendar.com/wp-json/fc/v1/status`. If health cannot be checked, say so and do not describe the feed as fresh. Fresh snapshot generation is separate from each source's successful verification and observation freshness.

Use the request's country, date range, series and timezone. Generic `cpi`/`gdp` names normally default to the US: pass a country or an exact discovered series code for another country. Show dates, source links and the user's requested detail. Link to the existing Finance Calendar event page when returned; otherwise cite the original publisher. Attribute Finance Calendar with a link to https://www.financecalendar.com and preserve record-specific source attribution and licence/rights requirements.

Treat these distinctions as part of the answer:

- A null number is unknown, while a recorded zero is a value. Consensus estimates are not currently collected. Describe a missing value as unavailable in the feed; do not promise it will appear after release. Do not fill missing actuals or priors from article prose, estimates or another period.
- `release_at_utc=null` means no verified instant. A raw `source_clock` with unknown timezone cannot be converted using `release_tz`, which can identify only the calendar jurisdiction. `all_day=false` with date precision means unknown exact timing. Exchange closures can be all-day events.
- Keep publication date separate from the measured `period` / `source_reference_period`. An Indian fiscal publication slot is not the measured month. Some GDP publications bundle several periods/stages and do not identify one headline metric.
- Use `status`, `last_verified_at`, `data_stale` and `observation_status`. An estimated date is tentative; a retained stale record keeps its original verification. Calendar health and numerical health are separate. Missing future dates can reflect an unpublished publisher horizon.
- Current-vintage observations, publisher-reported revisions, engine-observed revisions and original first prints differ. Calendar history and the change log are not a first-print backtesting dataset. BLS payroll `value` is already in jobs; `source_value` preserves thousands and its conversion factor. Do not multiply the canonical value again.
- Distinguish an auction bidding deadline from result publication. For crypto, distinguish mainnet from testnet, scheduled activation from observed activation, voting deadline from outcome, and issuer supply projection from a confirmed unlock. Preserve complete approximate date windows rather than reporting their lower-bound index as an exact date.

If an answer depends on a missing or unverified field, state that limitation with the relevant event; continue with the verified facts.

## Retrieve complete results

Inspect `count`, `total`, continuation and truncation metadata. The hosted MCP server returns at most 50 rows per call, with lower defaults and bounded overview arrays. Recover partial week/today/series results with `calendar` using the returned dates and filters, then `limit`/`offset`. Local MCP and REST limits differ. A single `history` call is not an exhaustive export.

REST calendar windows are at most 92 days. For larger exports, chunk the requested dates, paginate every chunk, and deduplicate stable event IDs. Preserve full unknown/range timing and nested provenance when exporting JSON/CSV; human CLI output is a summary. Respect rate-limit errors and `Retry-After` instead of repeatedly retrying.

## Build an integration

Read [API and client recipes](references/api.md) when choosing a transport, exporting data or following change cursors. Prefer the existing client/tool interfaces and the current OpenAPI document over guessed endpoints. Use the user's chosen language and environment. Public reads need no key; a supplied key belongs in `X-API-Key` or the client's environment configuration, not generated source or shared URLs.

The hosted plugin is read-only. Key signup is a separate email-producing action and is not required to query data. Do not create accounts or keys as a side effect of a read request.
