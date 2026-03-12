"""Configuration du scan multi-URL.

Les valeurs sont définies dans config/settings.yml, section ``multi_scan``.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class MultiScanSettings:
    """Paramètres du scan multi-URL.

    Attributes:
        max_urls: Nombre maximum d'URLs par scan (toutes valeurs de plan confondues).
        concurrent_pages: Nombre maximum de pages analysées simultanément (semaphore).
        page_timeout: Timeout GET par page en secondes.
    """

    max_urls: int
    concurrent_pages: int
    page_timeout: float


@lru_cache(maxsize=1)
def get_multi_scan_settings() -> MultiScanSettings:
    """Charge la section ``multi_scan`` depuis config/settings.yml."""
    data = _load_settings_yml()
    ms: dict = data.get("multi_scan") or {}
    if not ms:
        raise RuntimeError(
            "Section 'multi_scan' absente de config/settings.yml. " "Ajoutez-la avec les clés max_urls, concurrent_pages et page_timeout."
        )
    return MultiScanSettings(
        max_urls=int(ms["max_urls"]),
        concurrent_pages=int(ms["concurrent_pages"]),
        page_timeout=float(ms["page_timeout"]),
    )
