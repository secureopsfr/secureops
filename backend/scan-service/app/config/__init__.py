"""Configuration du scan-service, découpée par domaine.

Réexporte toutes les fonctions get_* pour compatibilité avec config_loader.
settings reste dans config_loader (caller_file pour create_simple_settings).
"""

from app.config.cache import CacheSettings, get_cache_settings
from app.config.cookies import CookiesSettings, get_cookies_settings
from app.config.cors_cross_origin import CorsCrossOriginSettings, get_cors_cross_origin_settings
from app.config.external_services import ExternalServicesSettings, get_external_services_settings
from app.config.information_disclosure import InformationDisclosureSettings, get_information_disclosure_max_body, get_information_disclosure_settings
from app.config.integrity import IntegritySettings, get_integrity_settings
from app.config.path_checks import (
    DirectoryListingConfig,
    ExposedFileConfig,
    PathCheckConfig,
    get_directory_listing_max_body,
    get_directory_listing_partial_extensions,
    get_directory_listing_partial_min_links,
    get_directory_listing_sensitive_403_paths,
    get_directory_listing_settings,
    get_exposed_files_max_body,
    get_exposed_files_settings,
    get_exposed_files_severity_upgrade,
)
from app.config.robots_txt import get_robots_txt_settings
from app.config.scoring import ScoringSettings, get_scoring_settings
from app.config.security_headers import SecurityHeaderConfig, get_security_headers_settings
from app.config.sitemap import get_sitemap_fallback_paths
from app.config.ssrf import SsrfSettings, get_ssrf_settings
from app.config.tech_fingerprinting import get_tech_fingerprinting_thresholds
from app.config.timeouts import ScanTimeoutsSettings, get_scan_timeouts
from app.config.url_validation import UrlValidationSettings, get_url_validation_settings

__all__ = [
    "CacheSettings",
    "CorsCrossOriginSettings",
    "CookiesSettings",
    "DirectoryListingConfig",
    "ExternalServicesSettings",
    "ExposedFileConfig",
    "InformationDisclosureSettings",
    "IntegritySettings",
    "PathCheckConfig",
    "ScanTimeoutsSettings",
    "ScoringSettings",
    "SecurityHeaderConfig",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_cache_settings",
    "get_cors_cross_origin_settings",
    "get_directory_listing_max_body",
    "get_directory_listing_partial_extensions",
    "get_directory_listing_partial_min_links",
    "get_directory_listing_settings",
    "get_directory_listing_sensitive_403_paths",
    "get_external_services_settings",
    "get_exposed_files_max_body",
    "get_exposed_files_settings",
    "get_exposed_files_severity_upgrade",
    "get_information_disclosure_max_body",
    "get_information_disclosure_settings",
    "get_integrity_settings",
    "get_robots_txt_settings",
    "get_sitemap_fallback_paths",
    "get_cookies_settings",
    "get_tech_fingerprinting_thresholds",
    "get_scoring_settings",
    "get_scan_timeouts",
    "get_security_headers_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
]
