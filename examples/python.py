"""Paid-plan Finance Calendar API examples with a private FC_API_KEY. For finite evaluation access use calendar JSON with limit=10."""
import json
import os
import urllib.parse
import urllib.request

BASE = "https://www.financecalendar.com/wp-json/fc/v1"
API_KEY = os.environ.get("FC_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("Set FC_API_KEY to your account API key. These wider-route examples need a paid plan. For 48-hour, 25-request free JSON calendar access with verified email and a key, visit https://www.financecalendar.com/account/?trial=1.")


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


opener = urllib.request.build_opener(NoRedirects())


def get(path, **params):
    url = f"{BASE}{path}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    req = urllib.request.Request(url, headers={"User-Agent": "my-app/1.0", "X-API-Key": API_KEY, "Accept": "application/json"})
    with opener.open(req, timeout=20) as response:
        return json.load(response)


nxt = get("/next", series="fomc")["next"]
print("Next Fed decision:", nxt["date"], nxt.get("time_et") or "time unknown", "ET", "| consensus", nxt.get("consensus"))

for event in get("/calendar", impact="high", tz="Europe/London", limit=20)["events"]:
    clock = event.get("time_local") or ("all day" if event.get("all_day") else "time unknown")
    print(event["date"], clock, event["country"], event["name"], "| prior", event.get("prior"), "| consensus", event.get("consensus"))

for holiday in get("/holidays", exchange="lse", year=2027)["holidays"]:
    print(holiday["date"], holiday["name"], holiday["status"])
