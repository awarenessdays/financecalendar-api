"""Synthetic official observations: value semantics, freshness and lineage."""
import csv
import io
import json
from zoneinfo import ZoneInfo

import httpx

from financecalendar import Client
from financecalendar.cli import format_event, main


def row():
    return {"id": "synthetic-cpi", "name": "Synthetic CPI", "date": "2026-10-21", "country": "GB", "period": "2026-09", "actual": 0,
            "source_id": "ons", "native_id": "synthetic-native", "source_reference_period": {"date": "2026-09-01", "formatted": "2026-09", "frequency": "MONTHLY"},
            "data_stale": False, "observation_status": "stale", "observation_metric_id": "test-cpi", "observation_fields": ["actual", "prior"], "observations": [
                {"role": "actual", "value": 0, "unit": "% y/y", "reference_period": "2026-09", "source_id": "ons-observations-test", "known_at": "2026-10-21T08:00:00Z", "data_stale": False,
                 "revision_history": [{"value": "0.1", "known_at": "2026-10-20T08:00:00Z"}], "source_url": "https://www.ons.gov.uk/synthetic-observation",
                 "source_license": {"spdx": "OGL-UK-3.0", "attribution": "Source: Office for National Statistics", "url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"}},
                {"role": "prior", "value": "0", "unit": "% y/y", "reference_period": "2026-08", "data_stale": True, "value_basis": "previous-reference-period-current-vintage"}]}


def test_observations_render_zero_periods_current_vintage_and_independent_staleness():
    event = row()
    text = format_event(event, ZoneInfo("UTC"))
    assert "Official actual: 0 % y/y · reference period 2026-09 · current observed vintage" in text
    assert "Official prior: 0 % y/y · reference period 2026-08" in text
    assert "Prior is the previous reference period at the current observed vintage, not the original first print." in text
    assert "Stale official prior observation; schedule freshness is independent." in text
    assert "Stale source data" not in text and "Stale official actual observation" not in text
    assert "Recorded value revisions: 1 (observed by Finance Calendar)." in text
    assert "not the publisher's first-print timestamp" in text
    assert event["observations"][0]["source_url"] in text and event["observations"][0]["source_license"]["url"] in text
    assert "OGL-UK-3.0 · Source: Office for National Statistics" in text


def test_python_raw_json_preserves_nested_observations_and_native_metadata():
    event, output = row(), []
    with Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"events": [event]}))) as client:
        assert client.calendar()["events"][0] == event
        assert main(["calendar", "--json"], client=client, out=output.append) == 0
    assert json.loads(output[0])["events"][0] == event


def test_python_csv_passes_server_columns_and_nested_lineage_without_reordering_or_loss():
    event, output, stream = row(), [], io.StringIO()
    columns = ["date", "name", "actual", "observations", "source_reference_period", "observation_status", "observation_fields", "source_id", "native_id"]
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerow({key: json.dumps(event[key]) if isinstance(event.get(key), (list, dict)) else event.get(key, "") for key in columns})
    content = stream.getvalue()
    with Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, text=content))) as client:
        assert main(["calendar", "--csv"], client=client, out=output.append) == 0
    assert output[0].splitlines()[0] == content.splitlines()[0]
    parsed = next(csv.DictReader(io.StringIO(output[0])))
    assert json.loads(parsed["observations"]) == event["observations"]
    assert json.loads(parsed["source_reference_period"]) == event["source_reference_period"]
    assert parsed["actual"] == "0" and parsed["source_id"] == "ons" and parsed["native_id"] == event["native_id"]


def test_native_economic_schedule_licence_accepts_spdx_credit():
    text = format_event({"date": "2026-10-22", "name": "Synthetic release", "source_license": {
        "spdx": "CC-BY-4.0", "attribution": "Source: DOSM", "url": "https://creativecommons.org/licenses/by/4.0/"}})
    assert "Source: DOSM · CC-BY-4.0" in text
