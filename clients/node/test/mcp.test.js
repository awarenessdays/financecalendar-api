import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const TOOLS = ["next_event", "calendar", "today", "week", "series_list", "series_detail", "history", "market_holidays", "market_status", "changes", "countries"];

/** Minimal JSON-RPC client over the server's stdio. */
function startServer() {
  const child = spawn(process.execPath, ["--import", "./test/mock-fetch.mjs", "mcp.js"], { cwd: ROOT, stdio: ["pipe", "pipe", "pipe"], env: { ...process.env, FC_API_KEY: "" } });
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

async function initialised() {
  const s = startServer();
  const init = await s.send("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "test", version: "0" } });
  assert.equal(init.result.serverInfo.name, "financecalendar");
  assert.equal(init.result.serverInfo.version, "0.2.0");
  await s.send("notifications/initialized", {}, true);
  return s;
}

describe("MCP server over stdio", () => {
  test("initialize + tools/list exposes the 11 tools with schemas", async () => {
    const s = await initialised();
    try {
      const res = await s.send("tools/list", {});
      const names = res.result.tools.map((t) => t.name).sort();
      assert.deepEqual(names, [...TOOLS].sort());
      assert.equal(res.result.tools.length, 11);
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
      assert.deepEqual(props("changes"), ["change", "limit", "series", "since"]);
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
