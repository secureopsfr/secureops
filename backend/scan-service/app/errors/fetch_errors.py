"""Gestion centralisée des erreurs du scan : fetch, timeout global, validation, inattendues.

Centralise la classification des exceptions réseau et la construction des payloads
d'erreur SSE pour le flux de scan. Roadmap §6 : gestion erreurs site inaccessible,
timeout, TLS error.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from httpx import Response

# Chargement des messages depuis messages.json
_MESSAGES_PATH = Path(__file__).parent / "messages.json"
with _MESSAGES_PATH.open(encoding="utf-8") as f:
    _MESSAGES = json.load(f)

# Types d'erreur pour le payload SSE (rétrocompatibles : message + status_code conservés)
ERROR_TYPE_CONNECTION_FAILED = "connection_failed"
ERROR_TYPE_TIMEOUT = "timeout"
ERROR_TYPE_TLS_ERROR = "tls_error"
ERROR_TYPE_TIMEOUT_GLOBAL = "timeout_global"
ERROR_TYPE_VALIDATION = "validation_error"
ERROR_TYPE_UNKNOWN = "unknown"

# Alias pour compatibilité (tests, imports externes)
MSG_SITE_INACCESSIBLE = _MESSAGES["site_inaccessible"]
MSG_TIMEOUT = _MESSAGES["timeout"]
MSG_TLS_ERROR = _MESSAGES["tls_error"]
MSG_TLS_OPENSSL_LEGACY = _MESSAGES["tls_openssl_legacy"]
MSG_UNKNOWN = _MESSAGES["unknown"]


@dataclass
class FetchResult:
    """Résultat d'un fetch HTTP avec classification d'erreur en cas d'échec.

    Attributes:
        success (bool): True si la requête a abouti.
        response (Response | None): Réponse httpx si success, None sinon.
        error_type (str): Type d'erreur (connection_failed, timeout, tls_error, unknown).
        message (str): Message utilisateur pour l'affichage.
        status_code (int): Code HTTP pour le payload SSE (503, 504, 502, 500).
        details (str | None): Message technique optionnel (pour debug).
    """

    success: bool
    response: "Response | None"
    error_type: str
    message: str
    status_code: int
    details: str | None = None


def classify_fetch_exception(exc: BaseException) -> FetchResult:
    """Classifie une exception de fetch et retourne un FetchResult.

    Args:
        exc: Exception levée lors du GET (ConnectError, Timeout, SSL, etc.).

    Returns:
        FetchResult: Résultat avec error_type, message et status_code.
    """
    err_str = str(exc).lower()
    cause = getattr(exc, "__cause__", None)
    if cause:
        err_str += " " + str(cause).lower()

    # Timeout (connexion ou lecture)
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout)):
        return FetchResult(
            success=False,
            response=None,
            error_type=ERROR_TYPE_TIMEOUT,
            message=_MESSAGES["timeout"],
            status_code=504,
            details=str(exc),
        )

    # Connexion refusée, DNS, etc.
    if isinstance(exc, httpx.ConnectError):
        return FetchResult(
            success=False,
            response=None,
            error_type=ERROR_TYPE_CONNECTION_FAILED,
            message=_MESSAGES["site_inaccessible"],
            status_code=503,
            details=str(exc),
        )

    # Erreurs TLS / SSL (OpenSSL 3.x TLS 1.0/1.1, handshake, etc.)
    if "no_protocols_available" in err_str or "unsupported protocol" in err_str:
        return FetchResult(
            success=False,
            response=None,
            error_type=ERROR_TYPE_TLS_ERROR,
            message=_MESSAGES["tls_openssl_legacy"],
            status_code=502,
            details=str(exc),
        )
    if "ssl" in err_str or "certificate" in err_str or "tls" in err_str:
        return FetchResult(
            success=False,
            response=None,
            error_type=ERROR_TYPE_TLS_ERROR,
            message=_MESSAGES["tls_error"],
            status_code=502,
            details=str(exc),
        )

    # Erreur inconnue
    return FetchResult(
        success=False,
        response=None,
        error_type=ERROR_TYPE_UNKNOWN,
        message=_MESSAGES["unknown"],
        status_code=500,
        details=str(exc),
    )


def build_sse_error_payload(
    fetch_result: FetchResult,
    *,
    include_details: bool = False,
) -> dict:
    """Construit le payload JSON pour l'événement SSE error.

    Rétrocompatible : message et status_code conservés. error_type et details ajoutés.

    Args:
        fetch_result: Résultat du fetch (échec).
        include_details: Si True, inclut le champ details (message technique).

    Returns:
        dict: Payload pour sse_message("error", payload).
    """
    payload: dict = {
        "message": fetch_result.message,
        "status_code": fetch_result.status_code,
        "error_type": fetch_result.error_type,
    }
    if include_details and fetch_result.details:
        payload["details"] = fetch_result.details
    return payload


def build_sse_error_payload_simple(
    message: str,
    status_code: int,
    *,
    error_type: str = "",
) -> dict:
    """Construit un payload SSE error pour les cas simples (timeout global, validation, etc.).

    Args:
        message: Message utilisateur.
        status_code: Code HTTP (400, 408, 500).
        error_type: Type d'erreur optionnel (timeout_global, validation_error, unknown).

    Returns:
        dict: Payload pour sse_message("error", payload).
    """
    payload: dict = {"message": message, "status_code": status_code}
    if error_type:
        payload["error_type"] = error_type
    return payload


def build_timeout_global_error_payload() -> dict:
    """Payload SSE pour dépassement du délai global du scan (408)."""
    return build_sse_error_payload_simple(_MESSAGES["timeout_global"], 408, error_type=ERROR_TYPE_TIMEOUT_GLOBAL)


def build_validation_error_payload(message: str) -> dict:
    """Payload SSE pour erreur de validation d'URL (400)."""
    return build_sse_error_payload_simple(message, 400, error_type=ERROR_TYPE_VALIDATION)


def build_unexpected_error_payload(detail: str) -> dict:
    """Payload SSE pour erreur inattendue (500)."""
    message = _MESSAGES["unexpected_scan"].format(detail=detail)
    return build_sse_error_payload_simple(message, 500, error_type=ERROR_TYPE_UNKNOWN)
