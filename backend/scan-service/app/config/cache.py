"""Configuration du module Cache et performances (roadmap §5.3.1 et §5.3.2).

Cette configuration contrôle :

- les chemins considérés comme sensibles (login, admin, API, etc.) ;
- le nombre maximal de sous-ressources analysées (scripts, CSS, images) ;
- le timeout appliqué aux requêtes HEAD/GET sur les sous-ressources ;
- le pattern des assets immuables (hash dans l'URL) ;
- le max-age recommandé pour ces assets immuables.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class CacheSettings:
    """Configuration pour la vérification Cache et performances.

    Attributes:
        sensitive_paths (tuple[str, ...]): Fragments de chemin utilisés pour identifier une page sensible
            (login, admin, API). La détection se fait par simple appartenance au chemin de l'URL.
        max_sub_resources (int): Nombre maximal de sous-ressources (JS/CSS/images) analysées par page.
        subresource_timeout (float): Timeout en secondes pour chaque requête HEAD/GET sur une sous-ressource.
        immutable_pattern (str): Expression régulière pour reconnaître un asset
            immuable (hash dans le nom).
        immutable_max_age (int): Durée minimale attendue (en secondes) pour le
            max-age d'un asset immuable.
        sensitive_max_age (int): Durée maximale acceptable (en secondes) pour
            une page sensible avant de considérer que le cache est trop
            permissif.
    """

    sensitive_paths: tuple[str, ...]
    max_sub_resources: int
    subresource_timeout: float
    immutable_pattern: str
    immutable_max_age: int
    sensitive_max_age: int


_DEFAULT_SENSITIVE_PATHS: tuple[str, ...] = ("/login", "/admin", "/auth", "/api/")
_DEFAULT_MAX_SUB_RESOURCES = 50
_DEFAULT_SUBRESOURCE_TIMEOUT = 3.0
_DEFAULT_IMMUTABLE_PATTERN = r"\.[a-f0-9]{8,}\.(js|css)$"
_DEFAULT_IMMUTABLE_MAX_AGE = 31536000
_DEFAULT_SENSITIVE_MAX_AGE = 0


@lru_cache(maxsize=1)
def get_cache_settings() -> CacheSettings:
    """Charge la section cache depuis config/settings.yml.

    Returns:
        CacheSettings: Configuration normalisée pour les vérifications cache.
    """
    data = _load_settings_yml()
    raw = data.get("cache") or {}

    sensitive_paths_raw = raw.get("sensitive_paths") or list(_DEFAULT_SENSITIVE_PATHS)
    sensitive_paths = tuple(str(p) for p in sensitive_paths_raw)

    max_sub_resources = int(raw.get("max_sub_resources", _DEFAULT_MAX_SUB_RESOURCES))
    subresource_timeout = float(raw.get("subresource_timeout", _DEFAULT_SUBRESOURCE_TIMEOUT))

    immutable_pattern = str(raw.get("immutable_pattern", _DEFAULT_IMMUTABLE_PATTERN))
    immutable_max_age = int(raw.get("immutable_max_age", _DEFAULT_IMMUTABLE_MAX_AGE))
    sensitive_max_age = int(raw.get("sensitive_max_age", _DEFAULT_SENSITIVE_MAX_AGE))

    return CacheSettings(
        sensitive_paths=sensitive_paths,
        max_sub_resources=max_sub_resources,
        subresource_timeout=subresource_timeout,
        immutable_pattern=immutable_pattern,
        immutable_max_age=immutable_max_age,
        sensitive_max_age=sensitive_max_age,
    )
