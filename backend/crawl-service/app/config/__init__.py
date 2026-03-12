"""Réexporte la configuration depuis config_loader (compatibilité)."""

from app.config_loader import (
    CrawlerSettings,
    SsrfSettings,
    UrlValidationSettings,
    get_crawler_settings,
    get_robots_txt_messages,
    get_robots_txt_settings,
    get_ssrf_settings,
    get_url_validation_settings,
)

__all__ = [
    "CrawlerSettings",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_crawler_settings",
    "get_robots_txt_messages",
    "get_robots_txt_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
]
