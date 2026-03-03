"""Vérifications Information disclosure (roadmap §5.2).

Ce module implémente les contrôles décrits dans
``docs/verifications/information-disclosure.md`` :

- détection de stack traces dans le corps de réponse ;
- détection de messages d'erreur en mode debug (development server, DEBUG=True, etc.) ;
- recherche de patterns sensibles (mots de passe, tokens, clés API) dans le HTML/JSON ;
- détection des en-têtes de débogage (X-Debug, X-Debug-Token, X-Runtime) ;
- détection des en-têtes révélant la stack (Server avec version, X-Powered-By, X-AspNet-Version,
  X-Generator, X-Version, X-Drupal-Cache).

Les vérifications restent passives : aucune requête supplémentaire n'est effectuée, seule la
réponse HTTPS principale (headers + body tronqué) est analysée.
"""

import re
from dataclasses import dataclass

import httpx

from app.config_loader import get_information_disclosure_max_body
from app.services.tech_fingerprinting.checks import _parse_version
from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class InformationDisclosureCheckResult:
    """Résultat des vérifications de fuites d'information.

    Attributes:
        findings (tuple[str, ...]): Messages bruts décrivant les fuites détectées
            (stack traces, secrets, headers de debug, etc.).
        fetch_ok (bool): Indique si la réponse HTTPS a pu être analysée. False
            si la réponse est absente ou illisible.
    """

    findings: tuple[str, ...]
    fetch_ok: bool


_STACK_TRACE_MARKERS: tuple[str, ...] = (
    "traceback (most recent call last):",
    "fatal error",
    "stack trace:",
    "exception in thread",
    "at system.",
)

_DEBUG_BODY_MARKERS: tuple[str, ...] = (
    "django debug = true",
    "flask_debug",
    "development server",
    "debug mode",
    "xdebug",
    "you are seeing this error because you have debug = true",
)

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "api_key",
        re.compile(r'(?i)"api_key"\s*:\s*"([^"\s]{16,})'),
    ),
    (
        "api_key",
        re.compile(r"(?i)\bapi_key\s*=\s*([A-Za-z0-9_\-]{16,})"),
    ),
    (
        "bearer",
        re.compile(r"(?i)\bbearer\s+([A-Za-z0-9\.\-_]{24,})"),
    ),
    (
        "password",
        re.compile(r'(?i)"password"\s*:\s*"([^"\s]{8,})'),
    ),
)

_PLACEHOLDER_MARKERS: tuple[str, ...] = ("example", "demo", "test", "dummy")


def _extract_snippet(body: str, index: int, window: int = 200) -> str:
    """Extrait un extrait court autour d'un index dans le corps.

    Args:
        body: Contenu textuel de la réponse.
        index: Position du motif détecté dans le texte.
        window: Taille maximale de la fenêtre (caractères).

    Returns:
        str: Extrait nettoyé (saut de ligne aplatis).
    """
    if index < 0 or not body:
        return ""
    half = max(window // 2, 1)
    start = max(index - half, 0)
    end = min(index + half, len(body))
    snippet = body[start:end].replace("\n", " ").replace("\r", " ")
    return snippet.strip()


def _detect_stack_traces(body: str) -> list[str]:
    """Détecte des stack traces typiques dans le corps de la réponse.

    Args:
        body: Contenu textuel de la réponse HTTP.

    Returns:
        list[str]: Messages de findings pour les stack traces détectées.
    """
    findings: list[str] = []
    if not body:
        return findings
    lowered = body.lower()
    for marker in _STACK_TRACE_MARKERS:
        idx = lowered.find(marker)
        if idx != -1:
            snippet = _extract_snippet(body, idx)
            findings.append(f"Stack trace détectée dans la réponse (extrait : {snippet}).")
            break
    return findings


def _detect_debug_body_markers(body: str) -> list[str]:
    """Détecte des messages d'erreur ou bannières de mode debug dans le body.

    Args:
        body: Contenu textuel de la réponse HTTP.

    Returns:
        list[str]: Messages de findings pour le mode debug exposé.
    """
    findings: list[str] = []
    if not body:
        return findings
    lowered = body.lower()
    for marker in _DEBUG_BODY_MARKERS:
        idx = lowered.find(marker)
        if idx != -1:
            snippet = _extract_snippet(body, idx)
            findings.append(
                f"Message d'erreur debug ou mode développement détecté dans le corps (extrait : {snippet}).",
            )
            break
    return findings


def _is_placeholder_secret(value: str) -> bool:
    """Indique si une valeur ressemble à un placeholder de secret.

    Args:
        value: Valeur candidate (clé API, token, etc.).

    Returns:
        bool: True si la valeur ressemble à un exemple ou un placeholder.
    """
    lowered = value.lower()
    if not value or all(ch == "x" for ch in lowered):
        return True
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _mask_secret(value: str) -> str:
    """Masque une valeur de secret en conservant quelques caractères.

    Args:
        value: Valeur d'origine.

    Returns:
        str: Valeur partiellement masquée (aucun secret complet n'est logué).
    """
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    prefix = value[:4]
    suffix = value[-4:]
    masked_mid = "*" * max(len(value) - 8, 4)
    return f"{prefix}{masked_mid}{suffix}"


def _detect_secrets(body: str) -> list[str]:
    """Recherche des patterns sensibles (secrets) dans le body.

    Args:
        body: Contenu textuel de la réponse HTTP.

    Returns:
        list[str]: Messages de findings pour les secrets potentiels détectés.
    """
    findings: list[str] = []
    if not body:
        return findings

    for kind, pattern in _SECRET_PATTERNS:
        for match in pattern.finditer(body):
            raw = match.group(1).strip()
            if _is_placeholder_secret(raw):
                continue
            masked = _mask_secret(raw)
            findings.append(
                f"Secret potentiel détecté dans la réponse ({kind}), valeur masquée : {masked}.",
            )
            if len(findings) >= 3:
                return findings

    return findings


def _detect_debug_headers(response: httpx.Response) -> list[str]:
    """Détecte les en-têtes de débogage (X-Debug, X-Debug-Token, X-Runtime).

    Args:
        response: Réponse HTTP analysée.

    Returns:
        list[str]: Messages de findings si des en-têtes de debug sont présents.
    """
    debug_headers: list[str] = []
    for name in ("X-Debug", "X-Debug-Token", "X-Runtime"):
        value = get_header_insensitive(response, name)
        if value is not None:
            debug_headers.append(f"{name}: {value}")
    if not debug_headers:
        return []
    joined = ", ".join(debug_headers)
    return [f"Header de debug détecté dans la réponse ({joined})."]


def _detect_server_and_runtime_versions(response: httpx.Response) -> list[str]:
    """Détecte les versions détaillées dans Server, X-Powered-By, X-AspNet-Version.

    Args:
        response: Réponse HTTP analysée.

    Returns:
        list[str]: Messages de findings pour les versions exposées.
    """
    findings: list[str] = []

    server = get_header_insensitive(response, "Server")
    if server:
        server_version = _parse_version(server)
        if server_version:
            findings.append(
                f"Version serveur exposée dans l'en-tête Server : {server}.",
            )

    x_powered_by = get_header_insensitive(response, "X-Powered-By")
    if x_powered_by:
        runtime_version = _parse_version(x_powered_by)
        if runtime_version:
            findings.append(
                f"Version runtime exposée dans l'en-tête X-Powered-By : {x_powered_by}.",
            )

    x_aspnet = get_header_insensitive(response, "X-AspNet-Version")
    if x_aspnet:
        findings.append(
            f"Version ASP.NET exposée dans l'en-tête X-AspNet-Version : {x_aspnet}.",
        )

    return findings


def _detect_custom_stack_headers(response: httpx.Response) -> list[str]:
    """Détecte des en-têtes custom révélant la stack applicative.

    Args:
        response: Réponse HTTP analysée.

    Returns:
        list[str]: Messages de findings pour les en-têtes révélateurs.
    """
    findings: list[str] = []
    for name in ("X-Generator", "X-Version", "X-Drupal-Cache"):
        value = get_header_insensitive(response, name)
        if value:
            findings.append(f"En-tête custom révélant la stack : {name}: {value}.")
    return findings


def check_information_disclosure_from_response(
    response: httpx.Response | None,
) -> InformationDisclosureCheckResult:
    """Analyse une réponse HTTPS pour détecter les fuites d'information.

    La fonction travaille uniquement en lecture sur la réponse fournie, sans
    émettre de nouvelle requête. Le corps est tronqué à une taille maximale
    configurable (information_disclosure.max_body_bytes).

    Args:
        response: Réponse HTTP de la page principale (ou None si le fetch a échoué).

    Returns:
        InformationDisclosureCheckResult: Résultat agrégé des vérifications.
    """
    findings: list[str] = []

    if response is None:
        findings.append("Réponse HTTPS indisponible pour analyser les fuites d'information.")
        return InformationDisclosureCheckResult(findings=tuple(findings), fetch_ok=False)

    max_body = get_information_disclosure_max_body()
    try:
        body_bytes = bytes(response.content[:max_body])
    except Exception:
        body_bytes = b""

    try:
        encoding = response.encoding or "utf-8"
    except Exception:
        encoding = "utf-8"

    body_text = body_bytes.decode(encoding, errors="replace")

    findings.extend(_detect_stack_traces(body_text))
    findings.extend(_detect_debug_body_markers(body_text))
    findings.extend(_detect_secrets(body_text))
    findings.extend(_detect_debug_headers(response))
    findings.extend(_detect_server_and_runtime_versions(response))
    findings.extend(_detect_custom_stack_headers(response))

    return InformationDisclosureCheckResult(findings=tuple(findings), fetch_ok=True)
