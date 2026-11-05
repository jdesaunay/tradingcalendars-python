# tradingcalendars

Python client for the [TradingCalendars.com](https://tradingcalendars.com) API: **business days,
T+N settlement dates and holidays** for FX markets, currency clearing, bank holidays, payment
systems (TARGET2, Fedwire, CHAPS…) and stock exchanges, including half days and early closes.

- 50 currencies, 69 financial centres, 29 payment systems, 61 exchanges ([coverage](https://tradingcalendars.com/coverage))
- Maintained from official sources, past and future years
- Standard library only, Python 3.9+
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

# T+2 value date for a EUR/USD trade done on 23 December 2026
tc.add_business_days(["USD.FX", "EUR.FX"], "2026-12-23", 2)
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
`business_days_between_details`) returns the full answer, including each skipped day and why.

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
