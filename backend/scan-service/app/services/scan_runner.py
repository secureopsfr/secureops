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


def _ssl_context_for_scan() -> ssl.SSLContext:
    """Contexte SSL permissif pour le scan : TLS 1.0+ accepté, pas de vérif. certificat.

    Permet de se connecter aux serveurs TLS 1.0-only (ex. badssl.com:1010) pour les détecter.

    Returns:
        ssl.SSLContext: Contexte configuré.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    return ctx


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
        tls_versions_obsolete (tuple[str, ...]): Versions TLS obsolètes supportées (ex. ("1.0", "1.1")).
        findings (tuple[str, ...]): Liste des findings.
    """

    https_enabled: bool
    http_redirects_to_https: bool | None
    certificate_status: str | None
    tls_versions_obsolete: tuple[str, ...]
    findings: tuple[str, ...]


def _build_https_url(url: str) -> str:
    """Construit l'URL HTTPS à tester à partir de l'URL fournie.

    Préserve le port explicite non standard pour HTTPS (ex. badssl.com:1010 pour tests TLS 1.0).
    Pour http://host:80, produit https://host/ (port 443 implicite).

    Args:
        url: URL normalisée (http ou https).

    Returns:
        str: URL https://host[:port]/ (port 443 implicite si absent ou standard).
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc.split(":")[0]
    # Port non-443 uniquement si l'URL source est https avec port explicite
    port = parsed.port if (parsed.scheme or "").lower() == "https" else None
    netloc = f"{host}:{port}" if port is not None and port != 443 else host
    return urlunparse(("https", netloc, "/", "", "", ""))


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


def _get_https_port_from_url(url: str) -> int:
    """Extrait le port HTTPS de l'URL (443 par défaut si absent ou si http)."""
    parsed = urlparse(url)
    if (parsed.scheme or "").lower() == "https" and parsed.port is not None:
        return parsed.port
    return 443


def _format_https_connection_error(exc: BaseException) -> str | None:
    """Formate une erreur de connexion HTTPS avec message explicatif si pertinent.

    Détecte les erreurs SSL (ex. TLS 1.0 désactivé dans OpenSSL 3.x).

    Args:
        exc: Exception capturée.

    Returns:
        str | None: Message formaté ou None pour utiliser le message par défaut.
    """
    err_str = str(exc).lower()
    cause = getattr(exc, "__cause__", None)
    if cause:
        err_str += " " + str(cause).lower()
    if "no_protocols_available" in err_str or "unsupported protocol" in err_str:
        return (
            "Impossible de se connecter en HTTPS. Le serveur n'accepte peut-être que TLS 1.0/1.1, "
            "désactivés par défaut dans OpenSSL 3.x (limitation de l'environnement de scan)."
        )
    if "connection refused" in err_str or "timeout" in err_str:
        return "HTTPS non activé (connexion refusée ou timeout). Risque d'interception."
    return None


def _try_tls_version(host: str, port: int, timeout: float, min_ver: ssl.TLSVersion, max_ver: ssl.TLSVersion) -> bool:
    """Tente une connexion TLS avec les versions min/max spécifiées.

    Args:
        host: Nom d'hôte.
        port: Port (443).
        timeout: Timeout en secondes.
        min_ver: Version TLS minimale.
        max_ver: Version TLS maximale.

    Returns:
        bool: True si la connexion réussit.
    """
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = min_ver
        context.maximum_version = max_ver
        with socket.create_connection((host, port), timeout=timeout) as sock, context.wrap_socket(sock, server_hostname=host) as ssock:
            _ = ssock.version()
        return True
    except (ssl.SSLError, OSError):
        return False


def _check_tls_versions_obsolete(host: str, port: int, timeout: float) -> tuple[list[str], list[str]]:
    """Détecte si le serveur accepte TLS 1.0 ou 1.1 (obsolètes).

    Args:
        host: Nom d'hôte.
        port: Port (ex. 443 ou 1010 pour badssl.com).
        timeout: Timeout en secondes.

    Returns:
        tuple[list[str], list[str]]: (versions_obsolete, findings).
    """
    obsolete: list[str] = []
    findings: list[str] = []

    if _try_tls_version(host, port, timeout, ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1):
        obsolete.append("1.0")
    if _try_tls_version(host, port, timeout, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1):
        obsolete.append("1.1")

    if obsolete:
        findings.append(f"TLS {' et '.join(obsolete)} encore accepté(s). Versions obsolètes à désactiver.")

    return obsolete, findings


async def _check_tls_versions(host: str, port: int, timeouts: ScanTimeoutsSettings, findings: list[str]) -> tuple[str, ...]:
    """Vérification 4 : détecte TLS 1.0/1.1. Retourne la liste des versions obsolètes."""
    try:
        obsolete, tls_findings = await asyncio.to_thread(_check_tls_versions_obsolete, host, port, timeouts.connection)
        findings.extend(tls_findings)
        return tuple(obsolete)
    except Exception:
        return ()


async def _check_certificate(host: str, port: int, timeouts: ScanTimeoutsSettings, findings: list[str]) -> str | None:
    """Vérification 3 : récupère et analyse le certificat. Retourne le statut ou None."""
    try:
        cert_der = await asyncio.to_thread(_fetch_certificate_der, host, port, timeouts.connection)
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
            verify=_ssl_context_for_scan(),
            timeout=httpx.Timeout(
                timeouts.connection,
                read=timeouts.read,
            ),
        ) as client:
            response = await client.get(https_url)
            # Toute réponse (200, 301, 404, etc.) indique que HTTPS répond
            _ = response.status_code
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout) as e:
        err_msg = _format_https_connection_error(e) or "HTTPS non activé (connexion refusée ou timeout). Risque d'interception."
        findings.append(err_msg)
        return TlsCheckResult(
            https_enabled=False,
            http_redirects_to_https=None,
            certificate_status=None,
            tls_versions_obsolete=(),
            findings=tuple(findings),
        )
    except Exception as e:
        err_msg = _format_https_connection_error(e) or f"HTTPS non activé : {e!s}"
        findings.append(err_msg)
        return TlsCheckResult(
            https_enabled=False,
            http_redirects_to_https=None,
            certificate_status=None,
            tls_versions_obsolete=(),
            findings=tuple(findings),
        )

    # Vérification 2 : Redirection HTTP→HTTPS (uniquement si HTTPS activé)
    http_redirects_to_https: bool | None = None
    http_url = _build_http_url(url)
    try:
        async with httpx.AsyncClient(
            verify=_ssl_context_for_scan(),
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

    # Vérification 3 et 4 : certificat et versions TLS (utiliser le port de l'URL)
    host = _get_host_from_url(url)
    port = _get_https_port_from_url(url)
    certificate_status = await _check_certificate(host, port, timeouts, findings)

    # Vérification 4 : Versions TLS obsolètes (1.0, 1.1)
    tls_versions_obsolete = await _check_tls_versions(host, port, timeouts, findings)

    return TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=http_redirects_to_https,
        certificate_status=certificate_status,
        tls_versions_obsolete=tls_versions_obsolete,
        findings=tuple(findings),
    )
