"""Offline fixtures: an httpx.MockTransport that answers from recorded API responses."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from financecalendar import Client

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def fixture_for(request: httpx.Request) -> dict:
    # Match on the endpoint only, whatever base URL the client was built with.
    segs = request.url.path.strip("/").split("/")
    path = f"/series/{segs[-1]}" if len(segs) >= 2 and segs[-2] == "series" else f"/{segs[-1]}"
    q = dict(request.url.params)
    if path == "/next":
        if q.get("country") == "no":
            return load("error_next_404")
        if q.get("country") == "uk":
            return load("next_cpi_uk")
        return load("next_fomc_tz" if q.get("tz") else "next_fomc")
    if path == "/calendar":
        if q.get("tz") == "Mars/Olympus":
            return load("error_bad_tz")
        if q.get("series") == "nope":
            return load("error_unknown_series")
        if q.get("format") == "csv":
            return {"status": 200, "headers": {"Content-Type": "text/csv; charset=utf-8"}, "text": (FIXTURES / "calendar_csv.txt").read_text()}
        if q.get("include") == "holidays":
            return load("calendar_holidays")
        if q.get("impact") == "high":
            return load("calendar_high")
        return load("calendar_tz" if q.get("tz") else "calendar")
    if path == "/today":
        return load("today")
    if path == "/week":
        return load("week_next" if q.get("which") == "next" else "week")
    if path == "/series":
        return load("series")
    if path in ("/series/fomc", "/series/fed"):
        return load("series_detail_fomc")
    if path.startswith("/series/"):
        return load("error_series_404")
    if path == "/history":
        return load("history_us_cpi")
    if path == "/holidays":
        return load("holidays_lse_2027" if q.get("exchange") == "lse" else "holidays_nyse")
    if path == "/market-status":
        return load("market_status_lse" if q.get("exchange") == "lse" else "market_status_nyse")
    if path == "/changes":
        return load("changes")
    if path == "/countries":
        return load("countries")
    if path == "/status":
        return load("status")
    if path == "/openapi":
        return load("openapi")
    if path == "/rate-limited":
        return load("error_429")
    return {"status": 404, "headers": {}, "body": {"error": f"No route for {path}"}}


def to_response(rec: dict) -> httpx.Response:
    headers = {"Content-Type": "application/json", **rec.get("headers", {})}
    if "text" in rec:
        return httpx.Response(rec["status"], headers=headers, text=rec["text"])
    return httpx.Response(rec["status"], headers=headers, json=rec["body"])


class Recorder:
    """Mock transport that records every request."""

    def __init__(self, handler=None):
        self.requests: list[httpx.Request] = []
        self._handler = handler or (lambda r: to_response(fixture_for(r)))
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
def client(recorder: Recorder, monkeypatch: pytest.MonkeyPatch) -> Client:
    monkeypatch.delenv("FC_API_KEY", raising=False)
    monkeypatch.delenv("FC_API_BASE", raising=False)
    with Client(transport=recorder.transport) as c:
        yield c
