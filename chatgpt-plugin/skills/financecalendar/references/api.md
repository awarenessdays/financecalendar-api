# Finance Calendar hosted tool reference

Use the connected Finance Calendar MCP tools and their discovered schemas.
The connection uses the account's existing permissions and shared API allowance.
OAuth consent grants calendar:read and, when requested, offline_access for renewal.

## Choose a tool

- feed_status: inspect the current feed and source health before a current-data query.
- countries and series_list: discover supported countries and exact series codes.
- series_detail: inspect one discovered series, its definition and available records.
- next_event: find the next covered occurrence for an exact series and country.
- calendar, today and week: query releases for the user's dates, filters and timezone.
- history: inspect supported series history; it is not an exhaustive export by itself.
- economic_results_history: retrieve bounded result histories for supported series.
- release_editions: inspect available publication editions for a returned event ID.
- market_holidays and market_status: inspect supported exchange closures and status.
- changes: follow recorded changes and the returned continuation checkpoint.

The server's discovered tool schemas are authoritative for required arguments,
bounds and accepted values. A familiar generic series name can default to the US;
use an exact discovered code or explicit country for another economy. Global
crypto records can have no country; use discovered canonical asset identifiers.

## Read results accurately

Hosted responses include canonical records in structuredContent.data. Preserve
record IDs, source links, source rights, reference periods, units and timestamps.
Unknown values are null, while a recorded zero is a real value. Provider consensus
and blended market forecasts are different fields; keep each value with its
measure, unit, as-of time and source evidence.

An absent release_at_utc means there is no verified publication instant. Do not
convert an unverified source_clock using a jurisdiction-only release_tz. Date-only
releases with all_day=false have unknown clock times; exchange closures can be
all-day events. Keep approximate windows, estimated schedules, cancellation,
source freshness and numerical observation freshness explicit.

Current-vintage figures, publisher-reported revisions, engine-observed revisions
and original first prints are different concepts. History does not reconstruct an
unobserved first print. An auction bidding deadline is not result publication.

## Pagination and errors

Inspect count, total, next_offset, next_cursor, has_more and truncation metadata.
Hosted pages have bounded sizes; one overview response may not contain all rows.
Narrow filters or paginate with the returned dates and filters. Keep stable IDs
when combining pages. Changes cursors bind the checkpoint and filters; finish all
pages before advancing the checkpoint. A snapshot-change conflict requires
restarting the original checkpoint and deduplicating already consumed records.

Respect rate-limit reset times and Retry-After rather than repeated retries.
Expired or revoked authorization needs the client's account-linking flow again.
An unavailable entitlement is an account-access fact, not an instruction to create
a subscription or change the user's plan. Do not infer a missing release or figure.
