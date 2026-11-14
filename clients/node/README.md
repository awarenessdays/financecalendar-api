# financecalendar-mcp

Bring economic-release dates, consensus forecasts and published results into AI assistants and terminal workflows. Paid plans support release forecasts for 60 mapped headline measures across 10 economies. Available values appear in each event’s `forecasts` field, refreshed hourly and labelled with their update time and source count. Coverage varies by release; the mapped total is not the number with a live forecast at any moment. The [financecalendar.com API](https://www.financecalendar.com/api/) also includes provider consensus across **12 selected US headline release series**, with source-linked actual/prior values for covered records. The same API also supplies central bank decisions, exchange holidays and source-backed crypto events. Use each record’s metric, reference period and source evidence when comparing expectations with results.

One package, two binaries:

- `financecalendar-mcp`: an MCP server over stdio for Claude Desktop, Claude Code, Cursor and any other MCP client.
- `financecalendar`: a CLI for your terminal and scripts.

[Paid API plans](https://www.financecalendar.com/pricing/) start at **US$9.99/year** for Starter (**1,000 requests/UTC day and 25,000/UTC calendar month**). Build is **US$9.99/month or US$95.90/year** for **100,000/day**. Scale is **US$29/month or US$278.40/year** for **1,000,000/day** and the complete current dataset download. [Inspect the public sample](https://www.financecalendar.com/api/sample/) before choosing a plan.

[Free Developer](https://www.financecalendar.com/account/?free=1) is ongoing schedule JSON access: **100 successful responses per UTC calendar month, at most 10 per UTC day**, one verified account and one active key, no card or automatic charge. Use `GET /calendar` or `/today` for economic-release and central-bank schedules from UTC today through the following six days, with up to 20 records and no pagination. Country (up to three codes) and impact filters are supported; `from` and `to` may narrow, but cannot extend, the seven-date UTC window. Free `/today` is the current UTC date’s schedule, without market-status or holiday payloads. Free responses omit forecasts, consensus, actual/prior figures and numerical evidence, and mark releases that have them (`figures_available`, `result_available`); Starter adds release forecasts across 10 economies, these recorded fields, wider dates/history, formats, hosted MCP and browser tools.

The [public calendar remains free to browse](https://www.financecalendar.com/events/). Hosted MCP, status and the wider data examples below require eligible paid access or an applicable retained grant. The public sample, product offer and OpenAPI document can be read directly without a key; SDK requests consistently use your configured account key. Set `FC_API_KEY` securely for local clients.

Starter costs **US$9.99/year** and includes **1,000 requests per UTC day and 25,000 per UTC calendar month**. Build includes **100,000 requests per day** and Scale **1,000,000 per day**. All account keys share the applicable allowance. Daily usage resets at 00:00 UTC; monthly usage resets at 00:00 UTC on the first day of the next calendar month. Existing paid customers retain their contracted prices and applicable allowances; check your account or `/keys/me` for effective limits. See [current plans](https://www.financecalendar.com/pricing/) for billing options and complete snapshot downloads.

Free Developer counts successful committed HTTP 200 JSON schedule responses, including valid empty responses. Invalid or denied requests, quota errors and pre-commit server failures do not consume its allowance. Usage is shared by the account and survives key rotation; daily and monthly resets follow UTC. Already-enrolled evaluations retain their original 25-successful-request budget, 48-hour clock from first use and original scope. New trial enrolment is closed. Existing paid, legacy and custom access grants are preserved; no account is silently converted to Free Developer.

For paid plans, daily and monthly quota usage counts admitted requests, not successful responses. Requests refused with HTTP 429 do not consume more allowance; a request that passes the quota check can still consume allowance if it later returns an error. Retained per-key request history remains a separate attempt diagnostic and can include rejected requests.

## Install the tested beta download

[Download packages and SHA-256 checksums](https://github.com/awarenessdays/financecalendar-api/releases/tag/clients-free-developer-2026-11-12). Use the direct package URL in your chosen environment:

```sh
npm install --global https://github.com/awarenessdays/financecalendar-api/releases/download/clients-free-developer-2026-11-12/financecalendar-mcp-0.2.3.tgz
```

Registry publication remains pending. The GitHub release is a versioned, tested distribution; source installation is also available below.

## Hosted MCP connector: ChatGPT and Claude

The public beta connects over HTTPS without installing this package. Server URL:

```text
https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
```

Use **Streamable HTTP** and **OAuth account linking** in Claude, ChatGPT or another compatible hosted client. Sign in on `www.financecalendar.com`, review the client and read-only `calendar:read` permission, then approve the connection. Optional `offline_access` lets the client renew its connection. Hosted access requires an existing verified account with eligible paid access or an applicable retained grant. Linking does not create a subscription, change your plan or add quota.

Existing header-capable HTTP MCP clients can continue to send their own private `X-API-Key` or `Authorization: Bearer` credential on every POST. Configure it in the client's private authentication settings; never put credentials in URLs, shared configuration files or a conversation. Platform and workspace policies still govern custom connectors. No directory listing or automatic installation in another platform is implied.

A missing or invalid credential returns HTTP 401; revoked or disallowed accounts return an access error. Reauthenticate an expired OAuth connection through the client's sign-in flow. Review or revoke linked assistants in your [Finance Calendar connection settings](https://www.financecalendar.com/?fc_oauth_connections=1). Disconnecting does not cancel your subscription or revoke unrelated API keys. The local stdio package below uses `FC_API_KEY` in its private process environment; hosted OAuth does not change the local package's authentication.

Try: “Find the next UK CPI release, show its time in Europe/London and cite its
publisher. Check source health and say which values or dates are uncertain.”

### Hosted tools and output

The hosted server provides the 13 tools listed below plus `feed_status()` for
snapshot age, source health, stale records and numerical coverage. All are
read-only. It does not expose the local briefing prompt or OpenAPI resource,
tasks, sessions, server notifications or subscriptions. GET and DELETE return
405; Streamable HTTP requests use POST and receive JSON, without an SSE stream.

Hosted results include identical JSON text and `structuredContent` containing:

```json
{
  "data": { "count": 0, "total": 0, "events": [] },
  "attribution": { "source": "financecalendar.com" },
  "transport": { "api_status": 200, "rate_limit": {} }
}
```

This illustrates the envelope, not a live event result. `data` holds the
canonical API body; `attribution` also carries links and rights guidance.
`transport.rate_limit` carries available rate headers and `Retry-After`.
API failures return `isError: true`; inspect `transport.api_status` even when
the MCP HTTP response is 200. Local stdio tools return the API body directly,
without this envelope.

`economic_results_history` returns 1–5 releases per call (default 5) in both
local and hosted MCP, preserving complete edition evidence. Continue with
`next_offset` and both first-page pins, `ledger_cursor` and
`publication_revision`. Hosted `calendar`, `history`, `release_editions`
and initial `changes` calls default to 20 rows and accept 1–50.
Calendar supports `offset`. Continue changes with only `cursor`;
do not inject a new limit. Overview tools bound large arrays to at most 50
entries and can return fewer to meet the 120,000-byte encoded response cap.
Partial results carry `truncation.fields`, original counts and recovery
instructions; check canonical totals too. Narrow filters, page `calendar`, or
use the supplied full REST endpoint. A partial overview is not a complete
export. Cursor pages are never trimmed after a cursor is issued: a size error
requires restarting from the original checkpoint with a smaller initial limit
and deduplicating. Requests are limited to 32,768 bytes; unknown arguments are
rejected.

Every hosted protocol POST, including initialize, ping and tools/list, validates
the OAuth account link or private caller API key. Data tool calls retain that
caller's account identity at the canonical REST API and consume the same account
allowance as direct API calls. Initialization, ping and tool discovery do not
consume data quota. No shared customer credential or anonymous proxy allowance is
provided. Respect account rate headers and `Retry-After`. Cookies and unrelated
client headers are not forwarded. OAuth connections do not consume ordinary
personal API-key slots.
See the [MCP reference](https://www.financecalendar.com/api/mcp/).

## Install from source

Registry publication is pending. Install the current version from the public
source repository:

```sh
git clone https://github.com/awarenessdays/financecalendar-api.git
cd financecalendar-api/clients/node
npm ci
npm link
financecalendar --help
```

For MCP, configure `node` as the command and the absolute path to this checkout's `mcp.js` as its argument, as shown below. The `financecalendar-mcp` name is not currently published on npm; use the tested download or source command above.

Requires Node 20 or newer.

Human CLI output shows the reference `period` and `release_stage` when provided.
Unknown economic release times are labelled `time unknown`; exchange holidays
retain `all day`. Raw JSON preserves the API fields unchanged.

## Local MCP server

A Free Developer key can call the bounded JSON `/calendar` and `/today` routes through curl, Python, the CLI or a custom local MCP wrapper. Hosted MCP and wider data tools require eligible paid access or an applicable retained grant. For a first Free request, use `calendar` with `limit=20` and no timezone, category or pagination parameters.

### Claude Desktop

Add to `claude_desktop_config.json` (Settings, Developer, Edit Config), using
your actual API key in a private local configuration:

```json
{
  "mcpServers": {
    "financecalendar": {
      "command": "node",
      "args": ["/absolute/path/financecalendar-api/clients/node/mcp.js"],
      "env": { "FC_API_KEY": "fc_live_YOUR_ACTUAL_KEY" }
    }
  }
}
```

Use the absolute path to your own source checkout. Missing keys fail before any data request. Local wrappers can use only the documented Free Developer JSON schedule scope; hosted MCP and wider data tools require paid access.

### Claude Code

```sh
claude mcp add financecalendar -e FC_API_KEY=your-key -- node /absolute/path/financecalendar-api/clients/node/mcp.js
```

### Cursor

Add to `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "financecalendar": { "command": "node", "args": ["/absolute/path/financecalendar-api/clients/node/mcp.js"], "env": { "FC_API_KEY": "fc_live_YOUR_ACTUAL_KEY" } }
  }
}
```

### Tools

| Tool | What it does |
|---|---|
| `next_event(series, country?, tz?, asset?, category?)` | Next occurrence of a series: `fomc`, `cpi`, `nfp`, `ecb`, `boe`, `uk-cpi`... |
| `calendar(from?, to?, country?, impact?, category?, asset?, series?, include_holidays?, status?, tz?, limit?, offset?)` | Events in a date range (max 92 days) |
| `today(country?, impact?, tz?, asset?, category?)` | Today's releases, NYSE status and exchange closures |
| `week(which?, country?, impact?, category?, asset?, series?, include_holidays?, tz?)` | This week or next, Monday to Sunday |
| `series_list(country?, category?, kind?, asset?)` | Every series with code, aliases and next date |
| `series_detail(code, tz?, asset?)` | One series: next, last, upcoming, history, long-run dataset |
| `history(series, from?, to?, limit?, tz?, asset?)` | Past releases with consensus, prior and actual |
| `economic_results_history(series, from?, to?, limit?, offset?, ledger_cursor?, publication_revision?)` | Consensus and results across 12 US release series, with source and edition evidence |
| `release_editions(event_id, limit?, offset?, ledger_cursor?, publication_revision?)` | Accepted numerical editions with reference periods, exact values and availability/receipt clocks |
| `market_holidays(exchange?, year?)` | Exchange holidays and early closes (nyse, lse, cme, jpx...) |
| `market_status(exchange?)` | Is the exchange open right now? |
| `changes(since?, series?, change?, limit?, cursor?)` | A page of changes with explicit continuation metadata |
| `countries()` | Countries covered with series and event counts |

Every tool returns the API's JSON as text and `structuredContent`, with read-only annotations. Errors (bad parameter, unknown series, rate limit) come back as tool errors with the API's message.

Also included:

- Prompt `economic_calendar_briefing(country?, days?)`: asks the model to pull the high-impact calendar and summarise the week's risk events.
- Resource `financecalendar://openapi`: the live OpenAPI 3.1 document from `{base}/openapi`.

## Crypto coverage

Use canonical asset IDs such as `ethereum`, rather than ticker symbols. Discover
currently covered series and assets with `series_list(category="crypto")`.
The existing `calendar`, `today`, `week`, `next_event`, `series_list`,
`series_detail` and `history` MCP tools accept `asset`; calendar-like tools also
accept `category="crypto"`. Macro queries and existing tool names remain valid.

```sh
financecalendar series --category crypto
financecalendar calendar --category crypto --asset ethereum --json
financecalendar next ethereum-network-upgrades --asset ethereum --tz UTC
financecalendar week --category crypto --asset ethereum
```

Crypto is global (`country=null`), with nullable impact. Do not add a country
filter to a global asset query. A testnet environment is distinct from mainnet;
`crypto.activation_status="scheduled"` is configuration evidence, not proof of
observed activation. Roadmap targets retain their complete `date_window_start`
and `date_window_end`; `date` is only the lower-bound index. Calendar filters
include overlapping windows; history includes them only after the upper bound.

Coverage includes network schedules, vesting installments, governance voting
deadlines and issuer supply projections. Inspect `crypto.event_type`:

- `network-upgrade`: check `environment` and `activation_status`; a configured schedule is not observed activation.
- `token-unlock`: retain `schedule_id`, `installment`, `beneficiaries`, `unlock_status`, `date_basis`, `token_amount` and `token_amount_basis` when supplied. A schedule or upper-bound amount does not prove tokens were transferred or sold.
- `governance-vote`: retain `dao`, `space_id`, `proposal_id`, optional `proposal_title`, `voting_start`, `voting_end`, `voting_state`, `voting_type` and `choice_count`. The event marks a deadline, not approval, rejection or execution.
- `supply-projection`: retain `projection_status`, `projected_circulating_supply`, `projected_monthly_supply_change` and `date_basis`. These are issuer estimates, not confirmed unlocks or observed circulating supply; decimal strings retain source precision.

Check `verification_url`, `verification_method`, `manually_reviewed_at`,
`last_verified_at` and `data_stale`. Public records combine licensed feeds and
independently normalised factual records. `source_license` carries an actual
upstream licence and its credit requirements when applicable; `source_rights`
carries the factual provenance, access basis, review time, attribution and
notice without asserting a publisher copyright licence. Either may be null.
An optional `discovery_url` identifies where an event was found, including an
aggregator; it is separate from primary `source_url` and verification evidence.
CoinMarketCal internal API evaluation payloads are never returned.

MCP JSON, CLI `--json` and API CSV via CLI `--csv` preserve these nested fields;
CSV stores structured objects as JSON cells. Retain all source-specific rights,
licence and attribution metadata when redistributing. PatternPlus records
require the linked credit [Data: PatternPlus](https://pattern.plus), carried in
`source_license.attribution` and `source_license.attribution_url`, alongside the
licence link and adaptation notice. Human CLI output includes source credits,
attribution links and factual notices, but remains a summary; use JSON/CSV to
retain every metadata field when redistributing.
Coverage varies by source and asset; an empty result is valid and does not
establish comprehensive crypto coverage.

This server retains its existing SDK v1 dependency. SDK v2 is the current stable
line; `npx @modelcontextprotocol/codemod@latest v1-to-v2 .` is the migration path.

## CLI

```sh
financecalendar next fomc
financecalendar next cpi --country uk --tz Europe/London
financecalendar today
financecalendar week --next --impact high
financecalendar calendar --from 2026-11-01 --to 2026-11-30 --country us,gb --holidays
financecalendar calendar --from 2026-11-01 --to 2026-11-30 --csv > november.csv
financecalendar series --country gb
financecalendar show boe
financecalendar history us-cpi --limit 12
financecalendar results us-adp --from 2026-01-01 --limit 20
financecalendar editions adp-2026-09 --limit 20 --offset 0
financecalendar holidays lse 2027
financecalendar status hkex
financecalendar changes --since 2026-10-18T00:00:00Z
financecalendar countries
```

Add `--json` to any command for the raw API response and `--help` for the full usage. Times are shown in your local zone unless you pass `--tz`:

For change-feed polling, follow `next_cursor` using `changes --cursor …` until
`has_more` is false. A cursor binds the snapshot, original filters and page size;
omit those parameters when continuing. Advance your `since` checkpoint only
after the entire traversal. On HTTP 409, restart from the original `since` and
filters and deduplicate repeated changes. If that checkpoint has expired from
the 30-day retention window, reload the full snapshot.

```
$ financecalendar next fomc --tz America/New_York
Wed 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold
https://www.financecalendar.com/event/fomc-rate-decision-october-2026/
```

`results` and `editions` return JSON by default so decimal strings, null values,
edition IDs and pagination stay together. Follow `next_offset` with the same
filters plus `ledger_cursor` and `publication_revision` returned on the first
page. Both pins are required when offset is above zero; pass CLI flags
`--ledger-cursor` and `--publication-revision`. Ledger appends cannot enter a
pinned traversal. A changed publication returns HTTP 409: restart at offset
zero without old pins. The corresponding MCP tools use canonical series `us-jolts`, `us-adp`,
`us-ism-services` and `us-trade-balance`; availability follows the enrichment
service and account access gate. `available_at` and `received_at` distinguish
recorded source availability from Finance Calendar receipt. Provider archives
are labelled separately from engine captures. `as_of_supported` is false;
these endpoints do not reconstruct an original first print. Calls use the same
API key and quota rules as other data requests.

## Environment variables

| Variable | Purpose |
|---|---|
| `FC_API_KEY` | Required account API key, sent as `X-API-Key` on every request. Create one in your [account](https://www.financecalendar.com/account/). |
| `FC_API_BASE` | Alternative base URL. Default `https://www.financecalendar.com/wp-json/fc/v1`; an edge mirror at `https://api.financecalendar.com/v1` is planned. |

## Use it as a library

```js
import { api, formatEvent } from "financecalendar-mcp/lib.js";

const { next } = await api("/next", { series: "ecb" }, { apiKey: process.env.FC_API_KEY });
console.log(formatEvent(next, { tz: "Europe/Frankfurt" }));
```

`api()` throws an `Error` whose message carries the API's `error` text and HTTP status; on 429 it adds the `Retry-After` seconds (`err.retryAfter`).

## Data terms

Free Developer provides the bounded schedule scope above; richer data and wider features require a paid plan. Use is subject to the current [API service terms](https://www.financecalendar.com/api/terms/) and applicable source terms and credits. Include a visible link to [financecalendar.com](https://www.financecalendar.com) wherever the data appears. Retain each record's `source_license` requirements, including `attribution_url`, source and licence links, full notices and adaptation labels; PatternPlus records require [Data: PatternPlus](https://pattern.plus). Preserve `source_rights` attribution, evidence, access basis and notice for independently normalised facts. This rights metadata does not assert a publisher copyright licence. Earnings dates are not included. Full terms, rate limits and the changelog: [financecalendar.com/api](https://www.financecalendar.com/api/).

## Source and issues

[Client source and tests](https://github.com/awarenessdays/financecalendar-api/tree/main/clients/node) · [Report an issue](https://github.com/awarenessdays/financecalendar-api/issues).

## Development

```sh
npm test            # node --test, fully offline (fetch is mocked with recorded fixtures)
npm pack --dry-run  # confirm the published file list
```

Client source code: MIT, Awareness Days Ltd / financecalendar.com. The code licence does not license upstream data; data terms and record-level rights metadata apply separately.

## Official numerical observations

Where a result is explicitly mapped, responses retain `observations`,
`observation_status`, `observation_metric_id` and `observation_fields`. Each
observation identifies its value, unit, reference period, source, engine capture
time and any revisions. The previous value uses the previous reference period
at the current observed vintage; it is not a reconstructed original first print.
Numerical-source staleness is separate from calendar schedule staleness.
Text output explains this distinction and retains source credits; JSON and CSV
retain the available lineage. Unknown consensus stays absent. See the
[REST reference](https://www.financecalendar.com/api/reference/) for the contract.

Expanded US coverage brings consensus forecasts and release results together for
CPI, nonfarm payrolls, PPI, retail sales, headline PCE, ISM Manufacturing,
industrial production, Consumer Confidence, JOLTS, ADP employment, ISM Services
and goods-and-services Trade Balance. Inspect each value's source, reference
period and recorded edition through its numerical evidence. Official observations
retain priority for mapped actual/prior values.
BLS payroll `value` is already converted to jobs. `source_value` remains in
`source_unit` thousands of jobs with `conversion_factor="1000"`; do not multiply
the canonical value again. `publisher_reported_revisions` retains publisher units
and is separate from engine-observed `revision_history`. Neither establishes
original first prints. Preserve document manifests, occurrence bindings and
record-level source credits when reusing data.

## Korean official calendars

Filter with `country=KR` (aliases `korea` and `south korea`) or a `kr-` series
code. MODS and BOK schedules retain explicit reference periods and release
stages; unsupported or ambiguous identities are withheld. Coverage ends at the
publisher's verified horizon: a year selector does not establish published dates.

These records currently have date precision and `all_day=false`. BOK's raw
media-publication clock is carried in `source_clock`, distinct from ECOS
availability. Its timezone has not been explicitly verified, so `release_at_utc`
and local display time remain null. `release_tz=Asia/Seoul` identifies the calendar
jurisdiction; do not use it to manufacture an instant. Numerical results and
consensus remain null until separately verified by an implemented result source.

## Indian official release dates

MoSPI dates use `country=IN` and `in-` series codes. Publisher-planned dates remain
estimated, with no computed holiday adjustment or clock. The source's explicitly
recorded publication dates take precedence. A publication month is not the
measured month: `period` and `source_reference_period` stay null where omitted.
GDP publications may bundle multiple quarterly/annual estimate components;
these retain their original description and do not imply one headline result.
Reference-year conflicts and indistinguishable release identities are held for
review. Inspect per-source health and the verified fiscal-year horizon.
