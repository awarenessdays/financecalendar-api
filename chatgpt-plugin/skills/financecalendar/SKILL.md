---
name: financecalendar
description: Find economic releases, central-bank decisions, exchange holidays and covered crypto events through the linked Finance Calendar account, preserving recorded timing and source evidence.
license: MIT
---

# Finance Calendar

Use the OAuth-linked Finance Calendar tools for release schedules and available official observations. Hosted MCP requires existing eligible account access (paid access or an applicable retained grant); connected tool requests share that account's API allowance. Sign-in and consent happen on Finance Calendar, never in the conversation. Do not ask for passwords, API keys or tokens. Discover covered countries and series instead of assuming a fixed country list or that a familiar series name means the US release. A country filter excludes global crypto rows; use canonical asset IDs for asset queries.

## Find and explain events

For a current-data question, call `feed_status` once, then query the requested events. Inspect each returned record's `last_verified_at` and `data_stale`. If the connected health tool is unavailable, say health could not be checked and do not describe the feed as fresh. Do not bypass the linked connection, retrieve a private credential or create a replacement key to answer a query. Fresh snapshot generation is separate from each source's successful verification and observation freshness.

If the client requests authentication, let its OAuth flow link the user's existing account. For missing account permission, explain which requested capability is unavailable. Do not promote plans, quote prices, suggest an upgrade or link to checkout. For expired or revoked authorization, explain that the connection needs to be authenticated again. For rate limits, report the returned reset time and stop repeated retries; a conversation can use several metered calls.

Use the request's country, date range, series and timezone. Generic `cpi`/`gdp` names normally default to the US: pass a country or an exact discovered series code for another country. Show dates, source links and the user's requested detail. Link to the existing Finance Calendar event page when returned; otherwise cite the original publisher. Attribute Finance Calendar with a link to https://www.financecalendar.com and preserve record-specific source attribution and licence/rights requirements.

Treat these distinctions as part of the answer:

- A null number is unknown, while a recorded zero is a value. Provider consensus is recorded for 12 selected US headline series where evidence is available; a missing consensus remains unknown. Paid responses also carry `forecasts`: a Finance Calendar blend of market forecasts for headline measures across 10 economies, each with its measure, unit, `as_of` time and `source_families` count. Present it as a blended market forecast, quote the measure it belongs to, and keep it separate from consensus. Describe a missing value as unavailable in the feed; do not promise it will appear after release. Do not fill missing actuals or priors from article prose, estimates or another period.
- `release_at_utc=null` means no verified instant. A raw `source_clock` with unknown timezone cannot be converted using `release_tz`, which can identify only the calendar jurisdiction. `all_day=false` with date precision means unknown exact timing. Exchange closures can be all-day events.
- Keep publication date separate from the measured `period` / `source_reference_period`. An Indian fiscal publication slot is not the measured month. Some GDP publications bundle several periods/stages and do not identify one headline metric.
- Use `status`, `last_verified_at`, `data_stale` and `observation_status`. An estimated date is tentative; a retained stale record keeps its original verification. Calendar health and numerical health are separate. Missing future dates can reflect an unpublished publisher horizon.
- Current-vintage observations, publisher-reported revisions, engine-observed revisions and original first prints differ. Calendar history and the change log are not a first-print backtesting dataset. BLS payroll `value` is already in jobs; `source_value` preserves thousands and its conversion factor. Do not multiply the canonical value again.
- Distinguish an auction bidding deadline from result publication. For crypto, distinguish mainnet from testnet, scheduled activation from observed activation, voting deadline from outcome, and issuer supply projection from a confirmed unlock. Preserve complete approximate date windows rather than reporting their lower-bound index as an exact date.

If an answer depends on a missing or unverified field, state that limitation with the relevant event; continue with the verified facts.

## Retrieve complete results

Inspect `count`, `total`, continuation and truncation metadata. The hosted MCP server returns at most 50 rows per call, with lower defaults and bounded overview arrays. Recover partial week/today/series results with `calendar` using the returned dates and filters, then `limit`/`offset`. A single `history` call is not an exhaustive export.

For larger exports, chunk the requested dates, paginate every chunk, and deduplicate stable event IDs. Preserve full unknown/range timing and nested provenance when exporting JSON/CSV. Respect rate-limit errors and `Retry-After` instead of repeatedly retrying. The complete snapshot download remains subject to the connected account's existing entitlement; do not imply that installing this plugin grants it.

Read [hosted tool usage and record semantics](references/api.md) for tool selection, interpretation and continuation handling.
