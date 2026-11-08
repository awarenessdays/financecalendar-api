"""Offline integration tests: execute the real CLIs against numeric loopback."""
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
KEY = "fc_live_" + "a" * 32  # Invented fixture credential, never sent outside loopback.
OTHER_KEY = "fc_live_" + "b" * 32
NOW = "2026-11-08T12:00:00Z"
LANGUAGES = {"python": [sys.executable, str(ROOT / "python/calendar_watchlist.py")],
             "node": ["node", str(ROOT / "node/calendar-watchlist.mjs")]}


def envelope(rows, total=None):
    return {"from": "2026-11-08", "to": "2026-11-14", "count": len(rows),
            "total": len(rows) if total is None else total, "events": rows,
            "attribution": {"text": "Fixture source credit", "url": "https://example.invalid/source"}}


def reply(payload=None, status=200, headers=None, raw=None, delay=0):
    return status, headers or {}, json.dumps(payload).encode() if raw is None else raw, delay


class Examples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("node"):
            raise RuntimeError("Node 20+ is required to test both delivered examples.")
        major = int(subprocess.check_output(["node", "-p", "process.versions.node.split('.')[0]"], text=True).strip())
        if major < 20:
            raise RuntimeError("Node 20+ is required.")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fc-trading-fixtures-")
        self.directory = Path(self.temporary.name)
        self.requests = []
        self.responder = lambda request: reply(envelope([{"id": "one"}]))
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                request = {"path": urlsplit(self.path).path,
                           "query": parse_qs(urlsplit(self.path).query),
                           "key": self.headers.get("X-API-Key")}
                owner.requests.append(request)
                status, headers, body, delay = owner.responder(request)
                time.sleep(delay)
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    for name, value in headers.items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/calendar"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def run_cli(self, language, key=KEY, now=NOW, args=(), **extra):
        env = os.environ.copy()
        for name in tuple(env):
            if name.startswith("FC_"):
                del env[name]
        env.update(FC_API_KEY=key, FC_CACHE_DIR=str(self.directory / language),
                   FC_TRADING_TOOLS_TEST_HTTP="1", FC_TRADING_TOOLS_TEST_URL=self.url,
                   FC_TRADING_TOOLS_TEST_NOW=now)
        env.update(extra)
        result = subprocess.run([*LANGUAGES[language], *args], env=env, text=True,
                                capture_output=True, timeout=8, cwd=ROOT)
        # Error details and JSON must never echo credentials or a response body.
        self.assertNotIn(KEY, result.stdout + result.stderr)
        self.assertNotIn(OTHER_KEY, result.stdout + result.stderr)
        return result

    def clear(self, language):
        shutil.rmtree(self.directory / language, ignore_errors=True)
        self.requests.clear()

    def test_full_records_pagination_private_cache_and_key_change(self):
        special = {"id": "event-0", "time_utc": None, "release_at_utc": None,
                   "time_precision": "unknown", "actual": 0, "consensus": None,
                   "data_stale": True, "stale_since": "2026-11-07T10:00:00Z",
                   "source_url": "https://example.invalid/official", "source_name": "Official source",
                   "source_rights": {"attribution_required": True, "redistribution": "review"},
                   "source_license": {"name": "Fixture terms"},
                   "observations": [{"value": 0, "unit": "percent"}],
                   "release_bundle": {"future_unknown_field": [None, 0, "keep"]}}
        rows = [special] + [{"id": f"event-{i}", "impact": "high"} for i in range(1, 501)]
        self.responder = lambda r: reply(envelope(rows[int(r["query"]["offset"][0]):int(r["query"]["offset"][0]) + 500], 501))
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.clear(language)
                first = self.run_cli(language)
                self.assertEqual(first.returncode, 0, first.stderr)
                data = json.loads(first.stdout)
                self.assertEqual(data["events"], rows)
                self.assertEqual(data["attribution"]["text"], "Fixture source credit")
                self.assertEqual(data["cache"]["state"], "fresh")
                self.assertEqual([r["query"]["offset"] for r in self.requests], [["0"], ["500"]])
                self.assertEqual(self.requests[0]["query"], {"from": ["2026-11-08"], "to": ["2026-11-14"],
                                 "impact": ["high"], "status": ["confirmed,estimated,rescheduled"], "limit": ["500"], "offset": ["0"]})
                cached = self.run_cli(language, now="2026-11-08T12:14:59Z")
                self.assertEqual(json.loads(cached.stdout)["cache"]["state"], "cached")
                self.assertEqual(len(self.requests), 2)
                files = list((self.directory / language).glob("watchlist-*.json"))
                self.assertEqual(len(files), 1)
                self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)
                self.assertNotIn(KEY, files[0].read_text())
                other = self.run_cli(language, key=OTHER_KEY)
                self.assertEqual(other.returncode, 0, other.stderr)
                self.assertEqual(len(self.requests), 4)
                self.assertEqual(self.requests[-1]["key"], OTHER_KEY)
                self.assertEqual(len(list((self.directory / language).glob("watchlist-*.json"))), 2)

    def test_python_and_node_share_the_same_private_cache(self):
        shared = str(self.directory / "shared")
        first = self.run_cli("python", FC_CACHE_DIR=shared)
        second = self.run_cli("node", FC_CACHE_DIR=shared)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["cache"]["state"], "cached")
        self.assertEqual(len(self.requests), 1)

    def test_missing_malformed_key_and_external_test_transport_send_no_http(self):
        for language in LANGUAGES:
            for key in ("", "not-a-key"):
                with self.subTest(language=language, key_present=bool(key)):
                    result = self.run_cli(language, key=key)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("FC_API_KEY", result.stderr)
            result = self.run_cli(language, FC_TRADING_TOOLS_TEST_URL="https://example.invalid/calendar")
            self.assertEqual(result.returncode, 1)
        self.assertEqual(self.requests, [])

    def test_access_errors_stop_persistently_and_clear_cache_does_not_request(self):
        self.responder = lambda r: reply(status=self.status, raw=("private body " + KEY).encode())
        for language in LANGUAGES:
            for status in (401, 402, 403):
                with self.subTest(language=language, status=status):
                    self.clear(language)
                    self.status = status
                    result = self.run_cli(language)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(f"HTTP {status}", result.stderr)
                    self.assertIn("https://www.financecalendar.com/account/", result.stderr)
                    self.assertNotIn("private body", result.stderr)
                    again = self.run_cli(language, now="2026-11-10T13:00:00Z")
                    self.assertEqual(again.returncode, 1)
                    self.assertEqual(len(self.requests), 1)
                    cleared = self.run_cli(language, args=["--clear-cache"])
                    self.assertEqual(cleared.returncode, 0)
                    self.assertEqual(len(self.requests), 1)

    def test_429_retry_after_seconds_and_date_not_retried_early(self):
        for language in LANGUAGES:
            for retry in ("3600", format_datetime(datetime(2026, 11, 8, 13, tzinfo=timezone.utc), usegmt=True)):
                with self.subTest(language=language, retry_kind="seconds" if retry.isdigit() else "HTTP-date"):
                    self.clear(language)
                    self.responder = lambda r: reply(status=429, headers={"Retry-After": retry}, raw=b"do not print this body")
                    result = self.run_cli(language)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("3600 seconds", result.stderr)
                    self.assertEqual(len(self.requests), 1)
                    again = self.run_cli(language, now="2026-11-08T12:30:00Z")
                    self.assertEqual(again.returncode, 1)
                    self.assertEqual(len(self.requests), 1)
                    self.responder = lambda r: reply(envelope([]))
                    ready = self.run_cli(language, now="2026-11-08T13:00:01Z")
                    self.assertEqual(ready.returncode, 0, ready.stderr)
                    self.assertEqual(len(self.requests), 2)

    def test_malformed_json_and_other_http_errors_return_no_body(self):
        for language in LANGUAGES:
            for response, expected in ((reply(raw=("invalid " + KEY).encode()), "not valid JSON"),
                                       (reply(status=500, raw=("internal " + KEY).encode()), "HTTP 500")):
                with self.subTest(language=language, error=expected):
                    self.clear(language)
                    self.responder = lambda r: response
                    result = self.run_cli(language)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(expected, result.stderr)
                    self.assertEqual(len(self.requests), 1)

    def test_delayed_429_wait_starts_at_receipt_including_earlier_pages(self):
        logical_start = int(datetime(2026, 11, 8, 12, tzinfo=timezone.utc).timestamp() * 1000)
        for language in LANGUAGES:
            for retry in ("3600", "5"):
                with self.subTest(language=language, retry_seconds=retry):
                    self.clear(language)
                    def responder(request):
                        if request["query"]["offset"] == ["0"]:
                            return reply(envelope([{"id": "first"}], 2), delay=0.12)
                        return reply(status=429, headers={"Retry-After": retry}, raw=b"", delay=0.22)
                    self.responder = responder
                    result = self.run_cli(language)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("HTTP 429", result.stderr)
                    self.assertEqual(len(self.requests), 2)
                    files = list((self.directory / language).glob("watchlist-*.json"))
                    cached = json.loads(files[0].read_text())
                    until = cached["block"]["until_ms"]
                    self.assertGreaterEqual(until, logical_start + 340 + max(900000, int(retry) * 1000))
                    # Just before this stored receipt-based deadline: no request.
                    before = datetime.fromtimestamp((until - 1) / 1000, timezone.utc).isoformat()
                    again = self.run_cli(language, now=before)
                    self.assertEqual(again.returncode, 1)
                    self.assertEqual(len(self.requests), 2)
                    # Once it has passed, a new invocation may fetch successfully.
                    self.responder = lambda r: reply(envelope([]))
                    after = datetime.fromtimestamp((until + 1) / 1000, timezone.utc).isoformat()
                    ready = self.run_cli(language, now=after)
                    self.assertEqual(ready.returncode, 0, ready.stderr)
                    self.assertEqual(len(self.requests), 3)

    def test_timeout_is_bounded(self):
        self.responder = lambda r: reply(envelope([]), delay=0.5)
        for language in LANGUAGES:
            with self.subTest(language=language):
                started = time.monotonic()
                result = self.run_cli(language, FC_TRADING_TOOLS_TEST_TIMEOUT_MS="100")
                self.assertEqual(result.returncode, 1)
                self.assertIn("timed out", result.stderr)
                self.assertLess(time.monotonic() - started, 3)

    def test_response_size_bound(self):
        self.responder = lambda r: reply(raw=b"x" * (4 * 1024 * 1024 + 1))
        for language in LANGUAGES:
            with self.subTest(language=language):
                result = self.run_cli(language)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn("4 MiB bound", result.stderr)

    def test_changed_total_duplicate_id_and_excess_total_never_return_partial(self):
        for language in LANGUAGES:
            for kind in ("changed", "duplicate", "excess"):
                with self.subTest(language=language, kind=kind):
                    self.clear(language)
                    def responder(request):
                        if kind == "excess":
                            return reply(envelope([], 5001))
                        if request["query"]["offset"] == ["0"]:
                            return reply(envelope([{"id": "one"}], 2))
                        return reply(envelope([{"id": "one" if kind == "duplicate" else "two"}], 2 if kind == "duplicate" else 3))
                    self.responder = responder
                    result = self.run_cli(language)
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("no partial watchlist", result.stderr)

    def test_redirect_is_not_followed(self):
        self.responder = lambda r: reply(status=302, headers={"Location": self.url + "?redirected=1"}, raw=b"")
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.clear(language)
                result = self.run_cli(language)
                self.assertEqual(result.returncode, 1)
                self.assertIn("HTTP 302", result.stderr)
                self.assertEqual(len(self.requests), 1)

    def test_metatrader_sources_match_and_are_manual_only(self):
        four = (ROOT / "metatrader/FinanceCalendarFetch.mq4").read_text()
        five = (ROOT / "metatrader/FinanceCalendarFetch.mq5").read_text()
        self.assertEqual(four, five)
        self.assertIn('WebRequest("GET", url, headers, 12000, request, response, response_headers)', four)
        self.assertIn("void OnStart()", four)
        self.assertNotIn("OrderSend", four)
        self.assertNotIn("EventSetTimer", four)
        self.assertNotIn("FILE_COMMON", four)


if __name__ == "__main__":
    unittest.main()
