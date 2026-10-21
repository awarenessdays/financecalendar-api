"""HTTP client for the financecalendar.com API (OpenAPI 3.1, v2)."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Iterator
from urllib.parse import quote

import httpx

__version__ = "0.1.0"

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
        api_key: Optional free key, sent as X-API-Key. Defaults to FC_API_KEY.
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
        self.api_key = api_key or os.environ.get("FC_API_KEY") or None
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
        series, include_holidays, status, tz, limit, offset.
        """
        return self._request("/calendar", params)

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
        while chunk_start <= end:
            chunk_end = min(chunk_start + timedelta(days=MAX_RANGE_DAYS), end)
            offset = 0
            while True:
                page = self.calendar(from_=chunk_start, to=chunk_end, limit=limit, offset=offset, **params)
                events = page.get("events") or []
                yield from events
                offset += len(events)
                total = page.get("total")
                if not events or (total is not None and offset >= total) or len(events) < limit:
                    break
            chunk_start = chunk_end + timedelta(days=1)

    def today(self, country: str | None = None, tz: str | None = None) -> dict[str, Any]:
        """Today's releases, NYSE status and exchange closures."""
        return self._request("/today", {"country": country, "tz": tz})

    def week(self, which: str = "this", **params: Any) -> dict[str, Any]:
        """This week (Monday to Sunday) or next. Extra params: country, impact, tz."""
        return self._request("/week", {"which": which, **params})

    def next(self, series: str, country: str | None = None, tz: str | None = None) -> dict[str, Any]:
        """The next occurrence of a series (fomc, cpi, nfp, ecb, boe, uk-cpi...)."""
        return self._request("/next", {"series": series, "country": country, "tz": tz})

    # -- series ------------------------------------------------------------

    def series(self, **params: Any) -> dict[str, Any]:
        """Every series the API covers. Params: country, category, kind."""
        return self._request("/series", params)

    def series_detail(self, code: str, tz: str | None = None) -> dict[str, Any]:
        """One series: next, last, upcoming dates, history and dataset."""
        return self._request(f"/series/{quote(code, safe='')}", {"tz": tz})

    def history(self, series: str, **params: Any) -> dict[str, Any]:
        """Past releases of a series with consensus, prior and actual. Params: from_, to, limit, tz."""
        return self._request("/history", {"series": series, **params})

    # -- markets -----------------------------------------------------------

    def holidays(self, exchange: str = "nyse", year: int | None = None) -> dict[str, Any]:
        """Exchange holidays and early closes."""
        return self._request("/holidays", {"exchange": exchange, "year": year})

    def market_status(self, exchange: str = "nyse") -> dict[str, Any]:
        """Is the exchange open right now?"""
        return self._request("/market-status", {"exchange": exchange})

    # -- changes and meta --------------------------------------------------

    def changes(self, since: str | datetime | None = None, **params: Any) -> dict[str, Any]:
        """What changed since a datetime (default 24 hours ago). Params: series, change, limit."""
        if isinstance(since, datetime):
            since = since.isoformat()
        return self._request("/changes", {"since": since, **params})

    def countries(self) -> dict[str, Any]:
        """Countries covered, with series and event counts."""
        return self._request("/countries")

    def status(self) -> dict[str, Any]:
        """API health: snapshot age and counts."""
        return self._request("/status")

    def openapi(self) -> dict[str, Any]:
        """The OpenAPI 3.1 document."""
        return self._request("/openapi")


def to_dataframe(events: list[dict[str, Any]] | dict[str, Any]) -> "Any":
    """Turn a list of event rows (or a calendar/history response) into a pandas DataFrame.

    pandas is imported lazily; install it with `pip install financecalendar[pandas]`.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - exercised via sys.modules patch in tests
        raise ImportError("to_dataframe needs pandas: pip install financecalendar[pandas]") from exc
    if isinstance(events, dict):
        events = events.get("events") or []
    frame = pd.DataFrame(list(events))
    if "release_at_utc" in frame.columns:
        frame["release_at_utc"] = pd.to_datetime(frame["release_at_utc"], utc=True, errors="coerce")
    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame
