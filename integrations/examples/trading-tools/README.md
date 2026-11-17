# Finance Calendar trading-tool examples

Python and Node produce a high-impact economic-event watchlist as JSON. They request **seven UTC calendar dates, inclusive: today through today + 6 days**, with `status=confirmed,estimated,rescheduled`. The window includes today's scheduled events; it is not a filter to the current second. These examples fetch calendar data and place no orders.

The Python and Node programs have no third-party dependencies. Use **Python 3.10+** or **Node 20+**. Run either program from this directory:

```sh
python3 python/calendar_watchlist.py
node node/calendar-watchlist.mjs
```

## Set up a private key

The watchlist’s wider fields, filters and pagination use paid API access. Choose Starter, Build or Scale from the [current plans](https://www.financecalendar.com/pricing/); the [canonical product offer](https://www.financecalendar.com/wp-json/fc/v1/product-offer) defines current prices and account allowances. Inspect the [public fixed sample](https://www.financecalendar.com/api/sample/) before choosing a plan. Keys on one account share its allowance.

The secondary Free Developer option provides a bounded schedule-only response on documented `/calendar` and `/today` queries after account verification and request approval. It has a 48-hour review window, no card or automatic paid conversion, and excludes numerical figures, wider dates, richer filters, pagination and hosted tools. These trading-tool examples use the richer paid contract.

Get your key from [your Finance Calendar account](https://www.financecalendar.com/account/). Set `FC_API_KEY` in the process environment. The programs require the current `fc_live_` key format and check it before making a request. They do not accept a key in command-line arguments or URLs and do not automatically load `.env` files. `.env.example` contains a placeholder only.

For an interactive **Bash** session, this avoids putting the key in shell history or displaying it:

```bash
read -r -s -p 'Finance Calendar API key: ' FC_API_KEY
export FC_API_KEY
printf '\n'
python3 python/calendar_watchlist.py
# Or: node node/calendar-watchlist.mjs
unset FC_API_KEY
```

Keep the key out of browser code, public repositories, screenshots, saved MetaTrader presets and shared logs. For a scheduled job, use its private environment/secret settings. Review your account's allowance before running continuously.

## Output and source information

On success, stdout is one JSON document containing `source`, `fetched_at`, `cache`, `from`, `to`, `count`, `total`, `events` and the API's `attribution`. Each event remains a full record: unknown future fields, nested observations, source credits, `source_rights`, `source_license` and provenance are retained. Display the supplied credits and review the source terms before redistributing data.

`fetched_at` records when this local program fetched the response. It does not certify the publisher's freshness. Preserve and check each record's `data_stale`, `stale_since`, `last_verified_at`, `data_quality` and status fields when available. A `null` release time stays `null`; unknown, date-only or range precision is not converted to midnight. Numeric zero remains distinct from a missing observation. The scripts do not calculate trade signals or invent results.

The programs page through `/calendar` with `limit=500`, increasing `offset` by the returned count. They stop rather than return a partial result if totals change, identities repeat or a response is invalid. Reviewed bounds are ten pages, 5,000 events, 4 MiB per page and 8 MiB combined. Node uses a 12-second timeout per page; Python uses a 12-second socket timeout. Neither follows redirects with your key.

## Cache and continuous use

The default cache lifetime is **15 minutes**. Run the one-shot program from your own scheduler when needed. With one page per refresh, a continuously running 15-minute schedule has **96 refresh opportunities per day, or 2,880 in 30 days**. Every additional page requires another API call, and other applications using your account also consume its allowance. Date changes can trigger a new window immediately. A cache hit makes no API call.

The default directory is `~/.cache/financecalendar-trading-tools`. You can set `FC_CACHE_DIR` to another directory private to your OS user. Cache names are partitioned by a SHA-256 digest of the key and endpoint, so changing keys cannot serve another key's cached response. The key itself is never stored. New cache files use mode `0600`, are atomically replaced, and can be shared by these Python and Node examples when run as the same OS user.

Run a single scheduled process per cache. These small examples do not coordinate simultaneous processes; overlapping cold starts can each make a request. Do not use a shared web directory or a directory writable by other users. Files contain calendar data and account-specific request-stop state.

## Errors and request stops

A failure exits with status 1, writes a safe message to stderr, and emits no watchlist. Error bodies and credentials are not logged. There is no automatic retry and no stale-data fallback output.

- **401, 402 or 403:** requests for that key stop persistently, including future scheduled runs. Fix the key/account first, then clear this key's private cache or replace the key.
- **429:** the program reads both numeric and HTTP-date `Retry-After`. Future invocations stop locally until that time, with a minimum 15-minute pause when the header is short, missing or invalid. A very large delay requires manual review. It does not sleep and resend the request.
- **Other HTTP, connection, JSON or pagination errors:** stop this invocation and pause further requests for 15 minutes. The previous private cache is retained, but is not returned as a fresh watchlist.

After repairing an access problem, clear only the current key's cache with either command. This command itself makes no HTTP request. Do not clear a 429 pause to bypass `Retry-After`.

```sh
python3 python/calendar_watchlist.py --clear-cache
node node/calendar-watchlist.mjs --clear-cache
```

## MetaTrader 4 and 5 manual download

`metatrader/FinanceCalendarFetch.mq4` and `.mq5` contain the same manual `OnStart` script using the documented seven-argument custom-header `WebRequest` overload. See the release's dated MetaEditor/native-terminal acceptance evidence; a source review or local C++ stand-in is not a native compile or broker test.
1. Copy the matching file to your terminal's `MQL4/Scripts` or `MQL5/Scripts` directory. Open it in MetaEditor and compile it locally.
2. In the terminal, open Tools → Options → Expert Advisors and allow WebRequest for `https://www.financecalendar.com`.
3. Run the script manually and enter your key in `InputAPIKey` locally. Do not publish or share a preset containing it.
4. A successful HTTP 200 is saved unchanged to the terminal-local `MQL4/Files/FinanceCalendar-calendar.json` or `MQL5/Files/FinanceCalendar-calendar.json`. It contains data, not the key. The Experts log reports status and file success.

This deliberately demonstrates **one page, up to 500 records**. Inspect the JSON `count` and `total` before using it; it does not implement pagination, JSON interpretation, scheduling, a 15-minute cache or orders. For a complete paged watchlist, use the Python or Node program. A failed run does not certify any older file as current. Keep source attribution and check freshness/time precision before interpreting the data.

The script stops on access errors, shows `Retry-After` on a 429 and makes no automatic repeat requests. Wait for that delay before manually running it again. MetaTrader WebRequest is synchronous, requires its URL allowlist, and is unavailable in indicators and the Strategy Tester. See the official [MQL4 WebRequest](https://docs.mql4.com/common/webrequest) and [MQL5 WebRequest](https://www.mql5.com/en/docs/network/webrequest) references.

## MetaTrader 4 and 5 news windows

Use `metatrader/FinanceCalendarNews.mqh` with `FinanceCalendarNewsFilter.mq4` or `.mq5`. The include downloads a paid-plan release schedule and matches the forex symbol's base and quote currencies, including broker prefixes/suffixes where broker currency metadata is available. XAUUSD watches USD releases; unsupported bases are unknown. It performs no order operations.

```mql5
string reason;
int state = FcNewsState(_Symbol, 30, 30, reason);
if(state != FC_NEWS_CLEAR) return;
// Your existing entry logic.
```

Initialise with `FcNewsInit(apiKey, "high", 180, 500)` and call `FcNewsRefresh()` from `OnTimer()`. The defaults request two days ago through today+6 UTC every three hours (8 requests/day; 248 in 31 days), using the two preceding publisher dates and interior UTC coverage buffers to preserve windows up to 24 hours across timezone boundaries. This wider scope requires paid access. The same-key/settings charts share a terminal-local cache and an atomic request lease; keys never appear in file names, cache data or logs.

`FcNewsState()` returns `FC_NEWS_QUIET` (1), `FC_NEWS_CLEAR` (0) or `FC_NEWS_UNKNOWN` (-1). Unknown includes failed, truncated or stale schedules, missing source freshness, imprecise/estimated timing and unsupported symbols. `FcNewsBlocked()` conservatively returns true for quiet **and unknown**. The clear state describes the queried schedule, not trading safety. The example publishes a state and UTC timestamp for other EAs; missing or expired timestamps must be treated as unknown. Use one publisher per symbol/tag and distinct `InpStateTag` values for different settings.

Read the [complete MetaTrader installation, state and recovery guide](../../../docs/metatrader.md), or the README supplied with the downloadable package. Release evidence distinguishes MetaEditor compilation, local stand-in fixtures, native terminal/timer fixtures, a public-sample HTTPS smoke and any separately recorded paid-key/broker acceptance. Do not infer one from another.

## Run the offline checks

No real key, account or external connection is required:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The suite starts a temporary numeric-loopback HTTP server and invokes both actual CLIs with invented fixture credentials. It exercises pagination, full-record/null/zero/staleness retention, private cache hits and key separation, cross-language cache use, persistent access stops, `Retry-After`, malformed JSON, other HTTP failures, redirects, timeouts and response bounds. MetaTrader parser/state/transport/cache/EA-adapter checks execute the actual MQL source through a C++ stand-in runtime. The shared MQL fixture cases also run in the Windows native-terminal workflow; local tests alone are not a MetaEditor compile or live broker test.

For these offline tests only, `FC_TRADING_TOOLS_TEST_HTTP=1` enables a transport restricted to `http://127.0.0.1:<port>/calendar`, plus a fixed clock and shorter timeout. There is no arbitrary external endpoint flag. Leave all `FC_TRADING_TOOLS_TEST_*` variables unset for normal use. The production destination is fixed to `https://www.financecalendar.com/wp-json/fc/v1/calendar`.

For the focused MQL logic check (C++ compiler required):

```sh
python3 tests/metatrader/run_mql_tests.py
```
