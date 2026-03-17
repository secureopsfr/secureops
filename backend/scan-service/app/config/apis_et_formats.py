"""Configuration des vérifications APIs et formats.

Référence : docs/verifications/passive/apis-et-formats.md
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_GRAPHQL_PATHS = ("/graphql", "/api/graphql", "/v1/graphql")
_DEFAULT_SWAGGER_PATHS = ("/swagger", "/api-docs", "/openapi.json", "/openapi.yaml", "/swagger.json", "/api-docs.json")
_DEFAULT_API_LIST_PATHS = ("/api/users", "/api/orders", "/api/items", "/api/products", "/api/list")


@dataclass(frozen=True)
class ApisEtFormatsSettings:
    """Paramètres pour les vérifications APIs et formats.

    Attributes:
        graphql_paths: Chemins à tester pour GraphQL introspection.
        swagger_paths: Chemins à tester pour Swagger/OpenAPI.
        api_list_paths: Chemins à tester pour listes REST non paginées.
        unpaginated_list_threshold: Seuil nombre d'éléments pour considérer une liste non paginée.
        compression_min_body_bytes: Seuil minimal (octets) pour émettre finding compression.
    """

    graphql_paths: tuple[str, ...]
    swagger_paths: tuple[str, ...]
    api_list_paths: tuple[str, ...]
    unpaginated_list_threshold: int
    compression_min_body_bytes: int


@lru_cache(maxsize=1)
def get_apis_et_formats_settings() -> ApisEtFormatsSettings:
    """Charge la section apis_et_formats depuis config/settings.yml."""
    data = _load_settings_yml()
    raw = data.get("apis_et_formats") or {}

    graphql_paths = tuple(str(p) for p in raw.get("graphql_paths") or list(_DEFAULT_GRAPHQL_PATHS))
    swagger_paths = tuple(str(p) for p in raw.get("swagger_paths") or list(_DEFAULT_SWAGGER_PATHS))
    api_list_paths = tuple(str(p) for p in raw.get("api_list_paths") or list(_DEFAULT_API_LIST_PATHS))
    unpaginated_list_threshold = int(raw.get("unpaginated_list_threshold", 50))
    compression_min_body_bytes = int(raw.get("compression_min_body_bytes", 1024))

    return ApisEtFormatsSettings(
        graphql_paths=graphql_paths,
        swagger_paths=swagger_paths,
        api_list_paths=api_list_paths,
        unpaginated_list_threshold=unpaginated_list_threshold,
        compression_min_body_bytes=compression_min_body_bytes,
    )
