"""Validation et normalisation des URLs — délègue à common."""

from common.url_utils import URLValidationError  # noqa: F401
from common.url_validator import validate_and_normalize_url as _validate_and_normalize_url

from app.config_loader import get_url_validation_settings


def validate_and_normalize_url(url: str) -> str:
    """Valide l'URL avec la config du crawl-service."""
    return _validate_and_normalize_url(url, get_url_validation_settings())
