"""HTTP client (standard library only)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, Sequence, Union

from tradingcalendars.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TradingCalendarsError,
)

DEFAULT_BASE_URL = "https://api.tradingcalendars.com/v1"
USER_AGENT = "tradingcalendars-python/0.1.0"

DateLike = Union[date, str]
Calendars = Union[str, Sequence[str]]


def _iso(value: Optional[DateLike]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, date) else str(value)


def _codes(calendars: Calendars) -> str:
    if isinstance(calendars, str):
        return calendars
    return ",".join(calendars)


def _parse_date(value: Optional[str]) -> Optional[date]:
    return date.fromisoformat(value) if value else None


@dataclass(frozen=True)
class Holiday:
    """One holiday row. ``is_half_day`` rows are shortened business days, not closures."""

    date: date
    event: str
    is_half_day: bool = False
    half_day: str = "NONE"
    early_close_time: Optional[str] = None
    is_observed: bool = False
    original_date: Optional[date] = None
    is_estimated: bool = False
    is_bridge: bool = False
    name_local: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    raw: dict = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_api(cls, row: dict) -> "Holiday":
        return cls(
            date=date.fromisoformat(row["date"]),
            event=row.get("event", ""),
            is_half_day=bool(row.get("is_half_day")),
            half_day=row.get("half_day") or "NONE",
            early_close_time=row.get("early_close_time"),
            is_observed=bool(row.get("is_observed")),
            original_date=_parse_date(row.get("original_date")),
            is_estimated=bool(row.get("is_estimated")),
            is_bridge=bool(row.get("is_bridge")),
            name_local=row.get("name_local"),
            source=row.get("source"),
            notes=row.get("notes"),
            raw=row,
        )


class TradingCalendars:
    """Client for https://api.tradingcalendars.com/v1.

    >>> tc = TradingCalendars(api_key="YOUR_API_KEY")  # or set TRADINGCALENDARS_API_KEY
    >>> tc.add_business_days(["USD.FX", "EUR.FX"], "2026-12-23", 2)
    datetime.date(2026, 12, 28)

    Get a free key at https://tradingcalendars.com/signup?ref=pypi
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("TRADINGCALENDARS_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                401,
                "No API key. Pass api_key=... or set TRADINGCALENDARS_API_KEY. "
                "A free key takes a minute: https://tradingcalendars.com/signup?ref=pypi",
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ---- transport -------------------------------------------------------
    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise _error_from(exc) from None

    # ---- business days ---------------------------------------------------
    def is_business_day(self, calendars: Calendars, day: Optional[DateLike] = None) -> bool:
        """True when ``day`` (default today) is open in every calendar given."""
        return bool(self.is_business_day_details(calendars, day)["is_business_day"])

    def is_business_day_details(self, calendars: Calendars, day: Optional[DateLike] = None) -> dict:
        """Full answer, including why each calendar is closed (holiday name, weekend)."""
        return self._get("/is-business-day", {"calendars": _codes(calendars), "date": _iso(day)})

    def add_business_days(self, calendars: Calendars, day: Optional[DateLike], days: int) -> date:
        """Date ``days`` business days after ``day`` (negative goes back). T+2 = 2."""
        return date.fromisoformat(self.add_business_days_details(calendars, day, days)["result"])

    def add_business_days_details(self, calendars: Calendars, day: Optional[DateLike], days: int) -> dict:
        """Full answer, including every skipped day and why."""
        return self._get(
            "/add-business-days",
            {"calendars": _codes(calendars), "date": _iso(day), "days": days},
        )

    def business_days_between(self, calendars: Calendars, start: DateLike, end: DateLike) -> int:
        """Business days from ``start`` (counted) to ``end`` (not counted)."""
        return int(self.business_days_between_details(calendars, start, end)["business_days"])

    def business_days_between_details(self, calendars: Calendars, start: DateLike, end: DateLike) -> dict:
        return self._get(
            "/business-days-between",
            {"calendars": _codes(calendars), "start": _iso(start), "end": _iso(end)},
        )

    # ---- holidays --------------------------------------------------------
    def holidays(
        self,
        calendar: str,
        start: Optional[DateLike] = None,
        end: Optional[DateLike] = None,
    ) -> list:
        """Holidays for one calendar code (e.g. ``XNYS.TRADE``), from ``start`` (default today)."""
        payload = self._get("/holidays", {"calendar": calendar, "start": _iso(start), "end": _iso(end)})
        return [Holiday.from_api(row) for row in payload.get("data", [])]

    def closure_dates(
        self,
        calendar: str,
        start: Optional[DateLike] = None,
        end: Optional[DateLike] = None,
    ) -> list:
        """Full-closure dates only (half days excluded), ready for numpy/pandas business-day
        helpers, e.g. ``pandas.offsets.CustomBusinessDay(holidays=...)``."""
        return [h.date for h in self.holidays(calendar, start, end) if not h.is_half_day]

    def weekends(self, calendar: str) -> dict:
        """Weekend definition in force (ISO weekdays) and its history."""
        return self._get("/weekends", {"calendar": calendar})

    # ---- reference & live ------------------------------------------------
    def calendars(self, calendar_type: Optional[str] = None) -> list:
        """Published calendars your plan covers (``calendar_type`` e.g. ``CURRENCY_FX``)."""
        return self._get("/calendars", {"calendar_type": calendar_type}).get("data", [])

    def market_status(self, market: Optional[str] = None) -> list:
        """Live open / half day / closed status, with next open and close (MIC, e.g. ``XNYS``)."""
        return self._get("/market-status", {"market": market}).get("data", [])


def _error_from(exc: urllib.error.HTTPError) -> TradingCalendarsError:
    try:
        body = json.loads(exc.read().decode("utf-8"))
        message = body.get("detail") if isinstance(body, dict) else str(body)
    except Exception:
        message = exc.reason
    message = str(message or exc.reason)
    if exc.code in (401, 403):
        return AuthenticationError(exc.code, message)
    if exc.code == 404:
        return NotFoundError(exc.code, message)
    if exc.code == 429:
        return RateLimitError(exc.code, message)
    return TradingCalendarsError(exc.code, message)


