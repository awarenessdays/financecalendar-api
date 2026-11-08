#!/usr/bin/env node
/** One-shot, cached high-impact calendar watchlist. Node 20+, no packages. */
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, lstat, open, rename, unlink } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join, dirname } from 'node:path';
import { performance } from 'node:perf_hooks';

const OFFICIAL = 'https://www.financecalendar.com/wp-json/fc/v1/calendar';
const ACCOUNT = 'https://www.financecalendar.com/account/';
const CACHE_MS = 900_000, BODY_LIMIT = 4 * 1024 * 1024, TOTAL_LIMIT = 8 * 1024 * 1024, ROW_LIMIT = 5000;
class Failure extends Error {
  constructor(message, status = null, until = null) { super(message); this.status = status; this.until = until; }
}
const hash = value => createHash('sha256').update(value).digest('hex');

function configuration() {
  const key = String(process.env.FC_API_KEY || '').trim();
  if (!/^fc_live_[a-f0-9]{32}$/.test(key)) throw new Failure(`Set a valid FC_API_KEY in your private environment. Get a key at ${ACCOUNT}`);
  let endpoint = OFFICIAL, now = Date.now(), timeout = 12000;
  // Explicit test transport supports numeric loopback only; production cannot
  // accept an arbitrary credential destination through a command-line flag.
  if (process.env.FC_TRADING_TOOLS_TEST_HTTP === '1') {
    endpoint = process.env.FC_TRADING_TOOLS_TEST_URL || '';
    const url = new URL(endpoint);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || !url.port || url.pathname !== '/calendar' || url.username || url.password || url.search || url.hash) throw new Failure('Invalid local test transport.');
    if (process.env.FC_TRADING_TOOLS_TEST_NOW) now = Date.parse(process.env.FC_TRADING_TOOLS_TEST_NOW);
    timeout = Number(process.env.FC_TRADING_TOOLS_TEST_TIMEOUT_MS || 12000);
    if (!Number.isFinite(now) || !Number.isFinite(timeout) || timeout < 50 || timeout > 12000) throw new Failure('Invalid local test clock or timeout.');
  }
  const from = new Date(now).toISOString().slice(0, 10), to = new Date(Date.parse(from + 'T00:00:00Z') + 6 * 86400000).toISOString().slice(0, 10);
  const params = { from, to, impact: 'high', status: 'confirmed,estimated,rescheduled', limit: '500' };
  const partition = hash('financecalendar-trading-tools-v1\0' + endpoint + '\0' + key);
  const path = join(process.env.FC_CACHE_DIR || join(homedir(), '.cache/financecalendar-trading-tools'), `watchlist-${partition}.json`);
  return { key, endpoint, now, timeout, params, partition, path };
}

async function readCache(path, partition) {
  try {
    const stat = await lstat(path);
    if (stat.isSymbolicLink() || stat.size > TOTAL_LIMIT + 65536) return null;
    const value = JSON.parse(await readFile(path, 'utf8'));
    return value && value.version === 1 && value.partition === partition ? value : null;
  } catch { return null; }
}
async function saveCache(path, value) {
  await mkdir(dirname(path), { recursive: true, mode: 0o700 });
  const temporary = join(dirname(path), `.watchlist-${randomUUID()}`);
  let handle;
  try {
    handle = await open(temporary, 'wx', 0o600);
    await handle.writeFile(JSON.stringify(value)); await handle.sync(); await handle.close(); handle = null;
    await rename(temporary, path);
  } finally {
    if (handle) await handle.close();
    await unlink(temporary).catch(() => {});
  }
}
function retryUntil(header, now) {
  if (header && /^\d+$/.test(header.trim())) {
    const seconds = Number(header.trim());
    if (!Number.isSafeInteger(seconds) || seconds > 100 * 365 * 86400) return null;
    return now + Math.max(CACHE_MS, seconds * 1000);
  }
  const parsed = header ? Date.parse(header) : NaN;
  return Number.isFinite(parsed) ? Math.max(now + CACHE_MS, parsed) : now + CACHE_MS;
}
function statusFailure(status, header, now) {
  if ([401, 402, 403].includes(status)) return new Failure(`HTTP ${status}: access was not accepted. Fix your key/account at ${ACCOUNT} then clear this key's cache. Requests are stopped.`, status);
  if (status === 429) {
    const until = retryUntil(header, now), wait = until === null ? 'manual review of Retry-After' : `at least ${Math.max(0, Math.ceil((until - now) / 1000))} seconds`;
    return new Failure(`HTTP 429: wait ${wait}. No automatic retry. Check allowance at ${ACCOUNT}`, status, until);
  }
  return new Failure(`HTTP ${status}: calendar request failed; no automatic retry.`, status, now + CACHE_MS);
}

async function fetchCalendar({ endpoint, key, params, now, timeout }) {
  const events = [], seen = new Set();
  // Logical fixture time plus monotonic elapsed time includes earlier pages.
  // Numeric Retry-After starts at response receipt rather than run start.
  const started = performance.now();
  let total = null, attribution = null, offset = 0, byteCount = 0;
  for (let pageIndex = 0; pageIndex < 10; pageIndex++) {
    const url = new URL(endpoint); url.search = new URLSearchParams({ ...params, offset: String(offset) }).toString();
    let raw;
    try {
      const response = await fetch(url, { headers: { 'X-API-Key': key, Accept: 'application/json', 'User-Agent': 'financecalendar-trading-tools/1.0' }, redirect: 'manual', signal: AbortSignal.timeout(timeout) });
      if (response.status !== 200) {
        const receivedAt = now + Math.ceil(performance.now() - started);
        await response.body?.cancel();
        throw statusFailure(response.status, response.headers.get('Retry-After'), receivedAt);
      }
      let size = 0; const chunks = [];
      for await (const chunk of response.body || []) {
        size += chunk.byteLength;
        if (size > BODY_LIMIT) throw new Failure('Calendar response exceeded the 4 MiB bound.', null, now + CACHE_MS);
        chunks.push(chunk);
      }
      raw = Buffer.concat(chunks); byteCount += raw.byteLength;
      if (byteCount > TOTAL_LIMIT) throw new Failure('Combined calendar pages exceeded the 8 MiB bound.', null, now + CACHE_MS);
    } catch (error) {
      if (error instanceof Failure) throw error;
      throw new Failure('Calendar connection failed or timed out; no automatic retry.', null, now + CACHE_MS);
    }
    let page;
    try { page = JSON.parse(raw.toString('utf8')); } catch { throw new Failure('Calendar response was not valid JSON.', null, now + CACHE_MS); }
    if (!page || !Array.isArray(page.events)) throw new Failure('Calendar response had no valid events list.', null, now + CACHE_MS);
    const count = page.count, pageTotal = page.total;
    if (!Number.isSafeInteger(count) || !Number.isSafeInteger(pageTotal) || count !== page.events.length || count < 0 || count > 500 || pageTotal < 0 || pageTotal > ROW_LIMIT || offset + count > pageTotal || (count === 0 && offset < pageTotal) || (total !== null && total !== pageTotal)) throw new Failure('Calendar pagination changed or exceeded its reviewed bound; no partial watchlist returned.', null, now + CACHE_MS);
    if (total === null) { total = pageTotal; attribution = page.attribution ?? null; }
    for (const row of page.events) {
      const id = row?.id;
      if (!row || Array.isArray(row) || !['string', 'number'].includes(typeof id) || (typeof id === 'number' && !Number.isSafeInteger(id)) || String(id) === '' || seen.has(String(id))) throw new Failure('Calendar event identities changed or were missing; no partial watchlist returned.', null, now + CACHE_MS);
      seen.add(String(id)); events.push(row);
    }
    offset += count;
    if (offset >= total) return { from: params.from, to: params.to, count: events.length, total, events, attribution };
  }
  throw new Failure('Calendar exceeded ten pages; no partial watchlist returned.', null, now + CACHE_MS);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.some(arg => arg !== '--clear-cache') || args.length > 1) throw new Failure('Usage: node node/calendar-watchlist.mjs [--clear-cache]');
  const c = configuration();
  if (args.includes('--clear-cache')) {
    await unlink(c.path).catch(error => { if (error.code !== 'ENOENT') throw error; });
    console.error('Private cache cleared; no API request sent.'); return;
  }
  let cache = await readCache(c.path, c.partition) || { version: 1, partition: c.partition };
  if (cache.block && (cache.block.until_ms === null || c.now < cache.block.until_ms)) throw new Failure(cache.block.message || 'Requests are paused; review your account and private cache.');
  const query = new URLSearchParams(c.params).toString();
  const hit = cache.query === query && Number.isFinite(cache.expires_at_ms) && c.now < cache.expires_at_ms && cache.payload && typeof cache.payload === 'object';
  if (!hit) {
    try {
      const payload = await fetchCalendar(c);
      cache = { version: 1, partition: c.partition, query, stored_at_ms: c.now, expires_at_ms: c.now + CACHE_MS, payload };
    } catch (error) {
      if (!(error instanceof Failure)) throw error;
      cache.block = { until_ms: error.until, message: error.message, status: error.status };
      await saveCache(c.path, cache); throw error;
    }
    await saveCache(c.path, cache);
  }
  console.log(JSON.stringify({ source: 'Finance Calendar', fetched_at: new Date(cache.stored_at_ms).toISOString(), cache: { state: hit ? 'cached' : 'fresh', max_age_seconds: CACHE_MS / 1000 }, ...cache.payload }));
}
main().catch(error => {
  console.error(error instanceof Failure ? error.message : 'Watchlist could not be read or saved. Check the private cache directory and configuration.');
  process.exitCode = 1;
});
