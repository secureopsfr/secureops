"""Exécution du scan : étapes métier (TLS, etc.). Utilise get_scan_timeouts pour le client HTTP."""

import asyncio
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import httpx
from cryptography import x509

from app.config_loader import ScanTimeoutsSettings, get_scan_timeouts


class CertificateStatus:
    """Statut du certificat TLS."""

    VALID = "valid"
    EXPIRED = "expired"
    SELF_SIGNED = "self_signed"
    NOT_YET_VALID = "not_yet_valid"


@dataclass
class TlsCheckResult:
    """Résultat des vérifications TLS/HTTPS.

    Attributes:
        https_enabled (bool): True si le site répond en HTTPS.
        http_redirects_to_https (bool | None): True si HTTP redirige vers HTTPS, False sinon.
            None si non vérifiable (HTTP inaccessible ou HTTPS non activé).
        certificate_status (str | None): "valid", "expired" ou "self_signed". None si non vérifiable.
        findings (tuple[str, ...]): Liste des findings.
    """

    https_enabled: bool
    http_redirects_to_https: bool | None
    certificate_status: str | None
    findings: tuple[str, ...]


def _build_https_url(url: str) -> str:
    """Construit l'URL HTTPS à tester à partir de l'URL fournie.

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL https://host/ (port 443 implicite).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    return urlunparse(("https", host, "/", "", "", ""))


def _build_http_url(url: str) -> str:
    """Construit l'URL HTTP à tester (pour la vérification redirection).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL http://host/ (port 80 implicite).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    return urlunparse(("http", host, "/", "", "", ""))


def _location_redirects_to_https(location: str | None) -> bool:
    """Vérifie si l'en-tête Location pointe vers https://.

    Args:
        location: Valeur de l'en-tête Location.

    Returns:
        bool: True si Location commence par https:// (insensible à la casse).
    """
    if not location or not isinstance(location, str):
        return False
    return location.strip().lower().startswith("https://")


def _fetch_certificate_der(host: str, port: int, timeout: float) -> bytes:
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


def _analyze_certificate(cert_der: bytes, host: str) -> tuple[str, list[str]]:
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


def _get_host_from_url(url: str) -> str:
    """Extrait le hostname de l'URL."""
    parsed = urlparse(url)
    return parsed.hostname or parsed.netloc.split(":")[0]


async def _check_certificate(host: str, timeouts: ScanTimeoutsSettings, findings: list[str]) -> str | None:
    """Vérification 3 : récupère et analyse le certificat. Retourne le statut ou None."""
    try:
        cert_der = await asyncio.to_thread(_fetch_certificate_der, host, 443, timeouts.connection)
        status, cert_findings = _analyze_certificate(cert_der, host)
        findings.extend(cert_findings)
        return status
    except Exception as e:
        findings.append(f"Impossible d'analyser le certificat : {e!s}")
        return None


async def run_tls_checks(url: str) -> TlsCheckResult:
    """Vérifications TLS/HTTPS (roadmap §3.1).

    Vérification 1 : HTTPS activé ? Une requête GET vers https://<host>/ doit aboutir
    (même si le certificat est invalide ou auto-signé). Si connexion refusée ou timeout,
    HTTPS n'est pas proposé.

    Args:
        url: URL normalisée à scanner (sera utilisée pour extraire le host).

    Returns:
        TlsCheckResult: https_enabled et liste des findings.
    """
    timeouts = get_scan_timeouts()
    https_url = _build_https_url(url)
    findings: list[str] = []

    try:
        async with httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(
                timeouts.connection,
                read=timeouts.read,
            ),
        ) as client:
            response = await client.get(https_url)
            # Toute réponse (200, 301, 404, etc.) indique que HTTPS répond
            _ = response.status_code
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        findings.append("HTTPS non activé (connexion refusée ou timeout). Risque d'interception.")
        return TlsCheckResult(
            https_enabled=False,
            http_redirects_to_https=None,
            certificate_status=None,
            findings=tuple(findings),
        )
    except Exception as e:
        findings.append(f"HTTPS non activé : {e!s}")
        return TlsCheckResult(
            https_enabled=False,
            http_redirects_to_https=None,
            certificate_status=None,
            findings=tuple(findings),
        )

    # Vérification 2 : Redirection HTTP→HTTPS (uniquement si HTTPS activé)
    http_redirects_to_https: bool | None = None
    http_url = _build_http_url(url)
    try:
        async with httpx.AsyncClient(
            verify=False,
            follow_redirects=False,
            timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
        ) as client:
            response = await client.get(http_url)
            if response.status_code in (301, 302, 307, 308):
                location = response.headers.get("location")
                http_redirects_to_https = _location_redirects_to_https(location)
                if not http_redirects_to_https:
                    findings.append("Pas de redirection HTTP→HTTPS : la redirection ne pointe pas vers https://.")
            else:
                http_redirects_to_https = False
                findings.append("Pas de redirection HTTP→HTTPS (réponse 200 ou autre sans redirection). " "Le trafic peut rester en clair.")
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
        http_redirects_to_https = None
        # HTTP inaccessible : non vérifiable (site peut être HTTPS-only)
    except Exception:
        http_redirects_to_https = None

    # Vérification 3 : Certificat valide / expiré / auto-signé
    host = _get_host_from_url(url)
    certificate_status = await _check_certificate(host, timeouts, findings)

    return TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=http_redirects_to_https,
        certificate_status=certificate_status,
        findings=tuple(findings),
    )
