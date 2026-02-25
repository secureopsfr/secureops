"""Utilitaires de date/heure partagés.

Fournit ``now_utc()`` en remplacement de ``datetime.utcnow()`` (deprecated
depuis Python 3.12).
"""

from __future__ import annotations

from datetime import UTC, datetime


def now_utc() -> datetime:
    """Retourne l'instant courant en UTC (timezone-aware).

    Returns:
        datetime: instant courant avec tzinfo=UTC.
    """
    return datetime.now(UTC)
