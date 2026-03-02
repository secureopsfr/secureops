"""Analyse des certificats TLS : récupération et statut (valide, expiré, auto-signé)."""

import socket
import ssl
from datetime import datetime, timezone

from cryptography import x509


class CertificateStatus:
    """Statut du certificat TLS."""

    VALID = "valid"
    EXPIRED = "expired"
    SELF_SIGNED = "self_signed"
    NOT_YET_VALID = "not_yet_valid"


def fetch_certificate_der(host: str, port: int, timeout: float) -> bytes:
    """Récupère le certificat du serveur en format DER (synchrone, pour asyncio.to_thread).

    Args:
        host: Nom d'hôte.
        port: Port (généralement 443).
        timeout: Timeout en secondes.

    Returns:
        bytes: Certificat au format DER.

    Raises:
        OSError: En cas d'erreur de connexion.
    """
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout) as sock, context.wrap_socket(sock, server_hostname=host) as ssock:
        return ssock.getpeercert(binary_form=True)


def analyze_certificate(cert_der: bytes, host: str) -> tuple[str, list[str]]:
    """Analyse le certificat : valide, expiré ou auto-signé.

    Args:
        cert_der: Certificat au format DER.
        host: Nom d'hôte attendu (pour vérification CN/SAN).

    Returns:
        tuple[str, list[str]]: (status, findings).
    """
    findings: list[str] = []
    cert = x509.load_der_x509_certificate(cert_der)

    now = datetime.now(timezone.utc)
    if now < cert.not_valid_before_utc:
        findings.append("Certificat pas encore valide (notBefore dans le futur).")
        return CertificateStatus.NOT_YET_VALID, findings
    if now > cert.not_valid_after_utc:
        findings.append(
            f"Certificat expiré (notAfter: {cert.not_valid_after_utc.date()}). " "Les navigateurs bloquent ou avertissent ; risque de MITM."
        )
        return CertificateStatus.EXPIRED, findings

    if _is_self_signed(cert):
        findings.append("Certificat auto-signé (émetteur = sujet). " "Aucune confiance par défaut ; les utilisateurs peuvent accepter par habitude.")
        return CertificateStatus.SELF_SIGNED, findings

    return CertificateStatus.VALID, findings


def _is_self_signed(cert: x509.Certificate) -> bool:
    """Vérifie si le certificat est auto-signé (issuer == subject).

    Args:
        cert: Certificat X.509.

    Returns:
        bool: True si auto-signé.
    """
    return cert.issuer == cert.subject
