"""Python client for the TradingCalendars.com API.

Business days, settlement dates and holidays for FX, currency clearing,
banks, payment systems and exchanges. Docs: https://tradingcalendars.com/documentation
"""

from tradingcalendars.client import Holiday, TradingCalendars
from tradingcalendars.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TradingCalendarsError,
)

__all__ = [
    "AuthenticationError",
    "Holiday",
    "NotFoundError",
    "RateLimitError",
    "TradingCalendars",
    "TradingCalendarsError",
]
__version__ = "0.1.0"
