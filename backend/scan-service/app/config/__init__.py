"""Configuration du scan-service, découpée par domaine.

Réexporte toutes les fonctions get_* pour compatibilité avec config_loader.
settings reste dans config_loader (caller_file pour create_simple_settings).
"""

from app.config.path_checks import (
    DirectoryListingConfig,
    ExposedFileConfig,
    PathCheckConfig,
    get_directory_listing_max_body,
    get_directory_listing_settings,
    get_exposed_files_max_body,
    get_exposed_files_settings,
    get_exposed_files_severity_upgrade,
)
from app.config.pdf import PdfSettings, get_pdf_settings
from app.config.robots_txt import get_robots_txt_settings
from app.config.scoring import ScoringSettings, get_scoring_settings
from app.config.security_headers import SecurityHeaderConfig, get_security_headers_settings
from app.config.ssrf import SsrfSettings, get_ssrf_settings
from app.config.timeouts import ScanTimeoutsSettings, get_scan_timeouts
from app.config.url_validation import UrlValidationSettings, get_url_validation_settings

__all__ = [
    "DirectoryListingConfig",
    "ExposedFileConfig",
    "PathCheckConfig",
    "PdfSettings",
    "ScanTimeoutsSettings",
    "ScoringSettings",
    "SecurityHeaderConfig",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_pdf_settings",
    "get_directory_listing_max_body",
    "get_directory_listing_settings",
    "get_exposed_files_max_body",
    "get_exposed_files_settings",
    "get_exposed_files_severity_upgrade",
    "get_robots_txt_settings",
    "get_scoring_settings",
    "get_scan_timeouts",
    "get_security_headers_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
]
