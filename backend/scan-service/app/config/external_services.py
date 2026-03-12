"""Configuration des services externes appelés par scan-service."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_GATEWAY_URL = "http://localhost:8000"
_DEFAULT_PDF_SERVICE_URL = "http://localhost:8013"
_DEFAULT_FETCH_SCAN_TIMEOUT = 10.0
_DEFAULT_PDF_REQUEST_TIMEOUT = 60.0
_DEFAULT_SAVE_TIMEOUT = 15.0


@dataclass(frozen=True)
class ExternalServicesSettings:
    """Paramètres d'appel vers gateway et pdf-service."""

    gateway_url: str
    pdf_service_url: str
    fetch_scan_timeout: float
    pdf_request_timeout: float
    save_timeout: float


@lru_cache(maxsize=1)
def get_external_services_settings() -> ExternalServicesSettings:
    """Charge la section external_services depuis config/settings.yml."""
    data = _load_settings_yml()
    e = data.get("external_services") or {}
    return ExternalServicesSettings(
        gateway_url=str(e.get("gateway_url", _DEFAULT_GATEWAY_URL)),
        pdf_service_url=str(e.get("pdf_service_url", _DEFAULT_PDF_SERVICE_URL)),
        fetch_scan_timeout=float(e.get("fetch_scan_timeout", _DEFAULT_FETCH_SCAN_TIMEOUT)),
        pdf_request_timeout=float(e.get("pdf_request_timeout", _DEFAULT_PDF_REQUEST_TIMEOUT)),
        save_timeout=float(e.get("save_timeout", _DEFAULT_SAVE_TIMEOUT)),
    )
