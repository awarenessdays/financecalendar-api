// Pure presentation helpers shared by the browser and the offline tests.
export function validDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const stamp = new Date(`${value}T12:00:00Z`);
  return Number.isFinite(stamp.getTime()) && stamp.toISOString().slice(0, 10) === value ? value : null;
}

export function dateInZone(stamp, timeZone) {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(stamp);
  const part = type => parts.find(value => value.type === type)?.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

export function addDays(date, count) {
  const stamp = new Date(`${date}T12:00:00Z`);
  stamp.setUTCDate(stamp.getUTCDate() + count);
  return stamp.toISOString().slice(0, 10);
}

export function eventTiming(event, timeZone = 'Europe/London') {
  const precision = event.time_precision || 'unknown';
  const raw = event.release_at_utc;
  const precise = ['minute', 'second'].includes(precision) && typeof raw === 'string' && validDate(raw.slice(0, 10)) && /^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(raw);
  const stamp = precise ? new Date(raw) : null;
  if (stamp && Number.isFinite(stamp.getTime())) {
    return {
      date: dateInZone(stamp, timeZone),
      time: new Intl.DateTimeFormat('en-GB', { timeZone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(stamp),
      precision, exact: true,
    };
  }
  return {
    date: validDate(event.date),
    time: precision === 'range' ? 'Date window' : event.all_day === true && precision === 'day' ? 'All day' : 'Time unknown',
    precision, exact: false,
  };
}

export function shortDate(date, options = {}) {
  if (!validDate(date)) return 'Date not confirmed';
  // Date-only records are calendar dates, not midnight UTC instants to convert.
  return new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC', day: 'numeric', month: 'short', ...options }).format(new Date(`${date}T12:00:00Z`));
}

export function formatValue(value, unit = '') {
  if (value === null || value === undefined || value === '') return '—';
  // Significant digits preserve small nonzero observations. Numeric strings
  // retain the publisher's exact text instead of being coerced to a float.
  const magnitude = typeof value === 'number' ? Math.abs(value) : null;
  const label = typeof value === 'number' ? new Intl.NumberFormat('en-GB', {
    maximumSignificantDigits: 17,
    notation: magnitude !== 0 && (magnitude < 0.0001 || magnitude >= 1e12) ? 'scientific' : 'standard',
  }).format(value) : String(value);
  return unit ? `${label} ${unit}` : label;
}

export function safeLink(value) {
  if (typeof value !== 'string') return null;
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; } catch { return null; }
}

export function statusBadge(status) {
  const badges = {
    cancelled: { label: 'Cancelled', tone: 'cancelled' },
    rescheduled: { label: 'Rescheduled', tone: 'rescheduled' },
    released: { label: 'Released', tone: 'released' },
    estimated: { label: 'Estimated date', tone: 'estimated' },
  };
  return Object.hasOwn(badges, status) ? badges[status] : null;
}
