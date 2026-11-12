import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const TOOLS = ["next_event", "calendar", "today", "week", "series_list", "series_detail", "history", "economic_results_history", "release_editions", "market_holidays", "market_status", "changes", "countries"];

/** Minimal JSON-RPC client over the server's stdio. */
function startServer(apiKey="fc_live_0123456789abcdef0123456789abcdef") {
  const child = spawn(process.execPath, ["--import", "./test/mock-fetch.mjs", "mcp.js"], { cwd: ROOT, stdio: ["pipe", "pipe", "pipe"], env: { ...process.env, FC_API_KEY: apiKey } });
  const pending = new Map();
  let buf = "";
  child.stdout.on("data", (chunk) => {
    buf += chunk;
    let i;
    while ((i = buf.indexOf("\n")) !== -1) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      const msg = JSON.parse(line);
      if (msg.id !== undefined && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    }
  });
  let nextId = 1;
  const send = (method, params, notify = false) => {
    const msg = { jsonrpc: "2.0", method, params };
    if (!notify) msg.id = nextId++;
    child.stdin.write(JSON.stringify(msg) + "\n");
    if (notify) return Promise.resolve();
    return new Promise((resolve, reject) => {
      pending.set(msg.id, resolve);
      setTimeout(() => reject(new Error(`timeout waiting for ${method}`)), 15000).unref();
    });
  };
  const stop = () => { child.stdin.end(); child.kill(); };
  return { send, stop, child };
}

async function initialised(apiKey) {
  const s = startServer(apiKey);
  const init = await s.send("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "0" } });
  assert.equal(init.result.serverInfo.name, "financecalendar");
  assert.equal(init.result.serverInfo.version, "0.2.2");
  await s.send("notifications/initialized", {}, true);
  return s;
}

describe("MCP server over stdio", () => {
  test("local protocol discovery works but no-key data calls return actionable401 tool error", async () => {
    const server=await initialised("");
    try {const response=await server.send("tools/call",{name:"countries",arguments:{}});assert.equal(response.result.isError,true);assert.match(response.result.content[0].text,/HTTP 401/);assert.match(response.result.content[0].text,/FC_API_KEY/);assert.match(response.result.content[0].text,/account\//);}finally{server.stop();}
  });
  test("initialize + tools/list exposes the 13 tools with schemas", async () => {
    const s = await initialised();
    try {
      const res = await s.send("tools/list", {});
      const names = res.result.tools.map((t) => t.name).sort();
      assert.deepEqual(names, [...TOOLS].sort());
      assert.equal(res.result.tools.length, 13);
      for (const t of res.result.tools) {
        assert.ok(t.description && t.description.length > 30, `${t.name} needs a description`);
        assert.equal(t.inputSchema.type, "object");
        assert.equal(t.annotations.readOnlyHint, true);
        assert.equal(t.annotations.destructiveHint, false);
      }
      const next = res.result.tools.find((t) => t.name === "next_event");
      assert.deepEqual(next.inputSchema.required, ["series"]);
      assert.deepEqual(Object.keys(next.inputSchema.properties).sort(), ["asset", "category", "country", "series", "tz"]);
      const cal = res.result.tools.find((t) => t.name === "calendar");
      assert.deepEqual(Object.keys(cal.inputSchema.properties).sort(), ["asset", "category", "country", "from", "impact", "include_holidays", "limit", "offset", "series", "status", "to", "tz"]);
      const props = (n) => Object.keys(res.result.tools.find((t) => t.name === n).inputSchema.properties).sort();
      assert.deepEqual(props("today"), ["asset", "category", "country", "impact", "tz"]);
      assert.deepEqual(props("week"), ["asset", "category", "country", "impact", "include_holidays", "series", "tz", "which"]);
      assert.deepEqual(props("history"), ["asset", "from", "limit", "series", "to", "tz"]);
      assert.deepEqual(props("changes"), ["change", "cursor", "limit", "series", "since"]);
      assert.deepEqual(props("economic_results_history"), ["from", "ledger_cursor", "limit", "offset", "publication_revision", "series", "to"]);
      assert.deepEqual(props("release_editions"), ["event_id", "ledger_cursor", "limit", "offset", "publication_revision"]);
      const results = res.result.tools.find((t) => t.name === "economic_results_history");
      assert.equal(results.inputSchema.additionalProperties, false);
      assert.deepEqual(results.inputSchema.properties.series.enum, ["us-jolts", "us-adp", "us-ism-services", "us-trade-balance", "us-cpi", "us-nfp", "us-ppi", "us-retail-sales", "us-pce", "us-ism-manufacturing", "us-industrial-production", "us-consumer-confidence"]);
      assert.equal(results.inputSchema.properties.limit.maximum, 5);
      assert.equal(results.inputSchema.properties.limit.default, 5);
      assert.ok(!results.inputSchema.required.includes("limit"));
      assert.equal(results.inputSchema.properties.offset.maximum, 999999);
      assert.equal(results.inputSchema.properties.ledger_cursor.maximum, Number.MAX_SAFE_INTEGER);
      assert.equal(results.inputSchema.properties.publication_revision.minimum, 1);
      assert.match(results.description, /12 supported US headline series/);
      assert.match(results.description, /missing values remain null/);
      const editions = res.result.tools.find((t) => t.name === "release_editions");
      for (const tool of [results, editions]) {
        assert.match(tool.description, /REST \/enrichment\/as-of/);
        assert.match(tool.description, /Python enrichment_as_of\(\)/);
        assert.match(tool.description, /tool does not accept as_of/);
        assert.match(tool.description, /does not establish complete original first-print history/);
        assert.match(tool.description, /both first-page pins/);
        assert.ok(!("as_of" in tool.inputSchema.properties));
        assert.doesNotMatch(tool.description, /as_of queries.*unsupported/);
      }
      assert.match(editions.description, /Provider archives are labelled separately from engine captures/);
    } finally { s.stop(); }
  });

  test("typed crypto filters pass through every relevant tool and preserve structured data", async () => {
    const s = await initialised();
    try {
      const list = await s.send("tools/list", {});
      assert.ok(list.result.tools.find((t) => t.name === "calendar").inputSchema.properties.category.enum.includes("crypto"));
      for (const [name, args] of [
        ["calendar", { category: "crypto" }], ["today", { category: "crypto" }],
        ["week", { category: "crypto" }], ["series_list", { category: "crypto" }],
        ["next_event", { series: "ethereum-network-upgrades" }],
        ["series_detail", { code: "ethereum-network-upgrades" }],
        ["history", { series: "ethereum-network-upgrades" }],
      ]) {
        const response = await s.send("tools/call", { name, arguments: { ...args, asset: "ethereum" } });
        assert.equal(response.result.isError, undefined, name);
        const data = JSON.parse(response.result.content[0].text);
        assert.deepEqual(response.result.structuredContent, data);
        assert.match(JSON.stringify(data), /ethereum-network-upgrades/);
      }
      const response = await s.send("tools/call", { name: "calendar", arguments: { category: "crypto", asset: "ethereum" } });
      const row = response.result.structuredContent.events[1];
      assert.equal(row.country, null);
      assert.equal(row.actual, 0);
      assert.equal(row.crypto.environment, "sepolia");
      assert.equal(row.source_license.adapted, true);
    } finally { s.stop(); }
  });

  test("tools/call next_event returns the fixture as JSON text", async () => {
    const s = await initialised();
    try {
      const res = await s.send("tools/call", { name: "next_event", arguments: { series: "fomc" } });
      assert.equal(res.result.isError, undefined);
      const data = JSON.parse(res.result.content[0].text);
      assert.equal(data.next.title, "FOMC Rate Decision October 2026");
    } finally { s.stop(); }
  });

  test("change cursors reach the API and preserve continuation metadata", async () => {
    const s = await initialised();
    try {
      const first = await s.send("tools/call", { name: "changes", arguments: { limit: 1 } });
      assert.equal(first.result.structuredContent.has_more, true);
      const second = await s.send("tools/call", { name: "changes", arguments: { cursor: first.result.structuredContent.next_cursor } });
      assert.equal(second.result.structuredContent.has_more, false);
      assert.equal(second.result.structuredContent.count, 0);
    } finally { s.stop(); }
  });

  test("economic results and release editions preserve exact provenance and offset metadata", async () => {
    const s = await initialised();
    try {
      const first = await s.send("tools/call", { name: "economic_results_history", arguments: { series: "us-adp", from: "2026-01-01", to: "2026-11-05", limit: 1, offset: 0 } });
      const data = first.result.structuredContent;
      assert.deepEqual(JSON.parse(first.result.content[0].text), data);
      assert.equal(data.as_of_supported, false);
      assert.equal(data.releases[0].actual, "0");
      assert.equal(data.next_offset, 1);
      const second = await s.send("tools/call", { name: "economic_results_history", arguments: { series: "us-adp", limit: 1, offset: data.next_offset, ledger_cursor: data.ledger_cursor, publication_revision: data.publication_revision } });
      assert.equal(second.result.structuredContent.releases[0].consensus, null);
      assert.equal(second.result.structuredContent.next_offset, null);
      const editions = await s.send("tools/call", { name: "release_editions", arguments: { event_id: data.releases[0].event_id, limit: 1 } });
      const proof = editions.result.structuredContent.editions[0];
      assert.equal(proof.provider_edition_id, "vintage-1");
      assert.equal(proof.forecast_type, "survey_consensus");
      assert.notEqual(proof.available_at, proof.received_at);
      assert.equal(editions.result.structuredContent.next_offset, 1);
      const missingPins = await s.send("tools/call", { name: "economic_results_history", arguments: { series: "us-adp", offset: 1 } });
      assert.equal(missingPins.result.isError, true);
      const changedPublication = await s.send("tools/call", { name: "release_editions", arguments: { event_id: "adp-2026-09", offset: 1, ledger_cursor: 3, publication_revision: 6 } });
      assert.equal(changedPublication.result.isError, true);
      assert.match(changedPublication.result.content[0].text, /HTTP 409/);
      for (const series of ["us-cpi", "us-nfp", "us-ppi", "us-retail-sales", "us-pce", "us-ism-manufacturing", "us-industrial-production", "us-consumer-confidence"]) {
        const staged = await s.send("tools/call", { name: "economic_results_history", arguments: { series } });
        assert.equal(staged.result.isError, undefined);
        assert.equal(staged.result.structuredContent.series_code, series);
        assert.deepEqual(staged.result.structuredContent.releases, []);
      }
      for (const args of [{ series: "us-adp", as_of: "2026-11-01" }, { series: "us-adp", limit: 6 }, { series: "us-adp", offset: 1000000 }, { series: "us-core-cpi" }, { series: "us-adp", ledger_cursor: Number.MAX_SAFE_INTEGER + 1 }, { series: "us-adp", publication_revision: 0 }]) {
        const invalid = await s.send("tools/call", { name: "economic_results_history", arguments: args });
        assert.ok(invalid.error?.code === -32602 || invalid.result?.isError === true, JSON.stringify(invalid));
      }
    } finally { s.stop(); }
  });

  test("economic results default to five complete evidence rows and preserve pinned continuation", async () => {
    const s = await initialised();
    try {
      const ids = [], sizes = [];
      let offset = 0, pins = {};
      do {
        const response = await s.send("tools/call", { name: "economic_results_history", arguments: { series: "us-jolts", offset, ...pins } });
        assert.notEqual(response.result.isError, true);
        const data = response.result.structuredContent;
        assert.deepEqual(JSON.parse(response.result.content[0].text), data);
        assert.equal(data.ledger_cursor, 3);
        assert.equal(data.publication_revision, 7);
        assert.ok(data.releases.every((row) => row.selected_editions.consensus.evidence_note.length > 7000));
        sizes.push(data.releases.length);
        ids.push(...data.releases.map((row) => row.event_id));
        offset = data.next_offset;
        pins = { ledger_cursor: data.ledger_cursor, publication_revision: data.publication_revision };
      } while (offset !== null);
      assert.deepEqual(sizes, [5, 5, 2]);
      assert.equal(new Set(ids).size, 12);
    } finally { s.stop(); }
  });

  test("tools/call calendar maps include_holidays and reports API errors as isError", async () => {
    const s = await initialised();
    try {
      const ok = await s.send("tools/call", { name: "calendar", arguments: { from: "2026-11-23", to: "2026-11-30", include_holidays: true } });
      assert.equal(JSON.parse(ok.result.content[0].text).events[0].category, "market-holidays");
      const bad = await s.send("tools/call", { name: "calendar", arguments: { tz: "Mars/Olympus" } });
      assert.equal(bad.result.isError, true);
      assert.match(bad.result.content[0].text, /tz must be an IANA timezone.*HTTP 400/);
    } finally { s.stop(); }
  });

  test("prompts/list has the briefing prompt and prompts/get renders it", async () => {
    const s = await initialised();
    try {
      const list = await s.send("prompts/list", {});
      assert.deepEqual(list.result.prompts.map((p) => p.name), ["economic_calendar_briefing"]);
      const got = await s.send("prompts/get", { name: "economic_calendar_briefing", arguments: { country: "GB", days: "5" } });
      assert.match(got.result.messages[0].content.text, /briefing for GB covering the next 5 days/);
      assert.match(got.result.messages[0].content.text, /call the calendar tool/i);
    } finally { s.stop(); }
  });

  test("resources/list has financecalendar://openapi and resources/read fetches the spec", async () => {
    const s = await initialised();
    try {
      const list = await s.send("resources/list", {});
      assert.deepEqual(list.result.resources.map((r) => r.uri), ["financecalendar://openapi"]);
      const read = await s.send("resources/read", { uri: "financecalendar://openapi" });
      const spec = JSON.parse(read.result.contents[0].text);
      assert.equal(spec.openapi, "3.1.0");
      assert.ok(spec.paths["/calendar"]);
    } finally { s.stop(); }
  });
});
