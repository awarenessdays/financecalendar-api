import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { api, buildUrl, baseUrl, formatEvent, formatWhen, formatSeries, eventsToCsv, USER_AGENT, DEFAULT_BASE } from "../lib.js";
import { installMockFetch, fixture, toResponse } from "./fixtures.js";

const realFetch = globalThis.fetch;
const env = { ...process.env };
afterEach(() => {
  globalThis.fetch = realFetch;
  for (const k of ["FC_API_BASE", "FC_API_KEY"]) { if (env[k] === undefined) delete process.env[k]; else process.env[k] = env[k]; }
});

test("crypto requests retain canonical asset filters and structured zero/null data", async () => {
  const calls = installMockFetch();
  const response = await api("/calendar", { category: "crypto", asset: ["ethereum"], limit: 1, offset: 2 });
  const url = new URL(calls[0].url);
  assert.equal(url.searchParams.get("asset"), "ethereum");
  assert.equal(url.searchParams.get("category"), "crypto");
  assert.equal(url.searchParams.get("offset"), "2");
  const row = response.events[1];
  assert.equal(row.country, null);
  assert.equal(row.impact, null);
  assert.equal(row.actual, 0);
  assert.equal(row.crypto.block_height, 0);
  assert.equal(row.source_license.adapted, true);
});

test("crypto display shows global assets, testnet environment and upstream credit", () => {
  const row = fixture("crypto").body.events[1];
  const text = formatEvent(row, { tz: "UTC" });
  assert.match(text, /Ethereum upgrade \(ETH · Global\)  sepolia  prior 0  actual 0/);
  assert.match(text, /Ethereum Foundation and ethereum.org contributors · CC-BY-4\.0 · adapted by Finance Calendar/);
  assert.ok(text.includes(row.source_url) && text.includes(row.source_license.url));
  const csv = eventsToCsv([row]);
  assert.match(csv, /source_license/);
  assert.match(csv, /ethereum/);
  assert.match(csv, /CC-BY-4\.0/);
});

test("estimated crypto windows are displayed as windows, never their index date", () => {
  const row = fixture("crypto").body.events[0];
  assert.equal(formatWhen(row, "Asia/Tokyo"), "2026-10-01–2026-12-31 (estimated window)");
  assert.equal(formatWhen(row, "America/New_York"), "2026-10-01–2026-12-31 (estimated window)");
  assert.match(eventsToCsv([row]), /date_window_start,date_window_end/);
  assert.match(formatEvent(row), /estimated window/);
});

test("series targets use the complete estimated window instead of the date index", async () => {
  installMockFetch();
  const { series } = await api("/series", { category: "crypto", asset: "ethereum" });
  const text = formatSeries(series[0]);
  assert.match(text, /next target 2026-10-01–2026-12-31 \(estimated window\)$/);
  assert.ok(!text.includes("next 2026-10-01"));
  assert.match(formatSeries({ ...series[0], next_date_window_end: null }), /next target window tbc$/);
  assert.match(formatSeries({ ...series[0], next_date_window_start: null, next_date_window_end: null }), /next 2026-10-01$/);
});

describe("buildUrl / param encoding", () => {
  test("drops empty values, joins arrays, maps booleans", () => {
    const u = buildUrl("/calendar", { from: "2026-10-19", to: undefined, country: ["US", "GB"], impact: "", include: null, limit: 50, flag: true, off: false });
    assert.equal(u.origin + u.pathname, `${DEFAULT_BASE}/calendar`);
    assert.equal(u.searchParams.get("from"), "2026-10-19");
    assert.equal(u.searchParams.get("country"), "US,GB");
    assert.equal(u.searchParams.get("limit"), "50");
    assert.equal(u.searchParams.get("flag"), "1");
    assert.equal(u.searchParams.has("to"), false);
    assert.equal(u.searchParams.has("impact"), false);
    assert.equal(u.searchParams.has("include"), false);
    assert.equal(u.searchParams.has("off"), false);
  });

  test("honours FC_API_BASE and strips trailing slashes", () => {
    process.env.FC_API_BASE = "https://api.financecalendar.com/v1/";
    assert.equal(baseUrl(), "https://api.financecalendar.com/v1");
    assert.equal(buildUrl("/today").href, "https://api.financecalendar.com/v1/today");
    assert.equal(buildUrl("today", {}, "http://localhost:8080/x").href, "http://localhost:8080/x/today");
  });
});

describe("api()", () => {
  let calls;
  beforeEach(() => { calls = installMockFetch(); });

  test("returns parsed JSON and sends the User-Agent, no key by default", async () => {
    delete process.env.FC_API_KEY;
    const data = await api("/next", { series: "fomc" });
    assert.equal(data.next.id, "fomc-rate-decision-october-2026");
    assert.equal(calls[0].url, `${DEFAULT_BASE}/next?series=fomc`);
    assert.equal(calls[0].headers["User-Agent"], USER_AGENT);
    assert.equal(USER_AGENT, "financecalendar-mcp/0.2.0");
    assert.equal(calls[0].headers["X-API-Key"], undefined);
  });

  test("sends X-API-Key from FC_API_KEY", async () => {
    process.env.FC_API_KEY = "fc_env_key";
    await api("/today");
    assert.equal(calls[0].headers["X-API-Key"], "fc_env_key");
  });

  test("explicit apiKey option wins over the env var", async () => {
    process.env.FC_API_KEY = "fc_env_key";
    await api("/today", {}, { apiKey: "fc_explicit" });
    assert.equal(calls[0].headers["X-API-Key"], "fc_explicit");
  });

  test("raw: true returns text (CSV)", async () => {
    const csv = await api("/calendar", { format: "csv" }, { raw: true });
    assert.match(csv, /^date,time_utc,time_et/);
    assert.match(calls[0].headers.Accept, /text\/csv/);
  });

  test("surfaces the API error text and status for 400", async () => {
    await assert.rejects(api("/calendar", { tz: "Mars/Olympus" }), (e) => {
      assert.equal(e.status, 400);
      assert.equal(e.message, "tz must be an IANA timezone such as Europe/London or Asia/Tokyo. (HTTP 400)");
      return true;
    });
  });

  test("surfaces 404 for an unknown series", async () => {
    await assert.rejects(api("/series/zzz"), /Unknown series.*\(HTTP 404\)/);
  });

  test("429 carries Retry-After in the message and on the error", async () => {
    await assert.rejects(api("/rate-limited"), (e) => {
      assert.equal(e.status, 429);
      assert.equal(e.retryAfter, 29535);
      assert.match(e.message, /Daily limit of 2,000 keyless requests reached/);
      assert.match(e.message, /HTTP 429 rate limit reached, retry after 29535s/);
      return true;
    });
  });

  test("non-JSON error body falls back to HTTP status", async () => {
    globalThis.fetch = async () => new Response("<html>Bad gateway</html>", { status: 502, statusText: "Bad Gateway" });
    await assert.rejects(api("/today"), (e) => {
      assert.equal(e.status, 502);
      assert.match(e.message, /HTTP 502/);
      return true;
    });
  });

  test("custom fetch option is used", async () => {
    let seen;
    const data = await api("/countries", {}, { fetch: async (u) => { seen = String(u); return toResponse(fixture("countries")); } });
    assert.equal(seen, `${DEFAULT_BASE}/countries`);
    assert.equal(data.countries[0].code, "US");
  });
});

describe("formatting", () => {
  const fomc = fixture("next_fomc").body.next;

  test("formatEvent renders the documented one-line layout plus URL", () => {
    assert.equal(
      formatEvent(fomc, { tz: "America/New_York" }),
      "Wed 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold\nhttps://www.financecalendar.com/event/fomc-rate-decision-october-2026/"
    );
  });

  test("times follow the requested zone", () => {
    assert.equal(formatWhen(fomc, "Europe/London"), "Wed 28 Oct 18:00 GMT");
    assert.equal(formatWhen(fomc, "Asia/Tokyo"), "Thu 29 Oct 03:00 GMT+9");
    assert.equal(formatWhen(fomc, "UTC"), "Wed 28 Oct 18:00 UTC");
  });

  test("all-day holiday rows have no time and no URL line", () => {
    const hol = fixture("today").body.market_holidays[0];
    assert.equal(formatEvent(hol, { tz: "Europe/London" }), "Mon 19 Oct all day  HKEX closed: Day Following Chung Yeung Festival (HK)");
  });

  test("released rows show the actual", () => {
    const row = fixture("history_us_cpi").body.events[0];
    assert.match(formatEvent(row, { tz: "America/New_York" }), /^Wed 14 Oct 08:30 ET  US CPI \(US\)  period September 2026  cons\. 3\.0% y\/y  prior 3\.1% y\/y  actual 3\.0% y\/y\n/);
  });

  test("GDP estimate stages and catch-up reference periods distinguish otherwise identical names", () => {
    const row = { name: "US GDP", date: "2026-10-29", country: "US", period: "3rd Quarter 2026", release_at_utc: "2026-10-29T12:30:00Z" };
    const lines = ["advance", "second", "third"].map((release_stage) => formatEvent({ ...row, release_stage }, { tz: "UTC" }));
    assert.equal(new Set(lines).size, 3);
    assert.ok(lines.every((line) => line.includes("period 3rd Quarter 2026  stage ")));
    assert.notEqual(formatEvent({ ...row, period: "January 2026" }), formatEvent({ ...row, period: "February 2026" }));
  });

  test("displayed details do not repeat a stage or period already in the name", () => {
    const row = { name: "US GDP (Second Estimate), 3rd Quarter 2026", date: "2026-11-25", period: "3rd Quarter 2026", release_stage: "second" };
    const before = JSON.stringify(row);
    assert.equal(formatEvent(row, { tz: "UTC" }), "Wed 25 Nov time unknown  US GDP (Second Estimate), 3rd Quarter 2026");
    assert.equal(JSON.stringify(row), before);
    assert.match(formatEvent({ ...row, name: "Secondary GDP" }), /stage second$/);
  });

  test("date-only economic releases have unknown timing, while holidays stay all day", () => {
    const row = { date: "2026-11-25", name: "US GDP", category: "economic-indicators", release_at_utc: null, all_day: true };
    assert.equal(formatWhen(row, "Asia/Tokyo"), "Wed 25 Nov time unknown");
    assert.equal(formatWhen({ ...row, category: "market-holidays" }, "Asia/Tokyo"), "Wed 25 Nov all day");
    assert.match(formatEvent({ ...row, release_stage: "annual-update" }), /stage annual update$/);
  });

  test("publication windows render localized bounds without inventing an exact release time", () => {
    const row = { date: "2026-11-18", name: "Japan release", release_at_utc: null, all_day: false, time_precision: "range",
      time_window_start: "2026-11-18T12:00:00+09:00", time_window_end: "2026-11-18T12:15:00+09:00", time_role: "publication" };
    const before = JSON.stringify(row);
    assert.equal(formatWhen(row, "Asia/Tokyo"), "Wed 18 Nov 12:00–12:15 GMT+9");
    assert.equal(formatWhen(row, "America/New_York"), "Tue 17 Nov 22:00–22:15 ET");
    assert.equal(formatWhen({ ...row, time_window_end: "invalid" }, "UTC"), "Wed 18 Nov time unknown");
    assert.equal(formatWhen({ ...row, time_window_start: "2026-11-18T12:00:00" }, "UTC"), "Wed 18 Nov time unknown");
    assert.equal(JSON.stringify(row), before);
  });

  test("windows crossing midnight or a DST change show both dates and zone labels", () => {
    assert.equal(formatWhen({ time_window_start: "2026-11-18T23:55:00Z", time_window_end: "2026-11-19T00:05:00Z" }, "UTC"),
      "Wed 18 Nov 23:55 UTC–Thu 19 Nov 00:05 UTC");
    assert.equal(formatWhen({ time_window_start: "2026-11-01T05:55:00Z", time_window_end: "2026-11-01T06:10:00Z" }, "America/New_York"),
      "Sun 01 Nov 01:55 GMT-4–Sun 01 Nov 01:10 GMT-5");
  });

  test("auction close is labelled separately from result publication", () => {
    const row = { name: "US Treasury Bill Auction", date: "2026-11-18", release_at_utc: "2026-11-18T16:30:00Z", time_role: "auction-close",
      auction: { cusip: "912797AB1", high_rate: "4.050000", reopening: false } };
    const before = JSON.stringify(row);
    assert.match(formatEvent(row, { tz: "America/New_York" }), /11:30 ET  US Treasury Bill Auction  auction close$/);
    assert.equal(JSON.stringify(row), before);
  });

  test("eventsToCsv quotes fields containing commas", () => {
    const csv = eventsToCsv([{ date: "2026-10-22", name: "US Initial Jobless Claims: October 22, 2026", all_day: false, consensus: null }]);
    const [header, row] = csv.trim().split("\n");
    assert.match(header, /^date,time_utc,time_et,time_local,all_day,name/);
    assert.match(row, /"US Initial Jobless Claims: October 22, 2026"/);
    assert.match(row, /^2026-10-22,,,,false,/);
  });
});
