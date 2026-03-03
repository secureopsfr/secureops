"""Configuration PDF : catégories, libellés i18n, footer (settings.yml)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class PdfCategoryConfig:
    """Configuration des catégories pour le rapport PDF."""

    order: tuple[str, ...]
    checked: tuple[str, ...]
    labels_fr: dict[str, str]
    labels_en: dict[str, str]


@dataclass(frozen=True)
class PdfSettings:
    """Configuration PDF : footer et catégories."""

    footer_url: str
    categories: PdfCategoryConfig


_DEFAULT_ORDER = (
    "tls",
    "headers",
    "cache",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "sitemap",
    "tech_fingerprinting",
    "information_disclosure",
    "cors_cross_origin",
    "other",
)
_DEFAULT_CHECKED = (
    "tls",
    "headers",
    "cache",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "sitemap",
    "tech_fingerprinting",
    "information_disclosure",
    "cors_cross_origin",
)
_DEFAULT_LABELS_FR = {
    "tls": "TLS / HTTPS",
    "headers": "Security Headers",
    "cache": "Cache et performances",
    "cookies": "Cookies",
    "exposed_files": "Fichiers exposés",
    "directory_listing": "Directory listing",
    "robots_txt": "robots.txt",
    "sitemap": "Sitemap",
    "tech_fingerprinting": "Tech fingerprinting",
    "information_disclosure": "Fuites d'information",
    "cors_cross_origin": "CORS et cross-origin",
    "other": "Autres",
}
_DEFAULT_LABELS_EN = {
    "tls": "TLS / HTTPS",
    "headers": "Security Headers",
    "cache": "Cache and performance",
    "cookies": "Cookies",
    "exposed_files": "Exposed files",
    "directory_listing": "Directory listing",
    "robots_txt": "robots.txt",
    "sitemap": "Sitemap",
    "tech_fingerprinting": "Tech fingerprinting",
    "information_disclosure": "Information disclosure",
    "cors_cross_origin": "CORS and cross-origin",
    "other": "Other",
}


@lru_cache(maxsize=1)
def get_pdf_settings() -> PdfSettings:
    """Charge la section pdf depuis config/settings.yml."""
    data = _load_settings_yml()
    p = data.get("pdf") or {}
    footer_url = str(p.get("footer_url") or "https://secureops.example.com")
    cats = p.get("categories") or {}
    order = tuple(cats.get("order") or _DEFAULT_ORDER)
    checked = tuple(cats.get("checked") or _DEFAULT_CHECKED)
    labels_fr = dict(cats.get("labels_fr") or _DEFAULT_LABELS_FR)
    labels_en = dict(cats.get("labels_en") or _DEFAULT_LABELS_EN)
    return PdfSettings(
        footer_url=footer_url,
        categories=PdfCategoryConfig(
            order=order,
            checked=checked,
            labels_fr=labels_fr,
            labels_en=labels_en,
        ),
    )


def get_category_labels(lang: str) -> dict[str, str]:
    """Retourne les libellés de catégories pour la langue donnée."""
    settings = get_pdf_settings()
    return settings.categories.labels_en if lang == "en" else settings.categories.labels_fr
