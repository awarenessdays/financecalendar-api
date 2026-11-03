import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { addDays, dateInZone, safeLink, validDate } from './public/model.mjs';
import { demoCalendar } from './demo.mjs';

export const API_ENDPOINT = 'https://www.financecalendar.com/wp-json/fc/v1/calendar';
export const CACHE_MS = 30 * 60 * 1000;
const BODY_LIMIT = 4 * 1024 * 1024;
const ROOT = new URL('./public/', import.meta.url);
const ASSETS = new Map([
  ['/', ['index.html', 'text/html; charset=utf-8']],
  ['/favicon.svg', ['favicon.svg', 'image/svg+xml']],
  ['/app.mjs', ['app.mjs', 'text/javascript; charset=utf-8']],
  ['/model.mjs', ['model.mjs', 'text/javascript; charset=utf-8']],
  ['/styles.css', ['styles.css', 'text/css; charset=utf-8']],
  ['/fonts/Inter-Regular.ttf', ['fonts/Inter-Regular.ttf', 'font/ttf']],
  ['/fonts/Inter-Bold.ttf', ['fonts/Inter-Bold.ttf', 'font/ttf']],
  ['/fonts/LICENSE-Inter.txt', ['fonts/LICENSE-Inter.txt', 'text/plain; charset=utf-8']],
]);

export function readConfig(env = process.env, args = process.argv.slice(2)) {
  const demo = args.includes('--demo');
  const key = String(env.FC_API_KEY || '').trim();
  if (!demo && !key) throw new Error('Set FC_API_KEY in the server environment, or run npm run demo to preview labelled demo data.');
  if (key && (!/^[\x21-\x7e]{1,255}$/.test(key))) throw new Error('FC_API_KEY must contain a valid single-line API key.');
  const countries = [...new Set(String(env.FC_COUNTRIES || 'US,GB,EU').toUpperCase().split(',').map(value => value.trim()).filter(Boolean))];
  if (!countries.length || countries.length > 12 || countries.some(value => !/^[A-Z]{2}$/.test(value))) throw new Error('FC_COUNTRIES must contain 1–12 comma-separated two-letter country codes.');
  const timeZone = String(env.FC_TIMEZONE || 'Europe/London');
  try { new Intl.DateTimeFormat('en-GB', { timeZone }).format(); } catch { throw new Error('FC_TIMEZONE must be a valid IANA time zone, such as Europe/London.'); }
  const days = Number(env.FC_DAYS || 14);
  if (!Number.isInteger(days) || days < 1 || days > 28) throw new Error('FC_DAYS must be an integer from 1 to 28.');
  const port = Number(env.PORT || 3010);
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be an integer from 0 to 65535.');
  return Object.freeze({ demo, key, countries: Object.freeze(countries), timeZone, days, port, host: String(env.HOST || '127.0.0.1') });
}

const text = (value, max = 500) => typeof value === 'string' ? value.replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max) : null;
const scalar = value => typeof value === 'number' && Number.isFinite(value) ? value : typeof value === 'string' ? value : null;
const isoInstant = value => typeof value === 'string' && validDate(value.slice(0, 10)) && /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)) ? value : null;

export function normaliseEvent(row, index) {
  if (!row || typeof row !== 'object' || Array.isArray(row)) return null;
  // Preserve every supplied rights/credit field. The upstream response is
  // already bounded to 4 MiB; legal notices must not be silently shortened.
  const credits = [], pending = [
    { value: row.source_rights, path: ['Source rights'] },
    { value: row.source_license, path: ['Source licence'] },
  ];
  // Numerical observations can carry a different publisher, evidence and reuse
  // notice from the schedule itself. Preserve these with their metric and role
  // rather than treating only event-level rights as the complete source credit.
  for (const [index, observation] of (Array.isArray(row.observations) ? row.observations : []).entries()) {
    if (!observation || typeof observation !== 'object' || Array.isArray(observation)) continue;
    const path = [`Observation ${index + 1}`, ...[observation.metric_id, observation.role].filter(value => typeof value === 'string' && value.length)];
    for (const [key, label] of [['source_license', 'Source licence'], ['source_rights', 'Source rights'], ['source_url', 'Source evidence'], ['source_api_url', 'Publisher API evidence'], ['measurement_basis_url', 'Measurement basis']]) {
      pending.push({ value: observation[key], path: [...path, label] });
    }
  }
  const labels = { attribution_url: 'Attribution link', source_url: 'Source evidence', terms_url: 'Publisher terms', vintage_notice: 'Vintage notice', url: 'Link', policy: 'Policy' };
  while (pending.length) {
    const { value, path } = pending.pop();
    if (value === null || value === undefined) continue;
    if (typeof value === 'object') {
      const entries = Array.isArray(value) ? value.map((item, index) => [`Item ${index + 1}`, item]) : Object.entries(value);
      for (const [key, child] of entries.reverse()) pending.push({ value: child, path: [...path, labels[key] || key.replaceAll('_', ' ')] });
    } else if (['string', 'number', 'boolean'].includes(typeof value) && String(value).length) {
      const content = String(value);
      credits.push({ label: path.join(' / '), text: content, url: safeLink(content) });
    }
  }
  return {
    id: text(String(row.id ?? `record-${index}`), 200), name: text(row.name || row.title || row.series_name, 240) || 'Unnamed release',
    country: text(row.country, 8), category: text(row.category, 100), series_code: text(row.series_code, 150),
    impact: ['high', 'medium', 'low'].includes(row.impact) ? row.impact : null,
    date: validDate(row.date), release_at_utc: isoInstant(row.release_at_utc), release_tz: text(row.release_tz, 100),
    time_precision: text(row.time_precision, 40) || 'unknown', all_day: row.all_day === true,
    time_window_start: text(row.time_window_start, 100), time_window_end: text(row.time_window_end, 100),
    status: text(row.status, 80), actual: scalar(row.actual), prior: scalar(row.prior), unit: text(row.unit, 100), period: text(row.period, 200),
    source_name: text(row.source_name, 240), source_url: safeLink(row.source_url), page_url: safeLink(row.page_url || row.url),
    last_verified_at: isoInstant(row.last_verified_at), data_stale: typeof row.data_stale === 'boolean' ? row.data_stale : null,
    credits,
  };
}

class FeedError extends Error {
  constructor(code, message, status = null, retryAfter = null) { super(message); this.code = code; this.status = status; this.retryAfter = retryAfter; }
}

function retryDelay(header, now) {
  if (!header) return 0;
  const seconds = Number(header);
  if (Number.isFinite(seconds) && seconds >= 0) return seconds * 1000;
  const date = Date.parse(header);
  return Number.isFinite(date) ? Math.max(0, date - now) : 0;
}

async function readJson(response) {
  const chunks = []; let size = 0;
  for await (const chunk of response.body || []) {
    size += chunk.byteLength;
    if (size > BODY_LIMIT) throw new FeedError('invalid_response', 'The calendar response was too large. Narrow FC_COUNTRIES or FC_DAYS on the server.');
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch (error) {
    if (error instanceof FeedError) throw error;
    throw new FeedError('invalid_response', 'The calendar response could not be read. The last available view is retained.');
  }
}

export function createFeedStore({ config, fetchImpl = globalThis.fetch, now = Date.now, cacheMs = CACHE_MS }) {
  let cached = null, fetchedAt = null, lastAttemptAt = null, nextAttemptAt = 0, error = null, inFlight = null;
  const snapshot = () => ({
    state: config.demo ? 'demo' : error ? (cached ? 'stale' : 'unavailable') : 'fresh', demo: config.demo,
    fetched_at: fetchedAt === null ? null : new Date(fetchedAt).toISOString(),
    last_attempt_at: lastAttemptAt === null ? null : new Date(lastAttemptAt).toISOString(),
    next_refresh_at: new Date(nextAttemptAt).toISOString(), cache_minutes: cacheMs / 60000,
    error: error ? { code: error.code, message: error.message, upstream_status: error.status } : null,
    config: { countries: [...config.countries], timezone: config.timeZone, days: config.days },
    ...(cached ? structuredClone(cached) : { events: [], total: 0, truncated: false, window: null }),
  });
  async function refresh() {
    lastAttemptAt = now(); nextAttemptAt = lastAttemptAt + cacheMs;
    try {
      const from = dateInZone(new Date(lastAttemptAt), config.timeZone), to = addDays(from, config.days - 1);
      const url = new URL(API_ENDPOINT);
      for (const [name, value] of Object.entries({ country: config.countries.join(','), from, to, tz: config.timeZone, limit: '500' })) url.searchParams.set(name, value);
      let body;
      if (config.demo) {
        body = demoCalendar(from);
        body.events = body.events.filter(event => config.countries.includes(event.country) && event.date <= to);
        body.total = body.events.length;
      } else {
        const response = await fetchImpl(url, { headers: { 'X-API-Key': config.key, Accept: 'application/json', 'User-Agent': 'financecalendar-dashboard-starter/1.0' }, redirect: 'error', signal: AbortSignal.timeout(12000) });
        if (!response.ok) {
          const message = response.status === 429 ? 'The API allowance has been reached. Cached records remain available; check the account allowance before the next refresh.' : [401, 403].includes(response.status) ? 'The API key was not accepted. Check FC_API_KEY and account access on the server.' : 'The data provider is temporarily unavailable. The last available view is retained.';
          throw new FeedError(response.status === 429 ? 'rate_limited' : [401, 403].includes(response.status) ? 'authentication' : 'upstream_unavailable', message, response.status, retryDelay(response.headers.get('retry-after'), now()));
        }
        body = await readJson(response);
      }
      if (!body || !Array.isArray(body.events)) throw new FeedError('invalid_response', 'The calendar response did not contain an events list. The last available view is retained.');
      const events = body.events.slice(0, 500).map(normaliseEvent).filter(Boolean);
      const total = Number.isSafeInteger(body.total) && body.total >= events.length ? body.total : events.length;
      cached = { events, total, truncated: total > events.length || body.events.length > 500, window: { from, to } };
      fetchedAt = now(); nextAttemptAt = fetchedAt + cacheMs; error = null;
    } catch (cause) {
      error = cause instanceof FeedError ? cause : new FeedError('connection', 'The calendar could not be reached. Check the server connection; the last available view is retained.');
      nextAttemptAt = Math.max(nextAttemptAt, now() + Math.max(cacheMs, error.retryAfter || 0));
    }
  }
  return {
    async read() {
      if (inFlight) await inFlight;
      else if (now() >= nextAttemptAt) {
        inFlight = refresh();
        try { await inFlight; } finally { inFlight = null; }
      }
      return snapshot();
    },
  };
}

function secureHeaders(response) {
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
  response.setHeader('Cache-Control', 'no-store');
}
function json(response, status, value, secret = '') {
  let body = JSON.stringify(value);
  if (secret) body = body.replaceAll(secret, '[redacted]');
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' }); response.end(body);
}

export function createDashboardServer({ config = readConfig(), fetchImpl = globalThis.fetch, now = Date.now } = {}) {
  const store = createFeedStore({ config, fetchImpl, now });
  const server = createServer(async (request, response) => {
    secureHeaders(response);
    try {
      const url = new URL(request.url, 'http://localhost');
      if (!['GET', 'HEAD'].includes(request.method)) { response.setHeader('Allow', 'GET, HEAD'); return json(response, 405, { error: 'Use GET to read this dashboard.' }); }
      if (url.pathname === '/api/events') {
        if (url.search) return json(response, 400, { error: 'Use the on-page filters. Upstream countries, time zone and window are fixed in server configuration.' });
        if (request.method === 'HEAD') { response.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' }); return response.end(); }
        const data = await store.read(); return json(response, data.state === 'unavailable' ? 503 : 200, data, config.key);
      }
      if (url.pathname === '/favicon.ico' && !url.search) { response.writeHead(204); return response.end(); }
      const asset = ASSETS.get(url.pathname);
      if (!asset || url.search) return json(response, 404, { error: 'Not found.' });
      const content = await readFile(new URL(asset[0], ROOT));
      response.writeHead(200, { 'Content-Type': asset[1] }); response.end(request.method === 'HEAD' ? undefined : content);
    } catch { json(response, 500, { error: 'The dashboard could not complete this request.' }); }
  });
  return { server, store };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const config = readConfig(); const { server } = createDashboardServer({ config });
    server.listen(config.port, config.host, () => console.log(`Finance Calendar dashboard: http://${config.host}:${server.address().port}${config.demo ? ' (demo data)' : ''}`));
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
