#!/usr/bin/env node
// MCP server (stdio) for the financecalendar.com API.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { api, baseUrl, VERSION } from "./lib.js";

const server = new McpServer({ name: "financecalendar", version: VERSION });

const ok = (obj) => ({ content: [{ type: "text", text: JSON.stringify(obj, null, 1) }] });
const run = (fn) => async (args) => {
  try {
    return ok(await fn(args || {}));
  } catch (e) {
    return { isError: true, content: [{ type: "text", text: `financecalendar API error: ${e.message}` }] };
  }
};

const country = z.string().optional().describe("ISO alpha-2 country, comma-separated for several: US, GB, EU, DE, JP, CA, AU, CN, CH, NZ, NO, SE, IN, HK. 'uk' and 'eurozone' are accepted.");
const tz = z.string().optional().describe("IANA timezone such as Europe/London; adds time_local (HH:MM) to every row.");
const impact = z.string().optional().describe("high, medium or low; comma-separated for several.");
const date = (what) => z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(what);
const exchange = z.string().optional().describe("nyse (default, same calendar as nasdaq), sifma, cme, lse, tsx, asx, hkex, euronext, jpx, six, xetra, nse or all.");

server.registerTool("next_event", {
  title: "Next event",
  description: "The next occurrence of an economic series or central bank decision: fomc, cpi, nfp (jobs), gdp, pce, ppi, retail-sales, jobless-claims, ism, jolts, ecb, boe, boj, boc, rba, rbnz, snb, pboc, uk-cpi, eurozone-cpi, japan-cpi, or any keyword. Generic names default to the US release; pass country to override. Returns date, UTC and ET time, consensus, prior, actual and the financecalendar.com preview URL.",
  inputSchema: {
    series: z.string().describe("Series code, alias or keyword, e.g. 'fomc', 'cpi', 'nfp', 'boe'."),
    country,
    tz,
  },
}, run(({ series, country, tz }) => api("/next", { series, country, tz })));

server.registerTool("calendar", {
  title: "Economic calendar",
  description: "Scheduled economic releases and central bank decisions in a date range (default today to today + 14 days, at most 92 days). Filter by country, impact, category or series. Market holidays are left out unless include_holidays is true. Rows are soonest first with consensus, prior and actual where known.",
  inputSchema: {
    from: date("Start date YYYY-MM-DD, default today (America/New_York)."),
    to: date("End date YYYY-MM-DD, default from + 14 days, at most 92 days after from."),
    country,
    impact,
    category: z.enum(["economic-indicators", "central-banks-monetary-policy", "market-holidays"]).optional(),
    series: z.string().optional().describe("Series code or alias, comma-separated for several, e.g. 'us-cpi,fomc'."),
    include_holidays: z.boolean().optional().describe("Add exchange holiday rows to the economic rows."),
    status: z.string().optional().describe("confirmed, estimated or released; comma-separated for several."),
    tz,
    limit: z.number().int().min(1).max(500).optional().describe("Rows to return, 1 to 500 (default 100)."),
    offset: z.number().int().min(0).optional().describe("Skip this many rows (paging)."),
  },
}, run(({ include_holidays, ...rest }) => api("/calendar", { ...rest, include: include_holidays ? "holidays" : undefined })));

server.registerTool("today", {
  title: "Today",
  description: "Today's scheduled releases, whether the NYSE is open right now, and any exchange closures today.",
  inputSchema: { country, impact, tz },
}, run(({ country, impact, tz }) => api("/today", { country, impact, tz })));

server.registerTool("week", {
  title: "This or next week",
  description: "Every release Monday to Sunday for this week (default) or next week, optionally filtered by country and impact.",
  inputSchema: {
    which: z.enum(["this", "next"]).optional().describe("this (default) or next."),
    country,
    impact,
    category: z.enum(["economic-indicators", "central-banks-monetary-policy", "market-holidays"]).optional(),
    series: z.string().optional().describe("Series code or alias, comma-separated for several."),
    include_holidays: z.boolean().optional().describe("Add exchange holiday rows to the economic rows."),
    tz,
  },
}, run(({ include_holidays, ...rest }) => api("/week", { ...rest, include: include_holidays ? "holidays" : undefined })));

server.registerTool("series_list", {
  title: "List series",
  description: "Every series the API covers (CPI, NFP, FOMC, ECB and so on, plus exchange holiday calendars) with its code, aliases, country, impact, recurrence and next date. Use it to find the code for series_detail, history or calendar.",
  inputSchema: {
    country,
    category: z.string().optional().describe("economic-indicators, central-banks-monetary-policy or market-holidays."),
    kind: z.enum(["instance", "holiday"]).optional().describe("instance for releases and decisions, holiday for exchange calendars."),
  },
}, run(({ country, category, kind }) => api("/series", { country, category, kind })));

server.registerTool("series_detail", {
  title: "Series detail",
  description: "One series in depth: metadata, next and last events, upcoming dates, recent history and, where published, a verified long-run dataset (e.g. every FOMC decision since 2020).",
  inputSchema: { code: z.string().describe("Series code or alias, e.g. 'fomc', 'us-cpi', 'boe'."), tz },
}, run(({ code, tz }) => api(`/series/${encodeURIComponent(code)}`, { tz })));

server.registerTool("history", {
  title: "Release history",
  description: "Past releases of a series with consensus, prior and actual for each print. Default range is the last 12 months.",
  inputSchema: {
    series: z.string().describe("Series code or alias, e.g. 'us-cpi'."),
    from: date("Start date YYYY-MM-DD."),
    to: date("End date YYYY-MM-DD."),
    limit: z.number().int().min(1).max(500).optional().describe("Rows to return, 1 to 500 (default 100)."),
    tz,
  },
}, run(({ series, from, to, limit, tz }) => api("/history", { series, from, to, limit, tz })));

server.registerTool("market_holidays", {
  title: "Market holidays",
  description: "Exchange holidays and early closes for an exchange (NYSE and Nasdaq by default) and year.",
  inputSchema: { exchange, year: z.number().int().optional().describe("Four-digit year, default the current year.") },
}, run(({ exchange, year }) => api("/holidays", { exchange, year })));

server.registerTool("market_status", {
  title: "Market status",
  description: "Is the exchange open right now? Live session status for NYSE, holiday-aware for other exchanges, with today's holiday (if any) and the next one.",
  inputSchema: { exchange },
}, run(({ exchange }) => api("/market-status", { exchange })));

server.registerTool("changes", {
  title: "Change log",
  description: "What changed in the calendar: new dates, moved dates, consensus updates and actuals, newest first. Default window is the last 24 hours (at most 30 days).",
  inputSchema: {
    since: z.string().optional().describe("ISO 8601 datetime, e.g. 2026-10-18T00:00:00Z."),
    series: z.string().optional().describe("Series code or alias."),
    change: z.enum(["added", "updated", "removed"]).optional(),
    limit: z.number().int().min(1).max(500).optional().describe("Rows to return, 1 to 500 (default 100)."),
  },
}, run(({ since, series, change, limit }) => api("/changes", { since, series, change, limit })));

server.registerTool("countries", {
  title: "Countries",
  description: "Countries the calendar covers, with the number of series and events for each.",
  inputSchema: {},
}, run(() => api("/countries")));

server.registerPrompt("economic_calendar_briefing", {
  title: "Economic calendar briefing",
  description: "Summarise the high-impact economic events coming up for a country over the next few days.",
  argsSchema: {
    country: z.string().optional().describe("ISO alpha-2 country (default US)."),
    days: z.string().optional().describe("How many days ahead to cover (default 7)."),
  },
}, ({ country, days }) => {
  const c = country || "US";
  const n = Number(days) || 7;
  return {
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: [
          `Produce an economic calendar briefing for ${c} covering the next ${n} days.`,
          `1. Call the calendar tool with country="${c}", impact="high" and to set ${n} days after today (use the from/to defaults otherwise).`,
          "2. If fewer than three rows come back, call it again with impact=\"high,medium\".",
          "3. List each event in date order with its local time, consensus and prior, and say in one line why it matters for markets.",
          "4. Finish with a two-sentence summary of the week's main risk events.",
          "Attribute the data to financecalendar.com with a link to https://www.financecalendar.com.",
        ].join("\n"),
      },
    }],
  };
});

server.registerResource("openapi", "financecalendar://openapi", {
  title: "Finance Calendar API OpenAPI spec",
  description: `OpenAPI 3.1 description of the API, fetched from ${baseUrl()}/openapi.`,
  mimeType: "application/json",
}, async (uri) => ({
  contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await api("/openapi"), null, 1) }],
}));

await server.connect(new StdioServerTransport());
