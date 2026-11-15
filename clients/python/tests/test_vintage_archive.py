"""V2 SDK/CLI wire contracts: dates, exact values, clocks and complete exports."""
import json

import httpx
import pytest

from financecalendar import Client, FinanceCalendarError
from financecalendar.cli import main


def page(rows, cursor=None, revision=7):
    return {"schema_version": 2, "archive_revision": revision, "rows": rows, "count": len(rows),
            "has_more": cursor is not None, "next_cursor": cursor,
            "order_date_basis": "forecast_issue_period_start_index",
            "cutoff": {"basis": "verified_source_public_availability", "unknown_clocks_excluded": True}}


def fixture(pages):
    calls = []; responses = iter(pages)
    def respond(request):
        calls.append(request)
        body = next(responses)
        return httpx.Response(body.get("status", 200), json=body.get("body", body))
    return Client(api_key="synthetic-vintage-key", transport=httpx.MockTransport(respond)), calls


@pytest.mark.parametrize("method,suffix", [("archive_editions", "editions"),
    ("archive_forecasts", "forecasts"), ("vintage_coverage", "vintage-coverage")])
def test_sdk_new_routes_and_lossless_response(method, suffix):
    body = page([{"value": "0.000000000000000000123", "raw_value": "0", "scale": "1000",
                  "source_published_at": None, "available_at": None,
                  "issue_period": "2026-Q4", "reference_period": "2027",
                  "source_license": {"attribution": "Original data are freely available from the ECB."}}])
    body["access"] = {"date_basis": "edition_publication_and_reference_period_start" if suffix == "editions" else "forecast_issue_period_start_index" if suffix == "forecasts" else "per_row_edition_publication_and_reference_period_start_or_forecast_issue_index", "lookback_years": 1}
    client, calls = fixture([body])
    with client:
        actual = getattr(client, method)(series="eu-spf-gdp", source_id="ecb-spf", limit=1)
    assert actual == body and calls[0].url.path.endswith("/history/" + suffix)
    assert calls[0].url.params["series_code"] == "eu-spf-gdp"


@pytest.mark.parametrize("iterator,suffix", [("iter_archive_editions", "editions"),
    ("iter_archive_forecasts", "forecasts"), ("iter_vintage_coverage", "vintage-coverage")])
def test_sdk_complete_pagination_repeats_filters_and_keeps_unknowns(iterator, suffix):
    client, calls = fixture([page([{"id": "a", "value": "0"}], "page2"), page([{"id": "b", "value": None}])])
    with client:
        rows = list(getattr(client, iterator)(metric_id="exact-metric", limit=1))
    assert [r["value"] for r in rows] == ["0", None]
    assert all(r.url.path.endswith("/history/" + suffix) and r.url.params["metric_id"] == "exact-metric" and r.url.params["limit"] == "1" for r in calls)
    assert calls[1].url.params["cursor"] == "page2"


@pytest.mark.parametrize("kind", ["editions", "forecasts"])
def test_generic_archive_iterator_supports_v2_and_passes_distinct_cutoffs(kind):
    client, calls = fixture([page([])])
    with client:
        assert list(client.iter_archive(kind, metric_id="exact-metric", from_="2026-01-01",
            as_of="2026-11-15T08:00:00Z", available_before="2026-01-01T12:30:00Z")) == []
    query = calls[0].url.params
    assert query["as_of"] == "2026-11-15T08:00:00Z"
    assert query["available_before"] == "2026-01-01T12:30:00Z"


@pytest.mark.parametrize("bad", [{**page([]), "schema_version": 1}, {**page([]), "count": 1},
    {**page([]), "has_more": True}, {**page([]), "archive_revision": True},
    {**page([{"id": "b"}], "x"), "has_more": False}, page([], "x")])
def test_sdk_malformed_v2_page_fails_explicitly(bad):
    client, _ = fixture([bad])
    with client, pytest.raises(FinanceCalendarError):
        list(client.iter_archive_forecasts(metric_id="exact-metric"))


@pytest.mark.parametrize("command,suffix", [("historic-editions", "editions"),
    ("historic-forecasts", "forecasts"), ("vintage-coverage", "vintage-coverage")])
def test_cli_complete_json_export_new_routes(command, suffix):
    client, calls = fixture([page([{"id": "a", "value": "1.1234567890123456789"}], "next"), page([{"id": "b", "value": None}])])
    output = []
    with client:
        code = main([command, "--metric-id", "exact-metric", "--limit", "1", "--all"], client=client, out=output.append)
    result = json.loads(output[0])
    assert code == 0 and len(output) == 1 and result["count"] == 2 and result["pages"] == 2
    assert result["rows"][0]["value"] == "1.1234567890123456789" and result["rows"][1]["value"] is None
    assert all(r.url.path.endswith("/history/" + suffix) for r in calls)


@pytest.mark.parametrize("bad", [page([{"id": "b"}], revision=8), page([{"id": "b"}], "next"),
    {"status": 409, "body": {"error": "Archive changed"}}])
def test_cli_partial_traversal_never_prints_success(bad):
    client, _ = fixture([page([{"id": "a"}], "next"), bad]); output = []
    with client:
        assert main(["historic-forecasts", "--metric-id", "exact-metric", "--all"], client=client, out=output.append) == 1
    assert output == []


def test_cli_strict_availability_unknown_result_retains_metadata():
    client, calls = fixture([page([])]); output = []
    with client:
        assert main(["historic-forecasts", "--metric-id", "exact-metric", "--available-before", "2026-01-01T00:00:00Z"], client=client, out=output.append) == 0
    assert json.loads(output[0])["cutoff"]["unknown_clocks_excluded"] is True
    assert calls[0].url.params["available_before"] == "2026-01-01T00:00:00Z"


def test_vintage_coverage_rejects_date_and_observation_kind():
    for flags in (["--from", "2026-01-01"], ["--kind", "observations"]):
        client, calls = fixture([])
        with client, pytest.raises(SystemExit):
            main(["vintage-coverage", *flags], client=client)
        assert calls == []


@pytest.mark.parametrize("value", ["2026-01-01", "2026-Q1", "2026-01-01T12:30:00", "2026-01-01T12:30:00+00:00",
    "2026-02-31T00:00:00Z", "2099-01-01T00:00:00Z"])
def test_v2_cutoffs_reject_coarse_naive_invalid_and_future_clocks_before_request(value):
    client, calls = fixture([])
    with client, pytest.raises(ValueError):
        client.archive_forecasts(metric_id="exact-metric", available_before=value)
    assert calls == []


def test_v2_aware_datetime_is_canonical_utc_and_naive_datetime_is_rejected():
    from datetime import datetime, timedelta, timezone
    client, calls = fixture([page([])])
    with client:
        client.archive_forecasts(metric_id="exact-metric", available_before=datetime(2026, 1, 1, 12, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))))
        with pytest.raises(ValueError, match="aware"):
            client.archive_editions(metric_id="exact-metric", as_of=datetime(2026, 1, 1))
    assert len(calls) == 1 and calls[0].url.params["available_before"] == "2026-01-01T07:00:00Z"
