"""Utilitaires de validation et normalisation des URLs pour les scans.

Logique centralisée partagée par user-service et scan-service.
Schémas http/https uniquement, pas de credentials.
"""

from urllib.parse import urlparse, urlunparse


class URLValidationError(ValueError):
    """Erreur de validation d'URL (schéma, format)."""

    pass


def _ensure_https_scheme(url_stripped: str) -> tuple[str, str]:
    """Ajoute https:// si pas de schéma. Retourne (url_stripped, scheme)."""
    parsed = urlparse(url_stripped)
    scheme = (parsed.scheme or "").lower()
    if scheme:
        return url_stripped, scheme
    if "://" in url_stripped:
        raise URLValidationError("URL mal formée (schéma invalide).")
    return "https://" + url_stripped, "https"


def _validate_scheme_and_credentials(parsed, scheme: str) -> None:
    """Vérifie schéma autorisé et absence de credentials."""
    if scheme not in ("http", "https"):
        raise URLValidationError(f"Seuls les schémas http et https sont autorisés (reçu: {scheme}).")
    if parsed.username or parsed.password:
        raise URLValidationError("Les credentials dans l'URL (user:pass@host) ne sont pas autorisés.")
    if not parsed.netloc:
        raise URLValidationError("URL sans host (domaine manquant).")


def normalize_scan_url(url: str, max_length: int = 2048) -> str:
    """Normalise l'URL pour un scan : ajoute https:// si pas de schéma, valide le format.

    Garde-fous : schéma http/https uniquement, pas de credentials, netloc requis.

    Args:
        url: Chaîne URL à normaliser.
        max_length: Longueur max (défaut 2048).

    Returns:
        str: URL normalisée (https://example.com/ ou http://...).

    Raises:
        URLValidationError: Si l'URL est invalide.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL vide ou invalide.")
    url_stripped = url.strip()
    if not url_stripped:
        raise URLValidationError("URL vide.")
    if len(url_stripped) > max_length:
        raise URLValidationError(f"URL trop longue (max {max_length} caractères).")

    try:
        parsed = urlparse(url_stripped)
    except Exception as e:
        raise URLValidationError(f"URL mal formée: {e}") from e

    url_stripped, scheme = _ensure_https_scheme(url_stripped)
    parsed = urlparse(url_stripped)
    _validate_scheme_and_credentials(parsed, scheme)

    normalized_netloc = parsed.netloc.lower()
    result = urlunparse((scheme, normalized_netloc, parsed.path or "/", parsed.params, parsed.query, ""))
    if len(result) > max_length:
        raise URLValidationError(f"URL normalisée trop longue (max {max_length} caractères).")
    return result
