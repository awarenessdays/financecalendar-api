// Paid-plan Finance Calendar API examples from server-side Node 20+. Keep credentials out of browsers.
// For finite evaluation access use authenticated calendar JSON with limit=10; see README.md.
const BASE = "https://www.financecalendar.com/wp-json/fc/v1";
const API_KEY = String(process.env.FC_API_KEY || "").trim();
if (!API_KEY) throw new Error("Set FC_API_KEY to your account API key. These wider-route examples need a paid plan. For 48-hour, 25-request free JSON calendar access with verified email and a key, visit https://www.financecalendar.com/account/?trial=1.");

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) if (v != null) url.searchParams.set(k, v);
  const r = await fetch(url, { headers: { "X-API-Key": API_KEY, Accept: "application/json" }, redirect: "error" });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

async function main() {
  const { next } = await get("/next", { series: "us-cpi" });
  console.log("Next US CPI:", next.date, next.release_at_utc ?? "time unknown", "consensus", next.consensus);

  const { events } = await get("/week", { impact: "high", tz: "America/New_York" });
  for (const e of events) console.log(e.date, e.time_local ?? (e.all_day ? "all day" : "time unknown"), e.country, e.name);

  const status = await get("/market-status", { exchange: "nyse" });
  console.log(status.label);
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
