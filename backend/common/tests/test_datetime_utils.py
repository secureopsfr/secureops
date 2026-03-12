"""Tests unitaires pour common.datetime_utils."""

from datetime import UTC

from common.datetime_utils import now_utc


def test_now_utc_returns_timezone_aware() -> None:
    """now_utc retourne un datetime avec tzinfo UTC."""
    dt = now_utc()
    assert dt.tzinfo is not None
    assert dt.tzinfo == UTC


def test_now_utc_returns_datetime() -> None:
    """now_utc retourne un objet datetime."""
    from datetime import datetime

    dt = now_utc()
    assert isinstance(dt, datetime)
