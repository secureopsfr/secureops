"""Vérifications des formats de réponse (Content-Type, X-Content-Type-Options, compression).

Périmètre : les deux (frontend et backend). Utilisé sur la page principale et sur
les réponses API. X-CTO n'est vérifié que sur les réponses API (la page principale
est couverte par security_headers).
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.utils.headers import get_header_insensitive


@dataclass(frozen=True)
class FormatsIssue:
    """Issue format de réponse typée."""

    kind: str
    message: str
    url: str = ""


@dataclass(frozen=True)
class FormatsCheckResult:
    """Résultat des vérifications formats (Content-Type, X-CTO, compression)."""

    issues: tuple[FormatsIssue, ...]


def _looks_like_json(body: bytes) -> bool:
    """Indique si le corps ressemble à du JSON."""
    if not body or len(body) < 2:
        return False
    stripped = body.lstrip()
    return stripped.startswith(b"{") or stripped.startswith(b"[")


def _looks_like_html(body: bytes) -> bool:
    """Indique si le corps ressemble à du HTML."""
    if not body or len(body) < 5:
        return False
    stripped = body.lstrip()
    return stripped.startswith(b"<!") or stripped.startswith(b"<html")


def _check_content_type(
    response: httpx.Response,
    url: str,
    issues: list[FormatsIssue],
) -> None:
    """Vérifie que Content-Type correspond au contenu réel."""
    ct = get_header_insensitive(response, "Content-Type")
    if not ct:
        return
    ct_lower = ct.split(";")[0].strip().lower()
    body = getattr(response, "content", b"") or b""

    if _looks_like_json(body) and "application/json" not in ct_lower and "application/ld+json" not in ct_lower:
        msg = f"Contenu JSON servi avec Content-Type incorrect ({ct.split(';')[0].strip()}) : {url}."
        issues.append(FormatsIssue(kind="content_type_wrong", message=msg, url=url))
    elif _looks_like_html(body) and "text/html" not in ct_lower:
        msg = f"Contenu HTML servi avec Content-Type incorrect ({ct.split(';')[0].strip()}) : {url}."
        issues.append(FormatsIssue(kind="content_type_wrong", message=msg, url=url))


def _check_xcto(
    response: httpx.Response,
    url: str,
    issues: list[FormatsIssue],
) -> None:
    """Vérifie X-Content-Type-Options: nosniff."""
    xcto = get_header_insensitive(response, "X-Content-Type-Options")
    if xcto is None or xcto.strip().lower() != "nosniff":
        msg = f"X-Content-Type-Options: nosniff absent : {url}."
        issues.append(FormatsIssue(kind="xcto_missing", message=msg, url=url))


def _check_compression(
    response: httpx.Response,
    url: str,
    min_body_bytes: int,
    issues: list[FormatsIssue],
) -> None:
    """Vérifie si la réponse est compressée (gzip/brotli) pour les réponses textuelles volumineuses."""
    ce = get_header_insensitive(response, "Content-Encoding")
    if ce:
        ce_lower = ce.lower()
        if "gzip" in ce_lower or "br" in ce_lower or "deflate" in ce_lower:
            return  # OK
    body = getattr(response, "content", b"") or b""
    if len(body) < min_body_bytes:
        return
    ct = get_header_insensitive(response, "Content-Type") or ""
    if not any(t in ct.lower() for t in ("text/", "application/json", "application/javascript")):
        return
    msg = f"Réponse sans compression (gzip/brotli) pour {len(body)} octets : {url}."
    issues.append(FormatsIssue(kind="no_compression", message=msg, url=url))


def check_formats_from_response(
    response: httpx.Response | None,
    url: str = "",
    *,
    check_xcto: bool = True,
    compression_min_body_bytes: int = 1024,
) -> FormatsCheckResult:
    """Analyse une réponse HTTP pour les formats (Content-Type, X-CTO, compression).

    Args:
        response: Réponse HTTP à analyser.
        url: URL de la réponse (pour les messages).
        check_xcto: Si False, ne vérifie pas X-CTO (ex. page principale déjà couverte par security_headers).
        compression_min_body_bytes: Seuil minimal pour émettre un finding compression.

    Returns:
        FormatsCheckResult avec les issues détectées.
    """
    issues: list[FormatsIssue] = []
    if response is None:
        return FormatsCheckResult(issues=())

    if _looks_like_json(getattr(response, "content", b"") or b"") or _looks_like_html(getattr(response, "content", b"") or b""):
        _check_content_type(response, url or str(getattr(response, "url", "")), issues)
    if check_xcto:
        _check_xcto(response, url or str(getattr(response, "url", "")), issues)
    _check_compression(response, url or str(getattr(response, "url", "")), compression_min_body_bytes, issues)

    return FormatsCheckResult(issues=tuple(issues))
