import { eventTiming, formatValue, freeView, safeLink, shortDate, statusBadge } from './model.mjs';

const $ = selector => document.querySelector(selector);
const marketNames = { US: 'United States', GB: 'United Kingdom', EU: 'Euro area', CA: 'Canada', AU: 'Australia', JP: 'Japan', unknown: 'Not classified' };
const state = { feed: null, countries: new Set(), impacts: new Set(['high', 'medium', 'low', 'unknown']), date: 'all', search: '', loaded: false, plan: 'paid', source: null };
const make = (tag, text, className) => { const node = document.createElement(tag); if (text !== undefined && text !== null) node.textContent = String(text); if (className) node.className = className; return node; };
const countLabel = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

function stamp(value) {
  if (!value || !Number.isFinite(Date.parse(value))) return 'Not recorded';
  return new Intl.DateTimeFormat('en-GB', { timeZone: state.feed?.config.timezone || 'Europe/London', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZoneName: 'short' }).format(new Date(value));
}
function filteredEvents(includeDate = true) {
  const feed = state.feed;
  if (!feed) return [];
  return feed.events.filter(event => state.countries.has(event.country || 'unknown') && state.impacts.has(event.impact || 'unknown') &&
    (!state.search || [event.name, event.country, event.source_name, event.series_code, event.period].filter(Boolean).join(' ').toLowerCase().includes(state.search)) &&
    (!includeDate || state.date === 'all' || eventTiming(event, feed.config.timezone).date === state.date));
}
function buildCountries() {
  const countries = [...new Set([...state.feed.config.countries, ...state.feed.events.map(event => event.country || 'unknown')])];
  if (!state.loaded) state.countries = new Set(countries);
  const fragment = document.createDocumentFragment();
  for (const country of countries) {
    const label = make('label'); const input = make('input'); input.type = 'checkbox'; input.name = 'country'; input.value = country; input.checked = state.countries.has(country);
    const count = state.feed.events.filter(event => (event.country || 'unknown') === country).length;
    label.append(input, make('span', marketNames[country] || country), make('span', count, 'country-count')); fragment.append(label);
  }
  $('#country-filters').replaceChildren(fragment);
}
function renderDates() {
  const counts = new Map();
  for (const event of filteredEvents(false)) { const date = eventTiming(event, state.feed.config.timezone).date; if (date) counts.set(date, (counts.get(date) || 0) + 1); }
  const fragment = document.createDocumentFragment();
  for (const [date, count] of [['all', filteredEvents(false).length], ...[...counts].sort(([a], [b]) => a.localeCompare(b))]) {
    const button = make('button'); button.type = 'button'; button.dataset.date = date; button.setAttribute('aria-pressed', String(state.date === date));
    button.append(make('span', date === 'all' ? 'All dates' : shortDate(date, { weekday: 'short', month: undefined })));
    button.append(make('small', countLabel(count, 'release'))); fragment.append(button);
  }
  $('#date-filters').replaceChildren(fragment);
}
function eventValue(value, unit, className, onPaidPlans = false) {
  const cell = make('td', undefined, `${className} value${value === null ? ' missing' : ''}`);
  // A Free Developer response marks releases whose figures a paid plan returns.
  if (value === null && onPaidPlans) { cell.append(make('span', 'Paid plans', 'paid-tag')); cell.setAttribute('aria-label', 'Included with paid plans'); return cell; }
  cell.append(make('span', formatValue(value)));
  if (value !== null && unit) cell.append(make('span', unit, 'value-unit'));
  if (value === null) cell.setAttribute('aria-label', 'Not recorded');
  return cell;
}
function renderRows() {
  const feed = state.feed, fragment = document.createDocumentFragment();
  const events = filteredEvents().sort((a, b) => {
    const at = eventTiming(a, feed.config.timezone), bt = eventTiming(b, feed.config.timezone);
    return `${at.date || '9999'} ${at.exact ? at.time : '99:99'}`.localeCompare(`${bt.date || '9999'} ${bt.exact ? bt.time : '99:99'}`) || a.name.localeCompare(b.name);
  });
  $('#result-count').textContent = `${countLabel(events.length, 'release')} shown`;
  let previousDate;
  for (const event of events) {
    const timing = eventTiming(event, feed.config.timezone);
    if (timing.date !== previousDate) {
      const row = make('tr', undefined, 'day-row'), heading = make('th'); heading.scope = 'rowgroup'; heading.colSpan = 6;
      heading.append(make('strong', shortDate(timing.date, { weekday: 'long' })));
      row.append(heading); fragment.append(row); previousDate = timing.date;
    }
    const row = make('tr');
    if (['cancelled', 'rescheduled'].includes(event.status)) row.className = `event-${event.status}`;
    const time = make('td', timing.time, `event-time${timing.exact ? '' : ' uncertain'}`);
    const country = make('td', undefined, 'market-column'); country.append(make('span', event.country || '—', 'country-chip'));
    const name = make('td'), button = make('button', event.name, 'event-name'); button.type = 'button'; button.dataset.eventIndex = String(feed.events.indexOf(event));
    const meta = make('div', undefined, 'event-meta');
    meta.append(make('span', event.country || '—', 'country-chip mobile-country'), make('span', event.impact ? `${event.impact[0].toUpperCase()}${event.impact.slice(1)} impact` : 'Impact unknown', `impact-tag ${event.impact || 'unknown'}`));
    const badge = statusBadge(event.status);
    if (badge) meta.append(make('span', badge.label, `status-tag ${badge.tone}`));
    if (event.period) meta.append(make('span', event.period));
    if (event.data_stale === true) meta.append(make('span', 'Source review', 'freshness-flag'));
    name.append(button, meta); row.append(time, country, name);
    // One Free marker covers the forecast, consensus and previous figure together, so one tag spans both columns.
    if (event.figures_available && event.prior === null && !event.forecast) { const held = eventValue(null, event.unit, 'prior-column figures-held', true); held.colSpan = 2; row.append(held); }
    else {
      const forecast = eventValue(event.forecast?.value ?? null, event.forecast?.unit || event.unit, 'forecast-column');
      // Several measures can share one unit (for example headline and core CPI).
      // Keep the chosen measure visible so the number cannot imply a different headline.
      if (event.forecast?.measure) forecast.append(make('span', event.forecast.measure, 'forecast-measure'));
      row.append(eventValue(event.prior, event.unit, 'prior-column'), forecast);
    }
    row.append(eventValue(event.actual, event.unit, 'value-column', event.result_available)); fragment.append(row);
  }
  if (!events.length) {
    const row = make('tr'), cell = make('td', undefined, 'table-message'); cell.colSpan = 6;
    cell.append(make('p', feed.state === 'unavailable' ? 'No calendar data is available yet. Check the connection message above.' : 'No releases match this view.'));
    if (feed.events.length) { const clear = make('button', 'Reset filters'); clear.type = 'button'; clear.dataset.reset = 'true'; cell.append(clear); }
    row.append(cell); fragment.append(row);
  }
  $('#event-rows').replaceChildren(fragment);
}
function render() {
  if (!state.feed) return;
  renderDates(); renderRows();
}
function applyFeed(feed) {
  state.source = feed;
  if (feed.demo && state.plan === 'free') feed = freeView(feed);
  state.feed = feed;
  $('#plan-switch').hidden = !feed.demo;
  document.querySelectorAll('#plan-switch button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.plan === state.plan)));
  $('#paid-more').hidden = !(feed.more_on_paid_plans > 0);
  $('#paid-more-count').textContent = feed.more_on_paid_plans > 0 ? `${countLabel(feed.more_on_paid_plans, 'more release')} in this window on paid plans.` : '';
  $('#demo-notice').hidden = !feed.demo;
  $('#timezone-label').textContent = feed.config.timezone;
  $('#window-label').textContent = feed.window ? `Publisher dates: ${shortDate(feed.window.from)} – ${shortDate(feed.window.to, { year: 'numeric' })}. Times: ${feed.config.timezone}.` : `${feed.config.days}-day publisher-date window. Times: ${feed.config.timezone}.`;
  const labels = { demo: 'Demo preview', fresh: 'Cached calendar', stale: 'Stale cached view', unavailable: 'Data unavailable' };
  $('#state-label').textContent = labels[feed.state] || 'Calendar'; $('#state-label').dataset.state = feed.state;
  $('#freshness').textContent = feed.demo ? 'Illustrative dates and values' : feed.fetched_at ? `Fetched ${stamp(feed.fetched_at)}` : 'No successful fetch recorded';
  $('#feed-error').hidden = !feed.error; $('#feed-error').textContent = feed.error?.message || '';
  $('#next-refresh').textContent = `${feed.demo ? 'Preview generated' : 'Last fetched'}: ${stamp(feed.fetched_at)}. Next shared fetch is eligible after ${stamp(feed.next_refresh_at)}; checking this view does not bypass the cache.`;
  $('#truncation').hidden = !feed.truncated;
  $('#truncation').textContent = `This view contains ${feed.events.length} of ${feed.total} matching records. Narrow FC_COUNTRIES or FC_DAYS on the server for a complete view; this starter does not fetch extra pages automatically.`;
  buildCountries(); state.loaded = true; render();
}
async function load() {
  $('#refresh').disabled = true;
  try {
    const response = await fetch('/api/events', { cache: 'no-store' });
    const feed = await response.json();
    if (!feed || !Array.isArray(feed.events) || !feed.config) throw new Error('Unavailable');
    applyFeed(feed);
  } catch {
    $('#state-label').textContent = state.feed ? 'Cached view retained' : 'Dashboard unavailable'; $('#state-label').dataset.state = 'unavailable';
    $('#feed-error').hidden = false; $('#feed-error').textContent = 'The dashboard could not load its calendar view. Check that the local server is running, then check for updates again.';
    if (!state.feed) { const row = make('tr'), cell = make('td', 'Calendar records are unavailable.', 'table-message'); cell.colSpan = 6; row.append(cell); $('#event-rows').replaceChildren(row); }
  } finally { $('#refresh').disabled = false; }
}
function resetFilters() {
  state.search = ''; state.date = 'all'; $('#search').value = '';
  state.countries = new Set([...state.feed.config.countries, ...state.feed.events.map(event => event.country || 'unknown')]);
  state.impacts = new Set(['high', 'medium', 'low', 'unknown']);
  document.querySelectorAll('#impact-filters input').forEach(input => { input.checked = true; }); buildCountries(); render();
}
function detailField(list, label, value) { const row = make('div'); row.append(make('dt', label), make('dd', value ?? 'Not recorded')); list.append(row); }
function appendLink(parent, value, label, className) { const url = safeLink(value); if (!url) return; const link = make('a', label, className); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; parent.append(link); }
function showDetail(event) {
  const feed = state.feed, body = $('#detail-body'), fragment = document.createDocumentFragment();
  if (feed.demo) fragment.append(make('span', 'Demo data', 'detail-demo'));
  const title = make('h2', event.name); title.id = 'detail-title'; fragment.append(title);
  fragment.append(make('p', [marketNames[event.country] || event.country, event.period].filter(Boolean).join(' · ')));
  const timing = eventTiming(event, feed.config.timezone), list = make('dl');
  detailField(list, 'Publisher date', shortDate(event.date, { year: 'numeric' }));
  detailField(list, 'Date shown', shortDate(timing.date, { year: 'numeric' }));
  detailField(list, 'Time shown', `${timing.time}${timing.exact ? ` (${feed.config.timezone})` : ''}`);
  detailField(list, 'Time precision', event.time_precision);
  if (event.time_window_start || event.time_window_end) detailField(list, 'Recorded window', `${event.time_window_start || 'Unknown'} – ${event.time_window_end || 'Unknown'}`);
  detailField(list, 'Status', statusBadge(event.status)?.label || event.status); const paid = 'Included with paid plans';
  detailField(list, 'Actual', event.actual === null && event.result_available ? paid : formatValue(event.actual, event.unit));
  detailField(list, 'Forecast', event.forecast ? [formatValue(event.forecast.value, event.forecast.unit || event.unit), event.forecast.measure, event.forecast.source_families ? `${event.forecast.source_families} source${event.forecast.source_families === 1 ? '' : 's'}` : null, event.forecast.as_of ? `updated ${stamp(event.forecast.as_of)}` : null].filter(Boolean).join(' · ') : formatValue(null, event.unit));
  detailField(list, 'Prior', formatValue(event.prior, event.unit));
  if (event.figures_available && event.prior === null && !event.forecast) detailField(list, 'Figures', 'A forecast or previous figure is held. ' + paid + '.');
  detailField(list, 'Source checked', stamp(event.last_verified_at));
  detailField(list, 'Source freshness', event.data_stale === true ? 'Marked stale; inspect publisher' : event.data_stale === false ? 'Not marked stale' : 'Not recorded');
  fragment.append(list, make('h3', event.source_name || 'Publisher source'));
  if (event.source_url) appendLink(fragment, event.source_url, 'Open publisher source', 'publisher-link');
  else fragment.append(make('p', 'No publisher link is recorded for this event.'));
  fragment.append(make('p', 'A fresh dashboard fetch does not establish that the publisher or every observation is current. Missing values remain missing.', 'source-note'));
  if (!event.credits.length) fragment.append(make('p', 'No additional source-licence or rights notices were supplied for this record.', 'source-note'));
  for (const credit of event.credits) {
    if (credit.url) appendLink(fragment, credit.url, credit.label || 'Source evidence', 'credit-link');
    else {
      fragment.append(make('p', credit.label || 'Source credit', 'credit-label'));
      fragment.append(make('p', credit.text, 'credit-text'));
    }
  }
  appendLink(fragment, event.page_url, 'Read the Finance Calendar release page', 'credit-link');
  fragment.append(make('p', `Record: ${event.id}`, 'record-id')); body.replaceChildren(fragment); $('#event-detail').showModal();
}

$('#search').addEventListener('input', event => { state.search = event.target.value.trim().toLowerCase(); render(); });
$('#country-filters').addEventListener('change', event => { const input = event.target; if (input.name !== 'country') return; input.checked ? state.countries.add(input.value) : state.countries.delete(input.value); render(); });
$('#impact-filters').addEventListener('change', event => { const input = event.target; if (input.name !== 'impact') return; input.checked ? state.impacts.add(input.value) : state.impacts.delete(input.value); render(); });
$('#date-filters').addEventListener('click', event => { const button = event.target.closest('button[data-date]'); if (!button) return; state.date = button.dataset.date; render(); [...$('#date-filters').children].find(node => node.dataset.date === state.date)?.focus({ preventScroll: true }); });
$('#event-rows').addEventListener('click', event => { if (event.target.closest('[data-reset]')) return resetFilters(); const button = event.target.closest('button[data-event-index]'); if (button) showDetail(state.feed.events[Number(button.dataset.eventIndex)]); });
$('#clear-filters').addEventListener('click', resetFilters);
$('#plan-switch').addEventListener('click', event => { const button = event.target.closest('button[data-plan]'); if (!button || !state.source) return; state.plan = button.dataset.plan; state.loaded = false; applyFeed(state.source); });
$('#refresh').addEventListener('click', load);
$('#close-detail').addEventListener('click', () => $('#event-detail').close());
$('#event-detail').addEventListener('click', event => { if (event.target === $('#event-detail')) { const box = $('#event-detail').getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) $('#event-detail').close(); } });
load();
