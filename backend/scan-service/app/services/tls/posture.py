"""Calcul de la posture TLS : synthèse lisible (OK / avertissements / critique).

Permet une lecture rapide sans entrer dans le détail de chaque check.
"""

from app.services.tls.checks import TlsCheckResult

# Seuils pour la posture
POSTURE_OK = "ok"
POSTURE_WARNING = "warning"
POSTURE_CRITICAL = "critical"


def compute_tls_posture(result: TlsCheckResult) -> str:
    """Calcule la posture TLS à partir du résultat des vérifications.

    Critères :
    - Critical : HTTPS désactivé, pas de redirection, certificat expiré/auto-signé,
      TLS 1.0/1.1, connexion impossible.
    - Warning : certificat expire bientôt (< 30 jours), chaîne incomplète (à venir).
    - OK : tout conforme.

    Args:
        result: Résultat des vérifications TLS (TlsCheckResult).

    Returns:
        str: "ok", "warning" ou "critical".
    """
    if not result.fetch_ok or not result.https_enabled:
        return POSTURE_CRITICAL

    if result.http_redirects_to_https is False:
        return POSTURE_CRITICAL

    cert_status = result.certificate_status
    if cert_status in ("expired", "self_signed", "not_yet_valid"):
        return POSTURE_CRITICAL

    if len(result.tls_versions_obsolete) > 0:
        return POSTURE_CRITICAL

    if cert_status == "expires_soon":
        return POSTURE_WARNING

    return POSTURE_OK
