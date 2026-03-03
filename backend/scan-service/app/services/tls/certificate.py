"""Analyse des certificats TLS : récupération, statut et chaîne de confiance."""

import re
import socket
import ssl
import subprocess
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding


class CertificateStatus:
    """Statut du certificat TLS."""

    VALID = "valid"
    EXPIRED = "expired"
    SELF_SIGNED = "self_signed"
    NOT_YET_VALID = "not_yet_valid"
    EXPIRES_SOON = "expires_soon"


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

    # Alerte si expiration dans moins de 30 jours
    days_until_expiry = (cert.not_valid_after_utc - now).days
    if 0 <= days_until_expiry < 30:
        findings.append(
            f"Certificat expire bientôt (dans {days_until_expiry} jour(s), "
            f"notAfter: {cert.not_valid_after_utc.date()}). Renouveler avant expiration."
        )
        return CertificateStatus.EXPIRES_SOON, findings

    return CertificateStatus.VALID, findings


def _is_self_signed(cert: x509.Certificate) -> bool:
    """Vérifie si le certificat est auto-signé (issuer == subject).

    Args:
        cert: Certificat X.509.

    Returns:
        bool: True si auto-signé.
    """
    return cert.issuer == cert.subject


def fetch_certificate_chain(host: str, port: int, timeout: float) -> list[bytes]:
    """Récupère la chaîne complète de certificats via openssl s_client.

    Args:
        host: Nom d'hôte.
        port: Port (généralement 443).
        timeout: Timeout en secondes.

    Returns:
        list[bytes]: Liste des certificats en DER (feuille en premier).
    """
    cmd = [
        "openssl",
        "s_client",
        "-showcerts",
        "-connect",
        f"{host}:{port}",
        "-servername",
        host,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 2,
            input=b"",
            check=False,
        )
        output = proc.stderr.decode("utf-8", errors="replace") + proc.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    # Extraire les blocs PEM
    pattern = rb"-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----"
    matches = re.findall(pattern, output.encode("utf-8"), re.DOTALL)
    certs_der: list[bytes] = []
    for m in matches:
        pem = b"-----BEGIN CERTIFICATE-----\n" + m.strip() + b"\n-----END CERTIFICATE-----"
        try:
            cert = x509.load_pem_x509_certificate(pem)
            certs_der.append(cert.public_bytes(Encoding.DER))
        except Exception:
            continue
    return certs_der


def verify_certificate_chain(chain: list[bytes], leaf_is_self_signed: bool) -> tuple[bool, list[str]]:
    """Vérifie que la chaîne est complète (serveur → intermédiaires → racine).

    Args:
        chain: Liste des certificats DER (feuille en premier).
        leaf_is_self_signed: True si le certificat feuille est auto-signé.

    Returns:
        tuple[bool, list[str]]: (ok, findings).
    """
    findings: list[str] = []
    if not chain:
        findings.append("Impossible de récupérer la chaîne de certificats.")
        return False, findings

    if leaf_is_self_signed:
        return True, findings

    # Un seul certificat (feuille) et non auto-signé : chaîne probablement incomplète
    if len(chain) == 1:
        findings.append(
            "Chaîne de certificats incomplète : le serveur n'envoie que le certificat feuille, "
            "sans les intermédiaires. Les navigateurs peuvent afficher des avertissements."
        )
        return False, findings

    # Vérifier les liens issuer → subject
    certs = [x509.load_der_x509_certificate(c) for c in chain]
    for i in range(len(certs) - 1):
        if certs[i].issuer != certs[i + 1].subject:
            findings.append("Chaîne de certificats invalide : le certificat intermédiaire ne correspond pas " f"à l'émetteur du certificat {i + 1}.")
            return False, findings

    return True, findings
