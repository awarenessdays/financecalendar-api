// Fixture router: maps an API URL to a recorded response so tests never touch the network.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DIR = join(dirname(fileURLToPath(import.meta.url)), "fixtures");

export function fixture(name) {
  return JSON.parse(readFileSync(join(DIR, `${name}.json`), "utf8"));
}

export function fixtureFor(url) {
  const u = new URL(String(url));
  const path = u.pathname.replace(/^.*\/fc\/v1/, "").replace(/^\/v1(?=\/)/, "");
  const q = u.searchParams;
  if (q.get("asset") === "ethereum") {
    const rec = fixture("crypto");
    const row = rec.body.events[1];
    const window = rec.body.events[0];
    const series = { code: row.series_code, name: row.series_name, category: "crypto", country: null, impact: null, assets: row.assets, next_date: window.date, next_date_window_start: window.date_window_start, next_date_window_end: window.date_window_end };
    if (["/calendar", "/week", "/today", "/history"].includes(path)) return rec;
    if (path === "/next") return { ...rec, body: { next: row, series_code: row.series_code } };
    if (path === "/series") return { ...rec, body: { count: 1, series: [series] } };
    if (path === "/series/ethereum-network-upgrades") return { ...rec, body: { series, next: window, last: null, upcoming: [window, row], history: [] } };
  }
  switch (path) {
    case "/next":
      if (q.get("country") === "no") return fixture("error_next_404");
      if (q.get("country") === "uk") return fixture("next_cpi_uk");
      return fixture(q.get("tz") ? "next_fomc_tz" : "next_fomc");
    case "/calendar":
      if (q.get("tz") === "Mars/Olympus") return fixture("error_bad_tz");
      if (q.get("series") === "nope") return fixture("error_unknown_series");
      if (q.get("format") === "csv") return { status: 200, headers: { "Content-Type": "text/csv; charset=utf-8" }, text: readFileSync(join(DIR, "calendar_csv.txt"), "utf8") };
      if (q.get("include") === "holidays") return fixture("calendar_holidays");
      if (q.get("impact") === "high") return fixture("calendar_high");
      return fixture(q.get("tz") ? "calendar_tz" : "calendar");
    case "/today": return fixture("today");
    case "/week": return fixture(q.get("which") === "next" ? "week_next" : "week");
    case "/series": return fixture("series");
    case "/series/fomc": case "/series/fed": return fixture("series_detail_fomc");
    case "/history": return fixture("history_us_cpi");
    case "/holidays": return fixture(q.get("exchange") === "lse" ? "holidays_lse_2027" : "holidays_nyse");
    case "/market-status": return fixture(q.get("exchange") === "lse" ? "market_status_lse" : "market_status_nyse");
    case "/changes": {
      const rec = fixture("changes");
      if (q.get("cursor") === "page-2") return { ...rec, body: { ...rec.body, changes: [], count: 0, total: 100, has_more: false, next_cursor: null } };
      if (q.get("limit") === "1") return { ...rec, body: { ...rec.body, changes: rec.body.changes.slice(0, 1), count: 1, total: 100, has_more: true, next_cursor: "page-2" } };
      return rec;
    }
    case "/countries": return fixture("countries");
    case "/status": return fixture("status");
    case "/openapi": return fixture("openapi");
    case "/rate-limited": return fixture("error_429");
    default:
      if (path.startsWith("/series/")) return fixture("error_series_404");
      return { status: 404, headers: {}, body: { error: `No route for ${path}` } };
  }
}

/** Build a Response from a fixture record ({status, headers, body} or {status, headers, text}). */
export function toResponse(rec) {
  const headers = { "Content-Type": "application/json", ...(rec.headers || {}) };
  const text = rec.text !== undefined ? rec.text : JSON.stringify(rec.body);
  return new Response(text, { status: rec.status, headers });
}

/** Install a fetch mock on globalThis that answers from fixtures and records every call. */
export function installMockFetch() {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), headers: init.headers || {} });
    return toResponse(fixtureFor(url));
  };
  return calls;
}
