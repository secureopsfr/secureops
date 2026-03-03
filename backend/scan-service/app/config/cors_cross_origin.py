"""Configuration du module CORS et cross-origin (roadmap §5.4).

Contrôle :
- les chemins sensibles à tester en plus de la page principale (requêtes GET/OPTIONS avec Origin) ;
- l'origine fictive utilisée pour détecter la réflexion d'origine non validée ;
- les en-têtes considérés sensibles si exposés via Access-Control-Expose-Headers ;
- la limite de sous-ressources pour la détection du mixed content.
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class CorsCrossOriginSettings:
    """Configuration pour les vérifications CORS et cross-origin.

    Attributes:
        sensitive_paths: Fragments de chemin à tester en plus de la page principale
            (base_url + path). Ex. /api/, /user/, /admin/.
        test_origin: Origine fictive envoyée dans les requêtes (ex. https://evil.example.com)
            pour détecter une réflexion d'origine non validée.
        expose_headers_sensitive: Noms d'en-têtes considérés sensibles si présents
            dans Access-Control-Expose-Headers.
        max_sub_resources: Nombre maximal de sous-ressources analysées pour mixed content.
        subresource_timeout: Timeout (s) pour les requêtes sur sous-ressources.
    """

    sensitive_paths: tuple[str, ...]
    test_origin: str
    expose_headers_sensitive: tuple[str, ...]
    max_sub_resources: int
    subresource_timeout: float


_DEFAULT_SENSITIVE_PATHS: tuple[str, ...] = ("/api/", "/user/", "/admin/", "/auth/", "/login")
_DEFAULT_TEST_ORIGIN = "https://evil.example.com"
_DEFAULT_EXPOSE_HEADERS_SENSITIVE: tuple[str, ...] = ("X-Auth-Token", "X-Request-ID", "Authorization")
_DEFAULT_MAX_SUB_RESOURCES = 50
_DEFAULT_SUBRESOURCE_TIMEOUT = 3.0


@lru_cache(maxsize=1)
def get_cors_cross_origin_settings() -> CorsCrossOriginSettings:
    """Charge la section cors_cross_origin depuis config/settings.yml.

    Returns:
        CorsCrossOriginSettings: Configuration normalisée.
    """
    data = _load_settings_yml()
    raw = data.get("cors_cross_origin") or {}

    sensitive_paths_raw = raw.get("sensitive_paths") or list(_DEFAULT_SENSITIVE_PATHS)
    sensitive_paths = tuple(str(p) for p in sensitive_paths_raw)

    test_origin = str(raw.get("test_origin", _DEFAULT_TEST_ORIGIN))
    expose_raw = raw.get("expose_headers_sensitive") or list(_DEFAULT_EXPOSE_HEADERS_SENSITIVE)
    expose_headers_sensitive = tuple(str(h) for h in expose_raw)

    max_sub_resources = int(raw.get("max_sub_resources", _DEFAULT_MAX_SUB_RESOURCES))
    subresource_timeout = float(raw.get("subresource_timeout", _DEFAULT_SUBRESOURCE_TIMEOUT))

    return CorsCrossOriginSettings(
        sensitive_paths=sensitive_paths,
        test_origin=test_origin,
        expose_headers_sensitive=expose_headers_sensitive,
        max_sub_resources=max_sub_resources,
        subresource_timeout=subresource_timeout,
    )
