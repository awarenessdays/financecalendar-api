import { test } from "node:test";
import assert from "node:assert/strict";
import { main } from "../cli.js";

test("Free schedule commands render omitted paid fields without inventing results or market status", async (t) => {
  const payload = {
    from: "2026-11-12", to: "2026-11-12", count: 1, total: 1, truncated: false,
    events: [{ id: "example-release", series_code: "example", name: "Example release", country: "US",
      category: "economic-indicators", impact: "high", date: "2026-11-12",
      release_at_utc: "2026-11-12T13:30:00Z", time_precision: "minute", all_day: false,
      status: "scheduled", source_url: "https://example.org/release", source_name: "Example publisher", url: null }],
    generated_at: "2026-11-12T10:00:00Z", attribution: { source: "financecalendar.com" },
    free_developer: { daily_limit: 10, monthly_limit: 100, max_events_per_response: 20 },
  };
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.ok(["/calendar", "/today"].some(path => url.pathname.endsWith(path)));
    assert.equal(url.search, "");
    assert.equal(init.headers["X-API-Key"], "fixture-free-key");
    return new Response(JSON.stringify(payload));
  });
  const prior = process.env.FC_API_KEY;
  process.env.FC_API_KEY = "fixture-free-key";
  try {
    for (const command of ["today", "calendar"]) {
      const lines = [];
      assert.equal(await main([command], line => lines.push(line)), 0);
      assert.match(lines.join("\n"), /Example release \(US\)/);
      assert.doesNotMatch(lines.join("\n"), /cons\.|prior |actual |NYSE|Exchange closures|undefined|not available/);
    }
    const json = [];
    await main(["today", "--json"], line => json.push(line));
    assert.deepEqual(JSON.parse(json[0]), payload);
  } finally {
    if (prior === undefined) delete process.env.FC_API_KEY;
    else process.env.FC_API_KEY = prior;
  }
});
