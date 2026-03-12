"""Configuration sitemap."""

from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_SITEMAP_FALLBACK_PATHS: tuple[str, ...] = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")


@lru_cache(maxsize=1)
def get_sitemap_fallback_paths() -> tuple[str, ...]:
    """Charge les chemins fallback sitemap depuis config/settings.yml."""
    data = _load_settings_yml()
    section = data.get("sitemap") or {}
    paths = section.get("fallback_paths") or _DEFAULT_SITEMAP_FALLBACK_PATHS
    return tuple(str(p) for p in paths)
