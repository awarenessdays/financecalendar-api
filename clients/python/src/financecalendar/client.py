"""HTTP client for the financecalendar.com API (OpenAPI 3.1, v2)."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator
from urllib.parse import quote

import httpx

__version__ = "0.1.2"

DEFAULT_BASE = "https://www.financecalendar.com/wp-json/fc/v1"
USER_AGENT = f"financecalendar-python/{__version__}"
MAX_RANGE_DAYS = 92
MAX_LIMIT = 500


class FinanceCalendarError(Exception):
    """Raised for any 4xx or 5xx response. Carries the API's `error` text."""

    def __init__(self, status: int, message: str, retry_after: int | None = None):
        self.status = status
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

    def __str__(self) -> str:
        s = f"HTTP {self.status}: {self.message}"
        if self.retry_after is not None:
            s += f" (retry after {self.retry_after}s)"
        return s


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _clean_params(params: dict[str, Any]) -> dict[str, str]:
    """Drop empty values, rename from_ to from, join lists, map booleans."""
    out: dict[str, str] = {}
    for key, value in params.items():
        if value is None or value == "" or value is False:
            continue
        if key == "from_":
            key = "from"
        if key == "include_holidays":
            if value:
                out["include"] = "holidays"
            continue
        if isinstance(value, (list, tuple, set)):
            value = ",".join(str(v) for v in value)
        elif isinstance(value, (date, datetime)):
            value = value.isoformat()
        elif value is True:
            value = "1"
        out[key] = str(value)
    return out


class Client:
    """Client for the financecalendar.com API.

    Args:
        base_url: API root. Defaults to FC_API_BASE or the production URL.
        api_key: Required API key for requests, sent as X-API-Key. Defaults to FC_API_KEY.
        timeout: Request timeout in seconds.
        transport: An httpx transport (used in tests with httpx.MockTransport).
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 20,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = (base_url or os.environ.get("FC_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.api_key = (api_key or os.environ.get("FC_API_KEY") or "").strip() or None
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        self._http = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout, transport=transport)

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transport ---------------------------------------------------------

    def _request(self, path: str, params: dict[str, Any] | None = None, raw: bool = False) -> Any:
        if not self.api_key:
            raise FinanceCalendarError(401, "Finance Calendar requires an API key. Set FC_API_KEY or pass api_key. Starter API access starts at US$9.99/year: https://www.financecalendar.com/pricing/. Optional evaluation: 48 hours from first use, 25 total JSON calendar requests, verified email and one key: https://www.financecalendar.com/account/?trial=1.")
        headers = {"Accept": "text/csv, text/plain, */*"} if raw else None
        response = self._http.get(path, params=_clean_params(params or {}), headers=headers)
        if response.status_code >= 400:
            raise self._error(response)
        return response.text if raw else response.json()

    @staticmethod
    def _error(response: httpx.Response) -> FinanceCalendarError:
        message = ""
        try:
            body = response.json()
            if isinstance(body, dict) and isinstance(body.get("error"), str):
                message = body["error"]
        except ValueError:
            text = response.text.strip()
            message = text if 0 < len(text) < 200 else ""
        if not message:
            message = response.reason_phrase or f"HTTP {response.status_code}"
        retry_after = None
        ra = response.headers.get("Retry-After")
        if ra and ra.isdigit():
            retry_after = int(ra)
        return FinanceCalendarError(response.status_code, message, retry_after)

    # -- calendar ----------------------------------------------------------

    def calendar(self, **params: Any) -> dict[str, Any]:
        """Events in a date range (at most 92 days).

        Keyword arguments mirror the API: from_, to, country, impact, category,
        series, asset (canonical ID), include_holidays, status, tz, limit, offset.
        """
        return self._request("/calendar", params)

    def crypto_calendar(self, asset: str | list[str] | None = None, **params: Any) -> dict[str, Any]:
        """Public crypto events, filtered by canonical asset ID (e.g. ethereum).

        Only publicly redistributable snapshot data is returned. Estimated date
        windows and testnet environments remain explicit in the response.
        """
        return self.calendar(**{**params, "category": "crypto", "asset": asset})

    def calendar_csv(self, **params: Any) -> str:
        """The same range as calendar(), as the API's CSV text."""
        params["format"] = "csv"
        return self._request("/calendar", params, raw=True)

    def iter_calendar(self, from_: str | date, to: str | date, **params: Any) -> Iterator[dict[str, Any]]:
        """Yield every event between from_ and to (inclusive).

        Ranges longer than 92 days are split into consecutive requests and each
        range is paged with offset/limit, so any span works.
        """
        start = _as_date(from_)
        end = _as_date(to)
        if end < start:
            raise ValueError("to must be on or after from_")
        limit = int(params.pop("limit", MAX_LIMIT))
        params.pop("offset", None)
        params.pop("from", None)
        chunk_start = start
        seen: set[str] = set()
        while chunk_start <= end:
            chunk_end = min(chunk_start + timedelta(days=MAX_RANGE_DAYS), end)
            offset = 0
            while True:
                page = self.calendar(from_=chunk_start, to=chunk_end, limit=limit, offset=offset, **params)
                events = page.get("events") or []
                # An estimated date window can overlap consecutive chunks. Its
                # stable ID represents one event, not one event per request.
                for event in events:
                    event_id = event.get("id")
                    if event_id and event_id in seen:
                        continue
                    if event_id:
                        seen.add(event_id)
                    yield event
                offset += len(events)
                total = page.get("total")
                if not events or (total is not None and offset >= total) or len(events) < limit:
                    break
            chunk_start = chunk_end + timedelta(days=1)

    def today(self, country: str | None = None, tz: str | None = None, *, asset: str | None = None, category: str | None = None) -> dict[str, Any]:
        """Today's releases, NYSE status and exchange closures."""
        return self._request("/today", {"country": country, "tz": tz, "asset": asset, "category": category})

    def week(self, which: str = "this", **params: Any) -> dict[str, Any]:
        """This week (Monday to Sunday) or next. Extra params: country, impact, category, asset, series, tz."""
        return self._request("/week", {"which": which, **params})

    def next(self, series: str, country: str | None = None, tz: str | None = None, *, asset: str | None = None, category: str | None = None) -> dict[str, Any]:
        """The next occurrence of a series (fomc, cpi, nfp, ecb, boe, uk-cpi...)."""
        return self._request("/next", {"series": series, "country": country, "tz": tz, "asset": asset, "category": category})

    # -- series ------------------------------------------------------------

    def series(self, **params: Any) -> dict[str, Any]:
        """Every series the API covers. Params: country, category, asset, kind."""
        return self._request("/series", params)

    def series_detail(self, code: str, tz: str | None = None, *, asset: str | None = None) -> dict[str, Any]:
        """One series: next, last, upcoming dates, history and dataset."""
        return self._request(f"/series/{quote(code, safe='')}", {"tz": tz, "asset": asset})

    def history(self, series: str, **params: Any) -> dict[str, Any]:
        """Past releases of a series with consensus, prior and actual. Params: from_, to, limit, asset, tz."""
        return self._request("/history", {"series": series, **params})

    def enrichment_history(self, series: str, **params: Any) -> dict[str, Any]:
        """One page of evidenced economic results from the enrichment ledger.

        Canonical series: us-jolts, us-adp, us-ism-services, us-trade-balance,
        us-cpi, us-nfp, us-ppi, us-retail-sales, us-pce, us-ism-manufacturing,
        us-industrial-production, us-consumer-confidence. Published evidence
        varies by series, provider qualification and server activation.
        Params: from_, to (release dates), limit (1..100), offset (0..999999),
        ledger_cursor and publication_revision. Capture both returned pins on
        the first page and reuse them with the same filters for offset > 0.
        On HTTP 409 restart at offset=0 without the old pins. Selected editions retain exact
        decimal strings and availability/receipt clocks; missing values stay
        null. For accepted provider editions at a cutoff, use enrichment_as_of()
        (REST /enrichment/as-of). This history method does not accept as_of and
        does not establish complete original first-print history. Availability
        follows the server's feature/access gate.
        """
        return self._request("/enrichment/history", {"series": series, **params})

    def enrichment_editions(self, event_id: str, **params: Any) -> dict[str, Any]:
        """One page of immutable accepted editions for a canonical event ID.

        Params: limit (1..100), offset (0..999999), ledger_cursor and
        publication_revision. Follow next_offset with the same event_id and
        both pins returned on the first page; they are required for offset > 0.
        On HTTP 409 restart at offset=0 without the old pins. The provider's available_at and Finance Calendar's
        received_at have distinct meanings. Provider archives are labelled
        separately from engine captures. For accepted provider editions at a
        cutoff, use enrichment_as_of() (REST /enrichment/as-of). This editions
        method does not accept as_of and does not establish complete original
        first-print history.
        """
        return self._request("/enrichment/editions", {"event_id": event_id, **params})

    def enrichment_as_of(self, event_id: str, as_of: str | datetime, basis: str | None = None) -> dict[str, Any]:
        """What the accepted ledger had evidenced for one occurrence by a UTC cutoff.

        as_of is an aware datetime or an ISO instant with seconds and an explicit
        Z or +00:00 offset, not later than now. basis is engine_receipt (default:
        when Finance Calendar received each edition) or provider_availability
        (the evidenced provider time; provider-reported history has none and is
        excluded, never backdated). The view covers provider editions in the
        current canonical publication; official statistical observations are
        outside it. It does not prove customer availability at the cutoff or
        establish complete original first-print history. Available on Starter,
        Build and Scale plans.
        """
        if isinstance(as_of, datetime):
            if as_of.tzinfo is None:
                raise ValueError("as_of needs an explicit timezone")
            as_of = as_of.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return self._request("/enrichment/as-of", {"event_id": event_id, "as_of": as_of, "basis": basis})

    # -- webhooks ----------------------------------------------------------

    def _send(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        if not self.api_key:
            raise FinanceCalendarError(401, "Finance Calendar requires an API key. Set FC_API_KEY or pass api_key.")
        response = self._http.request(method, path, json=body)
        if response.status_code >= 400:
            raise self._error(response)
        return response.json()

    def webhooks(self) -> dict[str, Any]:
        """List this account's webhook subscriptions (secrets masked). Paid plans only."""
        return self._request("/webhooks")

    def create_webhook(self, url: str, events: list[str], series: list[str] | None = None) -> dict[str, Any]:
        """Register a public https destination for the given delivery types.

        events are drawn from result.published, schedule.cancelled,
        schedule.rescheduled, consensus.updated and event.added; series optionally
        restricts deliveries to canonical series codes. The signing secret is
        returned once in subscription.secret: store it, it is masked afterwards.
        Verify X-FC-Webhook-Signature as t=<unix seconds>,v1=HMAC-SHA256(secret,
        t + "." + raw body). At most five subscriptions per account.
        """
        body: dict[str, Any] = {"url": url, "events": list(events)}
        if series:
            body["series"] = list(series)
        return self._send("POST", "/webhooks", body)

    def webhook(self, subscription_id: int) -> dict[str, Any]:
        """One subscription with its 20 most recent deliveries."""
        return self._request(f"/webhooks/{int(subscription_id)}")

    def delete_webhook(self, subscription_id: int) -> dict[str, Any]:
        """Delete a subscription; its pending deliveries are cancelled."""
        return self._send("DELETE", f"/webhooks/{int(subscription_id)}")

    def rotate_webhook_secret(self, subscription_id: int) -> dict[str, Any]:
        """Issue a new signing secret (returned once) and resume a paused subscription."""
        return self._send("POST", f"/webhooks/{int(subscription_id)}/rotate")

    def test_webhook(self, subscription_id: int) -> dict[str, Any]:
        """Queue a webhook.test delivery to the subscription's destination."""
        return self._send("POST", f"/webhooks/{int(subscription_id)}/test")

    # -- markets -----------------------------------------------------------

    def holidays(self, exchange: str = "nyse", year: int | None = None) -> dict[str, Any]:
        """Exchange holidays and early closes."""
        return self._request("/holidays", {"exchange": exchange, "year": year})

    def market_status(self, exchange: str = "nyse") -> dict[str, Any]:
        """Is the exchange open right now?"""
        return self._request("/market-status", {"exchange": exchange})

    # -- changes and meta --------------------------------------------------

    def changes(self, since: str | datetime | None = None, **params: Any) -> dict[str, Any]:
        """One page of changes. Params: series, change, limit, cursor.

        Follow next_cursor while has_more is true. A 409 indicates a changed
        snapshot: restart from the original since and deduplicate; advance the
        checkpoint only after all pages have been read.
        """
        if isinstance(since, datetime):
            since = since.isoformat()
        return self._request("/changes", {"since": since, **params})

    def countries(self) -> dict[str, Any]:
        """Countries covered, with series and event counts."""
        return self._request("/countries")

    def status(self) -> dict[str, Any]:
        """API health: snapshot age and counts."""
        return self._request("/status")

    def quality(self, **params: Any) -> dict[str, Any]:
        """Current snapshot quality, provenance and supported evidence coverage.

        Returns the server's complete nested report. This is an engine-observed
        current snapshot, not historical first-print evidence. This report does
        not accept as_of; use enrichment_as_of() for accepted provider editions
        at a cutoff, a separate scope from current snapshot quality.
        Extra parameters are passed through using the normal API error handling.
        """
        return self._request("/quality", params)

    def observations(self, **params: Any) -> dict[str, Any]:
        """One page of validated current-vintage numerical evidence.

        Params: series, event_id, role, reference_period, limit, offset and
        snapshot_generated_at. Follow next_offset with the same filters and
        snapshot_generated_at; on HTTP 409 restart at offset=0. Nested source
        lineage and engine-observed revisions are preserved. This observations
        method does not accept as_of and does not establish original historical
        first-print evidence. Use enrichment_as_of() for accepted provider
        editions at a cutoff; official statistical observations are outside
        that separate view.
        """
        return self._request("/observations", params)

    def openapi(self) -> dict[str, Any]:
        """The OpenAPI 3.1 document."""
        return self._request("/openapi")


def to_dataframe(events: list[dict[str, Any]] | dict[str, Any]) -> "Any":
    """Turn a list of event rows (or a calendar/history response) into a pandas DataFrame.

    pandas is imported lazily; install it with `python -m pip install pandas` alongside this client.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - exercised via sys.modules patch in tests
        raise ImportError("to_dataframe needs pandas: python -m pip install pandas") from exc
    if isinstance(events, dict):
        events = events.get("events") or []
    frame = pd.DataFrame(list(events))
    if "release_at_utc" in frame.columns:
        frame["release_at_utc"] = pd.to_datetime(frame["release_at_utc"], utc=True, errors="coerce")
    for column in ("date", "date_window_start", "date_window_end"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    if "assets" in frame.columns:
        frame["asset_ids"] = frame["assets"].map(lambda assets: [a["id"] for a in (assets if isinstance(assets, (list, tuple)) else []) if isinstance(a, dict) and "id" in a])
        frame["asset_symbols"] = frame["assets"].map(lambda assets: [a["symbol"] for a in (assets if isinstance(assets, (list, tuple)) else []) if isinstance(a, dict) and "symbol" in a])
    if "crypto" in frame.columns:
        for field in ("event_type", "network", "exchange", "environment", "activation_status"):
            frame[f"crypto_{field}"] = frame["crypto"].map(lambda value: value.get(field) if isinstance(value, dict) else None)
    return frame
