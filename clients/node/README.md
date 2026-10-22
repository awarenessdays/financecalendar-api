# financecalendar-mcp

Economic calendar data for AI assistants and the terminal: scheduled releases (CPI, jobs report, GDP, PCE...), central bank decisions (Fed, ECB, BoE, BoJ...) exchange holidays and source-backed crypto events. Powered by the free [financecalendar.com API](https://www.financecalendar.com/api/). Availability varies by series: check each event's `status` and `source_url`; consensus and actual results are included where available.

One package, two binaries:

- `financecalendar-mcp`: an MCP server over stdio for Claude Desktop, Claude Code, Cursor and any other MCP client.
- `financecalendar`: a CLI for your terminal and scripts.

No API key needed. A free key raises the daily limit from 2,000 to 10,000 requests.

## Hosted MCP connector: ChatGPT and Claude

The public beta connects over HTTPS without installing this package. Server URL:

```text
https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
```

Use **Streamable HTTP** and **No authentication / No sign-in**. This is a custom
connection, not a listing in either platform's directory. Account and workspace
policies control whether you can add it.

- **ChatGPT:** in Plugins, choose **+ → Add custom MCP server**, enter the URL
  and **No authentication**, then create and install the plugin. Select it with
  `@` in a new conversation where supported. See the
  [official ChatGPT guide](https://developers.openai.com/plugins/deploy/connect-chatgpt).
- **Claude:** open [Customize → Connectors](https://claude.ai/customize/connectors),
  choose **Add custom connector**, paste the URL and choose **No sign-in** if
  shown. Leave OAuth credentials and request headers empty. Organization owners
  may need to add it first; see
  [Claude's custom connector guide](https://claude.com/docs/connectors/custom/add-unlisted).
- **Claude Code:** run:

  ```sh
  claude mcp add --transport http financecalendar https://www.financecalendar.com/wp-json/fc-mcp/v1/mcp
  ```

Try: “Find the next UK CPI release, show its time in Europe/London and cite its
publisher. Check source health and say which values or dates are uncertain.”

### Hosted tools and output

The hosted server provides the 11 tools listed below plus `feed_status()` for
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

Hosted `calendar`, `history` and initial `changes` calls default to 20 rows and
accept 1–50. Calendar supports `offset`. Continue changes with only `cursor`;
do not inject a new limit. Overview tools bound large arrays to at most 50
entries and can return fewer to meet the 120,000-byte encoded response cap.
Partial results carry `truncation.fields`, original counts and recovery
instructions; check canonical totals too. Narrow filters, page `calendar`, or
use the supplied full REST endpoint. A partial overview is not a complete
export. Cursor pages are never trimmed after a cursor is issued: a size error
requires restarting from the original checkpoint with a smaller initial limit
and deduplicating. Requests are limited to 32,768 bytes; unknown arguments are
rejected.

The public beta uses **2,000 data requests per IP per UTC day**, potentially
shared by users behind a ChatGPT or Claude proxy. It does not forward API keys,
cookies or authorization headers, provide OAuth, or assign personal paid quotas.
For production use, choose the keyed REST API or local stdio server. Each tool
call uses the same canonical API and its rate limits; discovery is separate.
Respect `Retry-After` where supplied. See the
[full hosted and local MCP reference](https://www.financecalendar.com/api/mcp/).

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

For MCP today, configure `node` as the command and the absolute path to this
checkout's `mcp.js` as its argument. The npm/npx configurations below apply after
registry publication.

After publication:

```sh
npm install -g financecalendar-mcp      # or run ad hoc with npx
```

Requires Node 20 or newer.

Human CLI output shows the reference `period` and `release_stage` when provided.
Unknown economic release times are labelled `time unknown`; exchange holidays
retain `all day`. Raw JSON preserves the API fields unchanged.

## Local MCP server

### Claude Desktop

Add to `claude_desktop_config.json` (Settings, Developer, Edit Config):

```json
{
  "mcpServers": {
    "financecalendar": {
      "command": "npx",
      "args": ["-y", "financecalendar-mcp"]
    }
  }
}
```

With a free key (only add the `env` block once you have a real key; a placeholder is rejected with 401):

```json
{
  "mcpServers": {
    "financecalendar": {
      "command": "npx",
      "args": ["-y", "financecalendar-mcp"],
      "env": { "FC_API_KEY": "fc_live_..." }
    }
  }
}
```

### Claude Code

```sh
claude mcp add financecalendar -- npx -y financecalendar-mcp
# with a key:
claude mcp add financecalendar -e FC_API_KEY=your-key -- npx -y financecalendar-mcp
```

### Cursor

Add to `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "financecalendar": { "command": "npx", "args": ["-y", "financecalendar-mcp"] }
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

## Environment variables

| Variable | Purpose |
|---|---|
| `FC_API_KEY` | Free API key, sent as `X-API-Key` on every request. Get one at [financecalendar.com/api](https://www.financecalendar.com/api/#key). |
| `FC_API_BASE` | Alternative base URL. Default `https://www.financecalendar.com/wp-json/fc/v1`; an edge mirror at `https://api.financecalendar.com/v1` is planned. |

## Use it as a library

```js
import { api, formatEvent } from "financecalendar-mcp/lib.js";

const { next } = await api("/next", { series: "ecb" }, { apiKey: process.env.FC_API_KEY });
console.log(formatEvent(next, { tz: "Europe/Frankfurt" }));
```

`api()` throws an `Error` whose message carries the API's `error` text and HTTP status; on 429 it adds the `Retry-After` seconds (`err.retryAfter`).

## Data terms

API access is currently free, including for commercial applications, subject to applicable source terms and credits. Include a visible link to [financecalendar.com](https://www.financecalendar.com) wherever the data appears. Retain each record's `source_license` requirements, including `attribution_url`, source and licence links, full notices and adaptation labels; PatternPlus records require [Data: PatternPlus](https://pattern.plus). Preserve `source_rights` attribution, evidence, access basis and notice for independently normalised facts. This rights metadata does not assert a publisher copyright licence. Earnings dates are not included. Full terms, rate limits and the changelog: [financecalendar.com/api](https://www.financecalendar.com/api/).

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

Current actual/prior fields require the supported official numerical evidence;
article metadata is not a fallback. Consensus estimates are not currently collected.
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
