import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { api, buildUrl, baseUrl, formatEvent, formatWhen, eventsToCsv, USER_AGENT, DEFAULT_BASE } from "../lib.js";
import { installMockFetch, fixture, toResponse } from "./fixtures.js";

const realFetch = globalThis.fetch;
const env = { ...process.env };
afterEach(() => {
  globalThis.fetch = realFetch;
  for (const k of ["FC_API_BASE", "FC_API_KEY"]) { if (env[k] === undefined) delete process.env[k]; else process.env[k] = env[k]; }
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
    assert.match(formatEvent(row, { tz: "America/New_York" }), /^Wed 14 Oct 08:30 ET  US CPI \(US\)  cons\. 3\.0% y\/y  prior 3\.1% y\/y  actual 3\.0% y\/y\n/);
  });

  test("eventsToCsv quotes fields containing commas", () => {
    const csv = eventsToCsv([{ date: "2026-10-22", name: "US Initial Jobless Claims: October 22, 2026", all_day: false, consensus: null }]);
    const [header, row] = csv.trim().split("\n");
    assert.match(header, /^date,time_utc,time_et,time_local,all_day,name/);
    assert.match(row, /"US Initial Jobless Claims: October 22, 2026"/);
    assert.match(row, /^2026-10-22,,,,false,/);
  });
});
