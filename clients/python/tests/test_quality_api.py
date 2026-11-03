"""Current-quality/evidence access preserves semantics, authentication and errors."""
from datetime import datetime, timezone

import httpx
import pytest

from financecalendar import Client, FinanceCalendarError


def test_quality_retains_nested_unknown_and_unavailable_evidence_with_same_auth():
    payload = {"reported": True, "snapshot_generated_at": "2026-11-01T18:00:00+00:00",
               "quality": {"by_source": {}, "fields": {"actual": {"available": 0, "missing_reason": "unsupported"}},
                           "future_metadata": {"verified": None}}}
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        assert client.quality() == payload
    assert requests[0].url.path.endswith("/quality")
    assert requests[0].headers["X-API-Key"] == "fc_test"


def test_observations_preserves_nested_lineage_zero_and_pagination_filters():
    generation = "2026-11-01T18:00:00+00:00"
    payload = {"reported": True, "basis": "engine-observed-current-vintage",
               "historical_first_print": False, "as_of_supported": False,
               "snapshot_generated_at": generation, "has_more": True, "next_offset": 20,
               "observations": [{"event_id": "cpi-sep", "observation_id": "source-metric-period",
                                 "observation": {"value": 0, "unit": "%", "source_rights": {"attribution": "Source: official agency"},
                                                 "revision_history": [{"value": None, "known_at": generation}],
                                                 "future_metadata": {"status": "unknown"}}}]}
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=payload)

    with Client(api_key="fc_test", transport=httpx.MockTransport(handle)) as client:
        assert client.observations(series="cpi", event_id="cpi-sep", role="actual",
                                   reference_period="2026-09", limit=20, offset=0,
                                   snapshot_generated_at=generation) == payload
    assert requests[0].url.path.endswith("/observations")
    assert requests[0].headers["X-API-Key"] == "fc_test"
    assert dict(requests[0].url.params) == {"series": "cpi", "event_id": "cpi-sep", "role": "actual",
        "reference_period": "2026-09", "limit": "20", "offset": "0", "snapshot_generated_at": generation}


@pytest.mark.parametrize("method", ["quality", "observations"])
def test_new_endpoints_keep_rate_limit_errors_and_retry_after(method):
    with Client(transport=httpx.MockTransport(lambda request: httpx.Response(
            429, headers={"Retry-After": "45"}, json={"error": "Daily allowance reached."}))) as client:
        with pytest.raises(FinanceCalendarError) as exc:
            getattr(client, method)()
    assert exc.value.status == 429 and exc.value.retry_after == 45
    assert exc.value.message == "Daily allowance reached."


@pytest.mark.parametrize("method", ["quality", "observations"])
def test_as_of_is_forwarded_and_server_rejection_remains_explicit(method):
    def handle(request):
        assert request.url.params["as_of"] == "2026-10-01T00:00:00+00:00"
        return httpx.Response(400, json={"error": "as_of is not supported: current engine snapshot only."})

    with Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(FinanceCalendarError, match="as_of is not supported") as exc:
            getattr(client, method)(as_of=datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert exc.value.status == 400


def test_observation_snapshot_change_requires_caller_restart():
    with Client(transport=httpx.MockTransport(lambda request: httpx.Response(
            409, json={"error": "The snapshot changed during pagination. Restart at offset=0."}))) as client:
        with pytest.raises(FinanceCalendarError, match="Restart at offset=0") as exc:
            client.observations(offset=20, snapshot_generated_at="older-generation")
    assert exc.value.status == 409
