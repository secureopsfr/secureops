"""Tests unitaires du scheduler de scans planifiés."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import app.services.scheduled_scan_scheduler as scheduler_module


class _DummySessionContext:
    """Context manager asynchrone minimal pour remplacer get_async_session."""

    def __init__(self, session_obj):
        self._session_obj = session_obj

    async def __aenter__(self):
        return self._session_obj

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio()
async def test_persist_result_passes_scan_type_to_create_scan(monkeypatch) -> None:
    """Le scheduler doit transmettre scan_type à create_scan."""
    captured = {}

    async def fake_get_subscription_by_user_id(session, user_id):  # type: ignore[no-untyped-def]
        return SimpleNamespace(history_retention="30")

    async def fake_create_scan(**kwargs):  # type: ignore[no-untyped-def]
        captured.update(kwargs)
        return SimpleNamespace()

    async def fake_update_next_run_at(session, scan_id, next_run):  # type: ignore[no-untyped-def]
        return None

    def fake_compute_next_run(**kwargs):  # type: ignore[no-untyped-def]
        return datetime.now(UTC)

    monkeypatch.setattr(scheduler_module, "get_subscription_by_user_id", fake_get_subscription_by_user_id)
    monkeypatch.setattr(scheduler_module, "create_scan", fake_create_scan)
    monkeypatch.setattr(scheduler_module, "update_next_run_at", fake_update_next_run_at)
    monkeypatch.setattr(scheduler_module, "compute_next_run", fake_compute_next_run)
    monkeypatch.setattr(
        scheduler_module,
        "get_async_session",
        lambda: _DummySessionContext(SimpleNamespace()),
    )

    scan = SimpleNamespace(
        id="scan-1",
        user_id="user-1",
        url="https://example.com",
        frequency="daily",
        schedule_hour=8,
        schedule_minute=0,
        schedule_day_of_week=None,
        schedule_day_of_month=None,
        timezone="UTC",
        scan_type="backend",
    )
    data = {
        "url": "https://example.com",
        "status": "success",
        "score": 95,
        "findings": [],
        "timestamp": datetime.now(UTC).isoformat(),
        "duration": 1.5,
    }

    await scheduler_module._persist_result_and_schedule_next(scan, data, datetime.now(UTC))

    assert captured["scan_type"] == "backend"
