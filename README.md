# tradingcalendars

Python client for the [TradingCalendars.com](https://tradingcalendars.com) API: **business days,
FX value dates, T+N settlement dates and holidays** for FX markets, currency clearing, bank holidays, payment
systems (TARGET2, Fedwire, CHAPS…) and stock exchanges, including half days and early closes.

- 50 currencies, 69 financial centres, 29 payment systems, 61 exchanges ([coverage](https://tradingcalendars.com/coverage))
- Maintained from official sources, past and future years
- Standard library only, Python 3.10+
- Installs as `tradingcalendars-client`, imports as `tradingcalendars`

## Install

```bash
pip install tradingcalendars-client
```

Get a free API key (a minute, no card): https://tradingcalendars.com/signup?ref=pypi

## Quick start

```python
from tradingcalendars import TradingCalendars

tc = TradingCalendars(api_key="YOUR_API_KEY")   # or set TRADINGCALENDARS_API_KEY

# Spot value date for a EUR/USD trade done on 25 November 2026
tc.fx_value_date("EURUSD", "2026-11-25")
# datetime.date(2026, 11, 27)  -> US Thanksgiving on day 1 does not delay spot (the USD rule)

# T+1 settlement of a NYSE trade done on 24 December 2026
tc.add_business_days("XNYS.SETTLE", "2026-12-24", 1)
# datetime.date(2026, 12, 28)  -> skips Christmas and the weekend

# Is a date open in several calendars at once?
tc.is_business_day(["TARGET2.PAY", "FEDWIRE.PAY"], "2026-12-28")   # True

# Business days between two dates (start counted, end not)
tc.business_days_between(["GBP.FX", "SGD.FX"], "2027-01-01", "2027-02-01")   # 20

# Holidays, with half days and early closes
for h in tc.holidays("XLON.TRADE", start="2026-12-01", end="2026-12-31"):
    print(h.date, h.event, h.early_close_time or "")
# 2026-12-24 Christmas Eve (half day) 12:30
# 2026-12-25 Christmas Day
# 2026-12-28 Boxing Day
# 2026-12-31 New Year's Eve (half day) 12:30

# Is the New York Stock Exchange open right now?
tc.market_status("XNYS")
```

Every `*_details` variant (`add_business_days_details`, `is_business_day_details`,
`business_days_between_details`, `fx_value_date_details`, `adjust_date_details`,
`schedule_details`) returns the full answer, including each skipped day and why.

## FX spot and value dates

`fx_value_date` applies the market's spot conventions for you: T+2 (T+1 for USD/CAD,
USD/TRY and USD/PHP), each currency counting its own business days, the USD rule (a US
holiday before the value date does not delay spot, except against MXN and the South
American currencies), and a cross taking the later of its two spot dates against USD.
It uses each currency's FX market calendar (`EUR.FX`, `USD.FX`…).

```python
tc.fx_value_date("USD/CAD", "2026-12-24")          # datetime.date(2026, 12, 29): T+1 pair
tc.fx_value_date("EURGBP", "2026-11-24")           # datetime.date(2026, 11, 27): Thanksgiving is
                                                   # a US holiday, so not a value date for a cross
tc.fx_value_date("USDMXN", "2026-11-25")           # datetime.date(2026, 11, 30): against the peso,
                                                   # the US holiday counts
tc.fx_value_date("EURUSD", "2026-11-25", tenor="tom")

answer = tc.fx_value_date_details("EURUSD", "2026-11-25")
answer["joint_calendar_date"]   # '2026-11-30': what a plain count on both calendars gives
for day in answer["days"]:
    print(day["date"], day["counted"], day["closed"])
# 2026-11-26 True {'USD': 'Thanksgiving Day'}
# 2026-11-27 True {}
```

Try it without code in the free [FX value date calculator](https://tradingcalendars.com/tools/fx-value-date-calculator).

## Business day conventions and cash-flow schedules

For swaps, bonds and loans: ISDA conventions on joint calendars, and adjusted schedules
with payment and fixing dates. Holidays are stored through 2077, so long-dated trades
don't run out of data.

```python
# Saturday 29 May 2027 under modified following, New York + London
tc.adjust_date(["USNYC.BANK", "GBLON.BANK"], "2027-05-29", "modified_following")
# datetime.date(2027, 5, 28)   (following gives 1 June: 31 May is a holiday in both)

# Quarterly schedule, payment 2 days after each period end, fixing 2 London days before start
for p in tc.schedule(["USD.FX", "GBP.FX"], "2026-11-26", "2027-11-26", frequency="3M",
                     payment_lag=2, fixing_lag=2, fixing_calendars=["GBP.FX"]):
    print(p["start"], p["end"], p["payment_date"], p["fixing_date"], p["accrual_days"])
# 2026-11-27 2027-02-26 2027-03-02 2026-11-25 91   <- 26 Nov 2026 is Thanksgiving
# ...
```

`schedule` also takes `stub` (`short_front`, `long_front`, `short_back`, `long_back`) and
`end_of_month=True`; `schedule_details` returns warnings and data coverage too.

## With pandas or numpy

```python
import pandas as pd

closures = tc.closure_dates("XNYS.TRADE", start="2026-01-01", end="2027-12-31")
nyse_day = pd.offsets.CustomBusinessDay(holidays=closures)
pd.Timestamp("2026-11-25") + 2 * nyse_day   # skips Thanksgiving
```

## Calendar codes

| Family | Code | Example |
| --- | --- | --- |
| FX market | `<ISO 4217>.FX` | `USD.FX`, `EUR.FX` |
| Currency non-clearing days | `<ISO 4217>.CLEAR` | `USD.CLEAR` |
| Bank holidays (financial centre) | `<UN/LOCODE>.BANK` | `GBLON.BANK`, `USNYC.BANK` |
| Payment systems | `<SYSTEM>.PAY` | `TARGET2.PAY`, `FEDWIRE.PAY` |
| Exchange trading | `<MIC>.TRADE` | `XNYS.TRADE`, `XLON.TRADE` |
| Exchange settlement | `<MIC>.SETTLE` | `XNYS.SETTLE` |

`tc.calendars()` lists every code your plan covers. Browse them at
[tradingcalendars.com/coverage](https://tradingcalendars.com/coverage).

## Errors

`AuthenticationError` (401/403), `NotFoundError` (404), `RateLimitError` (429, resets at
midnight UTC) and `TradingCalendarsError` for anything else. Messages come from the API and say
what to do next.

## Also available

- REST API reference: https://tradingcalendars.com/documentation
- MCP server for Claude, ChatGPT and Cursor: https://tradingcalendars.com/mcp
- Calendar subscriptions (Google Calendar, Outlook, Apple): a "Subscribe" box on every
  calendar page, e.g. https://tradingcalendars.com/calendars/XNYS.TRADE

## License

MIT. The data itself is provided under the
[TradingCalendars.com terms](https://tradingcalendars.com/terms-and-conditions).
