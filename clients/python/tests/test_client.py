from __future__ import annotations

import sys
from datetime import date, datetime, timezone

import httpx
import pytest

from financecalendar import DEFAULT_BASE, Client, FinanceCalendarError, __version__, to_dataframe
from financecalendar.client import USER_AGENT, _clean_params

from conftest import Recorder, load


def test_version():
    assert __version__ == "0.1.0"
    assert USER_AGENT == "financecalendar-python/0.1.0"


# -- construction and env defaults -------------------------------------------

def test_defaults_without_env(client, recorder):
    client.today()
    assert str(recorder.last.url) == f"{DEFAULT_BASE}/today"
    assert recorder.last.headers["User-Agent"] == USER_AGENT
    assert "X-API-Key" not in recorder.last.headers


def test_env_base_and_key(monkeypatch, recorder):
    monkeypatch.setenv("FC_API_BASE", "https://api.financecalendar.com/v1/")
    monkeypatch.setenv("FC_API_KEY", "fc_env")
    with Client(transport=recorder.transport) as c:
        assert c.base_url == "https://api.financecalendar.com/v1"
        c.countries()
    assert str(recorder.last.url) == "https://api.financecalendar.com/v1/countries"
    assert recorder.last.headers["X-API-Key"] == "fc_env"


def test_explicit_args_win_over_env(monkeypatch, recorder):
    monkeypatch.setenv("FC_API_BASE", "https://wrong.example/v1")
    monkeypatch.setenv("FC_API_KEY", "fc_env")
    with Client(base_url="http://localhost:8080/fc", api_key="fc_explicit", transport=recorder.transport) as c:
        c.status()
    assert str(recorder.last.url) == "http://localhost:8080/fc/status"
    assert recorder.last.headers["X-API-Key"] == "fc_explicit"


def test_timeout_is_applied(recorder):
    c = Client(timeout=3.5, transport=recorder.transport)
    assert c._http.timeout.read == 3.5
    c.close()


# -- param encoding ----------------------------------------------------------

def test_clean_params():
    out = _clean_params({"from_": date(2026, 10, 19), "to": None, "country": ["US", "GB"], "impact": "", "include_holidays": True, "limit": 50, "flag": True, "off": False})
    assert out == {"from": "2026-10-19", "country": "US,GB", "include": "holidays", "limit": "50", "flag": "1"}
    assert _clean_params({"include_holidays": False}) == {}


# -- every method hits the right path with the right params ------------------

def test_calendar(client, recorder):
    data = client.calendar(from_="2026-10-19", to="2026-10-25", country="us,gb", include_holidays=True, limit=8)
    assert data["events"][0]["category"] == "market-holidays"
    assert recorder.last.url.path.endswith("/calendar")
    assert dict(recorder.last.url.params) == {"from": "2026-10-19", "to": "2026-10-25", "country": "us,gb", "include": "holidays", "limit": "8"}


def test_calendar_csv(client, recorder):
    csv = client.calendar_csv(from_="2026-10-19", to="2026-10-25", limit=5)
    assert csv.startswith("date,time_utc,time_et,all_day,name,title")
    assert "Source: financecalendar.com" in csv
    assert recorder.last.url.params["format"] == "csv"
    assert "text/csv" in recorder.last.headers["Accept"]


def test_today_week_next(client, recorder):
    t = client.today(country="us", tz="Europe/London")
    assert t["date"] == "2026-10-19" and t["market"]["open"] is True
    assert dict(recorder.last.url.params) == {"country": "us", "tz": "Europe/London"}

    w = client.week()
    assert (w["from"], w["to"]) == ("2026-10-19", "2026-10-25")
    assert dict(recorder.last.url.params) == {"which": "this"}
    w = client.week("next", impact="high")
    assert w["from"] == "2026-10-26"
    assert dict(recorder.last.url.params) == {"which": "next", "impact": "high"}

    n = client.next("fomc")
    assert n["next"]["id"] == "fomc-rate-decision-october-2026"
    assert n["next"]["consensus"] == "Hold at 3.50-3.75%"
    n = client.next("cpi", country="uk")
    assert n["series_code"] == "gb-cpi"
    assert dict(recorder.last.url.params) == {"series": "cpi", "country": "uk"}


def test_series_methods(client, recorder):
    s = client.series(country="us")
    assert s["count"] == 25 and s["series"][0]["code"] == "beige-book"
    d = client.series_detail("fed", tz="Asia/Tokyo")
    assert d["series"]["code"] == "fomc" and d["dataset"]["rows"]
    assert recorder.last.url.path.endswith("/series/fed")
    assert dict(recorder.last.url.params) == {"tz": "Asia/Tokyo"}
    h = client.history("us-cpi", from_="2025-10-19", limit=4)
    assert h["count"] == 4 and h["events"][0]["actual"] == "3.0% y/y"
    assert dict(recorder.last.url.params) == {"series": "us-cpi", "from": "2025-10-19", "limit": "4"}


def test_markets(client, recorder):
    h = client.holidays()
    assert h["exchange"] == "nyse" and h["count"] == 13
    assert dict(recorder.last.url.params) == {"exchange": "nyse"}
    h = client.holidays("lse", year=2027)
    assert h["exchange"] == "lse"
    assert dict(recorder.last.url.params) == {"exchange": "lse", "year": "2027"}
    m = client.market_status()
    assert m["open"] is True and m["label"] == "NYSE open"
    m = client.market_status("lse")
    assert m["exchange"] == "lse"


def test_changes_countries_status_openapi(client, recorder):
    c = client.changes(since=datetime(2026, 10, 18, tzinfo=timezone.utc), series="cpi", change="updated")
    assert c["count"] == 100
    assert dict(recorder.last.url.params) == {"since": "2026-10-18T00:00:00+00:00", "series": "cpi", "change": "updated"}
    assert client.countries()["countries"][0]["code"] == "US"
    assert client.status()["ok"] is True
    assert client.openapi()["openapi"] == "3.1.0"


def test_changes_cursor_is_passed_without_a_new_since_checkpoint(client, recorder):
    client.changes(cursor="opaque-page-2", limit=10)
    assert dict(recorder.last.url.params) == {"cursor": "opaque-page-2", "limit": "10"}


# -- errors ------------------------------------------------------------------

def test_error_mapping_400(client):
    with pytest.raises(FinanceCalendarError) as exc:
        client.calendar(tz="Mars/Olympus")
    assert exc.value.status == 400
    assert exc.value.message.startswith("tz must be an IANA timezone")
    assert exc.value.retry_after is None
    assert str(exc.value) == "HTTP 400: tz must be an IANA timezone such as Europe/London or Asia/Tokyo."


def test_error_mapping_404(client):
    with pytest.raises(FinanceCalendarError) as exc:
        client.series_detail("zzz")
    assert exc.value.status == 404 and "Unknown series" in exc.value.message
    with pytest.raises(FinanceCalendarError) as exc:
        client.next("cpi", country="no")
    assert exc.value.status == 404


def test_error_mapping_429_retry_after(client):
    with pytest.raises(FinanceCalendarError) as exc:
        client._request("/rate-limited")
    assert exc.value.status == 429
    assert exc.value.retry_after == 29535
    assert "Daily limit of 2,000 keyless requests" in exc.value.message
    assert str(exc.value).endswith("(retry after 29535s)")


def test_error_non_json_body():
    rec = Recorder(lambda r: httpx.Response(502, text="<html>Bad gateway</html>"))
    with Client(transport=rec.transport) as c:
        with pytest.raises(FinanceCalendarError) as exc:
            c.today()
    assert exc.value.status == 502
    assert exc.value.message in ("<html>Bad gateway</html>", "Bad Gateway")


# -- iter_calendar: paging and the 92-day splitter ---------------------------

def _paged_server(total_per_chunk: int):
    """Serve `total_per_chunk` synthetic rows per date range, honouring limit/offset."""
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        q = dict(request.url.params)
        calls.append(q)
        limit, offset = int(q["limit"]), int(q.get("offset", 0))
        rows = [{"id": f"{q['from']}#{i}", "date": q["from"]} for i in range(total_per_chunk)]
        page = rows[offset:offset + limit]
        return httpx.Response(200, json={"from": q["from"], "to": q["to"], "count": len(page), "total": total_per_chunk, "events": page})

    return calls, handler


def test_iter_calendar_pages_with_offset():
    calls, handler = _paged_server(7)
    with Client(transport=Recorder(handler).transport) as c:
        rows = list(c.iter_calendar("2026-01-01", "2026-01-31", limit=3, country="us"))
    assert len(rows) == 7
    assert [q.get("offset") for q in calls] == ["0", "3", "6"]
    assert all(q["country"] == "us" and q["from"] == "2026-01-01" and q["to"] == "2026-01-31" for q in calls)


def test_iter_calendar_splits_ranges_longer_than_92_days():
    calls, handler = _paged_server(1)
    with Client(transport=Recorder(handler).transport) as c:
        rows = list(c.iter_calendar(date(2026, 1, 1), date(2026, 12, 31)))
    spans = [(q["from"], q["to"]) for q in calls]
    assert spans == [
        ("2026-01-01", "2026-04-03"),
        ("2026-04-04", "2026-07-05"),
        ("2026-07-06", "2026-10-06"),
        ("2026-10-07", "2026-12-31"),
    ]
    for f, t in spans:
        assert (date.fromisoformat(t) - date.fromisoformat(f)).days <= 92
    assert len(rows) == 4
    assert calls[0]["limit"] == "500"


def test_iter_calendar_exact_92_days_is_one_request():
    calls, handler = _paged_server(1)
    with Client(transport=Recorder(handler).transport) as c:
        list(c.iter_calendar("2026-01-01", "2026-04-03"))
    assert len(calls) == 1
    calls.clear()
    with Client(transport=Recorder(handler).transport) as c:
        list(c.iter_calendar("2026-01-01", "2026-04-04"))
    assert [(q["from"], q["to"]) for q in calls] == [("2026-01-01", "2026-04-03"), ("2026-04-04", "2026-04-04")]


def test_iter_calendar_rejects_reversed_range(client):
    with pytest.raises(ValueError):
        list(client.iter_calendar("2026-02-01", "2026-01-01"))


def test_iter_calendar_stops_on_empty_page():
    calls, _ = _paged_server(0)

    def handler(request):
        calls.append(dict(request.url.params))
        return httpx.Response(200, json={"count": 0, "total": 0, "events": []})

    with Client(transport=Recorder(handler).transport) as c:
        assert list(c.iter_calendar("2026-01-01", "2026-01-10")) == []
    assert len(calls) == 1


# -- pandas helper -----------------------------------------------------------

def test_to_dataframe_is_lazy_and_reports_missing_pandas(monkeypatch):
    monkeypatch.setitem(sys.modules, "pandas", None)
    with pytest.raises(ImportError, match=r"pip install financecalendar\[pandas\]"):
        to_dataframe([])


def test_to_dataframe_with_pandas():
    pd = pytest.importorskip("pandas")
    df = to_dataframe(load("history_us_cpi")["body"])
    assert len(df) == 4
    assert pd.api.types.is_datetime64_any_dtype(df["release_at_utc"])
    assert str(df["release_at_utc"].dt.tz) == "UTC"
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert list(df["actual"]) == ["3.0% y/y", "3.1% y/y", "3.1% y/y", "2.9% y/y"]
