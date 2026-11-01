"""Crypto contracts: requests, estimated timing, attribution and dataframe data types."""
from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

import httpx
import pytest

from financecalendar import Client, to_dataframe
from financecalendar.cli import format_event, format_when, format_series, main
from conftest import Recorder, load


@pytest.mark.parametrize("method,args,params,path", [
    ("calendar", (), {"category": "crypto", "limit": 1, "offset": 2}, "/calendar"),
    ("crypto_calendar", (), {}, "/calendar"),
    ("today", (), {"category": "crypto"}, "/today"),
    ("week", (), {"category": "crypto"}, "/week"),
    ("next", ("ethereum-network-upgrades",), {}, "/next"),
    ("series", (), {"category": "crypto"}, "/series"),
    ("series_detail", ("ethereum-network-upgrades",), {}, "/series/ethereum-network-upgrades"),
    ("history", ("ethereum-network-upgrades",), {}, "/history"),
])
def test_asset_passthrough_every_client_workflow(client, recorder, method, args, params, path):
    data = getattr(client, method)(*args, asset="ethereum", **params)
    assert recorder.last.url.path.endswith(path)
    assert recorder.last.url.params["asset"] == "ethereum"
    assert "ethereum-network-upgrades" in str(data)
    if method in ("calendar", "crypto_calendar"):
        assert recorder.last.url.params["category"] == "crypto"
        assert data["events"][1]["country"] is None
        assert data["events"][1]["impact"] is None
        assert data["events"][1]["actual"] == 0
        assert data["events"][1]["crypto"]["block_height"] == 0
        assert data["events"][1]["source_license"]["adapted"] is True


def test_crypto_calendar_cannot_be_accidentally_overridden_to_macro(client, recorder):
    client.crypto_calendar(asset=["ethereum", "bitcoin"], category="economic-indicators")
    assert recorder.last.url.params["category"] == "crypto"
    assert recorder.last.url.params["asset"] == "ethereum,bitcoin"


def test_iter_calendar_preserves_asset_filters_and_deduplicates_overlapping_windows():
    window, exact = load("crypto")["body"]["events"]
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        # A broad date window overlaps both 92-day chunks but is still one event.
        return httpx.Response(200, json={"count": 2, "total": 2, "events": [window, exact]})

    with Client(transport=httpx.MockTransport(handler)) as client:
        rows = list(client.iter_calendar(date(2026, 9, 1), date(2027, 1, 1), asset="ethereum", category="crypto"))
    assert len(calls) == 2
    assert len(rows) == 2
    assert [row["id"] for row in rows] == [window["id"], exact["id"]]
    assert all(q["asset"] == "ethereum" and q["category"] == "crypto" for q in calls)


@pytest.mark.parametrize("command", [
    ["calendar", "--category", "crypto"], ["today", "--category", "crypto"],
    ["week", "--category", "crypto"], ["series", "--category", "crypto"],
    ["next", "ethereum-network-upgrades"], ["show", "ethereum-network-upgrades"],
    ["history", "ethereum-network-upgrades"],
])
def test_cli_crypto_commands_pass_asset(client, recorder, command):
    output = []
    code = main([*command, "--asset", "ethereum", "--json"], client=client, out=output.append)
    assert code == 0
    assert recorder.last.url.params["asset"] == "ethereum"
    assert "ethereum-network-upgrades" in output[0]


def test_human_crypto_output_distinguishes_global_testnets_and_estimates():
    window, exact = load("crypto")["body"]["events"]
    assert format_when(window, ZoneInfo("Asia/Tokyo")) == "2026-10-01–2026-12-31 (estimated window)"
    assert format_when(window, ZoneInfo("America/New_York")) == format_when(window, ZoneInfo("UTC"))
    text = format_event(exact, ZoneInfo("UTC"))
    assert "Ethereum upgrade (ETH · Global)  sepolia  prior 0  actual 0" in text
    assert "Ethereum Foundation and ethereum.org contributors · CC-BY-4.0 · adapted by Finance Calendar" in text
    assert exact["source_url"] in text and exact["source_license"]["url"] in text
    assert "all day" not in text


def test_licensed_provider_credit_keeps_required_link_and_notices_in_human_output():
    row = {**load("crypto")["body"]["events"][1], "source_rights": None,
           "source_license": {"id": "CC-BY-4.0", "attribution": "Data: PatternPlus", "attribution_url": "https://pattern.plus", "url": "https://creativecommons.org/licenses/by/4.0/", "terms_url": "https://pattern.plus/developers", "notice": "Retain provider attribution.", "adapted": True}}
    text = format_event(row, ZoneInfo("UTC"))
    assert "Data: PatternPlus · CC-BY-4.0 · adapted by Finance Calendar" in text
    assert "Attribution: https://pattern.plus" in text
    assert all(row["source_license"][key] in text for key in ("url", "terms_url", "notice"))
    assert row["source_url"] in text
    assert "independently verified" not in text


@pytest.mark.parametrize("event_type,qualification", [
    ("supply-projection", "Issuer supply projection; not a confirmed unlock or observed circulating supply."),
    ("governance-vote", "Governance voting deadline; not a proposal outcome or execution."),
])
def test_factual_crypto_output_retains_primary_provenance_and_no_licence_claim(event_type, qualification):
    rights = {"basis": "independently-normalized-facts", "access_basis": "manual-review", "attribution": "Test issuer factual schedule", "source_url": "https://issuer.example/rights", "terms_url": "https://issuer.example/terms", "notice": "No publisher copyright licence is asserted."}
    row = {**load("crypto")["body"]["events"][1], "source_license": None, "source_rights": rights, "source_url": "https://issuer.example/schedule", "discovery_url": "https://coinmarketcal.com/en/event/discovery-only", "crypto": {"event_type": event_type}}
    text = format_event(row, ZoneInfo("UTC"))
    assert "Factual source: " + rights["attribution"] in text
    assert row["source_url"] in text
    assert "Rights evidence: " + rights["source_url"] in text
    assert rights["terms_url"] in text and rights["notice"] in text
    assert "Rights basis: independently-normalized-facts; not a publisher copyright licence." in text
    assert "Source access: manual-review" in text
    assert "Discovery (not verification): " + row["discovery_url"] in text
    assert qualification in text
    assert "MIT" not in text and "CC-BY" not in text


def test_series_target_output_uses_the_full_window(client):
    series = client.series(category="crypto", asset="ethereum")["series"][0]
    expected = "next target 2026-10-01–2026-12-31 (estimated window)"
    assert format_series(series).endswith(expected)
    assert "next 2026-10-01" not in format_series(series)
    assert format_series({**series, "next_date_window_end": None}).endswith("next target window tbc")
    assert format_series({**series, "next_date_window_start": None, "next_date_window_end": None}).endswith("next 2026-10-01")
    output = []
    assert main(["series", "--category", "crypto", "--asset", "ethereum"], client=client, out=output.append) == 0
    assert expected in output[0]
    assert "next 2026-10-01" not in output[0]


def test_dataframe_retains_asset_objects_license_zero_and_null():
    pd = pytest.importorskip("pandas")
    window, exact = load("crypto")["body"]["events"]
    # Also accept callers mixing older macro rows which predate the assets field.
    frame = to_dataframe([window, exact, {"id": "macro", "country": "US", "actual": None}])
    assert frame.loc[0, "asset_ids"] == ["ethereum"]
    assert frame.loc[1, "asset_symbols"] == ["ETH"]
    assert frame.loc[2, "asset_ids"] == []
    assert frame.loc[1, "actual"] == 0
    # pandas 2 can retain None in object columns; pandas 3's inferred string
    # dtype uses its missing-value sentinel. Both preserve a null country.
    assert pd.isna(frame.loc[1, "country"])
    assert frame.loc[2, "country"] == "US"
    assert frame.loc[1, "source_license"]["id"] == "CC-BY-4.0"
    assert frame.loc[0, "date_window_end"] == pd.Timestamp("2026-12-31")
    assert pd.isna(frame.loc[0, "release_at_utc"])
