"""Orchestration des vérifications TLS/HTTPS (roadmap §3.1)."""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from app.config_loader import ScanTimeoutsSettings, get_scan_timeouts
from app.constants import MSG_HTTPS_UNAVAILABLE
from app.errors.fetch_errors import classify_fetch_exception
from app.services.tls.certificate import analyze_certificate, fetch_certificate_chain, fetch_certificate_der, verify_certificate_chain
from app.services.tls.versions import check_tls_versions_obsolete, get_negotiated_tls_version
from app.utils.http_fetch import get_with_client
from app.utils.ssl_scan import ssl_context_for_scan
from app.utils.url_helpers import build_http_url, build_https_url, get_host_from_url, get_https_port_from_url, location_redirects_to_https

if TYPE_CHECKING:
    from httpx import AsyncClient

# Sentinel pour distinguer "paramètre non fourni" de "fetch a échoué (None)"
_UNSET = object()


@dataclass
class TlsCheckResult:
    """Résultat des vérifications TLS/HTTPS.

    Attributes:
        https_enabled (bool): True si le site répond en HTTPS.
        http_redirects_to_https (bool | None): True si HTTP redirige vers HTTPS, False sinon.
            None si non vérifiable (HTTP inaccessible ou HTTPS non activé).
        certificate_status (str | None): "valid", "expired" ou "self_signed". None si non vérifiable.
        tls_versions_obsolete (tuple[str, ...]): Versions TLS obsolètes supportées (ex. ("1.0", "1.1")).
        tls_version (str | None): Version TLS négociée (ex. "TLS 1.2", "TLS 1.3"). None si non détectable.
        chain_incomplete (bool): True si la chaîne de certificats est incomplète (intermédiaires manquants).
        findings (tuple[str, ...]): Liste des findings.
        fetch_ok (bool): True si la requête HTTPS a abouti.
    """

    https_enabled: bool
    http_redirects_to_https: bool | None
    certificate_status: str | None
    tls_versions_obsolete: tuple[str, ...]
    findings: tuple[str, ...]
    fetch_ok: bool = True
    tls_version: str | None = None
    chain_incomplete: bool = False

    def is_posture_valid(self) -> bool:
        """Indique si la posture TLS est acceptable (HTTPS OK, redirect OK, cert valide, pas de TLS obsolète).

        Returns:
            bool: True si tous les critères sont satisfaits ou non vérifiables.
        """
        redirect_ok = self.http_redirects_to_https is None or self.http_redirects_to_https
        cert_ok = self.certificate_status is None or self.certificate_status == "valid"
        no_obsolete = len(self.tls_versions_obsolete) == 0
        return self.https_enabled and redirect_ok and cert_ok and no_obsolete

    def to_dict(self) -> dict:
        """Sérialise le résultat pour l'événement SSE result."""
        return {
            "https_enabled": self.https_enabled,
            "http_redirects_to_https": self.http_redirects_to_https,
            "certificate_status": self.certificate_status,
            "tls_versions_obsolete": list(self.tls_versions_obsolete),
            "tls_version": self.tls_version,
            "findings": list(self.findings),
            "fetch_ok": self.fetch_ok,
        }


def _format_https_connection_error(exc: BaseException) -> str:
    """Formate une erreur de connexion HTTPS via le module centralisé.

    Délègue à classify_fetch_exception pour cohérence avec le flux principal.

    Args:
        exc: Exception capturée.

    Returns:
        str: Message utilisateur pour le finding.
    """
    return classify_fetch_exception(exc).message


async def _check_tls_versions(host: str, port: int, timeouts: ScanTimeoutsSettings, findings: list[str]) -> tuple[str, ...]:
    """Vérification 4 : détecte TLS 1.0/1.1. Retourne la liste des versions obsolètes."""
    try:
        obsolete, tls_findings = await asyncio.to_thread(check_tls_versions_obsolete, host, port, timeouts.connection)
        findings.extend(tls_findings)
        return tuple(obsolete)
    except Exception:
        return ()


async def _check_certificate(host: str, port: int, timeouts: ScanTimeoutsSettings, findings: list[str]) -> tuple[str | None, bool]:
    """Vérification 3 : récupère et analyse le certificat et la chaîne.

    Returns:
        tuple[str | None, bool]: (certificate_status, chain_incomplete).
    """
    try:
        # Tenter d'abord la chaîne complète (openssl) pour vérifier les intermédiaires
        chain = await asyncio.to_thread(fetch_certificate_chain, host, port, timeouts.connection)
        cert_der = chain[0] if chain else await asyncio.to_thread(fetch_certificate_der, host, port, timeouts.connection)
        status, cert_findings = analyze_certificate(cert_der, host)
        findings.extend(cert_findings)

        chain_incomplete = False
        if chain and status != "self_signed":
            chain_ok, chain_findings = verify_certificate_chain(chain, leaf_is_self_signed=False)
            findings.extend(chain_findings)
            chain_incomplete = not chain_ok

        return status, chain_incomplete
    except Exception as e:
        findings.append(f"Impossible d'analyser le certificat : {e!s}")
        return None, False


async def _fetch_https_when_unset(https_url: str, timeouts: ScanTimeoutsSettings, findings: list[str]) -> httpx.Response | None:
    """Effectue le GET HTTPS si la réponse n'a pas été fournie. Retourne None en cas d'erreur."""
    async with httpx.AsyncClient(
        verify=ssl_context_for_scan(),
        follow_redirects=False,
        timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
    ) as client:
        try:
            return await client.get(https_url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout) as e:
            findings.append(_format_https_connection_error(e))
            return None
        except Exception as e:
            findings.append(_format_https_connection_error(e))
            return None


async def _check_http_redirect(
    http_url: str,
    timeouts: ScanTimeoutsSettings,
    findings: list[str],
    *,
    client: "AsyncClient | None" = None,
) -> bool | None:
    """Vérification 2 : redirection HTTP→HTTPS. Retourne True/False/None."""
    if client is not None:
        response = await get_with_client(client, http_url, follow_redirects=False)
    else:
        try:
            async with httpx.AsyncClient(
                verify=ssl_context_for_scan(),
                follow_redirects=False,
                timeout=httpx.Timeout(timeouts.connection, read=timeouts.read),
            ) as ac:
                response = await ac.get(http_url)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout):
            return None
        except Exception:
            return None

    if response is None:
        return None
    if response.status_code in (301, 302, 307, 308):
        location = response.headers.get("location")
        ok = location_redirects_to_https(location)
        if not ok:
            findings.append("Pas de redirection HTTP→HTTPS : la redirection ne pointe pas vers https://.")
        return ok
    findings.append("Pas de redirection HTTP→HTTPS (réponse 200 ou autre sans redirection). Le trafic peut rester en clair.")
    return False


async def run_tls_checks(
    url: str,
    https_response: httpx.Response | None = _UNSET,
    *,
    client: "AsyncClient | None" = None,
) -> TlsCheckResult:
    """Vérifications TLS/HTTPS (roadmap §3.1).

    Vérification 1 : HTTPS activé ? Une requête GET vers https://<host>/ doit aboutir
    (même si le certificat est invalide ou auto-signé). Si connexion refusée ou timeout,
    HTTPS n'est pas proposé.

    Args:
        url: URL normalisée à scanner (sera utilisée pour extraire le host).
        https_response: Réponse HTTPS pré-fetchée (évite un GET dupliqué). Si None explicitement
            passé, considère que le fetch a échoué. Si omis, effectue le GET.
        client: Client httpx optionnel pour la requête HTTP de redirection (réutilisation connexion).

    Returns:
        TlsCheckResult: https_enabled et liste des findings.
    """
    timeouts = get_scan_timeouts()
    https_url = build_https_url(url)
    http_url = build_http_url(url)
    findings: list[str] = []

    # Cas : fetch préalable a échoué (None passé explicitement)
    if https_response is None:
        findings.append(MSG_HTTPS_UNAVAILABLE)
        return TlsCheckResult(
            https_enabled=False,
            http_redirects_to_https=None,
            certificate_status=None,
            tls_versions_obsolete=(),
            findings=tuple(findings),
            fetch_ok=False,
        )

    # Cas : pas de réponse fournie, on fait le GET nous-mêmes
    if https_response is _UNSET:
        https_response = await _fetch_https_when_unset(https_url, timeouts, findings)
        if https_response is None:
            return TlsCheckResult(
                https_enabled=False,
                http_redirects_to_https=None,
                certificate_status=None,
                tls_versions_obsolete=(),
                findings=tuple(findings),
                fetch_ok=False,
            )

    # On a une réponse HTTPS (fournie ou venant de notre GET)
    # Vérification 2 : Redirection HTTP→HTTPS (uniquement si HTTPS activé)
    http_redirects_to_https = await _check_http_redirect(http_url, timeouts, findings, client=client)

    # Vérification 3 et 4 : certificat et versions TLS (utiliser le port de l'URL)
    host = get_host_from_url(url)
    port = get_https_port_from_url(url)
    certificate_status, chain_incomplete = await _check_certificate(host, port, timeouts, findings)

    # Vérification 4 : Versions TLS obsolètes (1.0, 1.1)
    tls_versions_obsolete = await _check_tls_versions(host, port, timeouts, findings)

    # Version TLS négociée (ex. TLS 1.2, TLS 1.3) pour affichage dans le résumé
    tls_version = await asyncio.to_thread(get_negotiated_tls_version, host, port, timeouts.connection)

    return TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=http_redirects_to_https,
        certificate_status=certificate_status,
        tls_versions_obsolete=tls_versions_obsolete,
        findings=tuple(findings),
        tls_version=tls_version,
        chain_incomplete=chain_incomplete,
    )
