"""Errors raised by the client. Messages come from the API and say what to do next."""


class TradingCalendarsError(Exception):
    """Any error answer from the API (status code and message)."""

    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message


class AuthenticationError(TradingCalendarsError):
    """401 missing or invalid API key, or 403 (unconfirmed email, plan does not cover it)."""


class NotFoundError(TradingCalendarsError):
    """404 unknown calendar, currency, exchange or centre."""


class RateLimitError(TradingCalendarsError):
    """429 daily call limit reached; it resets at midnight UTC."""
