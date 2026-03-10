"""Validation et normalisation des URLs avec vérification des ports.

Unifie la logique de scan-service et crawl-service :
- Délègue à url_utils.normalize_scan_url pour schéma, credentials, netloc.
- Ajoute la validation des ports (config) en mode production uniquement.
"""

from urllib.parse import urlparse

from common.config_base import UrlValidationSettings
from common.env_utils import is_prod_env
from common.url_utils import URLValidationError, normalize_scan_url


def validate_and_normalize_url(url: str, settings: UrlValidationSettings) -> str:
    """Valide l'URL et retourne une forme normalisée.

    Utilise common.url_utils pour schéma, credentials, netloc. Ajoute
    la validation des ports en mode production uniquement.

    Args:
        url: Chaîne URL à valider.
        settings: Configuration (max_url_length, allowed_ports).

    Returns:
        str: URL normalisée.

    Raises:
        URLValidationError: Si l'URL est invalide.
    """
    normalized = normalize_scan_url(url, max_length=settings.max_url_length)

    parsed = urlparse(normalized)
    if is_prod_env() and parsed.port is not None and parsed.port not in settings.allowed_ports:
        ports_str = ", ".join(str(p) for p in sorted(settings.allowed_ports))
        raise URLValidationError(f"Seuls les ports {ports_str} sont autorisés.")

    return normalized
