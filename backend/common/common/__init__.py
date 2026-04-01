"""Package commun partagé entre les micro-services.

Seuls les modules légers (pas de dépendances lourdes type sqlalchemy)
sont importés ici.  Les modules optionnels doivent être importés
directement par les services qui en ont besoin :

    from common.async_database import AsyncDatabase
    from common.cognito import REGION, USERPOOL_ID, CLIENT_ID
    from common.jwt_verifier import verify_cognito_jwt
"""

from common.config_base import (
    AppSettings,
    GeneralSettings,
    RoutersSettings,
    SsrfSettings,
    UrlValidationSettings,
    create_load_settings_yml,
    create_simple_settings,
    parse_ssrf_settings,
    parse_url_validation_settings,
)
from common.datetime_utils import now_utc
from common.env_utils import is_prod_env
from common.error_handlers import register_exception_handlers
from common.health import create_health_router
from common.logging_config import get_logger, mask_email, setup_logging
from common.middleware import CorrelationIdMiddleware
from common.schemas import DeleteResponse, ErrorResponse, PaginatedResponse, SuccessResponse, make_pagination_meta
from common.ssrf import check_ssrf, is_hostname_blocked, is_ip_blocked
from common.url_helpers import (
    build_http_url,
    build_https_url,
    build_url_with_path,
    extract_host_from_url,
    extract_port_from_url,
    get_host_from_url,
    get_https_port_from_url,
    get_scan_base_url,
    location_redirects_to_https,
)
from common.url_utils import URLValidationError, normalize_scan_url
from common.url_validator import validate_and_normalize_url
from common.version import get_app_version

__all__ = [
    # config_base
    "AppSettings",
    "GeneralSettings",
    "RoutersSettings",
    "SsrfSettings",
    "UrlValidationSettings",
    "create_load_settings_yml",
    "create_simple_settings",
    "parse_ssrf_settings",
    "parse_url_validation_settings",
    "get_app_version",
    # datetime_utils
    "now_utc",
    # env_utils
    "is_prod_env",
    # error_handlers
    "register_exception_handlers",
    # health
    "create_health_router",
    # logging_config
    "setup_logging",
    "get_logger",
    "mask_email",
    # middleware
    "CorrelationIdMiddleware",
    # schemas
    "DeleteResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "SuccessResponse",
    "make_pagination_meta",
    # url_helpers
    "build_http_url",
    "build_https_url",
    "build_url_with_path",
    "extract_host_from_url",
    "extract_port_from_url",
    "get_host_from_url",
    "get_https_port_from_url",
    "get_scan_base_url",
    "location_redirects_to_https",
    # url_utils
    "URLValidationError",
    "normalize_scan_url",
    # url_validator
    "validate_and_normalize_url",
    # ssrf
    "check_ssrf",
    "is_hostname_blocked",
    "is_ip_blocked",
]
