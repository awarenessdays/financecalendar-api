"""Finance Calendar API from Python with only the standard library (or pip install financecalendar)."""
import json
import urllib.parse
import urllib.request

BASE = "https://www.financecalendar.com/wp-json/fc/v1"


def get(path, **params):
    url = f"{BASE}{path}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    req = urllib.request.Request(url, headers={"User-Agent": "my-app/1.0"})  # add "X-API-Key": "fc_live_..." for a higher limit
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


nxt = get("/next", series="fomc")["next"]
print("Next Fed decision:", nxt["date"], nxt["time_et"], "ET", "|", nxt["consensus"] or "no consensus yet")

for e in get("/calendar", impact="high", tz="Europe/London", limit=20)["events"]:
    print(e["date"], e.get("time_local") or "all day", e["country"], e["name"], "| prior", e["prior"], "| consensus", e["consensus"])

for h in get("/holidays", exchange="lse", year=2027)["holidays"]:
    print(h["date"], h["name"], h["status"])
