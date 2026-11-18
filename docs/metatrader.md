# Finance Calendar news filter for MetaTrader 4 and 5

Add configurable economic-news windows to an Expert Advisor. The filter loads the Finance Calendar release schedule, matches both currencies of a forex symbol, and returns `quiet`, `clear` or `unknown`. It places, changes and closes no orders. Gold pairs such as XAUUSD use their quote currency; other unsupported bases return unknown.

**Choose your platform:** the MT5 source has passed native timer and public-sample HTTPS checks. The MT4 download is a **source preview**: it compiles and passes native parser/decision checks; timer callbacks and HTTPS still need validation in a connected demo terminal.

## Install

1. In MetaTrader choose **File → Open Data Folder**. Copy the package's `MQL4` or `MQL5` folder into that data folder, merging the `Experts` folders.
2. Open `Experts/FinanceCalendarNewsFilter.mq4` or `.mq5` in MetaEditor and compile it. Keep `FinanceCalendarNews.mqh` beside it.
3. Under **Tools → Options → Expert Advisors**, allow WebRequest for `https://www.financecalendar.com`. No DLL imports are needed.
4. Attach the example EA to a demo chart and enter your API key in `InpApiKey`. Keep keys out of shared presets, screenshots and source control.
5. Inspect the chart state and the Experts log. Test your own entry logic on a demo account before using it in a trading workflow.

Use an active paid API plan for this package. [Compare current plans](https://www.financecalendar.com/pricing/) and [create a key](https://www.financecalendar.com/api/key/). The defaults request two days ago through today+6 UTC, high-impact releases, up to 500 rows, every 180 minutes. The two preceding publisher dates and one-day interior UTC coverage buffer preserve windows up to 24 hours across timezone boundaries. At one page per refresh this is 8 requests/day (248 in a 31-day month), plus other activity sharing your account. A truncated response is unknown; this package does not silently accept the first page or automatically page through more results. The secondary Free Developer schedule scope does not cover this package's wider dates, filters and freshness requirements.

All charts in one terminal using the same key/impact/limit settings share a terminal-local cache and atomic fetch lease. Different keys use different non-credential cache identifiers. Keys are sent in request headers and are never saved in the cache or written to logs. The schedule file retains the full returned source/rights evidence. Local files are data caches, not certified historical snapshots.

## Integrate with an EA

```mql5
#include "FinanceCalendarNews.mqh"
input string InpApiKey = "";
int OnInit() {
   FcNewsInit(InpApiKey, "high", 180, 500);
   EventSetTimer(30);
   return INIT_SUCCEEDED;
}
void OnTimer() { FcNewsRefresh(); }
void OnTick() {
   string reason;
   int state = FcNewsState(_Symbol, 30, 30, reason);
   if(state != FC_NEWS_CLEAR) return;
   // Your existing entry logic.
}
void OnDeinit(const int reason) { EventKillTimer(); }
```

`FcNewsState(symbol, beforeMinutes, afterMinutes, reason)` returns:

- `FC_NEWS_QUIET` (`1`): inside a recorded, sufficiently precise release window.
- `FC_NEWS_CLEAR` (`0`): outside the configured windows in the loaded calendar.
- `FC_NEWS_UNKNOWN` (`-1`): stale, incomplete, failed or missing data; uncertain timing/freshness; an unsupported symbol; or invalid window parameters.

`clear` describes the schedule only. It is not a statement that trading is safe, a trade signal, or a prop-firm compliance guarantee. Windows are inclusive, configurable separately before and after a release, and bounded to 0–1,440 minutes. Source uncertainty, estimated times and date-only records are not turned into midnight releases. An uncertain publisher-local date is conservatively padded by one UTC day on each side. Source freshness that is stale or unavailable, or a missing/invalid/future source-verification timestamp, keeps the affected pair unknown. Valid UTC verification timestamps may include fractional seconds. A quiet window is sufficient to block even if another relevant row is uncertain.

`FcNewsBlocked(...)` remains available for existing integrations; it returns **true for quiet or unknown**. `FcNewsReady()` checks shared cache/readiness; symbol-level uncertainties still require `FcNewsState()`. `FcNewsNext()` returns a known future release in the loaded schedule. Unsupported symbols and unknown times remain explicit.

## Read the chart EA from another program

One example EA instance may publish each symbol/tag combination. Set `InpStateTag` to a distinct label (up to 12 letters, digits, `_` or `-`) if you use different settings on the same symbol. With an empty tag, the globals are:

- `FC_NEWS_BLOCK_<symbol>`: `1`, `0` or `-1`.
- `FC_NEWS_AT_<symbol>`: UTC time of the last published state.

A tag appends `_<tag>` to both names. Treat missing state, missing timestamp, a timestamp older than 90 seconds, a future timestamp, and any value other than `0` as unknown/blocked. Do not attach multiple publishers to the same symbol/tag or delete another instance's globals. Removing the example deletes its state and timestamp.

## Errors and recovery

A 401, 402 or 403 stops every chart using that key/settings scope. Repair your key/account first; call `FcNewsResumeAfterAccessFix()` explicitly once, then `FcNewsRefresh()`. This does not reset a rate-limit pause. If working only through the chart example, remove its `FCN2_ACCESS_…` global under **Tools → Global Variables**, then reattach after repairing access. Avoid deleting unrelated globals or clearing rate-limit stops.

A 429 respects a numeric or standard HTTP-date `Retry-After` delay with a 15-minute minimum. Other transport failures pause for 15 minutes. A failed refresh invalidates the shared readiness state, so another chart cannot keep presenting an older cache as current. A successful refresh resumes normal intervals. A calendar older than 26 hours, a truncated calendar, or a window outside queried dates is unknown.

## Acceptance and limits

The release compiles both versions with MetaEditor and checks the same 48 parser/decision cases in actual MT4 and MT5 terminals. MT5 also passed two real timer callbacks and an HTTPS request for the public fixed sample, without a broker connection.

MT4 remains a **source preview**. In the accountless Windows test environment, a standalone timer control with no Finance Calendar code returned success with no error, but delivered no callbacks. Its connected-demo callback and HTTPS acceptance is pending. Validate that workflow in a connected demo terminal before relying on the MT4 example. These results do not establish a product-specific parser defect or successful MT4 callback delivery.

Consult the dated acceptance receipt for source/package hashes and run links. The public-sample request uses no API key; an end-to-end paid-key/broker account test has not been performed for either platform. No order functions or broker account creation are part of these checks.

WebRequest is synchronous, unavailable to indicators and unavailable in Strategy Tester. The package does not provide historical backtesting, trade execution, automatic position management or guaranteed release delivery speed.

Data: [Finance Calendar](https://www.financecalendar.com/). Retain Finance Calendar attribution and the publisher credits/rights supplied with records when displaying data. [API terms](https://www.financecalendar.com/api/terms/). Source timestamps, coverage and missing values remain meaningful.
