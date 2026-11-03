import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { readConfig, createFeedStore, createDashboardServer, normaliseEvent, API_ENDPOINT, CACHE_MS } from '../server.mjs';
import { eventTiming, validDate, shortDate, formatValue, statusBadge } from '../public/model.mjs';
const SECRET = `fc_live_${'a'.repeat(32)}`;
const config = (overrides = {}) => readConfig({ FC_API_KEY: SECRET, PORT: '0', ...overrides }, []);
const initialTime = Date.parse('2026-11-03T08:00:00Z');
const release = overrides => ({ id: 'test-release', name: 'Test CPI', country: 'US', date: '2026-11-03', release_at_utc: '2026-11-03T13:30:00Z', time_precision: 'minute', actual: null, prior: 0, source_url: 'https://www.bls.gov/', source_license: { attribution: 'Publisher credit', terms_url: 'https://www.bls.gov/bls/linksite.htm' }, ...overrides });
const success = (events = [release()]) => new Response(JSON.stringify({ events, total: events.length }), { status: 200, headers: { 'Content-Type': 'application/json' } });
async function listening(t, options) {
  const { server } = createDashboardServer(options); server.listen(0, '127.0.0.1'); await once(server, 'listening');
  t.after(() => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }));
  return `http://127.0.0.1:${server.address().port}`;
}
test('real mode requires a private key; demo and configuration are explicit', () => {
  assert.throws(() => readConfig({}, []), /Set FC_API_KEY/); assert.equal(readConfig({}, ['--demo']).demo, true);
  assert.throws(() => config({ FC_API_KEY: 'bad\nkey' }), /single-line/); assert.throws(() => config({ FC_DAYS: '500' }), /1 to 28/);
  assert.throws(() => config({ FC_COUNTRIES: 'US,https://example.test' }), /country codes/); assert.throws(() => config({ FC_TIMEZONE: 'Mars/Olympus' }), /IANA/);
});
test('simultaneous visitors share one in-flight request and one 30-minute cache', async () => {
  let calls = 0, releaseFetch, now = initialTime; const barrier = new Promise(resolve => { releaseFetch = resolve; });
  const store = createFeedStore({ config: config(), now: () => now, fetchImpl: async () => { calls++; await barrier; return success(); } });
  const visits = Array.from({ length: 40 }, () => store.read()); assert.equal(calls, 1); releaseFetch(); const results = await Promise.all(visits);
  assert.ok(results.every(result => result.state === 'fresh' && result.events.length === 1));
  results[0].events[0].name = 'Visitor mutation'; assert.equal((await store.read()).events[0].name, 'Test CPI');
  now += CACHE_MS - 1; await store.read(); assert.equal(calls, 1); now++; await Promise.all(Array.from({ length: 20 }, () => store.read())); assert.equal(calls, 2);
});
test('upstream origin, route and date window are fixed by server configuration', async () => {
  let observed; const store = createFeedStore({ config: config({ FC_API_BASE: 'https://attacker.invalid', FC_COUNTRIES: 'US,GB', FC_DAYS: '7', FC_TIMEZONE: 'America/New_York' }), now: () => initialTime, fetchImpl: async (url, options) => { observed = { url, options }; return success(); } });
  await store.read(); assert.equal(observed.url.origin + observed.url.pathname, API_ENDPOINT); assert.equal(observed.url.searchParams.get('country'), 'US,GB');
  assert.equal(observed.url.searchParams.get('from'), '2026-11-03'); assert.equal(observed.url.searchParams.get('to'), '2026-11-09'); assert.equal(observed.url.searchParams.get('limit'), '500');
  assert.equal(observed.options.redirect, 'error'); assert.equal(observed.options.headers['X-API-Key'], SECRET); assert.equal(observed.options.signal instanceof AbortSignal, true);
});
test('failed refresh retains records and original fetch timestamp with an explicit stale state', async () => {
  let calls = 0, now = initialTime; const store = createFeedStore({ config: config(), now: () => now, fetchImpl: async () => { calls++; return calls === 1 ? success() : new Response('PRIVATE UPSTREAM ERROR', { status: 503 }); } });
  const first = await store.read(); now += CACHE_MS; const stale = await store.read();
  assert.equal(stale.state, 'stale'); assert.equal(stale.events[0].name, 'Test CPI'); assert.equal(stale.fetched_at, first.fetched_at); assert.equal(stale.error.code, 'upstream_unavailable'); assert.equal(JSON.stringify(stale).includes('PRIVATE'), false);
  await Promise.all(Array.from({ length: 100 }, () => store.read())); assert.equal(calls, 2);
});
test('429 honours Retry-After and repeated visitors cannot create a retry loop', async () => {
  let calls = 0, now = initialTime; const store = createFeedStore({ config: config(), now: () => now, fetchImpl: async () => { calls++; return new Response(`key=${SECRET}`, { status: 429, headers: { 'Retry-After': '7200' } }); } });
  const blocked = await store.read(); assert.equal(blocked.state, 'unavailable'); assert.equal(blocked.error.code, 'rate_limited'); assert.equal(Date.parse(blocked.next_refresh_at), initialTime + 7200000); assert.equal(JSON.stringify(blocked).includes(SECRET), false);
  now += CACHE_MS; await store.read(); now += CACHE_MS; await store.read(); assert.equal(calls, 1); now = initialTime + 7200000; await Promise.all([store.read(), store.read()]); assert.equal(calls, 2);
});
test('HTTP-date Retry-After works and short delays cannot bypass the cache interval', async () => {
  const now = initialTime; const store = createFeedStore({ config: config(), now: () => now, fetchImpl: async () => new Response('', { status: 429, headers: { 'Retry-After': new Date(now + 3600000).toUTCString() } }) });
  assert.equal(Date.parse((await store.read()).next_refresh_at), now + 3600000);
  const short = createFeedStore({ config: config(), now: () => now, fetchImpl: async () => new Response('', { status: 429, headers: { 'Retry-After': '1' } }) }); assert.equal(Date.parse((await short.read()).next_refresh_at), now + CACHE_MS);
});
test('malformed successful responses and transport exceptions fail safely', async () => {
  for (const fetchImpl of [async () => new Response('{broken secret body'), async () => { throw new Error(`private network details ${SECRET}`); }, async () => new Response(JSON.stringify({ private: SECRET }))]) {
    const result = await createFeedStore({ config: config(), now: () => initialTime, fetchImpl }).read(); assert.equal(result.state, 'unavailable'); assert.equal(result.events.length, 0); assert.equal(JSON.stringify(result).includes(SECRET), false); assert.equal(JSON.stringify(result).includes('private network'), false);
  }
});
test('bounded first page exposes incompleteness without automatic pagination', async () => {
  let calls = 0; const store = createFeedStore({ config: config(), now: () => initialTime, fetchImpl: async () => { calls++; return success(Array.from({ length: 501 }, (_, index) => release({ id: `event-${index}` }))); } });
  const result = await store.read(); assert.equal(result.events.length, 500); assert.equal(result.total, 501); assert.equal(result.truncated, true); assert.equal(calls, 1);
});
test('time precision never manufactures midnight; exact instants convert while date-only records do not', () => {
  assert.deepEqual(eventTiming(release({ time_precision: 'unknown', release_at_utc: '2026-11-03T00:00:00Z' }), 'America/New_York'), { date: '2026-11-03', time: 'Time unknown', precision: 'unknown', exact: false });
  assert.deepEqual(eventTiming(release({ release_at_utc: '2026-11-03T00:30:00Z' }), 'America/New_York'), { date: '2026-11-02', time: '19:30', precision: 'minute', exact: true });
  assert.equal(eventTiming(release({ time_precision: 'range' })).time, 'Date window'); assert.equal(eventTiming(release({ time_precision: 'day', all_day: true })).time, 'All day'); assert.equal(eventTiming(release({ release_at_utc: '2026-02-30T12:00:00Z' })).exact, false);
  assert.equal(validDate('2026-02-30'), null); assert.equal(validDate('2028-02-29'), '2028-02-29'); assert.equal(shortDate('2026-11-03'), '3 Nov'); assert.equal(formatValue(null, '%'), '—'); assert.equal(formatValue(0, '%'), '0 %');
});
test('normalisation preserves zero, nulls, freshness and credits without arbitrary fields or unsafe links', () => {
  const event = normaliseEvent(release({ actual: 0, prior: null, data_stale: true, source_url: 'javascript:alert(1)', private: SECRET, source_rights: { notice: 'Keep publisher evidence' } }), 0);
  assert.equal(event.actual, 0); assert.equal(event.prior, null); assert.equal(event.data_stale, true); assert.equal(event.source_url, null); assert.equal('private' in event, false); assert.ok(event.credits.some(item => item.text === 'Publisher credit')); assert.ok(event.credits.some(item => item.text === 'Keep publisher evidence'));
});
test('demo has explicit invented-data identity and never calls a network transport', async () => {
  const store = createFeedStore({ config: readConfig({ PORT: '0' }, ['--demo']), now: () => initialTime, fetchImpl: () => { throw new Error('Network must not run'); } });
  const result = await store.read(); assert.equal(result.demo, true); assert.equal(result.state, 'demo'); assert.ok(result.events.length > 0); assert.ok(result.events.every(event => event.credits.some(credit => credit.text.includes('invented'))));
});
test('HTTP never exposes secrets or arbitrary files and URL parameters cannot create an open proxy', async t => {
  let calls = 0; const base = await listening(t, { config: config(), now: () => initialTime, fetchImpl: async () => { calls++; return success([release({ name: `Echoed ${SECRET}` })]); } });
  const response = await fetch(base + '/api/events'), body = await response.text(); assert.equal(response.status, 200); assert.equal(body.includes(SECRET), false); assert.equal(body.includes('[redacted]'), true); assert.equal(response.headers.get('x-api-key'), null); assert.match(response.headers.get('content-security-policy'), /connect-src 'self'/);
  assert.equal((await fetch(base + '/api/events?url=https://attacker.invalid')).status, 400); assert.equal((await fetch(base + '/server.mjs')).status, 404); assert.equal((await fetch(base + '/api/events', { method: 'POST' })).status, 405); assert.equal((await fetch(base + '/api/events', { method: 'HEAD' })).status, 200); assert.equal(calls, 1);
  assert.equal((await fetch(base + '/favicon.ico')).status, 204);
  const html = await (await fetch(base)).text(); assert.match(html, /id="demo-notice"/); assert.equal(html.includes(SECRET), false);
});
test('HTTP authentication failure returns safe actionable state without upstream body', async t => {
  const base = await listening(t, { config: config(), now: () => initialTime, fetchImpl: async () => new Response(`AUTH PRIVATE ${SECRET}`, { status: 401 }) });
  const response = await fetch(base + '/api/events'), body = await response.text(); assert.equal(response.status, 503); assert.equal(body.includes('AUTH PRIVATE'), false); assert.equal(body.includes(SECRET), false); assert.match(body, /Check FC_API_KEY/);
});

test('complete licence and source-rights metadata survives normalisation without silent notice or entry truncation', () => {
  const longNotice = 'Preserve this full publisher notice. '.repeat(180);
  const event = normaliseEvent(release({
    source_license: { attribution: 'Full attribution', attribution_url: 'https://publisher.example/attribution', notice: longNotice },
    source_rights: { url: 'https://publisher.example/rights', source_url: 'https://publisher.example/evidence', policy: 'Use only within the recorded reuse policy.', vintage_notice: 'This is the current recorded vintage, not a first-print archive.', notices: Array.from({ length: 24 }, (_, i) => `Required notice ${i + 1}`) },
  }), 0);
  for (const url of ['https://publisher.example/attribution', 'https://publisher.example/rights', 'https://publisher.example/evidence']) assert.ok(event.credits.some(credit => credit.url === url));
  assert.ok(event.credits.some(credit => credit.text === longNotice));
  assert.ok(event.credits.some(credit => credit.text === 'Use only within the recorded reuse policy.'));
  assert.ok(event.credits.some(credit => credit.text.includes('not a first-print archive')));
  assert.equal(event.credits.filter(credit => credit.text.startsWith('Required notice ')).length, 24);
  assert.ok(event.credits.every(credit => typeof credit.label === 'string' && credit.label.length > 0));
});
test('numeric presentation never rounds a meaningful nonzero observation to zero', () => {
  for (const value of [0.000004, -0.000004, 0.0000000000000000000013, -0.0000000000000000000013, Number.MIN_VALUE, -Number.MIN_VALUE, Number.MAX_VALUE]) {
    const formatted = formatValue(value);
    assert.notEqual(formatted, '0'); assert.notEqual(formatted, '-0');
    assert.notEqual(Number(formatted.replaceAll(',', '')), 0);
  }
  const exact = '0.000004000000000000000000001';
  assert.equal(formatValue(exact), exact); assert.equal(normaliseEvent(release({ actual: exact }), 0).actual, exact);
  assert.equal(formatValue(null), '—'); assert.equal(formatValue(0), '0');
});
test('cancelled and rescheduled records are explicit; released does not claim a captured result', async () => {
  assert.equal(statusBadge('cancelled').label, 'Cancelled'); assert.equal(statusBadge('rescheduled').label, 'Rescheduled');
  assert.equal(statusBadge('released').label, 'Released'); assert.equal(statusBadge('confirmed'), null); assert.equal(statusBadge('__proto__'), null);
  const result = await createFeedStore({ config: readConfig({}, ['--demo']), now: () => initialTime }).read();
  const labels = result.events.map(event => statusBadge(event.status)?.label).filter(Boolean);
  for (const expected of ['Cancelled', 'Rescheduled', 'Released']) assert.ok(labels.includes(expected));
  assert.equal(formatValue(normaliseEvent(release({ status: 'released', actual: null }), 0).actual), '—');
});
test('publisher-date filtering can legitimately retain an adjacent displayed local date without extra calls', async () => {
  let calls = 0;
  const store = createFeedStore({ config: config({ FC_TIMEZONE: 'America/New_York' }), now: () => initialTime, fetchImpl: async url => {
    calls++; assert.equal(url.searchParams.get('from'), '2026-11-03');
    return success([release({ date: '2026-11-03', release_at_utc: '2026-11-03T00:30:00Z' })]);
  } });
  const result = await store.read();
  assert.equal(result.window.from, '2026-11-03'); assert.equal(result.events[0].date, '2026-11-03');
  assert.equal(eventTiming(result.events[0], result.config.timezone).date, '2026-11-02');
  await store.read(); assert.equal(calls, 1);
});
