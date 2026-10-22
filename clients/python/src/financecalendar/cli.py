"""financecalendar command line: the economic calendar in your terminal."""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from .client import Client, FinanceCalendarError, __version__

ZONE_LABELS = {"America/New_York": "ET", "America/Chicago": "CT", "America/Los_Angeles": "PT", "UTC": "UTC", "Etc/UTC": "UTC"}


def local_zone(tz: str | None):
    if tz:
        return ZoneInfo(tz)
    return datetime.now().astimezone().tzinfo or timezone.utc


def format_when(event: dict[str, Any], tz=None) -> str:
    if event.get("date_window_start") and event.get("date_window_end"):
        return f"{event['date_window_start']}–{event['date_window_end']} (estimated window)"
    window = _format_window(event.get("time_window_start"), event.get("time_window_end"), tz or local_zone(None))
    if window:
        return window
    if not event.get("release_at_utc") or event.get("all_day"):
        d = event.get("date")
        if not d:
            return ""
        timing = "all day" if event.get("category") == "market-holidays" else "time unknown"
        return datetime.fromisoformat(d).strftime("%a %d %b") + f" {timing}"
    zone = tz or local_zone(None)
    dt = datetime.fromisoformat(event["release_at_utc"].replace("Z", "+00:00")).astimezone(zone)
    name = getattr(zone, "key", None) or ""
    label = ZONE_LABELS.get(name) or dt.tzname() or name
    return dt.strftime("%a %d %b %H:%M") + f" {label}"


def _format_window(start: Any, end: Any, zone) -> str | None:
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    try:
        first = datetime.fromisoformat(start.replace("Z", "+00:00"))
        last = datetime.fromisoformat(end.replace("Z", "+00:00"))
        if first.tzinfo is None or last.tzinfo is None or last < first:
            return None
        first, last = first.astimezone(zone), last.astimezone(zone)
    except ValueError:
        return None
    key = getattr(zone, "key", None) or ""
    same_offset = first.utcoffset() == last.utcoffset()
    label = ZONE_LABELS.get(key) or first.tzname() or key
    if first.date() == last.date() and same_offset:
        return first.strftime("%a %d %b %H:%M") + "–" + last.strftime("%H:%M") + f" {label}"
    date_format = "%a %d %b %Y %H:%M" if first.year != last.year else "%a %d %b %H:%M"
    def endpoint(value):
        return value.strftime(date_format) + " " + ((ZONE_LABELS.get(key) if same_offset else None) or value.tzname() or key)
    return endpoint(first) + "–" + endpoint(last)


def format_event(event: dict[str, Any], tz=None) -> str:
    name = event.get("name") or event.get("title") or ""
    area = event.get("country")
    if not area and event.get("category") == "crypto":
        assets = "/".join(a.get("symbol") or a.get("id") or "" for a in event.get("assets") or [])
        area = f"{assets} · Global" if assets else "Global"
    bits = [format_when(event, tz), name + (f" ({area})" if area else "")]
    activation = (event.get("crypto") or {}).get("activation_status")
    if activation:
        bits.append(f"activation {activation}")
    environment = (event.get("crypto") or {}).get("environment")
    if environment and not _contains_detail(name, environment):
        bits.append(environment)
    if event.get("time_role") == "auction-close" and not _contains_detail(name, "auction close"):
        bits.append("auction close")
    if event.get("period") and not _contains_detail(name, event["period"]):
        bits.append(f"period {event['period']}")
    if event.get("release_stage") and not _contains_detail(name, event["release_stage"]):
        stage = re.sub(r"[-_]+", " ", str(event["release_stage"]))
        bits.append(f"stage {stage}")
    if event.get("consensus") is not None and event.get("consensus") != "":
        bits.append(f"cons. {event['consensus']}")
    if event.get("prior") is not None and event.get("prior") != "":
        bits.append(f"prior {event['prior']}")
    if event.get("actual") is not None and event.get("actual") != "":
        bits.append(f"actual {event['actual']}")
    if event.get("holiday_status") == "early_close" and event.get("close_time_local"):
        bits.append(f"closes {event['close_time_local']} local")
    line = "  ".join(b for b in bits if b)
    lines = [line]
    if event.get("url"):
        lines.append(event["url"])
    if event.get("data_stale"):
        lines.append("Stale source data" + (f" since {event['stale_since']}" if event.get("stale_since") else ""))
    if event.get("observation_status") == "stale":
        lines.append("Official observation data stale; calendar freshness is reported separately.")
    for observation in event.get("observations") or []:
        if not isinstance(observation, dict):
            continue
        role = observation.get("role") or "value"
        value = str(observation["value"]) if observation.get("value") is not None else "unknown"
        unit = " " + str(observation["unit"]) if observation.get("unit") else ""
        lines.append(f"Official {role}: {value}{unit} · reference period {observation.get('reference_period') or 'unknown'} · current observed vintage")
        if role == "prior":
            lines.append("Prior is the previous reference period at the current observed vintage, not the original first print.")
        if observation.get("data_stale"):
            lines.append(f"Stale official {role} observation; schedule freshness is independent.")
        if observation.get("known_at"):
            lines.append(f"Value observed by Finance Calendar: {observation['known_at']}; not the publisher's first-print timestamp.")
        if observation.get("revision_history"):
            lines.append(f"Recorded value revisions: {len(observation['revision_history'])} (observed by Finance Calendar).")
        if observation.get("source_url"):
            lines.append(f"Observation source: {observation['source_url']}")
        license_info = observation.get("source_license")
        if isinstance(license_info, dict):
            credit = " · " + license_info["attribution"] if license_info.get("attribution") else ""
            lines.append(f"Observation licence: {license_info.get('spdx') or license_info.get('id') or ''}{credit}")
            if license_info.get("url"):
                lines.append(license_info["url"])
            if license_info.get("notice"):
                lines.append(license_info["notice"])
    if event.get("verification_url"):
        lines.append(f"Verification: {event['verification_url']}")
    if event.get("manually_reviewed_at"):
        lines.append(f"Manually reviewed: {event['manually_reviewed_at']}")
    if (event.get("crypto") or {}).get("event_type") == "supply-projection":
        lines.append("Issuer supply projection; not a confirmed unlock or observed circulating supply.")
    if (event.get("crypto") or {}).get("event_type") == "governance-vote":
        lines.append("Governance voting deadline; not a proposal outcome or execution.")
    if event.get("source_license"):
        license_info = event["source_license"]
        adapted = " · adapted by Finance Calendar" if license_info.get("adapted") else ""
        lines.append(f"Original source: {license_info.get('attribution') or event.get('source_name') or ''} · {license_info.get('spdx') or license_info.get('id') or ''}{adapted}")
        if event.get("source_url"):
            lines.append(event["source_url"])
        if license_info.get("attribution_url"):
            lines.append(f"Attribution: {license_info['attribution_url']}")
        if license_info.get("url"):
            lines.append(license_info["url"])
        if license_info.get("terms_url"):
            lines.append(f"Publisher terms: {license_info['terms_url']}")
        if license_info.get("notice"):
            lines.append(license_info["notice"])
    if event.get("source_rights"):
        rights = event["source_rights"]
        lines.append(f"Factual source: {rights.get('attribution') or event.get('source_name') or ''}")
        if event.get("source_url") and not event.get("source_license"):
            lines.append(event["source_url"])
        if rights.get("source_url") and rights["source_url"] != event.get("source_url"):
            lines.append(f"Rights evidence: {rights['source_url']}")
        if rights.get("basis"):
            lines.append(f"Rights basis: {rights['basis']}; not a publisher copyright licence.")
        if rights.get("access_basis"):
            lines.append(f"Source access: {rights['access_basis']}")
        if rights.get("terms_url"):
            lines.append(f"Publisher terms: {rights['terms_url']}")
        if rights.get("notice"):
            lines.append(rights["notice"])
    if event.get("discovery_url"):
        lines.append(f"Discovery (not verification): {event['discovery_url']}")
    return "\n".join(lines)


def _contains_detail(name: str, detail: Any) -> bool:
    def words(value: Any) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()
    normalized = words(detail)
    return bool(normalized and f" {normalized} " in f" {words(name)} ")


def format_events(events: list[dict[str, Any]], tz=None) -> str:
    return "\n".join(format_event(e, tz) for e in events)


def format_holiday(h: dict[str, Any]) -> str:
    status = "closed" if h.get("status") != "early_close" else f"early close {h.get('close_time_local') or h.get('close_time_et') or ''}".strip()
    exch = f"{h['exchange'].upper()}  " if h.get("exchange") else ""
    return f"{h['date']}  {h['name']}  {exch}{status}"


def format_series(s: dict[str, Any]) -> str:
    start, end = s.get("next_date_window_start"), s.get("next_date_window_end")
    if start and end:
        nxt = f"next target {start}–{end} (estimated window)"
    elif start or end:
        nxt = "next target window tbc"
    else:
        nxt = f"next {s['next_date']}" if s.get("next_date") else "next tbc"
    return f"{s['code']:<24} {s.get('name') or '':<44} {s.get('country') or ('Global' if s.get('category') == 'crypto' else '--'):<3} {s.get('impact') or '':<7} {nxt}"


def format_change(c: dict[str, Any]) -> str:
    what = f"  {c['field']}: {c.get('old') or '-'} -> {c.get('new') or '-'}" if c.get("field") else ""
    return f"{c['at']}  {c['change']:<7} {c['series_code']:<16} {c['id']}{what}"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="financecalendar", description="Economic calendar in your terminal. Data: financecalendar.com, free with attribution.")
    p.add_argument("--version", action="version", version=f"financecalendar {__version__}")

    def add_global_options(parser: argparse.ArgumentParser, default: Any) -> None:
        # The top-level parser carries the real defaults; subparsers use SUPPRESS so the
        # options are accepted before or after the command without overwriting each other.
        parser.add_argument("--json", action="store_true", default=default if default is not None else False, help="print the raw API response")
        parser.add_argument("--tz", default=default, help="IANA zone for displayed times (default: your local zone)")
        parser.add_argument("--api-key", default=default, help="API key (default: FC_API_KEY)")
        parser.add_argument("--base-url", default=default, help="API base URL (default: FC_API_BASE or production)")

    add_global_options(p, None)
    common = argparse.ArgumentParser(add_help=False)
    add_global_options(common, argparse.SUPPRESS)
    subparsers = p.add_subparsers(dest="cmd", required=True)

    class _Sub:
        def add_parser(self, name: str, **kw: Any) -> argparse.ArgumentParser:
            return subparsers.add_parser(name, parents=[common], **kw)

    sub = _Sub()

    s = sub.add_parser("next", help="next occurrence of a series")
    s.add_argument("series")
    s.add_argument("--country")
    s.add_argument("--asset", help="canonical crypto asset ID, e.g. ethereum (not ETH)")
    s.add_argument("--category")

    s = sub.add_parser("today", help="today's releases and NYSE status")
    s.add_argument("--country")
    s.add_argument("--asset", help="canonical crypto asset ID, e.g. ethereum (not ETH)")
    s.add_argument("--category")

    s = sub.add_parser("week", help="this week, Monday to Sunday")
    s.add_argument("--next", action="store_true", help="next week instead")
    s.add_argument("--category")
    s.add_argument("--country")
    s.add_argument("--asset", help="canonical crypto asset ID, e.g. ethereum (not ETH)")
    s.add_argument("--impact")
    s.add_argument("--series")

    s = sub.add_parser("calendar", help="events in a date range (max 92 days)")
    s.add_argument("--from", dest="from_")
    s.add_argument("--to")
    s.add_argument("--country")
    s.add_argument("--asset", help="canonical crypto asset ID, e.g. ethereum (not ETH)")
    s.add_argument("--impact")
    s.add_argument("--category")
    s.add_argument("--series")
    s.add_argument("--holidays", action="store_true", help="include exchange holiday rows")
    s.add_argument("--status", help="confirmed, estimated or released; comma-separated")
    s.add_argument("--limit", type=int, help="rows to return, 1 to 500")
    s.add_argument("--offset", type=int, help="skip this many rows (paging)")
    s.add_argument("--csv", action="store_true", help="print the API's CSV")

    s = sub.add_parser("series", help="list every series")
    s.add_argument("--country")
    s.add_argument("--asset", help="canonical crypto asset ID, e.g. ethereum (not ETH)")
    s.add_argument("--category")
    s.add_argument("--kind", choices=["instance", "holiday"])

    s = sub.add_parser("show", help="one series in detail")
    s.add_argument("code")
    s.add_argument("--asset")

    s = sub.add_parser("history", help="past releases of a series")
    s.add_argument("series")
    s.add_argument("--asset")
    s.add_argument("--from", dest="from_")
    s.add_argument("--to")
    s.add_argument("--limit", type=int)

    s = sub.add_parser("holidays", help="exchange holidays")
    s.add_argument("exchange", nargs="?", default="nyse")
    s.add_argument("year", nargs="?", type=int)

    s = sub.add_parser("status", help="is the exchange open right now?")
    s.add_argument("exchange", nargs="?", default="nyse")

    s = sub.add_parser("changes", help="what changed in the calendar")
    s.add_argument("--since")
    s.add_argument("--series")
    s.add_argument("--change", choices=["added", "updated", "removed"])
    s.add_argument("--limit", type=int, help="rows to return, 1 to 500")

    sub.add_parser("countries", help="countries covered")
    sub.add_parser("health", help="API health (snapshot age and counts)")
    return p


def run(args: argparse.Namespace, client: Client, out: Callable[[str], None]) -> int:
    tz = args.tz
    # Resolved on first use, after the request, so an invalid tz sent to the API gets the API's own error.
    zone = functools.lru_cache(maxsize=None)(lambda: local_zone(tz))
    fmt = lambda events: format_events(events, zone())  # noqa: E731
    cmd = args.cmd

    if cmd == "next":
        data = client.next(args.series, country=args.country, asset=args.asset, category=args.category, tz=tz)
        return _emit(args, out, data, lambda: format_event(data["next"], zone()))
    if cmd == "today":
        data = client.today(country=args.country, asset=args.asset, category=args.category, tz=tz)

        def human() -> str:
            lines = []
            m = data.get("market")
            if m:
                lines.append(f"{data['date']}  {m['label']}" + (f" ({m['holiday']})" if m.get("holiday") else ""))
            lines.append(fmt(data["events"]) if data.get("events") else "No scheduled releases today.")
            if data.get("market_holidays"):
                lines += ["", "Exchange closures today:", fmt(data["market_holidays"])]
            return "\n".join(lines)

        return _emit(args, out, data, human)
    if cmd == "week":
        data = client.week("next" if args.next else "this", country=args.country, impact=args.impact, asset=args.asset, category=args.category, series=args.series, tz=tz)
        label = "Next week" if args.next else "This week"
        return _emit(args, out, data, lambda: f"{label}, {data['from']} to {data['to']} ({data.get('total', data['count'])} events)\n\n" + (fmt(data["events"]) if data.get("events") else "No scheduled releases."))
    if cmd == "calendar":
        params = dict(from_=args.from_, to=args.to, country=args.country, impact=args.impact, category=args.category, asset=args.asset, series=args.series, include_holidays=args.holidays, status=args.status, tz=tz, limit=args.limit, offset=args.offset)
        if args.csv:
            out(client.calendar_csv(**params).rstrip("\n"))
            return 0
        data = client.calendar(**params)
        return _emit(args, out, data, lambda: f"{data['from']} to {data['to']}: {data['count']} of {data['total']} events\n\n" + (fmt(data["events"]) if data.get("events") else "No scheduled releases in that range."))
    if cmd == "series":
        data = client.series(country=args.country, category=args.category, asset=args.asset, kind=args.kind)
        return _emit(args, out, data, lambda: "\n".join(format_series(s) for s in data["series"]))
    if cmd == "show":
        data = client.series_detail(args.code, asset=args.asset, tz=tz)

        def human() -> str:
            s = data["series"]
            lines = [f"{s['name']} ({s['code']})  {s.get('country') or ('Global' if s.get('category') == 'crypto' else '')}  {s['category']}  impact {s['impact'] if s['impact'] is not None else 'unrated'}  {s.get('recurrence') or ''}".rstrip()]
            if s.get("aliases"):
                lines.append("aliases: " + ", ".join(s["aliases"]))
            if s.get("publisher"):
                lines.append(f"publisher: {s['publisher']}" + (f"  {s['source_url']}" if s.get("source_url") else ""))
            if s.get("hub"):
                lines.append(f"hub: {s['hub']}")
            lines.append("")
            lines.append("Next:\n" + format_event(data["next"], zone()) if data.get("next") else "Next: none scheduled")
            if data.get("last"):
                lines.append("\nLast:\n" + format_event(data["last"], zone()))
            if len(data.get("upcoming") or []) > 1:
                lines += ["", f"Upcoming ({len(data['upcoming'])}):", fmt(data["upcoming"][:8])]
            return "\n".join(lines)

        return _emit(args, out, data, human)
    if cmd == "history":
        data = client.history(args.series, from_=args.from_, to=args.to, limit=args.limit, asset=args.asset, tz=tz)
        return _emit(args, out, data, lambda: f"{data.get('series_code') or args.series}: {data['count']} releases, {data['from']} to {data['to']}\n\n" + (fmt(data["events"]) if data.get("events") else "No past releases in that range."))
    if cmd == "holidays":
        data = client.holidays(args.exchange, year=args.year)
        return _emit(args, out, data, lambda: f"{data['exchange'].upper()} holidays ({data['count']})\n\n" + "\n".join(format_holiday(h) for h in data["holidays"]))
    if cmd == "status":
        data = client.market_status(args.exchange)

        def human() -> str:
            lines = [f"{data['label']}  ({data.get('local_time') or data.get('time_utc')})"]
            sess = data.get("session")
            if sess:
                lines.append(f"session {sess['open']}-{sess['close']}" + (f" (break {sess['break']})" if sess.get("break") else "") + f" {data.get('tz') or ''}".rstrip())
            if data.get("holiday_today"):
                lines.append(f"holiday today: {data['holiday_today']}")
            nh = data.get("next_holiday")
            if nh:
                lines.append(f"next holiday: {nh['date']}  {nh['name']}  {nh['status']}")
            return "\n".join(lines)

        return _emit(args, out, data, human)
    if cmd == "changes":
        data = client.changes(since=args.since, series=args.series, change=args.change, limit=args.limit)
        return _emit(args, out, data, lambda: f"{data['count']} changes since {data['since']}\n\n" + ("\n".join(format_change(c) for c in data["changes"]) if data.get("changes") else "No changes."))
    if cmd == "countries":
        data = client.countries()
        return _emit(args, out, data, lambda: "\n".join(f"{c['code']}  {c.get('name') or '':<16} {c['series']:>3} series  {c['events']:>5} events" for c in data["countries"]))
    if cmd == "health":
        data = client.status()
        return _emit(args, out, data, lambda: json.dumps(data, indent=2))
    raise SystemExit(f"Unknown command {cmd}")


def _emit(args: argparse.Namespace, out: Callable[[str], None], data: Any, human: Callable[[], str]) -> int:
    out(json.dumps(data, indent=2) if args.json else human())
    return 0


def main(argv: list[str] | None = None, client: Client | None = None, out: Callable[[str], None] = print) -> int:
    args = build_parser().parse_args(argv)
    own = client is None
    client = client or Client(base_url=args.base_url, api_key=args.api_key)
    try:
        return run(args, client, out)
    except FinanceCalendarError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(f"Error: could not reach {client.base_url}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    except ZoneInfoNotFoundError as exc:
        print(f"Error: unknown timezone {exc.args[0] if exc.args else args.tz}; use an IANA name such as Europe/London", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    finally:
        if own:
            client.close()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
