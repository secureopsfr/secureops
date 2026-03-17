"""Configuration des vérifications d'intégrité et de sous-ressources.

Cette section couvre les paramètres utilisés par le module
``app.services.integrity.checks`` pour :

- limiter la taille maximale du corps HTML analysé ;
- définir les chemins considérés comme « pages sensibles » pour les meta robots.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_CSRF_FIELD_NAMES = (
    "csrf_token",
    "_token",
    "authenticity_token",
    "_csrf",
    "csrf",
    "__RequestVerificationToken",
    "CSRFToken",
)


@dataclass(frozen=True)
class IntegritySettings:
    """Paramètres pour les vérifications d'intégrité et de sous-ressources.

    Attributes:
        max_body_bytes (int): Nombre maximal d'octets de HTML à analyser.
        sensitive_paths (tuple[str, ...]): Chemins considérés comme sensibles
            (login, admin, API, etc.) pour l'analyse des meta robots.
        csrf_field_names (tuple[str, ...]): Noms de champs hidden considérés
            comme token CSRF dans les formulaires POST.
    """

    max_body_bytes: int
    sensitive_paths: tuple[str, ...]
    csrf_field_names: tuple[str, ...]


@lru_cache(maxsize=1)
def get_integrity_settings() -> IntegritySettings:
    """Charge la section integrity depuis ``config/settings.yml``.

    Returns:
        IntegritySettings: Paramètres normalisés pour les checks intégrité.
    """
    data = _load_settings_yml()
    raw = data.get("integrity") or {}
    max_body_bytes = int(raw.get("max_body_bytes") or 524_288)
    raw_paths = raw.get("sensitive_paths") or [
        "/login",
        "/admin",
        "/auth",
        "/api/",
    ]
    sensitive_paths = tuple(str(p) for p in raw_paths)
    raw_csrf = raw.get("csrf_field_names") or list(_DEFAULT_CSRF_FIELD_NAMES)
    csrf_field_names = tuple(str(n).strip().lower() for n in raw_csrf if str(n).strip())
    return IntegritySettings(
        max_body_bytes=max_body_bytes,
        sensitive_paths=sensitive_paths,
        csrf_field_names=csrf_field_names or _DEFAULT_CSRF_FIELD_NAMES,
    )
