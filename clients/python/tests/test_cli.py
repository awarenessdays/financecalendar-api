from __future__ import annotations

from zoneinfo import ZoneInfo

import pytest

from financecalendar.cli import format_event, format_when, format_change, main

from conftest import load


def run(client, *argv):
    lines: list[str] = []
    code = main(list(argv), client=client, out=lines.append)
    return code, "\n".join(lines)


def test_changes_preserve_zero_and_object_array_types():
    change = {"at": "2026-10-22T09:00:00Z", "change": "updated", "series_code": "example", "id": "example", "field": "actual", "old": 0, "new": False}
    assert format_change(change).endswith("actual: 0 -> false")
    assert format_change({**change, "field": "source_rights", "old": {}, "new": []}).endswith("source_rights: {} -> []")


def test_format_event_documented_layout():
    fomc = load("next_fomc")["body"]["next"]
    assert format_event(fomc, ZoneInfo("America/New_York")) == (
        "Wed 28 Oct 14:00 ET  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold\n"
        "https://www.financecalendar.com/event/fomc-rate-decision-october-2026/"
    )
    assert format_when(fomc, ZoneInfo("Europe/London")) == "Wed 28 Oct 18:00 GMT"
    assert format_when(fomc, ZoneInfo("Asia/Tokyo")) == "Thu 29 Oct 03:00 JST"
    hol = load("today")["body"]["market_holidays"][0]
    assert format_event(hol, ZoneInfo("UTC")) == "Mon 19 Oct all day  HKEX closed: Day Following Chung Yeung Festival (HK)"


def test_release_stages_and_reference_periods_distinguish_events():
    event = {"name": "US GDP", "date": "2026-10-29", "country": "US", "period": "3rd Quarter 2026",
             "release_at_utc": "2026-10-29T12:30:00Z"}
    lines = [format_event({**event, "release_stage": stage}, ZoneInfo("UTC")) for stage in ("advance", "second", "third")]
    assert len(set(lines)) == 3
    assert all("period 3rd Quarter 2026  stage " in line for line in lines)
    assert format_event({**event, "period": "January 2026"}) != format_event({**event, "period": "February 2026"})


def test_details_already_in_name_are_not_repeated_and_input_stays_unchanged():
    event = {"name": "US GDP (Second Estimate), 3rd Quarter 2026", "date": "2026-11-25",
             "period": "3rd Quarter 2026", "release_stage": "second"}
    before = dict(event)
    assert format_event(event, ZoneInfo("UTC")) == "Wed 25 Nov time unknown  US GDP (Second Estimate), 3rd Quarter 2026"
    assert event == before
    assert format_event({**event, "name": "Secondary GDP"}).endswith("stage second")


def test_unknown_economic_release_time_is_not_an_all_day_holiday():
    event = {"date": "2026-11-25", "name": "US GDP", "category": "economic-indicators", "release_at_utc": None, "all_day": True}
    assert format_when(event, ZoneInfo("Asia/Tokyo")) == "Wed 25 Nov time unknown"
    assert format_when({**event, "category": "market-holidays"}, ZoneInfo("Asia/Tokyo")) == "Wed 25 Nov all day"
    assert format_event({**event, "release_stage": "annual-update"}).endswith("stage annual update")


def test_publication_windows_render_localized_bounds_without_exact_clock_synthesis():
    event = {"date": "2026-11-18", "name": "Japan release", "release_at_utc": None, "all_day": False, "time_precision": "range",
             "time_window_start": "2026-11-18T12:00:00+09:00", "time_window_end": "2026-11-18T12:15:00+09:00", "time_role": "publication"}
    before = dict(event)
    assert format_when(event, ZoneInfo("Asia/Tokyo")) == "Wed 18 Nov 12:00–12:15 JST"
    assert format_when(event, ZoneInfo("America/New_York")) == "Tue 17 Nov 22:00–22:15 ET"
    assert format_when({**event, "time_window_end": "invalid"}, ZoneInfo("UTC")) == "Wed 18 Nov time unknown"
    assert format_when({**event, "time_window_start": "2026-11-18T12:00:00"}, ZoneInfo("UTC")) == "Wed 18 Nov time unknown"
    assert event == before


def test_windows_crossing_midnight_or_dst_show_both_bounds():
    assert format_when({"time_window_start": "2026-11-18T23:55:00Z", "time_window_end": "2026-11-19T00:05:00Z"}, ZoneInfo("UTC")) == "Wed 18 Nov 23:55 UTC–Thu 19 Nov 00:05 UTC"
    assert format_when({"time_window_start": "2026-11-01T05:55:00Z", "time_window_end": "2026-11-01T06:10:00Z"}, ZoneInfo("America/New_York")) == "Sun 01 Nov 01:55 EDT–Sun 01 Nov 01:10 EST"


def test_auction_close_is_labelled_separately_from_result_publication():
    event = {"name": "US Treasury Bill Auction", "date": "2026-11-18", "release_at_utc": "2026-11-18T16:30:00Z", "time_role": "auction-close",
             "auction": {"cusip": "912797AB1", "high_rate": "4.050000", "reopening": False}}
    before = dict(event)
    assert format_event(event, ZoneInfo("America/New_York")).endswith("11:30 ET  US Treasury Bill Auction  auction close")
    assert event == before


def test_next_human_and_json(client):
    code, out = run(client, "--tz", "Europe/London", "next", "fomc")
    assert code == 0
    assert out == "Wed 28 Oct 18:00 GMT  FOMC Rate Decision (US)  cons. Hold at 3.50-3.75%  prior Hold\nhttps://www.financecalendar.com/event/fomc-rate-decision-october-2026/"
    code, out = run(client, "--json", "next", "fomc")
    assert '"series_code": "fomc"' in out


def test_today_week_calendar(client):
    _, out = run(client, "--tz", "UTC", "today")
    assert out.splitlines()[0] == "2026-10-19  NYSE open"
    assert "Exchange closures today:" in out
    _, out = run(client, "--tz", "UTC", "week", "--next")
    assert out.startswith("Next week, 2026-10-26 to 2026-11-01")
    _, out = run(client, "--tz", "UTC", "calendar", "--from", "2026-11-23", "--to", "2026-11-30", "--holidays")
    assert out.startswith("2026-11-23 to 2026-11-30: 15 of 15 events")
    assert "JPX closed: Labor Thanksgiving Day (JP)" in out
    _, out = run(client, "calendar", "--csv")
    assert out.startswith("date,time_utc,time_et")


def test_other_commands(client):
    _, out = run(client, "series", "--country", "us")
    assert out.splitlines()[0].startswith("beige-book")
    _, out = run(client, "--tz", "UTC", "show", "fomc")
    assert out.startswith("FOMC Rate Decision (fomc)  US  central-banks-monetary-policy  impact high  8x/year")
    assert "Next:\nWed 28 Oct 18:00 UTC  FOMC Rate Decision (US)" in out
    _, out = run(client, "--tz", "America/New_York", "history", "us-cpi", "--limit", "4")
    assert out.startswith("us-cpi: 4 releases, 2025-10-19 to 2026-10-19")
    assert "actual 3.0% y/y" in out
    _, out = run(client, "holidays")
    assert out.startswith("NYSE holidays (13)")
    assert "2026-11-27  Day After Thanksgiving  NYSE  early close 13:00" in out
    _, out = run(client, "status")
    assert out.startswith("NYSE open")
    assert "next holiday: 2026-11-26  Thanksgiving  closed" in out
    _, out = run(client, "changes", "--since", "2026-10-18T00:00:00Z")
    assert out.startswith("100 changes since 2026-10-18T15:47:45+00:00")
    _, out = run(client, "countries")
    assert out.startswith("US  United States     25 series    290 events")
    code, out = run(client, "health")
    assert code == 0 and '"ok": true' in out


def test_api_error_exit_code(client, capsys):
    code, out = run(client, "calendar", "--tz", "Mars/Olympus")
    assert code == 1 and out == ""
    assert capsys.readouterr().err == "Error: HTTP 400: tz must be an IANA timezone such as Europe/London or Asia/Tokyo.\n"


def test_missing_command_is_a_usage_error(client):
    with pytest.raises(SystemExit) as exc:
        run(client)
    assert exc.value.code == 2


def test_global_options_work_before_or_after_the_command(client):
    before = run(client, "--tz", "Asia/Tokyo", "--json", "next", "fomc")
    after = run(client, "next", "fomc", "--tz", "Asia/Tokyo", "--json")
    assert before == after and '"series_code": "fomc"' in before[1]
    _, out = run(client, "next", "fomc", "--tz", "Asia/Tokyo")
    assert out.startswith("Thu 29 Oct 03:00 JST  FOMC Rate Decision (US)")
    _, out = run(client, "--tz", "Asia/Tokyo", "next", "fomc")
    assert out.startswith("Thu 29 Oct 03:00 JST")


def test_invalid_tz_is_a_clean_error_when_the_api_does_not_reject_it(client, capsys):
    # The mock /next answers normally, so the bad zone is only noticed when times are formatted.
    code, out = run(client, "next", "fomc", "--tz", "Mars/Olympus")
    assert code == 2 and out == ""
    assert capsys.readouterr().err.startswith("Error: unknown timezone")


def test_connection_errors_are_reported_not_raised(capsys):
    import httpx
    from financecalendar import Client

    def boom(request):
        raise httpx.ConnectError("connection refused", request=request)

    with Client(base_url="http://127.0.0.1:9/v1", transport=httpx.MockTransport(boom)) as c:
        code = main(["today"], client=c, out=lambda s: None)
    assert code == 1
    err = capsys.readouterr().err
    assert err.startswith("Error: could not reach http://127.0.0.1:9/v1: ConnectError")


def test_calendar_status_offset_and_changes_limit(client, recorder):
    code, _ = run(client, "--json", "calendar", "--status", "estimated", "--offset", "5", "--limit", "2")
    assert code == 0
    assert dict(recorder.last.url.params) == {"status": "estimated", "limit": "2", "offset": "5"}
    run(client, "changes", "--limit", "10")
    assert dict(recorder.last.url.params) == {"limit": "10"}
    run(client, "changes", "--cursor", "opaque-page-2")
    assert dict(recorder.last.url.params) == {"cursor": "opaque-page-2"}


def test_series_code_is_url_quoted(client, recorder):
    with pytest.raises(Exception):
        client.series_detail("a b/c")
    assert recorder.last.url.raw_path.decode().endswith("/series/a%20b%2Fc")
