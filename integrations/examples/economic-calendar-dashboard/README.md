# Economic calendar dashboard starter

A complete, small dashboard for recorded economic releases, built with the [Finance Calendar API](https://www.financecalendar.com/api/). It includes a Node backend, a responsive browser calendar, local filters and source details. It uses **Node.js 20 or newer and no runtime packages**. The package is private and is not intended for registry publication.

The API key stays in the server environment. Every visitor shares one server cache. Search, market, date and impact filters operate on the records already loaded; they do not send additional upstream requests.

## Preview without an API key

From a fresh public checkout:

```sh
git clone https://github.com/awarenessdays/financecalendar-api.git
cd financecalendar-api/integrations/examples/economic-calendar-dashboard
npm run demo
```

Open [http://127.0.0.1:3010](http://127.0.0.1:3010). The **Demo data** notice is always visible in this mode. All release dates and values are invented illustrations. Demo mode never contacts the API, even if a key happens to be set.

In the working Awareness Days repository, the equivalent folder is `fc-integrations/examples/economic-calendar-dashboard`.

## Run with your own API key

1. [Create a free Finance Calendar account](https://www.financecalendar.com/account/?mode=register), confirm your email, sign in and create an API key.
2. Stop the demo server with Ctrl+C.
3. In the same example folder, read the key into your shell without placing it in shell history. Paste the key after `read`, then press Enter:

```sh
read -r -s FC_API_KEY
export FC_API_KEY
npm start
```

The `read` input is hidden in Bash and Zsh. For PowerShell 7.1 or newer:

```powershell
$env:FC_API_KEY = Read-Host "Finance Calendar API key" -MaskInput
npm start
```

You can instead supply `FC_API_KEY` through your hosting platform's private environment settings. This example does **not** read `.env` files. No `npm install` step is required: there are no package dependencies. Do not put the key in browser JavaScript, a URL, a committed file or a screenshot.

Real mode stops with a clear message if `FC_API_KEY` is missing. A rejected key produces an actionable connection state; it does not silently switch to demo data. Restart the process after changing server environment settings.

## Configure the shared view

Defaults are US, GB and EU; Europe/London; a 14-day publisher-date window starting on the current date in that time zone. Set these variables before `npm start`:

| Variable | Default | Meaning |
|---|---|---|
| `FC_API_KEY` | Required in real mode | Private account API key, sent to the official API in `X-API-Key`. |
| `FC_COUNTRIES` | `US,GB,EU` | One to twelve comma-separated two-letter country codes. Coverage varies by country and source. |
| `FC_TIMEZONE` | `Europe/London` | IANA zone used to choose the starting date and display known release times. |
| `FC_DAYS` | `14` | Integer from 1 to 28, including the current date in that time zone. |
| `PORT` | `3010` | Local HTTP port. |
| `HOST` | `127.0.0.1` | Listening address. Set `0.0.0.0` only when you intentionally need other hosts to reach it. |

For example:

```sh
export FC_COUNTRIES=US,GB
export FC_TIMEZONE=America/New_York
export FC_DAYS=7
npm start
```

The API filters the recorded **publisher dates** using `from` and `to`. This is not a promise that every converted local date falls within the same window. A precisely timed release can appear on an adjacent date in the display time zone. Date-only and unknown-time records retain their publisher date; the browser date buttons filter the displayed dates. No extra requests are needed for these local conversions.

The backend always requests the fixed official `/wp-json/fc/v1/calendar` endpoint, with a maximum first page of 500 records. There is no configurable upstream origin and no general-purpose proxy. Browser URL parameters cannot change the upstream request. If more than 500 records match, the dashboard explicitly marks the view incomplete; narrow the server configuration to get a complete view. It does not silently fetch extra pages.

## Cache, failures and allowance

A single process shares one in-memory cache and one in-flight request across all visitors. The cache lasts **30 minutes**. Opening another tab, filtering or clicking **Check for updates** cannot force an upstream cache bypass. There is no background poller, automatic pagination or immediate retry loop. A check only fetches upstream if the cache or failure cooldown has expired.

With one continuously running process, an always-used 30-minute cache makes at most **48 scheduled fetch opportunities per 24 hours**, approximately **1,440 per 30 days**. The new Free account allowance is **250 admitted requests/day and 5,000 per UTC calendar month**, shared across the account's REST, MCP and other integrations. A cache fetch is one API request; it may return many records. Other apps on the same account share the allowance. Check your workspace for effective limits, including any grandfathered allowance.

The cache is deliberately simple: restarting the server empties it, and multiple server processes each have their own cache. Frequent restarts, deployments or replicas can increase consumption beyond that estimate. Keep one process for the starter; use a shared durable cache if you later run multiple replicas.

On a failed refresh, the last valid records remain visible with a **Stale cached view** state and their original fetch timestamp. If no successful fetch exists, the dashboard clearly reports that data is unavailable. A 429 respects the longer of the 30-minute cooldown and the provider's `Retry-After`. Authentication errors, response errors and connection failures also wait at least 30 minutes before a subsequent check can attempt the API again. The browser receives safe messages, never the raw upstream error body or API key.

Rejected quota/authentication requests do not consume the admitted allowance. Admitted requests that later encounter processing errors can still count. This starter does not promise real-time updates or bypass limits.

## Data and attribution

- A missing actual or prior value stays `—`; a numeric zero stays `0`. Nonzero numbers retain meaningful precision, using scientific notation for very small or large magnitudes; numeric strings retain their exact text.
- A timestamp is used for local clock conversion only when `time_precision` explicitly indicates a minute or second. Unknown or date-only timing is not turned into midnight. Estimated dates and recorded windows remain labelled.
- `data_stale` is displayed separately from the dashboard's own fetch age. A newly fetched response does not establish a newly verified publisher record.
- Cancelled and rescheduled releases have explicit status badges. A `Released` status does not establish that an actual value was captured.
- Each release opens a source panel with its available publisher link, recorded verification time, full source credits and reuse terms. Attribution links, source-rights evidence, policy and vintage notices are retained without a character or entry-count cutoff. The upstream JSON response remains bounded to 4 MiB. The UI uses text nodes and validates link protocols.
- Finance Calendar and upstream publisher credits remain visible. The software does not relicense source data; retain applicable `source_license` and `source_rights` notices if you reuse the records elsewhere.
- Coverage varies. The recorded dataset is not a point-in-time first-print archive; consensus estimates are not currently collected. A schedule entry or an elapsed date does not guarantee a captured actual value.

The application has no account database, payment flow, analytics or tracking. It reads the configured calendar and presents it. If you expose it beyond localhost, add the ordinary deployment controls appropriate to your own application, including HTTPS and protection for your server environment.

## Copy instructions for a coding assistant

Paste this into your coding assistant, then provide the key through your server's private environment settings—not in the prompt:

```text
Use the Finance Calendar economic-calendar-dashboard starter in this repository.
Build a source-aware release watchlist from its working Node backend and browser UI.
Read README.md and the official API guide at https://www.financecalendar.com/api/.

Keep FC_API_KEY only in the server environment. Use the fixed official calendar
endpoint, one shared 30-minute cache and in-flight request deduplication. Preserve
failure cooldowns and Retry-After. Keep browser search/date/country/impact filters
local; do not create an upstream request for every visitor or filter change.

Preserve null versus zero, source credits, stale-source flags and time_precision.
Do not invent unknown release times, consensus values or missing observations.
Keep the demo-data label visible in demo mode. Run npm test before making changes.
Start with one process; do not claim the in-memory cache is shared across replicas.
```

## Files and checks

| File | Responsibility |
|---|---|
| `server.mjs` | Validated configuration, fixed upstream, safe response shaping, shared cache/cooldown and local HTTP routes. |
| `demo.mjs` | Explicitly invented preview records. |
| `public/index.html` | Accessible calendar structure and release dialog. |
| `public/app.mjs` | Local filtering, state display and source details. |
| `public/model.mjs` | Pure date/time/null/link presentation helpers shared with offline tests. |
| `public/styles.css` | Finance Calendar violet/white responsive interface. |
| `public/fonts/` | Bundled Inter fonts and their existing SIL Open Font License. |
| `test/dashboard.test.mjs` | Node built-in tests with injected transports and clocks; no external API calls. |

```sh
npm test
```

Tests cover cache expiry, concurrent visitor deduplication, stale retention, rate-limit cooldowns, invalid configuration, fixed-origin requests, incomplete pages, secret/error protection, demo isolation, unknown timing and null/zero handling. Two tests bind a temporary loopback HTTP port; test environments must permit local listening. All upstream responses are mocked.
