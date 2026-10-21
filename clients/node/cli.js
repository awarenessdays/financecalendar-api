#!/usr/bin/env node
// financecalendar: the economic calendar in your terminal.
import { pathToFileURL } from "node:url";
import { realpathSync } from "node:fs";
import { api, formatEvent, formatEvents, formatHoliday, formatSeries, formatChange, localZone, VERSION } from "./lib.js";

const HELP = `financecalendar ${VERSION}: economic calendar in your terminal

Usage:
  financecalendar next <series> [--country uk] [--tz Europe/London]
  financecalendar today [--country us] [--tz ...]
  financecalendar week [--next] [--country ...] [--impact high]
  financecalendar calendar [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--country ...]
                           [--impact high] [--category ...] [--series us-cpi,fomc]
                           [--status confirmed,estimated,released] [--holidays]
                           [--limit 100] [--offset 0] [--csv]
  financecalendar series [--country gb]
  financecalendar show <code>
  financecalendar history <series> [--limit 12]
  financecalendar holidays [exchange] [year]
  financecalendar status [exchange]
  financecalendar changes [--since 2026-10-18T00:00:00Z] [--series ...] [--change updated] [--limit 100]
  financecalendar countries

Options:
  --json      raw API response on any command
  --tz ZONE   render times in an IANA zone (default: your local zone)
  --help      this message

Environment:
  FC_API_KEY  free API key (raises the daily limit), sent as X-API-Key
  FC_API_BASE alternative base URL (default https://www.financecalendar.com/wp-json/fc/v1)

Data: financecalendar.com, free with attribution. https://www.financecalendar.com/api/`;

const BOOL_FLAGS = new Set(["json", "csv", "next", "holidays", "help"]);

export function parseArgs(argv) {
  const pos = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--") { pos.push(...argv.slice(i + 1)); break; }
    if (!a.startsWith("--")) { pos.push(a); continue; }
    const eq = a.indexOf("=");
    const name = eq === -1 ? a.slice(2) : a.slice(2, eq);
    if (eq !== -1) { flags[name] = a.slice(eq + 1); continue; }
    if (BOOL_FLAGS.has(name) || i + 1 >= argv.length || argv[i + 1].startsWith("--")) { flags[name] = true; continue; }
    flags[name] = argv[++i];
  }
  return { pos, flags };
}

function dateRangeLabel(from, to) {
  return `${from} to ${to}`;
}

export async function main(argv, out = console.log) {
  const { pos, flags } = parseArgs(argv);
  const [cmd, ...rest] = pos;
  if (!cmd || flags.help || cmd === "help") { out(HELP); return 0; }
  const tz = flags.tz;
  const zone = localZone(tz);
  const fmt = (events) => formatEvents(events, { tz: zone });
  const json = (obj) => out(JSON.stringify(obj, null, 2));

  switch (cmd) {
    case "next": {
      if (!rest[0]) throw new Error("next needs a series, e.g. financecalendar next fomc");
      const data = await api("/next", { series: rest[0], country: flags.country, tz });
      if (flags.json) return json(data), 0;
      out(formatEvent(data.next, { tz: zone }));
      return 0;
    }
    case "today": {
      const data = await api("/today", { country: flags.country, tz });
      if (flags.json) return json(data), 0;
      const lines = [];
      if (data.market) lines.push(`${data.date}  ${data.market.label}${data.market.holiday ? ` (${data.market.holiday})` : ""}`);
      lines.push(data.events?.length ? fmt(data.events) : "No scheduled releases today.");
      if (data.market_holidays?.length) lines.push("", "Exchange closures today:", fmt(data.market_holidays));
      out(lines.join("\n"));
      return 0;
    }
    case "week": {
      const data = await api("/week", { which: flags.next ? "next" : undefined, country: flags.country, impact: flags.impact, tz });
      if (flags.json) return json(data), 0;
      out(`${flags.next ? "Next week" : "This week"}, ${dateRangeLabel(data.from, data.to)} (${data.total ?? data.count} events)\n`);
      out(data.events?.length ? fmt(data.events) : "No scheduled releases.");
      return 0;
    }
    case "calendar": {
      const params = {
        from: flags.from, to: flags.to, country: flags.country, impact: flags.impact, category: flags.category,
        series: flags.series, include: flags.holidays ? "holidays" : undefined, status: flags.status, tz, limit: flags.limit, offset: flags.offset,
      };
      if (flags.csv) { out((await api("/calendar", { ...params, format: "csv" }, { raw: true })).replace(/\n$/, "")); return 0; }
      const data = await api("/calendar", params);
      if (flags.json) return json(data), 0;
      out(`${dateRangeLabel(data.from, data.to)}: ${data.count} of ${data.total} events\n`);
      out(data.events?.length ? fmt(data.events) : "No scheduled releases in that range.");
      return 0;
    }
    case "series": {
      const data = await api("/series", { country: flags.country, category: flags.category, kind: flags.kind });
      if (flags.json) return json(data), 0;
      out(data.series.map(formatSeries).join("\n"));
      return 0;
    }
    case "show": {
      if (!rest[0]) throw new Error("show needs a series code, e.g. financecalendar show fomc");
      const data = await api(`/series/${encodeURIComponent(rest[0])}`, { tz });
      if (flags.json) return json(data), 0;
      const s = data.series;
      const lines = [
        `${s.name} (${s.code})  ${s.country || ""}  ${s.category}  impact ${s.impact}  ${s.recurrence || ""}`.trim(),
        s.aliases?.length ? `aliases: ${s.aliases.join(", ")}` : "",
        s.publisher ? `publisher: ${s.publisher}${s.source_url ? "  " + s.source_url : ""}` : "",
        s.hub ? `hub: ${s.hub}` : "",
        "",
        data.next ? `Next:\n${formatEvent(data.next, { tz: zone })}` : "Next: none scheduled",
        data.last ? `\nLast:\n${formatEvent(data.last, { tz: zone })}` : "",
      ];
      if (data.upcoming?.length > 1) lines.push("", `Upcoming (${data.upcoming.length}):`, fmt(data.upcoming.slice(0, 8)));
      out(lines.filter((l) => l !== "").join("\n"));
      return 0;
    }
    case "history": {
      if (!rest[0]) throw new Error("history needs a series, e.g. financecalendar history us-cpi");
      const data = await api("/history", { series: rest[0], from: flags.from, to: flags.to, limit: flags.limit, tz });
      if (flags.json) return json(data), 0;
      out(`${data.series_code || rest[0]}: ${data.count} releases, ${dateRangeLabel(data.from, data.to)}\n`);
      out(data.events?.length ? fmt(data.events) : "No past releases in that range.");
      return 0;
    }
    case "holidays": {
      const data = await api("/holidays", { exchange: rest[0], year: rest[1] || flags.year });
      if (flags.json) return json(data), 0;
      out(`${data.exchange.toUpperCase()} holidays (${data.count})\n`);
      out(data.holidays.map(formatHoliday).join("\n"));
      return 0;
    }
    case "status": {
      const data = await api("/market-status", { exchange: rest[0] });
      if (flags.json) return json(data), 0;
      const lines = [`${data.label}  (${data.local_time || data.time_utc})`];
      if (data.session) lines.push(`session ${data.session.open}-${data.session.close}${data.session.break ? ` (break ${data.session.break})` : ""} ${data.tz || ""}`.trim());
      if (data.holiday_today) lines.push(`holiday today: ${data.holiday_today}`);
      if (data.next_holiday) lines.push(`next holiday: ${data.next_holiday.date}  ${data.next_holiday.name}  ${data.next_holiday.status}`);
      out(lines.join("\n"));
      return 0;
    }
    case "changes": {
      const data = await api("/changes", { since: flags.since, series: flags.series, change: flags.change, limit: flags.limit });
      if (flags.json) return json(data), 0;
      out(`${data.count} changes since ${data.since}\n`);
      out(data.changes.length ? data.changes.map(formatChange).join("\n") : "No changes.");
      return 0;
    }
    case "countries": {
      const data = await api("/countries");
      if (flags.json) return json(data), 0;
      out(data.countries.map((c) => `${c.code}  ${(c.name || "").padEnd(16)} ${String(c.series).padStart(3)} series  ${String(c.events).padStart(5)} events`).join("\n"));
      return 0;
    }
    default:
      throw new Error(`Unknown command "${cmd}". Run financecalendar --help.`);
  }
}

// Only run when executed directly (not when imported by tests).
if (process.argv[1] && import.meta.url === pathToFileURL(realpathSync(process.argv[1])).href) {
  try {
    process.exitCode = await main(process.argv.slice(2));
  } catch (e) {
    console.error("Error:", e.cause?.message || e.message);
    process.exitCode = 1;
  }
}
