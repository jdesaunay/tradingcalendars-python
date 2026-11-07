"""Client tests with the HTTP layer mocked (no network)."""

import io
import json
import urllib.error
import urllib.parse
from datetime import date

import pytest

import tradingcalendars.client as client_module
from tradingcalendars import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TradingCalendars,
)


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def calls(monkeypatch):
    seen = []
    replies = {}

    def fake_urlopen(request, timeout=None):
        url = urllib.parse.urlparse(request.full_url)
        seen.append(
            {
                "path": url.path,
                "query": dict(urllib.parse.parse_qsl(url.query)),
                "auth": request.get_header("Authorization"),
                "agent": request.get_header("User-agent"),
            }
        )
        status, body = replies[url.path]
        if status != 200:
            raise urllib.error.HTTPError(
                request.full_url, status, "error", {}, io.BytesIO(json.dumps(body).encode())
            )
        return _Response(json.dumps(body).encode())

    monkeypatch.setattr(client_module.urllib.request, "urlopen", fake_urlopen)
    return seen, replies


def test_requires_a_key(monkeypatch):
    monkeypatch.delenv("TRADINGCALENDARS_API_KEY", raising=False)
    with pytest.raises(AuthenticationError, match="signup"):
        TradingCalendars()


def test_key_from_environment(monkeypatch):
    monkeypatch.setenv("TRADINGCALENDARS_API_KEY", "tc_env")
    assert TradingCalendars().api_key == "tc_env"


def test_add_business_days(calls):
    seen, replies = calls
    replies["/v1/add-business-days"] = (200, {"result": "2026-12-28", "skipped": []})
    tc = TradingCalendars(api_key="tc_test")
    assert tc.add_business_days(["USD.FX", "EUR.FX"], date(2026, 12, 23), 2) == date(2026, 12, 28)
    assert seen[0]["query"] == {"calendars": "USD.FX,EUR.FX", "date": "2026-12-23", "days": "2"}
    assert seen[0]["auth"] == "Bearer tc_test"
    assert seen[0]["agent"].startswith("tradingcalendars-python/")


def test_is_business_day_and_between(calls):
    _, replies = calls
    replies["/v1/is-business-day"] = (200, {"is_business_day": False})
    replies["/v1/business-days-between"] = (200, {"business_days": 20})
    tc = TradingCalendars(api_key="k")
    assert tc.is_business_day("TARGET2.PAY", "2026-12-25") is False
    assert tc.business_days_between(["GBP.FX", "SGD.FX"], "2027-01-01", "2027-02-01") == 20


def test_holidays_and_closure_dates(calls):
    seen, replies = calls
    replies["/v1/holidays"] = (
        200,
        {
            "meta": {"calendar_code": "XLON.TRADE"},
            "data": [
                {"date": "2026-12-24", "event": "Christmas Eve (half day)", "is_half_day": True,
                 "half_day": "EARLY_CLOSE", "early_close_time": "12:30", "original_date": None},
                {"date": "2026-12-28", "event": "Boxing Day", "is_half_day": False,
                 "is_observed": True, "original_date": "2026-12-26"},
            ],
            "count": 2,
        },
    )
    tc = TradingCalendars(api_key="k")
    rows = tc.holidays("XLON.TRADE", start="2026-12-01", end=date(2026, 12, 31))
    assert seen[0]["query"] == {"calendar": "XLON.TRADE", "start": "2026-12-01", "end": "2026-12-31"}
    assert rows[0].early_close_time == "12:30" and rows[0].is_half_day
    assert rows[1].original_date == date(2026, 12, 26)
    assert tc.closure_dates("XLON.TRADE") == [date(2026, 12, 28)]


def test_none_params_are_not_sent(calls):
    seen, replies = calls
    replies["/v1/market-status"] = (200, {"data": [{"market": "XNYS"}], "count": 1})
    TradingCalendars(api_key="k").market_status()
    assert seen[0]["query"] == {}


@pytest.mark.parametrize(
    "status,error",
    [(401, AuthenticationError), (403, AuthenticationError), (404, NotFoundError), (429, RateLimitError)],
)
def test_errors_carry_the_api_message(calls, status, error):
    _, replies = calls
    replies["/v1/calendars"] = (status, {"detail": "Explained by the API."})
    with pytest.raises(error, match="Explained by the API"):
        TradingCalendars(api_key="k").calendars()


def test_adjust_date_and_schedule(calls):
    seen, replies = calls
    replies["/v1/adjust-date"] = (200, {"adjusted": "2027-05-28", "moved": True})
    replies["/v1/schedule"] = (
        200,
        {
            "periods": [
                {
                    "period": 1,
                    "start_unadjusted": "2026-11-26",
                    "end_unadjusted": "2027-02-26",
                    "start": "2026-11-27",
                    "end": "2027-02-26",
                    "payment_date": "2027-03-02",
                    "fixing_date": "2026-11-25",
                    "accrual_days": 91,
                    "is_stub": False,
                }
            ]
        },
    )
    tc = TradingCalendars(api_key="k")
    assert tc.adjust_date(["USNYC.BANK", "GBLON.BANK"], "2027-05-29", "MF") == date(2027, 5, 28)
    assert seen[-1]["query"] == {
        "calendars": "USNYC.BANK,GBLON.BANK", "date": "2027-05-29", "convention": "MF",
    }
    periods = tc.schedule(
        "USD.FX,GBP.FX", date(2026, 11, 26), "2027-11-26",
        payment_lag=2, fixing_lag=2, fixing_calendars=["GBP.FX"], end_of_month=True,
    )
    assert periods[0]["start"] == date(2026, 11, 27)
    assert periods[0]["payment_date"] == date(2027, 3, 2)
    assert periods[0]["fixing_date"] == date(2026, 11, 25)
    assert periods[0]["accrual_days"] == 91
    query = seen[-1]["query"]
    assert query["start"] == "2026-11-26" and query["end_of_month"] == "true"
    assert query["fixing_calendars"] == "GBP.FX" and query["fixing_lag"] == "2"
    assert query["frequency"] == "3M" and query["convention"] == "modified_following"
