"""Contexte SSL partagé pour le crawl (certificats non vérifiés)."""

import ssl


def ssl_context_for_scan() -> ssl.SSLContext:
    """Contexte SSL permissif pour le crawl : TLS 1.0+ accepté, pas de vérif. certificat."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx
