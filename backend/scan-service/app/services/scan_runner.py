"""Exécution du scan : étapes métier (TLS, etc.). Les timeouts (get_scan_timeouts) seront utilisés au moment du fetch HTTP."""


async def run_tls_checks(url: str) -> None:
    """Vérifications TLS/HTTPS (roadmap §3.1). Stub : ne fait rien pour l'instant.

    À implémenter : HTTPS activé, redirection HTTP→HTTPS, certificat (valide/expiré/auto-signé),
    version TLS, résumé posture TLS. Utiliser get_scan_timeouts() pour le client HTTP (connexion, lecture).
    """
    pass
