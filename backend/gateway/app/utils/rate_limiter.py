"""Rate limiter en mémoire à fenêtre fixe (single-instance MVP).

NOTE : non partagé entre plusieurs replicas. Acceptable pour un déploiement
single-instance. Pour multi-replica, migrer vers PostgreSQL ou Redis.
"""

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _Window:
    count: int = 0
    window_start: float = field(default_factory=time.monotonic)


class InMemoryRateLimiter:
    """Limiteur de débit à fenêtre fixe, thread-safe, sans dépendance externe."""

    def __init__(self) -> None:
        """Initialise le limiteur de débit en mémoire."""
        self._windows: dict[str, _Window] = {}
        self._lock = Lock()

    def is_allowed(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Vérifie si la requête est autorisée et incrémente le compteur.

        Args:
            key: Clé de rate limiting (ex: "user:<id>:POST:/scan/api/scan/async").
            limit: Nombre max de requêtes dans la fenêtre.
            window_seconds: Durée de la fenêtre en secondes.

        Returns:
            (allowed, retry_after_seconds) — retry_after=0 si autorisé.
        """
        now = time.monotonic()
        with self._lock:
            window = self._windows.get(key)
            if window is None or (now - window.window_start) >= window_seconds:
                self._windows[key] = _Window(count=1, window_start=now)
                return True, 0
            if window.count >= limit:
                retry_after = int(window_seconds - (now - window.window_start)) + 1
                return False, retry_after
            window.count += 1
            return True, 0

    def cleanup(self, max_age_seconds: int = 300) -> None:
        """Supprime les fenêtres expirées pour éviter les fuites mémoire."""
        now = time.monotonic()
        with self._lock:
            stale = [k for k, w in self._windows.items() if (now - w.window_start) > max_age_seconds]
            for k in stale:
                del self._windows[k]


_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    """Retourne l'instance singleton du rate limiter."""
    return _limiter
