"""Liste noire de domaines : blocage scan/crawl (roadmap 1.6.2).

Vérifie que l'URL ne cible pas un domaine interdit (ex. secureops.fr en prod).
"""

from common.config_base import BlacklistSettings
from common.url_helpers import extract_host_from_url
from common.url_utils import URLValidationError


def is_domain_blacklisted(hostname: str | None, settings: BlacklistSettings) -> bool:
    """Indique si le hostname est dans la liste noire.

    Un domaine "example.com" bloque exactement example.com et tous les
    sous-domaines (www.example.com, app.example.com, etc.).

    Args:
        hostname: Host extrait de l'URL (peut être None).
        settings: Configuration liste noire.

    Returns:
        bool: True si le host est interdit.
    """
    if not hostname:
        return False
    host = hostname.lower().strip()
    for domain in settings.domains:
        domain_clean = domain.lower().strip()
        if not domain_clean:
            continue
        if host == domain_clean:
            return True
        if host.endswith("." + domain_clean):
            return True
    return False


async def check_blacklist(url: str, settings: BlacklistSettings) -> None:
    """Vérifie que l'URL ne cible pas un domaine de la liste noire.

    Args:
        url: URL normalisée (après validate_and_normalize_url).
        settings: Configuration liste noire.

    Raises:
        URLValidationError: Si le host est interdit.
    """
    host = extract_host_from_url(url).strip()
    if is_domain_blacklisted(host, settings):
        raise URLValidationError(
            f"Le domaine {host} est interdit et ne peut pas être scanné. " "Veuillez choisir une autre URL.",
        )
