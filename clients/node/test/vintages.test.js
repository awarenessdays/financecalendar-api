import { test } from "node:test";
import assert from "node:assert/strict";
import { archivePage, archiveEditions, archiveForecasts, vintageCoverage, collectArchive } from "../lib.js";
import { main } from "../cli.js";
const page = (rows, cursor = null, revision = 7) => ({ schema_version: 2, rows, count: rows.length, archive_revision: revision,
  next_cursor: cursor, has_more: cursor !== null, order_date_basis: "forecast_issue_period_start_index" });
const fixture = (pages, calls) => ({ apiKey: "synthetic-key", fetch: async (url) => {
  calls.push(new URL(url)); const body = pages.shift(); assert.ok(body, "No unexpected request");
  return new Response(JSON.stringify(body.body ?? body), { status: body.status ?? 200 });
} });
for (const [read, route] of [[archiveEditions, "editions"], [archiveForecasts, "forecasts"], [vintageCoverage, "vintage-coverage"]]) {
  test(`new ${route} helper preserves exact row and source metadata`, async () => {
    const calls = [], body = page([{ value: "0.000000000000000000001", raw_value: "0", scale: "1000", available_at: null,
      issue_period: "2026-Q4", reference_period: "2027", source_license: { attribution: "Original data are freely available from the ECB." } }]);
    assert.deepEqual(await read({ metric_id: "exact", limit: 1 }, fixture([body], calls)), body);
    assert.ok(calls[0].pathname.endsWith(`/history/${route}`));
  });
}
for (const kind of ["editions", "forecasts", "vintage-coverage"]) test(`complete ${kind} export keeps filters and continuation`, async () => {
  const calls = [], result = await collectArchive(kind, { metric_id: "exact", limit: 1 }, fixture([page([{ value: "0" }], "next"), page([{ value: null }])], calls));
  assert.deepEqual(result.rows.map((r) => r.value), ["0", null]); assert.equal(result.pages, 2);
  assert.ok(calls.every((u) => u.searchParams.get("metric_id") === "exact" && u.searchParams.get("limit") === "1"));
  assert.equal(calls[1].searchParams.get("cursor"), "next");
});
test("v2 rejects a legacy-schema response and changed or repeated continuation", async () => {
  await assert.rejects(archivePage("forecasts", {}, fixture([{ ...page([]), schema_version: 1 }], [])), /schema/);
  for (const bad of [page([{ id: "b" }], null, 8), page([{ id: "b" }], "next"), page([], "another")])
    await assert.rejects(collectArchive("forecasts", {}, fixture([page([{ id: "a" }], "next"), bad], [])));
});
async function cli(argv, pages, output = [], calls = []) {
  const fetch = globalThis.fetch, key = process.env.FC_API_KEY;
  process.env.FC_API_KEY = "synthetic-key"; globalThis.fetch = fixture(pages, calls).fetch;
  try { await main(argv, (text) => output.push(text)); return { output, calls }; }
  finally { globalThis.fetch = fetch; if (key === undefined) delete process.env.FC_API_KEY; else process.env.FC_API_KEY = key; }
}
for (const [command, route] of [["historic-editions", "editions"], ["historic-forecasts", "forecasts"], ["vintage-coverage", "vintage-coverage"]])
  test(`CLI ${command} emits a complete buffered export`, async () => {
    const { output, calls } = await cli([command, "--metric-id", "exact", "--all", "--limit", "1"], [page([{ value: "0" }], "next"), page([{ value: null }])]);
    assert.equal(output.length, 1); assert.equal(JSON.parse(output[0]).count, 2);
    assert.ok(calls.every((u) => u.pathname.endsWith(`/history/${route}`)));
  });
test("CLI keeps strict availability distinct from FC receipt cutoff, and no partial output", async () => {
  const { output, calls } = await cli(["historic-forecasts", "--metric-id", "exact", "--as-of", "2026-11-15T08:00:00Z", "--available-before", "2026-01-01T00:00:00Z"], [page([])]);
  assert.equal(JSON.parse(output[0]).count, 0);
  assert.equal(calls[0].searchParams.get("available_before"), "2026-01-01T00:00:00Z");
  const partial = [];
  await assert.rejects(cli(["historic-editions", "--metric-id", "exact", "--all"], [page([{ id: "a" }], "next"), { status: 409, body: { error: "Archive changed" } }], partial));
  assert.deepEqual(partial, []);
  for (const args of [["vintage-coverage", "--from", "2026-01-01"], ["vintage-coverage", "--kind", "observations"], ["historic-forecasts", "--metric-id", "exact", "--target", "2027"]])
    await assert.rejects(cli(args, []));
});
test("strict cutoffs reject coarse, naive, invalid and future clocks before request", async () => {
  for (const value of ["2026-01-01", "2026-Q1", "2026-01-01T12:30:00", "2026-01-01T12:30:00+00:00", "2026-02-31T00:00:00Z", "2099-01-01T00:00:00Z"]) {
    const calls = [];
    await assert.rejects(archiveForecasts({ metric_id: "exact", available_before: value }, fixture([], calls)));
    assert.deepEqual(calls, []);
  }
});
