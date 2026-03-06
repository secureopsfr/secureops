"""Package commun partagé entre les micro-services.

Seuls les modules légers (pas de dépendances lourdes type sqlalchemy)
sont importés ici.  Les modules optionnels doivent être importés
directement par les services qui en ont besoin :

    from common.async_database import AsyncDatabase
    from common.cognito import REGION, USERPOOL_ID, CLIENT_ID
    from common.jwt_verifier import verify_cognito_jwt
"""

from common.config_base import AppSettings, GeneralSettings, RoutersSettings, create_simple_settings
from common.version import get_app_version
from common.datetime_utils import now_utc
from common.error_handlers import register_exception_handlers
from common.health import create_health_router
from common.logging_config import get_logger, mask_email, setup_logging
from common.middleware import CorrelationIdMiddleware
from common.schemas import DeleteResponse, ErrorResponse, PaginatedResponse, SuccessResponse
from common.url_utils import URLValidationError, normalize_scan_url

__all__ = [
    # config_base
    "AppSettings",
    "GeneralSettings",
    "RoutersSettings",
    "create_simple_settings",
    "get_app_version",
    # datetime_utils
    "now_utc",
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
    # url_utils
    "URLValidationError",
    "normalize_scan_url",
]
