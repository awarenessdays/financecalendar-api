"""Enrichment ledger clients preserve exact evidence and normal transport rules."""
from datetime import date

import httpx
import pytest

from financecalendar import Client, FinanceCalendarError


def test_history_and_edition_docs_direct_cutoff_reads_to_the_dedicated_method():
    for method in (Client.enrichment_history, Client.enrichment_editions):
        description = " ".join(method.__doc__.split())
        assert "use enrichment_as_of() (REST /enrichment/as-of)" in description
        assert "method does not accept as_of" in description
        assert "does not establish complete original first-print history" in description
        assert "both" in description and "pins" in description
        assert "as_of is unsupported" not in description
    history = " ".join(Client.enrichment_history.__doc__.split())
    assert "missing values stay null" in history
    editions = " ".join(Client.enrichment_editions.__doc__.split())
    assert "Provider archives are labelled separately from engine captures" in editions
    cutoff = " ".join(Client.enrichment_as_of.__doc__.split())
    assert "engine_receipt" in cutoff and "provider_availability" in cutoff
    assert "current canonical publication" in cutoff
    assert "official statistical observations are outside it" in cutoff
    assert "does not prove customer availability at the cutoff" in cutoff
    assert "Starter, Build and Scale" in cutoff


def test_results_filters_auth_and_nested_exact_values_are_preserved():
    payload = {"version": 1, "series_code": "us-adp", "as_of_supported": False,
               "history_basis": "evidenced-per-release", "next_offset": 1,
               "ledger_cursor": 3, "publication_revision": 7,
               "releases": [{"event_id": "adp-2026-09", "actual": "0", "prior": "-25000",
                             "consensus": None, "historical_first_print": False,
                             "selected_editions": {"actual": {"value": "0", "received_at": "2026-11-05T15:01:00Z",
                                                              "available_at": "2026-11-05T15:01:00Z",
                                                              "reference_period": "2026-09", "unit": "jobs"}}}]}
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        assert client.enrichment_history("us-adp", from_=date(2026, 1, 1), to="2026-11-05", limit=1, offset=0) == payload
    request = requests[0]
    assert request.url.path.endswith("/enrichment/history")
    assert request.headers["X-API-Key"] == "fc_test"
    assert dict(request.url.params) == {"series": "us-adp", "from": "2026-01-01", "to": "2026-11-05", "limit": "1", "offset": "0"}


def test_editions_retain_distinct_archive_availability_and_receipt_with_paging():
    payload = {"version": 1, "event_id": "adp-2026-09", "next_offset": None,
               "as_of_supported": False, "ledger_cursor": 3, "publication_revision": 7, "editions": [
                   {"edition_id": "survey-1", "value": "50000", "historical_basis": "provider_archived",
                    "provider_edition_id": "vintage-1", "available_at": "2026-11-05T14:59:00Z",
                    "received_at": "2026-11-05T15:01:00Z", "cutoff_verified": True,
                    "role": "consensus", "forecast_type": "survey_consensus"}]}
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        assert client.enrichment_editions("adp-2026-09", limit=20, offset=20,
                                          ledger_cursor=3, publication_revision=7) == payload
    assert requests[0].url.path.endswith("/enrichment/editions")
    assert dict(requests[0].url.params) == {"event_id": "adp-2026-09", "limit": "20", "offset": "20",
                                          "ledger_cursor": "3", "publication_revision": "7"}


@pytest.mark.parametrize("method,arg", [("enrichment_history", "us-adp"), ("enrichment_editions", "adp-2026-09")])
@pytest.mark.parametrize("status,retry", [(403, None), (429, "45"), (503, None)])
def test_enrichment_errors_use_same_status_and_retry_after(method, arg, status, retry):
    headers = {"Retry-After": retry} if retry else {}
    with Client(api_key="fc_test", transport=httpx.MockTransport(lambda request: httpx.Response(
            status, headers=headers, json={"error": "Not currently available."}))) as client:
        with pytest.raises(FinanceCalendarError) as exc:
            getattr(client, method)(arg)
    assert exc.value.status == status
    assert exc.value.retry_after == (45 if retry else None)


@pytest.mark.parametrize("method,arg", [("enrichment_history", "us-adp"), ("enrichment_editions", "adp-2026-09")])
def test_as_of_rejection_is_explicit_and_never_silently_ignored(method, arg):
    def handle(request):
        assert request.url.params["as_of"] == "2026-11-01T00:00:00Z"
        return httpx.Response(400, json={"error": "unsupported_query"})

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(FinanceCalendarError, match="unsupported_query"):
            getattr(client, method)(arg, as_of="2026-11-01T00:00:00Z")


@pytest.mark.parametrize("method,arg", [("enrichment_history", "us-adp"), ("enrichment_editions", "adp-2026-09")])
def test_missing_key_is_rejected_before_network(method, arg, monkeypatch):
    monkeypatch.delenv("FC_API_KEY", raising=False)
    with Client(transport=httpx.MockTransport(lambda request: pytest.fail("No anonymous request"))) as client:
        with pytest.raises(FinanceCalendarError) as exc:
            getattr(client, method)(arg)
    assert exc.value.status == 401


@pytest.mark.parametrize("method,arg", [("enrichment_history", "us-adp"), ("enrichment_editions", "adp-2026-09")])
def test_pagination_carries_both_first_page_pins_and_exposes_publication_change(method, arg):
    requests = []

    def handle(request):
        requests.append(request)
        if len(requests) == 1:
            assert "ledger_cursor" not in request.url.params and "publication_revision" not in request.url.params
            return httpx.Response(200, json={"next_offset": 1, "ledger_cursor": 9007199254740991,
                                             "publication_revision": 7, "as_of_supported": False})
        assert request.url.params["ledger_cursor"] == "9007199254740991"
        assert request.url.params["publication_revision"] == "7"
        assert request.url.params["offset"] == "1"
        return httpx.Response(409, json={"error": "fc_enrichment_publication_changed: restart first page"})

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        first = getattr(client, method)(arg, limit=1)
        with pytest.raises(FinanceCalendarError) as exc:
            getattr(client, method)(arg, limit=1, offset=first["next_offset"],
                                    ledger_cursor=first["ledger_cursor"], publication_revision=first["publication_revision"])
    assert exc.value.status == 409


def test_as_of_sends_explicit_cutoff_and_basis_and_keeps_exact_values():
    payload = {"version": 1, "event_id": "adp-2026-10", "as_of": "2026-11-03T14:00:00Z", "basis": "provider_availability",
               "values": {"consensus": "-1.4", "actual": None, "prior": "-2"}, "selected_editions": {},
               "editions_accepted": 5, "editions_considered": 2, "editions_after_cutoff": 3,
               "editions_without_availability": 0, "publication_revision": 9, "as_of_supported": True,
               "history_basis": "published-editions-by-cutoff", "scope": "enrichment_ledger_provider_editions",
               "official_observations_included": False, "customer_availability_at_cutoff_verified": False}
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    from datetime import datetime, timezone, timedelta
    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        assert client.enrichment_as_of("adp-2026-10", datetime(2026, 11, 3, 15, tzinfo=timezone(timedelta(hours=1))), basis="provider_availability") == payload
        assert client.enrichment_as_of("adp-2026-10", "2026-11-03T14:00:00Z") == payload
        with pytest.raises(ValueError):
            client.enrichment_as_of("adp-2026-10", datetime(2026, 11, 3, 14))
    assert requests[0].url.path.endswith("/enrichment/as-of")
    assert dict(requests[0].url.params) == {"event_id": "adp-2026-10", "as_of": "2026-11-03T14:00:00Z", "basis": "provider_availability"}
    assert dict(requests[1].url.params) == {"event_id": "adp-2026-10", "as_of": "2026-11-03T14:00:00Z"}


def test_webhook_methods_use_the_right_verbs_paths_and_bodies():
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "method": request.method, "path": request.url.path})

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        client.webhooks()
        client.create_webhook("https://hooks.example.com/fc", ["result.published", "schedule.cancelled"], series=["us-cpi"])
        client.webhook(7)
        client.test_webhook(7)
        client.rotate_webhook_secret(7)
        client.delete_webhook(7)
    assert [(r.method, r.url.path.split("/fc/v1")[-1]) for r in requests] == [
        ("GET", "/webhooks"), ("POST", "/webhooks"), ("GET", "/webhooks/7"), ("POST", "/webhooks/7/test"),
        ("POST", "/webhooks/7/rotate"), ("DELETE", "/webhooks/7")]
    import json
    assert json.loads(requests[1].content) == {"url": "https://hooks.example.com/fc", "events": ["result.published", "schedule.cancelled"], "series": ["us-cpi"]}
    assert all(r.headers["X-API-Key"] == "fc_test" for r in requests)


def test_as_of_datetime_preserves_microsecond_cutoff():
    from datetime import datetime, timezone

    def handler(request):
        assert request.url.params["as_of"] == "2026-11-03T14:00:00.500001Z"
        return httpx.Response(200, json={"ok": True})

    with Client(api_key="fixture", transport=httpx.MockTransport(handler)) as client:
        assert client.enrichment_as_of("event", datetime(2026, 11, 3, 14, 0, 0, 500001, tzinfo=timezone.utc)) == {"ok": True}
