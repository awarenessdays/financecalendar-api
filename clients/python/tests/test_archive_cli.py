import json

import httpx
import pytest

from financecalendar import Client
from financecalendar.cli import main


def page(rows, cursor=None, revision=7):
    return {"schema_version": 1, "archive_revision": revision, "count": len(rows), "rows": rows,
            "has_more": cursor is not None, "next_cursor": cursor, "as_of_basis": "fc_evidence_commit_observed_bound"}


def run(pages, *argv):
    calls, output = [], []
    responses = iter(pages)

    def respond(request):
        calls.append(request)
        body = next(responses)
        return httpx.Response(body.get("status", 200), json=body.get("body", body))

    with Client(api_key="synthetic-history-key", transport=httpx.MockTransport(respond)) as client:
        code = main(list(argv), client=client, out=output.append)
    return code, output, calls


@pytest.mark.parametrize("command,endpoint", [("archive-observations", "observations"), ("archive-releases", "releases")])
def test_archive_cli_page_retains_metadata_and_exact_filter_semantics(command, endpoint):
    body = page([{"id": "synthetic", "value": "0", "release_at_utc": None}], "continue")
    code, output, calls = run([body], command, "--metric-id", "gb-cpi-all-items-yoy", "--series-code", "gb-cpi", "--from", "2006-01-01", "--to", "2026-11-14", "--as-of", "2026-11-14T12:00:00Z", "--limit", "1")
    assert code == 0 and json.loads(output[0]) == body
    assert calls[0].url.path.endswith("/history/" + endpoint)
    assert calls[0].url.params["from"] == "2006-01-01"
    assert calls[0].url.params["series_code"] == "gb-cpi"
    assert calls[0].url.params["as_of"] == "2026-11-14T12:00:00Z"


def test_archive_cli_all_buffers_complete_pinned_export():
    code, output, calls = run([page([{"id": "a", "value": "1.234567890123456789012345"}], "next"), page([{"id": "b", "value": "0"}])],
                              "archive-observations", "--metric-id", "gb-cpi-all-items-yoy", "--from", "2006-01-01", "--limit", "1", "--all")
    result = json.loads(output[0])
    assert code == 0 and len(output) == 1 and result["count"] == 2 and result["pages"] == 2
    assert [row["value"] for row in result["rows"]] == ["1.234567890123456789012345", "0"]
    assert result["next_cursor"] is None and result["archive_revision"] == 7
    assert all(call.url.params["metric_id"] == "gb-cpi-all-items-yoy" and call.url.params["from"] == "2006-01-01" and call.url.params["limit"] == "1" for call in calls)
    assert calls[1].url.params["cursor"] == "next"


def test_archive_cli_coverage_all_keeps_coverage_kind_and_source():
    code, output, calls = run([page([{"metric_id": "a"}], "next"), page([{"metric_id": "b"}])],
                              "history-coverage", "--source-id", "ons", "--kind", "observations", "--limit", "1", "--all")
    assert code == 0 and json.loads(output[0])["count"] == 2
    assert all(call.url.path.endswith("/history/coverage") and call.url.params["kind"] == "observations" and call.url.params["source_id"] == "ons" for call in calls)


@pytest.mark.parametrize("second", [
    page([{"id": "b"}], revision=8),
    page([{"id": "b"}], "next"),
    page([], "another"),
    {**page([{"id": "b"}]), "count": 2},
    {**page([{"id": "b"}], "another"), "has_more": False},
    {"status": 409, "body": {"error": "Archive changed"}},
])
def test_archive_cli_failure_never_prints_partial_success(second, capsys):
    code, output, _ = run([page([{"id": "a"}], "next"), second], "archive-observations", "--metric-id", "gb-cpi-all-items-yoy", "--all")
    assert code == 1 and output == []
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["archive-observations"], ["history-coverage", "--limit", "501"],
    ["archive-releases", "--series-code", "gb-cpi", "--all", "--cursor", "old"],
    ["archive-observations", "--metric-id", "x", "--tz", "UTC"],
])
def test_archive_cli_invalid_options_fail_before_network(argv, capsys):
    code, output, calls = run([], *argv)
    assert code == 2 and output == [] and calls == []


def test_coverage_rejects_reference_date_option():
    with pytest.raises(SystemExit) as error:
        run([], "history-coverage", "--from", "2006-01-01")
    assert error.value.code == 2
