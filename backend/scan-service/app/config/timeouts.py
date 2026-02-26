"""Configuration des timeouts (roadmap §2.3)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class ScanTimeoutsSettings:
    """Timeouts pour le scan HTTP."""

    connection: float
    read: float
    scan_global: float


_DEFAULT_CONNECTION = 3.0
_DEFAULT_READ = 10.0
_DEFAULT_GLOBAL = 60.0


@lru_cache(maxsize=1)
def get_scan_timeouts() -> ScanTimeoutsSettings:
    """Charge la section timeouts depuis config/settings.yml."""
    data = _load_settings_yml()
    t = data.get("timeouts") or {}
    return ScanTimeoutsSettings(
        connection=float(t.get("connection", _DEFAULT_CONNECTION)),
        read=float(t.get("read", _DEFAULT_READ)),
        scan_global=float(t.get("scan_global", _DEFAULT_GLOBAL)),
    )
