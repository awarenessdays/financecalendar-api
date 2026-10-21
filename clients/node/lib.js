// Shared HTTP client and formatting helpers for the financecalendar.com API.
// Zero runtime dependencies: uses the global fetch available in Node 20+.

export const VERSION = "0.2.0";
export const DEFAULT_BASE = "https://www.financecalendar.com/wp-json/fc/v1";
export const USER_AGENT = `financecalendar-mcp/${VERSION}`;

/** Resolve the API base URL: explicit argument, then FC_API_BASE, then the production default. */
export function baseUrl(base) {
  return String(base || process.env.FC_API_BASE || DEFAULT_BASE).replace(/\/+$/, "");
}

/** Encode query params: drop empty values, join arrays with commas, map booleans to 1/0. */
export function buildUrl(path, params = {}, base) {
  const url = new URL(baseUrl(base) + (path.startsWith("/") ? path : "/" + path));
  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null || v === "" || v === false) continue;
    url.searchParams.set(k, Array.isArray(v) ? v.join(",") : v === true ? "1" : String(v));
  }
  return url;
}

/**
 * Call the API. Resolves to parsed JSON (or the raw text when {raw: true}).
 * Throws an Error whose message carries the API's `error` text, the HTTP status and,
 * for 429 responses, the Retry-After value. The Error also has .status and .retryAfter.
 */
export async function api(path, params = {}, { apiKey, base, raw = false, fetch: fetchFn } = {}) {
  const url = buildUrl(path, params, base);
  const key = apiKey || process.env.FC_API_KEY;
  const headers = { "User-Agent": USER_AGENT, Accept: raw ? "text/csv, text/plain, */*" : "application/json" };
  if (key) headers["X-API-Key"] = key;
  const doFetch = fetchFn || globalThis.fetch;
  const r = await doFetch(url, { headers });
  if (!r.ok) throw await errorFromResponse(r);
  return raw ? r.text() : r.json();
}

export async function errorFromResponse(r) {
  let detail = "";
  let body = "";
  try {
    body = await r.text();
    const j = JSON.parse(body);
    if (j && typeof j.error === "string") detail = j.error;
  } catch {
    detail = body.length && body.length < 200 ? body.trim() : "";
  }
  const retryAfter = r.headers && typeof r.headers.get === "function" ? r.headers.get("retry-after") : null;
  const parts = [`HTTP ${r.status}`];
  if (r.status === 429) parts[0] = "HTTP 429 rate limit reached";
  if (retryAfter) parts.push(`retry after ${retryAfter}s`);
  const msg = detail ? `${detail} (${parts.join(", ")})` : parts.join(", ");
  const err = new Error(msg);
  err.status = r.status;
  err.retryAfter = retryAfter ? Number(retryAfter) : null;
  err.body = body;
  return err;
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

/** The zone to render times in: explicit tz, else the user's local zone. */
export function localZone(tz) {
  if (tz) return tz;
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

const ZONE_LABELS = { "America/New_York": "ET", "America/Chicago": "CT", "America/Los_Angeles": "PT", UTC: "UTC", "Etc/UTC": "UTC" };

function zoneLabel(parts, tz) {
  if (ZONE_LABELS[tz]) return ZONE_LABELS[tz];
  const p = parts.find((x) => x.type === "timeZoneName");
  return p ? p.value : tz;
}

/** Render a UTC instant, or the source date with its timing precision. */
export function formatWhen(e, tz) {
  const zone = localZone(tz);
  const window = formatWindow(e.time_window_start, e.time_window_end, zone);
  if (window) return window;
  if (!e.release_at_utc || e.all_day) {
    const [y, m, d] = String(e.date || "").split("-").map(Number);
    if (!y) return "";
    const dt = new Date(Date.UTC(y, m - 1, d, 12));
    const f = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "2-digit", month: "short" });
    const timing = e.category === "market-holidays" ? "all day" : "time unknown";
    return `${pick(f.formatToParts(dt))} ${timing}`;
  }
  const dt = new Date(e.release_at_utc);
  const f = new Intl.DateTimeFormat("en-GB", {
    timeZone: zone, weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZoneName: "short",
  });
  const parts = f.formatToParts(dt);
  const g = (t) => (parts.find((x) => x.type === t) || {}).value || "";
  return `${g("weekday")} ${g("day")} ${g("month")} ${g("hour")}:${g("minute")} ${zoneLabel(parts, zone)}`;
}

function formatWindow(start, end, zone) {
  const zoned = (value) => typeof value === "string" && /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
  if (!zoned(start) || !zoned(end)) return null;
  const from = new Date(start), to = new Date(end);
  if (!Number.isFinite(from.getTime()) || !Number.isFinite(to.getTime()) || to < from) return null;
  const formatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: zone, weekday: "short", year: "numeric", day: "2-digit", month: "short",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZoneName: "short",
  });
  const a = formatter.formatToParts(from), b = formatter.formatToParts(to);
  const get = (parts, type) => parts.find((part) => part.type === type)?.value || "";
  const clock = (parts) => `${get(parts, "hour")}:${get(parts, "minute")}`;
  const sameDay = ["year", "month", "day"].every((type) => get(a, type) === get(b, type));
  const sameOffset = get(a, "timeZoneName") === get(b, "timeZoneName");
  if (sameDay && sameOffset) return `${pick(a)} ${clock(a)}–${clock(b)} ${zoneLabel(a, zone)}`;
  const endpoint = (parts) => `${pick(parts)}${get(a, "year") !== get(b, "year") ? " " + get(parts, "year") : ""} ${clock(parts)} ${sameOffset ? zoneLabel(parts, zone) : get(parts, "timeZoneName")}`;
  return `${endpoint(a)}–${endpoint(b)}`;
}

function pick(parts) {
  const g = (t) => (parts.find((x) => x.type === t) || {}).value || "";
  return `${g("weekday")} ${g("day")} ${g("month")}`;
}

/**
 * One event on a line, URL on the next:
 *   Tue 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold
 *   https://www.financecalendar.com/event/fomc-rate-decision-october-2026/
 */
export function formatEvent(e, { tz } = {}) {
  const name = e.name || e.title || "";
  const bits = [formatWhen(e, tz), `${name}${e.country ? ` (${e.country})` : ""}`];
  if (e.time_role === "auction-close" && !containsDetail(name, "auction close")) bits.push("auction close");
  if (e.period && !containsDetail(name, e.period)) bits.push(`period ${e.period}`);
  if (e.release_stage && !containsDetail(name, e.release_stage)) bits.push(`stage ${String(e.release_stage).replace(/[-_]+/g, " ")}`);
  if (e.consensus) bits.push(`cons. ${e.consensus}`);
  if (e.prior) bits.push(`prior ${e.prior}`);
  if (e.actual) bits.push(`actual ${e.actual}`);
  if (e.category === "market-holidays" && e.holiday_status === "early_close" && e.close_time_local) bits.push(`closes ${e.close_time_local} local`);
  const line = bits.filter(Boolean).join("  ");
  return e.url ? `${line}\n${e.url}` : line;
}

function containsDetail(name, detail) {
  const words = (value) => String(value).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const normalized = words(detail);
  return normalized && ` ${words(name)} `.includes(` ${normalized} `);
}

export function formatEvents(events, opts) {
  return (events || []).map((e) => formatEvent(e, opts)).join("\n");
}

export function formatHoliday(h) {
  const status = h.status === "early_close" ? `early close ${h.close_time_local || h.close_time_et || ""}`.trim() : "closed";
  return `${h.date}  ${h.name}  ${h.exchange ? h.exchange.toUpperCase() + "  " : ""}${status}`;
}

export function formatSeries(s) {
  const next = s.next_date ? `next ${s.next_date}` : "next tbc";
  return `${s.code.padEnd(24)} ${(s.name || "").padEnd(44)} ${(s.country || "--").padEnd(3)} ${(s.impact || "").padEnd(7)} ${next}`;
}

export function formatChange(c) {
  const what = c.field ? `${c.field}: ${c.old ?? "-"} -> ${c.new ?? "-"}` : "";
  return `${c.at}  ${c.change.padEnd(7)} ${c.series_code.padEnd(16)} ${c.id}${what ? "  " + what : ""}`;
}

const CSV_COLUMNS = ["date", "time_utc", "time_et", "time_local", "all_day", "name", "title", "country", "category", "impact", "status", "consensus", "prior", "actual", "unit", "period", "series_code", "id", "url", "source_url"];

/** Build CSV locally from event rows (used when the API's own CSV is not requested). */
export function eventsToCsv(events) {
  const esc = (v) => {
    if (v === null || v === undefined) return "";
    const s = typeof v === "boolean" ? String(v) : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [CSV_COLUMNS.join(",")];
  for (const e of events || []) lines.push(CSV_COLUMNS.map((c) => esc(e[c])).join(","));
  return lines.join("\n") + "\n";
}
