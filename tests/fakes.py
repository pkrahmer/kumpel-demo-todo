"""Test values shared by the test modules."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

T0 = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)


def ticking_clock() -> Callable[[], datetime]:
    """Return a clock that is one minute past the previous time, starting at T0 plus a minute."""
    ticks = 0

    def clock() -> datetime:
        nonlocal ticks
        ticks += 1
        return T0 + timedelta(minutes=ticks)

    return clock
