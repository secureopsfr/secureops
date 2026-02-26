"""Contexte SSL partagé pour le scan (certificats non vérifiés, TLS 1.0+)."""

import ssl


def ssl_context_for_scan() -> ssl.SSLContext:
    """Contexte SSL permissif pour le scan : TLS 1.0+ accepté, pas de vérif. certificat.

    Permet de se connecter aux serveurs avec certificats auto-signés ou invalides,
    et aux serveurs TLS 1.0-only (ex. badssl.com:1010) pour les détecter.

    Returns:
        ssl.SSLContext: Contexte configuré.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx


def ssl_context_for_version_test(min_ver: ssl.TLSVersion, max_ver: ssl.TLSVersion) -> ssl.SSLContext:
    """Contexte SSL pour tester une version TLS spécifique (ex. TLS 1.0 uniquement).

    Args:
        min_ver: Version TLS minimale.
        max_ver: Version TLS maximale.

    Returns:
        ssl.SSLContext: Contexte configuré.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = min_ver
    ctx.maximum_version = max_ver
    return ctx
