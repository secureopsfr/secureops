"""Point d'entrée de configuration (réexporte app.config + settings).

Pour compatibilité : tous les imports depuis app.config_loader restent valides.
Le chargement est découpé dans app.config/ par domaine.
"""

from common.config_base import create_simple_settings

from app.config import (
    DirectoryListingConfig,
    ExposedFileConfig,
    PathCheckConfig,
    ScanTimeoutsSettings,
    ScoringSettings,
    SecurityHeaderConfig,
    SsrfSettings,
    UrlValidationSettings,
    get_directory_listing_max_body,
    get_directory_listing_settings,
    get_exposed_files_max_body,
    get_exposed_files_settings,
    get_exposed_files_severity_upgrade,
    get_robots_txt_settings,
    get_scan_timeouts,
    get_scoring_settings,
    get_security_headers_settings,
    get_ssrf_settings,
    get_tech_fingerprinting_thresholds,
    get_url_validation_settings,
)

settings = create_simple_settings("scan-service", default_port=8012, caller_file=__file__)

__all__ = [
    "DirectoryListingConfig",
    "ExposedFileConfig",
    "PathCheckConfig",
    "ScanTimeoutsSettings",
    "ScoringSettings",
    "SecurityHeaderConfig",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_directory_listing_max_body",
    "get_directory_listing_settings",
    "get_exposed_files_max_body",
    "get_exposed_files_settings",
    "get_exposed_files_severity_upgrade",
    "get_robots_txt_settings",
    "get_tech_fingerprinting_thresholds",
    "get_scoring_settings",
    "get_scan_timeouts",
    "get_security_headers_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
    "settings",
]
