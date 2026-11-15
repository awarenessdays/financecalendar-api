from __future__ import annotations

import httpx
import pytest

from financecalendar import Client, FinanceCalendarError


def test_archive_iteration_preserves_decimals_and_filters():
    requests = []

    def respond(request):
        requests.append(request)
        second = request.url.params.get("cursor") == "opaque-page-two"
        return httpx.Response(200, json={"archive_revision": 8,
            "rows": [{"id": "b" if second else "a", "value": "0" if second else "1.23000000001"}],
            "next_cursor": None if second else "opaque-page-two"})

    with Client(api_key="fixture", transport=httpx.MockTransport(respond)) as client:
        result = list(client.iter_archive(series="gb-cpi", from_="2006-01-01", to="2026-11-14", limit=1))
    assert [row["value"] for row in result] == ["1.23000000001", "0"]
    assert all(request.url.path.endswith("/history/observations") for request in requests)
    assert all(request.url.params["series_code"] == "gb-cpi" and request.url.params["from"] == "2006-01-01" for request in requests)
    assert requests[1].url.params["cursor"] == "opaque-page-two"


@pytest.mark.parametrize("second", [
    {"archive_revision": 9, "rows": [{"id": "b"}], "next_cursor": None},
    {"archive_revision": 8, "rows": [{"id": "b"}], "next_cursor": "same"},
    {"archive_revision": 8, "rows": [], "next_cursor": "another"},
    {"archive_revision": 8, "rows": "invalid", "next_cursor": None},
])
def test_incomplete_or_changed_archive_fails(second):
    pages = iter([{"archive_revision": 8, "rows": [{"id": "a"}], "next_cursor": "same"}, second])
    with Client(api_key="fixture", transport=httpx.MockTransport(lambda request: httpx.Response(200, json=next(pages)))) as client:
        with pytest.raises(FinanceCalendarError):
            list(client.iter_archive())


def test_archive_routes_and_kind_validation():
    paths = []
    def respond(request):
        paths.append(request.url.path)
        return httpx.Response(200, json={"archive_revision": 1, "rows": [], "next_cursor": None})
    with Client(api_key="fixture", transport=httpx.MockTransport(respond)) as client:
        assert list(client.iter_archive("releases")) == []
        client.history_coverage(series="us-cpi")
        with pytest.raises(ValueError):
            list(client.iter_archive("calendar"))
    assert paths == ["/wp-json/fc/v1/history/releases", "/wp-json/fc/v1/history/coverage"]
