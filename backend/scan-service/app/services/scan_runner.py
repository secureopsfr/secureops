"""Exécution du scan (client HTTP, timeouts). Pour l'instant : stubs qui utilisent les settings."""

from app.config_loader import get_scan_timeouts


async def run_scan(url: str) -> None:
    """Lance le scan sur l'URL (stub : n'effectue pas encore les requêtes HTTP).

    Lit les timeouts (connexion, lecture, global) depuis les settings pour les
    intégrer au flux. À remplacer par le vrai client HTTP (httpx) plus tard.

    Args:
        url: URL normalisée et validée (SSRF ok).
    """
    get_scan_timeouts()
    # Stub : pas encore de requête HTTP ; url et timeouts seront utilisés plus tard.


async def run_tls_checks(url: str) -> None:
    """Vérifications TLS/HTTPS (roadmap §3.1). Stub : ne fait rien pour l'instant.

    À implémenter : HTTPS activé, redirection HTTP→HTTPS, certificat (valide/expiré/auto-signé),
    version TLS, résumé posture TLS.

    Args:
        url: URL normalisée et validée (SSRF ok).
    """
    pass
