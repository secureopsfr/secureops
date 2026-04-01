"""Extraction de paramètres injectables depuis URLs et corps de réponse.

Fournit :
- extract_query_params : paramètres query string
- extract_body_params  : paramètres JSON / form-urlencoded
- extract_html_params  : paramètres depuis formulaires et liens HTML (frontend)
- detect_output_context : contexte de sortie d'un marker dans du HTML
- Listes de paramètres courants par catégorie
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class ParamContext(Enum):
    """Contexte d'origine d'un paramètre injectable (query, body, header, etc.)."""

    QUERY_STRING = "query"
    BODY_JSON = "body_json"
    BODY_FORM = "body_form"
    HEADER = "header"
    PATH_SEGMENT = "path"
    HTML_FORM = "html_form"
    HTML_LINK = "html_link"


@dataclass(frozen=True)
class ExtractedParam:
    """Paramètre injectable avec sa valeur originale et son contexte."""

    name: str
    value: str
    context: ParamContext
    original_url: str


# ─── Listes de paramètres courants par catégorie ────────────────────────────

COMMON_REDIRECT_PARAMS: list[str] = [
    "redirect",
    "url",
    "next",
    "return",
    "redirect_uri",
    "returnUrl",
    "continue",
    "destination",
    "goto",
    "redir",
    "ref",
    "back",
    "forward",
    "location",
    "target",
    "to",
    "from",
    "link",
]

COMMON_FILE_PARAMS: list[str] = [
    "file",
    "path",
    "document",
    "template",
    "include",
    "page",
    "filename",
    "filepath",
    "doc",
    "resource",
    "view",
    "load",
    "read",
    "open",
    "get",
    "fetch",
    "dir",
    "folder",
]

COMMON_CMD_PARAMS: list[str] = [
    "cmd",
    "exec",
    "command",
    "run",
    "query",
    "search",
    "ping",
    "host",
    "ip",
    "shell",
    "execute",
    "system",
    "eval",
    "process",
    "call",
    "invoke",
]

COMMON_INJECTION_PARAMS: list[str] = [
    "id",
    "user",
    "username",
    "name",
    "search",
    "q",
    "query",
    "input",
    "data",
    "value",
    "filter",
    "sort",
    "order",
    "where",
    "select",
    "from",
    "key",
    "param",
    "field",
    "email",
    "password",
    "token",
    "code",
    "ref",
]

COMMON_UPLOAD_ENDPOINTS: list[str] = [
    "/upload",
    "/api/upload",
    "/files",
    "/api/files",
    "/attachments",
    "/media",
    "/images",
    "/documents",
    "/import",
    "/api/import",
    "/assets",
]

COMMON_LOGIN_ENDPOINTS: list[str] = [
    "/login",
    "/signin",
    "/sign-in",
    "/auth",
    "/authenticate",
    "/api/auth",
    "/api/login",
    "/api/signin",
    "/api/token",
    "/api/session",
    "/account/login",
    "/user/login",
]

COMMON_ADMIN_ROUTES: list[str] = [
    "/admin",
    "/api/admin",
    "/admin/",
    "/administrator",
    "/manage",
    "/management",
    "/dashboard",
    "/internal",
    "/api/internal",
    "/superadmin",
    "/sysadmin",
    "/_admin",
    "/admin/users",
    "/admin/settings",
]

COMMON_INTERNAL_ENDPOINTS: list[str] = [
    "/actuator",
    "/actuator/env",
    "/actuator/health",
    "/actuator/info",
    "/actuator/metrics",
    "/actuator/heapdump",
    "/actuator/loggers",
    "/metrics",
    "/debug",
    "/internal",
    "/health",
    "/ready",
    "/live",
    "/api/health",
    "/api/status",
    "/_admin",
    "/.well-known/health",
    "/env",
    "/info",
    "/configprops",
    "/beans",
]

# ─── Extracteurs ─────────────────────────────────────────────────────────────


def extract_query_params(url: str) -> list[ExtractedParam]:
    """Extrait les paramètres query string d'une URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    return [
        ExtractedParam(
            name=k,
            value=v[0],
            context=ParamContext.QUERY_STRING,
            original_url=url,
        )
        for k, v in params.items()
    ]


def inject_query_param(url: str, name: str, value: str) -> str:
    """Remplace ou ajoute un paramètre query string dans une URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params[name] = [value]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


def inject_param(param: ExtractedParam, payload: str) -> str:
    """Reconstruit l'URL ou le body en injectant le payload dans le paramètre."""
    if param.context == ParamContext.QUERY_STRING:
        return inject_query_param(param.original_url, param.name, payload)
    return param.original_url


def extract_body_params(body: str, content_type: str) -> list[ExtractedParam]:
    """Extrait les paramètres d'un body JSON ou form-urlencoded."""
    params: list[ExtractedParam] = []
    ct = content_type.lower()
    if "json" in ct:
        params.extend(_extract_json_params(body))
    elif "form" in ct or "urlencoded" in ct:
        try:
            qs = parse_qs(body, keep_blank_values=True)
            for k, v in qs.items():
                params.append(ExtractedParam(name=k, value=v[0], context=ParamContext.BODY_FORM, original_url=""))
        except Exception:
            pass
    return params


def _extract_json_params(body: str) -> list[ExtractedParam]:
    """Extrait les clés de premier niveau d'un objet JSON."""
    import json

    try:
        data = json.loads(body)
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    result = []
    for k, v in data.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            result.append(ExtractedParam(name=k, value=str(v), context=ParamContext.BODY_JSON, original_url=""))
    return result


class _FormParser(HTMLParser):
    """Parseur HTML minimaliste pour extraire les formulaires et leurs champs."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict] = []
        self.links: list[str] = []
        self.file_inputs: list[str] = []
        self._current_form: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "form":
            self._current_form = {
                "action": attr_dict.get("action", ""),
                "method": (attr_dict.get("method") or "GET").upper(),
                "inputs": [],
            }
            self.forms.append(self._current_form)
        elif tag == "input" and self._current_form is not None:
            input_type = (attr_dict.get("type") or "text").lower()
            name = attr_dict.get("name", "")
            if input_type == "file":
                self.file_inputs.append(name)
            elif name:
                self._current_form["inputs"].append(
                    {
                        "name": name,
                        "type": input_type,
                        "value": attr_dict.get("value", ""),
                    }
                )
        elif tag == "a":
            href = attr_dict.get("href") or ""
            if href and not href.startswith("#"):
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self._current_form = None


def extract_html_params(html_body: str, base_url: str) -> list[ExtractedParam]:
    """Extrait les paramètres depuis les formulaires et liens HTML.

    Utilisé pour scan_type=frontend uniquement.
    """
    parser = _FormParser()
    try:
        parser.feed(html_body)
    except Exception:
        return []

    params: list[ExtractedParam] = []
    # Paramètres des formulaires
    for form in parser.forms:
        action = form.get("action") or base_url
        for inp in form.get("inputs", []):
            if inp["name"] and inp["type"] not in ("hidden", "submit", "button", "reset"):
                params.append(
                    ExtractedParam(
                        name=inp["name"],
                        value=inp["value"],
                        context=ParamContext.HTML_FORM,
                        original_url=action,
                    )
                )
    # Paramètres dans les liens
    for href in parser.links:
        if "?" in href:
            full_url = href if href.startswith("http") else base_url.rstrip("/") + "/" + href.lstrip("/")
            params.extend(extract_query_params(full_url))
    return params


def has_file_input(html_body: str) -> bool:
    """Retourne True si le HTML contient un <input type='file'>."""
    parser = _FormParser()
    try:
        parser.feed(html_body)
    except Exception:
        return False
    return bool(parser.file_inputs)


def detect_output_context(html_body: str, marker: str) -> str:
    """Détecte le contexte de sortie d'un marker dans une réponse HTML.

    Returns:
        "script"  — dans un bloc <script> (exécutable)
        "attr"    — dans un attribut HTML (potentiellement exécutable)
        "text"    — dans du texte HTML brut
        "none"    — non trouvé
    """
    if marker not in html_body:
        return "none"

    # Vérifier contexte script
    script_pattern = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
    for m in script_pattern.finditer(html_body):
        if marker in m.group(1):
            return "script"

    # Vérifier contexte attribut
    attr_pattern = re.compile(r'<[^>]+(?:value|src|href|action|data-[^=]*)=["\']([^"\']*)["\']', re.IGNORECASE)
    for m in attr_pattern.finditer(html_body):
        if marker in m.group(1):
            return "attr"

    return "text"
