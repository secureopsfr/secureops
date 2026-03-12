"""Tests unitaires des utilitaires de planification des scans."""

from datetime import datetime, timezone

import pytest

from app.services.scheduled_scan_utils import compute_next_run


def test_compute_next_run_daily_valid_timezone() -> None:
    """Calcule une prochaine exécution timezone-aware avec fuseau valide."""
    now = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
    next_run = compute_next_run(
        from_dt=now,
        frequency="daily",
        schedule_hour=12,
        schedule_minute=0,
        timezone_name="Europe/Paris",
    )

    assert next_run.tzinfo is not None


def test_compute_next_run_raises_on_invalid_timezone() -> None:
    """Doit lever ValueError si le fuseau horaire est invalide."""
    now = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="Fuseau horaire invalide"):
        compute_next_run(
            from_dt=now,
            frequency="daily",
            schedule_hour=12,
            schedule_minute=0,
            timezone_name="Invalid/Timezone",
        )
