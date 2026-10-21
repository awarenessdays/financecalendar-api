"""financecalendar command line: the economic calendar in your terminal."""

from __future__ import annotations

import argparse
import functools
import json
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
    if not event.get("release_at_utc") or event.get("all_day"):
        d = event.get("date")
        if not d:
            return ""
        return datetime.fromisoformat(d).strftime("%a %d %b") + " all day"
    zone = tz or local_zone(None)
    dt = datetime.fromisoformat(event["release_at_utc"].replace("Z", "+00:00")).astimezone(zone)
    name = getattr(zone, "key", None) or ""
    label = ZONE_LABELS.get(name) or dt.tzname() or name
    return dt.strftime("%a %d %b %H:%M") + f" {label}"


def format_event(event: dict[str, Any], tz=None) -> str:
    bits = [format_when(event, tz), f"{event.get('name') or event.get('title')}" + (f" ({event['country']})" if event.get("country") else "")]
    if event.get("consensus"):
        bits.append(f"cons. {event['consensus']}")
    if event.get("prior"):
        bits.append(f"prior {event['prior']}")
    if event.get("actual"):
        bits.append(f"actual {event['actual']}")
    if event.get("holiday_status") == "early_close" and event.get("close_time_local"):
        bits.append(f"closes {event['close_time_local']} local")
    line = "  ".join(b for b in bits if b)
    return f"{line}\n{event['url']}" if event.get("url") else line


def format_events(events: list[dict[str, Any]], tz=None) -> str:
    return "\n".join(format_event(e, tz) for e in events)


def format_holiday(h: dict[str, Any]) -> str:
    status = "closed" if h.get("status") != "early_close" else f"early close {h.get('close_time_local') or h.get('close_time_et') or ''}".strip()
    exch = f"{h['exchange'].upper()}  " if h.get("exchange") else ""
    return f"{h['date']}  {h['name']}  {exch}{status}"


def format_series(s: dict[str, Any]) -> str:
    nxt = f"next {s['next_date']}" if s.get("next_date") else "next tbc"
    return f"{s['code']:<24} {s.get('name') or '':<44} {s.get('country') or '--':<3} {s.get('impact') or '':<7} {nxt}"


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

    s = sub.add_parser("today", help="today's releases and NYSE status")
    s.add_argument("--country")

    s = sub.add_parser("week", help="this week, Monday to Sunday")
    s.add_argument("--next", action="store_true", help="next week instead")
    s.add_argument("--country")
    s.add_argument("--impact")

    s = sub.add_parser("calendar", help="events in a date range (max 92 days)")
    s.add_argument("--from", dest="from_")
    s.add_argument("--to")
    s.add_argument("--country")
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
    s.add_argument("--category")
    s.add_argument("--kind", choices=["instance", "holiday"])

    s = sub.add_parser("show", help="one series in detail")
    s.add_argument("code")

    s = sub.add_parser("history", help="past releases of a series")
    s.add_argument("series")
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
        data = client.next(args.series, country=args.country, tz=tz)
        return _emit(args, out, data, lambda: format_event(data["next"], zone()))
    if cmd == "today":
        data = client.today(country=args.country, tz=tz)

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
        data = client.week("next" if args.next else "this", country=args.country, impact=args.impact, tz=tz)
        label = "Next week" if args.next else "This week"
        return _emit(args, out, data, lambda: f"{label}, {data['from']} to {data['to']} ({data.get('total', data['count'])} events)\n\n" + (fmt(data["events"]) if data.get("events") else "No scheduled releases."))
    if cmd == "calendar":
        params = dict(from_=args.from_, to=args.to, country=args.country, impact=args.impact, category=args.category, series=args.series, include_holidays=args.holidays, status=args.status, tz=tz, limit=args.limit, offset=args.offset)
        if args.csv:
            out(client.calendar_csv(**params).rstrip("\n"))
            return 0
        data = client.calendar(**params)
        return _emit(args, out, data, lambda: f"{data['from']} to {data['to']}: {data['count']} of {data['total']} events\n\n" + (fmt(data["events"]) if data.get("events") else "No scheduled releases in that range."))
    if cmd == "series":
        data = client.series(country=args.country, category=args.category, kind=args.kind)
        return _emit(args, out, data, lambda: "\n".join(format_series(s) for s in data["series"]))
    if cmd == "show":
        data = client.series_detail(args.code, tz=tz)

        def human() -> str:
            s = data["series"]
            lines = [f"{s['name']} ({s['code']})  {s.get('country') or ''}  {s['category']}  impact {s['impact']}  {s.get('recurrence') or ''}".rstrip()]
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
        data = client.history(args.series, from_=args.from_, to=args.to, limit=args.limit, tz=tz)
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
