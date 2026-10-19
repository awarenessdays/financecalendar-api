// Finance Calendar API from Node 18+ or the browser (CORS is open).
const BASE = "https://www.financecalendar.com/wp-json/fc/v1";

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) if (v != null) url.searchParams.set(k, v);
  const r = await fetch(url); // add { headers: { "X-API-Key": "fc_live_..." } } for a higher limit
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

const { next } = await get("/next", { series: "us-cpi" });
console.log("Next US CPI:", next.date, next.time_utc, "consensus", next.consensus);

const { events } = await get("/week", { impact: "high", tz: "America/New_York" });
for (const e of events) console.log(e.date, e.time_local ?? "all day", e.country, e.name);

const status = await get("/market-status", { exchange: "nyse" });
console.log(status.label);
