import { test } from "node:test";
import assert from "node:assert/strict";
import { archivePage, collectArchive } from "../lib.js";
import { main } from "../cli.js";

const page = (rows, cursor = null, revision = 7) => ({ schema_version: 1, archive_revision: revision, rows, count: rows.length,
  has_more: cursor !== null, next_cursor: cursor, as_of_basis: "fc_evidence_commit_observed_bound" });
const options = (pages, calls = []) => ({ apiKey: "synthetic-key", fetch: async (url) => {
  calls.push(new URL(url));
  const next = pages.shift();
  assert.ok(next, "No unexpected extra archive requests");
  return new Response(JSON.stringify(next.body ?? next), { status: next.status ?? 200, headers: { "Content-Type": "application/json" } });
} });

test("complete archive collection preserves exact decimals, original filters and receipt metadata", async () => {
  const calls = [], pages = [page([{ id: "a", value: "1.234567890123456789012345" }], "page-2"), page([{ id: "b", value: "0", release_at_utc: null }])];
  const result = await collectArchive("observations", { metric_id: "gb-cpi-all-items-yoy", from: "2006-01-01", limit: 1 }, options(pages, calls));
  assert.deepEqual(result.rows.map((row) => row.value), ["1.234567890123456789012345", "0"]);
  assert.equal(result.rows[1].release_at_utc, null);
  assert.equal(result.count, 2);
  assert.equal(result.pages, 2);
  assert.equal(result.next_cursor, null);
  assert.equal(result.archive_revision, 7);
  assert.ok(calls.every((url) => url.searchParams.get("metric_id") === "gb-cpi-all-items-yoy" && url.searchParams.get("from") === "2006-01-01" && url.searchParams.get("limit") === "1"));
  assert.equal(calls[1].searchParams.get("cursor"), "page-2");
});

test("one-page reads never silently truncate and retain cursor and null values", async () => {
  const body = page([{ id: "dated-release", value: null, release_at_utc: null }], "continue");
  assert.deepEqual(await archivePage("releases", { series_code: "gb-cpi" }, options([body])), body);
  await assert.rejects(archivePage("invalid", {}, options([])), /Archive kind/);
});

for (const [label, second] of [
  ["changed revision", page([{ id: "b" }], null, 8)],
  ["repeated cursor", page([{ id: "b" }], "same")],
  ["empty continuation", page([], "another")],
  ["mismatched count", { ...page([{ id: "b" }]), count: 2 }],
  ["false completion", { ...page([{ id: "b" }], "another"), has_more: false }],
  ["malformed row", { ...page([]), rows: ["bad"], count: 1 }],
  ["HTTP conflict", { status: 409, body: { error: "Archive changed" } }],
]) test(`a ${label} cannot return a partial archive success`, async () => {
  await assert.rejects(collectArchive("observations", {}, options([page([{ id: "a" }], "same"), second])));
});

async function cli(argv, pages) {
  const oldFetch = globalThis.fetch, oldKey = process.env.FC_API_KEY;
  const calls = [], output = [];
  process.env.FC_API_KEY = "synthetic-cli-key";
  globalThis.fetch = options(pages, calls).fetch;
  try { return { code: await main(argv, (text) => output.push(text)), output, calls }; }
  finally { globalThis.fetch = oldFetch; if (oldKey === undefined) delete process.env.FC_API_KEY; else process.env.FC_API_KEY = oldKey; }
}

test("CLI archive commands emit complete JSON pages using exact canonical filter names", async () => {
  for (const [command, suffix] of [["archive-observations", "observations"], ["archive-releases", "releases"]]) {
    const body = page([{ id: "x", value: "0", release_at_utc: null }], "next");
    const result = await cli([command, "--series-code", "gb-cpi", "--metric-id", "gb-cpi-all-items-yoy", "--from", "2006-01-01", "--to", "2026-11-14", "--as-of", "2026-11-14T12:00:00Z", "--limit", "1"], [body]);
    assert.equal(result.code, 0);
    assert.deepEqual(JSON.parse(result.output[0]), body);
    assert.ok(result.calls[0].pathname.endsWith(`/history/${suffix}`));
    assert.equal(result.calls[0].searchParams.get("series_code"), "gb-cpi");
    assert.equal(result.calls[0].searchParams.get("as_of"), "2026-11-14T12:00:00Z");
    assert.equal(result.calls[0].searchParams.get("from"), "2006-01-01");
  }
});

test("CLI --all buffers successful traversal and coverage follows its own pagination", async () => {
  const result = await cli(["history-coverage", "--source-id", "ons", "--kind", "observations", "--limit", "1", "--all"], [page([{ metric_id: "a" }], "next"), page([{ metric_id: "b" }])]);
  assert.equal(result.output.length, 1);
  assert.equal(JSON.parse(result.output[0]).count, 2);
  assert.equal(JSON.parse(result.output[0]).pages, 2);
  assert.ok(result.calls.every((url) => url.pathname.endsWith("/history/coverage") && url.searchParams.get("kind") === "observations"));
});

test("CLI --all produces no output when later traversal fails", async () => {
  const saved = globalThis.fetch, key = process.env.FC_API_KEY, output = [];
  process.env.FC_API_KEY = "synthetic-key";
  globalThis.fetch = options([page([{ id: "a" }], "next"), { status: 409, body: { error: "Archive changed" } }]).fetch;
  try { await assert.rejects(main(["archive-observations", "--metric-id", "gb-cpi-all-items-yoy", "--all"], (text) => output.push(text)), /409/); }
  finally { globalThis.fetch = saved; if (key === undefined) delete process.env.FC_API_KEY; else process.env.FC_API_KEY = key; }
  assert.deepEqual(output, []);
});

test("CLI rejects unsupported archive filters, missing values and misleading partial --all", async () => {
  for (const argv of [
    ["archive-observations"], ["archive-releases", "gb-cpi"], ["archive-releases", "--metric-id"],
    ["history-coverage", "--from", "2006-01-01"], ["history-coverage", "--limit", "501"],
    ["archive-observations", "--metric-id", "x", "--all", "--cursor", "old"],
    ["archive-observations", "--metric-id", "x", "--tz", "UTC"],
  ]) await assert.rejects(cli(argv, []));
});
