"""Vérifications APIs exposées (GraphQL, Swagger, REST) et formats sur réponses API.

Périmètre : backend. Exécuté en phase domaine. Réutilise check_formats_from_response
pour les réponses API (Content-Type, X-CTO, compression).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config_loader import get_apis_et_formats_settings, get_external_services_settings
from app.services.passive.both.formats.checks import check_formats_from_response
from app.utils.url_helpers import build_url_with_path

_GRAPHQL_INTROSPECTION_QUERY = '{"query":"{ __schema { types { name } } }"}'


@dataclass(frozen=True)
class ApiIssue:
    """Issue API ou format sur réponse API."""

    kind: str
    message: str
    url: str = ""


@dataclass(frozen=True)
class ApiCheckResult:
    """Résultat des vérifications APIs (GraphQL, Swagger, REST) + formats sur réponses API."""

    issues: tuple[ApiIssue, ...]


def _api_issue(kind: str, message: str, url: str = "") -> ApiIssue:
    return ApiIssue(kind=kind, message=message, url=url)


async def _check_graphql(
    base_url: str,
    path: str,
    client: httpx.AsyncClient,
    timeout: float,
    issues: list[ApiIssue],
) -> httpx.Response | None:
    """Envoie une requête introspection et signale si le schéma est retourné."""
    url = build_url_with_path(base_url, path)
    try:
        resp = await client.post(
            url,
            content=_GRAPHQL_INTROSPECTION_QUERY,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
    except Exception:
        return None
    if resp.status_code != 200:
        return resp
    try:
        data = resp.json()
    except Exception:
        return resp
    if isinstance(data, dict):
        schema = data.get("data", {}).get("__schema") if isinstance(data.get("data"), dict) else None
        if schema is not None and isinstance(schema.get("types"), list):
            issues.append(_api_issue("graphql_introspection", f"Introspection GraphQL activée : {url}.", url))
    return resp


def _is_swagger_or_openapi(body: bytes, ct: str | None) -> bool:
    """Indique si le corps est une doc Swagger/OpenAPI."""
    ct_lower = (ct or "").lower()
    if "application/json" in ct_lower or "application/yaml" in ct_lower:
        try:
            text = body.decode("utf-8", errors="replace")
            if text.strip().startswith("{"):
                data = json.loads(text)
                if isinstance(data, dict):
                    if "openapi" in data or "swagger" in data:
                        return True
        except Exception:
            pass
    text_lower = body.decode("utf-8", errors="replace").lower()
    if "swagger" in text_lower and ("paths" in text_lower or "api" in text_lower):
        return True
    return False


async def _check_swagger(
    base_url: str,
    path: str,
    client: httpx.AsyncClient,
    timeout: float,
    issues: list[ApiIssue],
) -> httpx.Response | None:
    """GET sur le chemin et vérifie si Swagger/OpenAPI est exposé."""
    url = build_url_with_path(base_url, path)
    try:
        resp = await client.get(url, timeout=timeout)
    except Exception:
        return None
    if resp.status_code != 200:
        return resp
    body = getattr(resp, "content", b"") or b""
    ct = resp.headers.get("Content-Type") or resp.headers.get("content-type")
    if _is_swagger_or_openapi(body, ct):
        issues.append(_api_issue("swagger_exposed", f"Swagger/OpenAPI exposé sans auth : {url}.", url))
    return resp


def _extract_list_count(obj: Any, threshold: int) -> int | None:
    """Extrait la taille d'une liste JSON si présente et >= threshold. Sinon None."""
    if isinstance(obj, list):
        return len(obj) if len(obj) >= threshold else None
    if isinstance(obj, dict):
        for key in ("items", "users", "orders", "data", "results", "list", "entries"):
            if key in obj and isinstance(obj[key], list):
                n = len(obj[key])
                if n >= threshold:
                    return n
        for v in obj.values():
            if isinstance(v, list) and len(v) >= threshold:
                return len(v)
    return None


async def _check_rest_list(
    base_url: str,
    path: str,
    client: httpx.AsyncClient,
    timeout: float,
    threshold: int,
    issues: list[ApiIssue],
) -> httpx.Response | None:
    """GET sur le chemin et vérifie si une liste non paginée est retournée."""
    url = build_url_with_path(base_url, path)
    try:
        resp = await client.get(url, timeout=timeout)
    except Exception:
        return None
    if resp.status_code != 200:
        return resp
    ct = (resp.headers.get("Content-Type") or "").lower()
    if "application/json" not in ct:
        return resp
    try:
        data = resp.json()
    except Exception:
        return resp
    count = _extract_list_count(data, threshold)
    if count is not None:
        has_pagination = isinstance(data, dict) and any(k in data for k in ("page", "pageSize", "limit", "offset", "total_pages"))
        if not has_pagination:
            issues.append(
                _api_issue(
                    "rest_unpaginated",
                    f"Liste REST non paginée ({count} éléments, seuil {threshold}) : {url}.",
                    url,
                )
            )
    return resp


def check_rest_from_response(
    url: str,
    response: httpx.Response | None,
    threshold: int = 50,
) -> ApiIssue | None:
    """Analyse une réponse page/API pour détecter une liste REST non paginée.

    Utilisé en phase page quand la réponse ressemble à une API JSON.
    """
    if response is None:
        return None
    ct = (response.headers.get("Content-Type") or "").lower()
    if "application/json" not in ct:
        return None
    try:
        data = response.json()
    except Exception:
        return None
    count = _extract_list_count(data, threshold)
    if count is None:
        return None
    has_pagination = isinstance(data, dict) and any(k in data for k in ("page", "pageSize", "limit", "offset", "total_pages"))
    if not has_pagination:
        return _api_issue(
            "rest_unpaginated",
            f"Liste REST non paginée ({count} éléments, seuil {threshold}) : {url}.",
            url,
        )
    return None


async def run_api_checks(
    base_url: str,
    client: httpx.AsyncClient,
) -> ApiCheckResult:
    """Exécute les vérifications APIs en phase domaine.

    Probes GraphQL, Swagger, API list paths. Pour chaque réponse API valide,
    exécute également les checks formats (Content-Type, X-CTO, compression).
    """
    issues: list[ApiIssue] = []
    settings = get_apis_et_formats_settings()
    timeout = get_external_services_settings().fetch_scan_timeout

    # 1. GraphQL
    for path in settings.graphql_paths:
        resp = await _check_graphql(base_url, path, client, timeout, issues)
        if resp is not None and resp.status_code == 200:
            fmt_result = check_formats_from_response(
                resp,
                url=str(resp.url),
                check_xcto=True,
                compression_min_body_bytes=settings.compression_min_body_bytes,
            )
            for fi in fmt_result.issues:
                issues.append(_api_issue(fi.kind, fi.message, fi.url or str(resp.url)))

    # 2. Swagger
    for path in settings.swagger_paths:
        resp = await _check_swagger(base_url, path, client, timeout, issues)
        if resp is not None and resp.status_code == 200:
            fmt_result = check_formats_from_response(
                resp,
                url=str(resp.url),
                check_xcto=True,
                compression_min_body_bytes=settings.compression_min_body_bytes,
            )
            for fi in fmt_result.issues:
                issues.append(_api_issue(fi.kind, fi.message, fi.url or str(resp.url)))

    # 3. REST listes
    for path in settings.api_list_paths:
        resp = await _check_rest_list(base_url, path, client, timeout, settings.unpaginated_list_threshold, issues)
        if resp is not None and resp.status_code == 200:
            fmt_result = check_formats_from_response(
                resp,
                url=str(resp.url),
                check_xcto=True,
                compression_min_body_bytes=settings.compression_min_body_bytes,
            )
            for fi in fmt_result.issues:
                issues.append(_api_issue(fi.kind, fi.message, fi.url or str(resp.url)))

    return ApiCheckResult(issues=tuple(issues))
