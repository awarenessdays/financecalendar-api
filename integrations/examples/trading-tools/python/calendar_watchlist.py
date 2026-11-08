#!/usr/bin/env python3
"""One-shot, cached high-impact calendar watchlist. Python 3.10+, stdlib only."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import sys

OFFICIAL = "https://www.financecalendar.com/wp-json/fc/v1/calendar"
ACCOUNT = "https://www.financecalendar.com/account/"
CACHE_MS = 900_000
BODY_LIMIT = 4 * 1024 * 1024
TOTAL_LIMIT = 8 * 1024 * 1024
ROW_LIMIT = 5000


class Failure(Exception):
    def __init__(self, message, status=None, until=None):
        super().__init__(message)
        self.status, self.until = status, until


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def configuration():
    key = os.environ.get("FC_API_KEY", "").strip()
    if not re.fullmatch(r"fc_live_[a-f0-9]{32}", key):
        raise Failure("Set a valid FC_API_KEY in your private environment. Get a key at " + ACCOUNT)
    endpoint, now, timeout = OFFICIAL, int(time.time() * 1000), 12.0
    # Fixture transport is deliberately restricted to numeric loopback, never an
    # arbitrary credential destination supplied in a command-line argument.
    if os.environ.get("FC_TRADING_TOOLS_TEST_HTTP") == "1":
        endpoint = os.environ.get("FC_TRADING_TOOLS_TEST_URL", "")
        u = urlsplit(endpoint)
        if u.scheme != "http" or u.hostname != "127.0.0.1" or not u.port or u.path != "/calendar" or u.username or u.password or u.query or u.fragment:
            raise Failure("Invalid local test transport.")
        if os.environ.get("FC_TRADING_TOOLS_TEST_NOW"):
            now = int(datetime.fromisoformat(os.environ["FC_TRADING_TOOLS_TEST_NOW"].replace("Z", "+00:00")).timestamp() * 1000)
        timeout = float(os.environ.get("FC_TRADING_TOOLS_TEST_TIMEOUT_MS", "12000")) / 1000
        if not 0.05 <= timeout <= 12:
            raise Failure("Invalid local test timeout.")
    today = datetime.fromtimestamp(now / 1000, timezone.utc).date()
    params = {"from": today.isoformat(), "to": (today + timedelta(days=6)).isoformat(),
              "impact": "high", "status": "confirmed,estimated,rescheduled", "limit": "500"}
    partition = hashlib.sha256(("financecalendar-trading-tools-v1\0" + endpoint + "\0" + key).encode()).hexdigest()
    directory = Path(os.environ.get("FC_CACHE_DIR", str(Path.home() / ".cache/financecalendar-trading-tools")))
    return key, endpoint, now, timeout, params, partition, directory / ("watchlist-" + partition + ".json")


def parse_json(raw):
    def invalid_constant(_):
        raise ValueError("Non-JSON constant")
    return json.loads(raw, parse_constant=invalid_constant)


def read_cache(path, partition):
    try:
        if path.is_symlink() or path.stat().st_size > TOTAL_LIMIT + 65536:
            return None
        value = parse_json(path.read_bytes())
        return value if isinstance(value, dict) and value.get("version") == 1 and value.get("partition") == partition else None
    except (OSError, ValueError, UnicodeError):
        return None


def save_cache(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".watchlist-", delete=False) as f:
            temporary = Path(f.name)
            os.fchmod(f.fileno(), 0o600)
            f.write(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode())
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def retry_until(header, now):
    if header and re.fullmatch(r"\d+", header.strip()):
        seconds = int(header.strip())
        if seconds > 100 * 365 * 86400:
            return None  # Conservative manual stop; never retry sooner than a huge delay.
        return now + max(CACHE_MS, seconds * 1000)
    if header:
        try:
            date = parsedate_to_datetime(header)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(now + CACHE_MS, int(date.timestamp() * 1000))
        except (ValueError, OverflowError, TypeError):
            pass
    return now + CACHE_MS


def status_failure(status, header, now):
    if status in (401, 402, 403):
        return Failure(f"HTTP {status}: access was not accepted. Fix your key/account at {ACCOUNT} then clear this key's cache. Requests are stopped.", status)
    if status == 429:
        until = retry_until(header, now)
        wait = f"at least {max(0, math.ceil((until - now) / 1000))} seconds" if until is not None else "manual review of Retry-After"
        return Failure(f"HTTP 429: wait {wait}. No automatic retry. Check allowance at {ACCOUNT}", status, until)
    return Failure(f"HTTP {status}: calendar request failed; no automatic retry.", status, now + CACHE_MS)


def fetch_calendar(endpoint, key, params, now, timeout):
    events, total, attribution, offset, byte_count = [], None, None, 0, 0
    started = time.monotonic()
    # Keep the fixture clock deterministic while accounting for all page/network
    # delays. A numeric Retry-After begins at receipt, never at run start.
    def received_at():
        return now + math.ceil((time.monotonic() - started) * 1000)

    seen = set()
    opener = build_opener(NoRedirect())
    for _ in range(10):
        url = endpoint + "?" + urlencode({**params, "offset": str(offset)})
        request = Request(url, headers={"X-API-Key": key, "Accept": "application/json",
                                       "User-Agent": "financecalendar-trading-tools/1.0"})
        try:
            with opener.open(request, timeout=timeout) as response:
                if response.status != 200:
                    raise status_failure(response.status, response.headers.get("Retry-After"), received_at())
                raw = response.read(BODY_LIMIT + 1)
        except HTTPError as error:
            raise status_failure(error.code, error.headers.get("Retry-After"), received_at()) from None
        except (URLError, TimeoutError, OSError):
            raise Failure("Calendar connection failed or timed out; no automatic retry.", until=now + CACHE_MS) from None
        if len(raw) > BODY_LIMIT:
            raise Failure("Calendar response exceeded the 4 MiB bound.", until=now + CACHE_MS)
        byte_count += len(raw)
        if byte_count > TOTAL_LIMIT:
            raise Failure("Combined calendar pages exceeded the 8 MiB bound.", until=now + CACHE_MS)
        try:
            page = parse_json(raw)
        except (ValueError, UnicodeError):
            raise Failure("Calendar response was not valid JSON.", until=now + CACHE_MS) from None
        if not isinstance(page, dict) or not isinstance(page.get("events"), list):
            raise Failure("Calendar response had no valid events list.", until=now + CACHE_MS)
        count, page_total = page.get("count"), page.get("total")
        if type(count) is not int or type(page_total) is not int or count != len(page["events"]) or not 0 <= count <= 500 or not 0 <= page_total <= ROW_LIMIT or offset + count > page_total or (count == 0 and offset < page_total) or (total is not None and total != page_total):
            raise Failure("Calendar pagination changed or exceeded its reviewed bound; no partial watchlist returned.", until=now + CACHE_MS)
        if total is None:
            total, attribution = page_total, page.get("attribution")
        for row in page["events"]:
            identifier = row.get("id") if isinstance(row, dict) else None
            if type(identifier) not in (str, int) or not str(identifier) or str(identifier) in seen:
                raise Failure("Calendar event identities changed or were missing; no partial watchlist returned.", until=now + CACHE_MS)
            seen.add(str(identifier)); events.append(row)
        offset += count
        if offset >= total:
            return {"from": params["from"], "to": params["to"], "count": len(events), "total": total,
                    "events": events, "attribution": attribution}
    raise Failure("Calendar exceeded ten pages; no partial watchlist returned.", until=now + CACHE_MS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clear-cache", action="store_true", help="Clear only this key's private cache and stop without making an HTTP request.")
    args = parser.parse_args()
    key, endpoint, now, timeout, params, partition, path = configuration()
    if args.clear_cache:
        path.unlink(missing_ok=True)
        print("Private cache cleared; no API request sent.", file=sys.stderr)
        return
    cache = read_cache(path, partition) or {"version": 1, "partition": partition}
    block = cache.get("block")
    if isinstance(block, dict) and (block.get("until_ms") is None or now < block["until_ms"]):
        raise Failure(str(block.get("message", "Requests are paused; review your account and private cache.")))
    query = urlencode(params)
    hit = cache.get("query") == query and type(cache.get("expires_at_ms")) in (int, float) and now < cache["expires_at_ms"] and isinstance(cache.get("payload"), dict)
    if not hit:
        try:
            payload = fetch_calendar(endpoint, key, params, now, timeout)
        except Failure as error:
            cache["block"] = {"until_ms": error.until, "message": str(error), "status": error.status}
            save_cache(path, cache)
            raise
        cache = {"version": 1, "partition": partition, "query": query, "stored_at_ms": now,
                 "expires_at_ms": now + CACHE_MS, "payload": payload}
        save_cache(path, cache)
    fetched = datetime.fromtimestamp(cache["stored_at_ms"] / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    output = {"source": "Finance Calendar", "fetched_at": fetched,
              "cache": {"state": "cached" if hit else "fresh", "max_age_seconds": CACHE_MS // 1000}, **cache["payload"]}
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except Failure as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    except Exception:
        print("Watchlist could not be read or saved. Check the private cache directory and configuration.", file=sys.stderr)
        raise SystemExit(1)
