import { addDays } from './public/model.mjs';

export function demoCalendar(from) {
  const rows = [
    ['US', 'US employment report', 0, '13:30', 'high', 'confirmed', null, 145, 'thousand jobs', 160, 'Bureau of Labor Statistics', 'https://www.bls.gov/'],
    ['GB', 'Bank of England rate decision', 0, '12:00', 'high', 'confirmed', null, 4.25, '%', 4.25, 'Bank of England', 'https://www.bankofengland.co.uk/'],
    ['EU', 'Euro area retail trade', 1, '10:00', 'medium', 'confirmed', null, 0.2, '% m/m', null, 'Eurostat', 'https://ec.europa.eu/eurostat/'],
    ['US', 'Initial jobless claims', 1, '13:30', 'medium', 'cancelled', null, 218, 'thousand claims', null, 'US Department of Labor', 'https://www.dol.gov/'],
    ['GB', 'UK GDP monthly estimate', 2, null, 'high', 'estimated', null, null, '% m/m', 0.1, 'Office for National Statistics', 'https://www.ons.gov.uk/'],
    ['US', 'Consumer price index', 3, '13:30', 'high', 'confirmed', null, 0.3, '% m/m', 0.2, 'Bureau of Labor Statistics', 'https://www.bls.gov/'],
    ['EU', 'Industrial production', 4, '10:00', 'medium', 'released', 0, -0.1, '% m/m', 0.1, 'Eurostat', 'https://ec.europa.eu/eurostat/'],
    ['GB', 'UK labour market release', 5, null, 'medium', 'rescheduled', null, null, '%', null, 'Office for National Statistics', 'https://www.ons.gov.uk/'],
  ];
  return { total: rows.length, events: rows.map(([country, name, offset, time, impact, status, actual, prior, unit, forecast, source_name, source_url], index) => ({
    id: `demo-${index + 1}`, country, name, series_code: `demo-series-${index + 1}`, category: 'economic-indicators',
    date: addDays(from, offset), release_at_utc: time ? `${addDays(from, offset)}T${time}:00+00:00` : null,
    time_precision: time ? 'minute' : 'unknown', all_day: false, impact, status, actual, prior, consensus: null, unit,
    forecasts: forecast === null ? [] : [{ measure: name, unit, value: String(forecast), kind: 'finance_calendar_blend', method: 'median', source_families: 2, as_of: `${addDays(from, offset - 1)}T09:00:00+00:00` }],
    period: 'Illustrative reference period', source_name, source_url, last_verified_at: null, data_stale: index === 4,
    source_license: { attribution: 'Demo record: dates and values are invented for this preview.', notice: 'Visit the publisher for real release dates, values and reuse terms.' },
  })) };
}
