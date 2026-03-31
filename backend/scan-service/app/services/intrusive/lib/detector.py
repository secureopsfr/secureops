"""Moteur de détection de vulnérabilités par signatures regex, timing et diff.

Fournit :
- detect_sql_error, detect_nosql_error, detect_template_error, detect_xxe,
  detect_path_traversal, detect_shell_output : détection par signatures regex
- detect_time_based : détection basée sur le délai de réponse
- detect_reflection : présence d'un marker dans la réponse
- detect_output_context : délégué à param_extractor
- diff_baseline : ratio de différence entre deux réponses
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Résultat d'une tentative de détection."""

    matched: bool
    pattern: str | None = None
    evidence: str | None = None
    detection_type: str = "regex"


# ─── Signatures ──────────────────────────────────────────────────────────────

_SQL_ERROR_PATTERNS: list[str] = [
    r"SQL syntax.*MySQL",
    r"Warning.*mysql_",
    r"valid MySQL result",
    r"MySqlClient\.",
    r"PostgreSQL.*ERROR",
    r"Warning.*pg_",
    r"valid PostgreSQL result",
    r"Npgsql\.",
    r"ORA-[0-9]{4,5}",
    r"Oracle.*Driver",
    r"Microsoft OLE DB Provider for SQL Server",
    r"Unclosed quotation mark",
    r"ODBC.*Driver",
    r"SQLServer JDBC",
    r"SQLite3?::Exception",
    r"sqlite3\.OperationalError",
    r"SQLITE_ERROR",
    r"System\.Data\.SQLite",
    r"near \"[^\"]+\": syntax error",
    r"unterminated quoted string at or near",
    r"quoted string not properly terminated",
]

_NOSQL_ERROR_PATTERNS: list[str] = [
    r"\$where",
    r"MongoError",
    r"CastError.*ObjectId",
    r"BSONTypeError",
    r"E11000 duplicate key",
    r'"operator":\s*"\$',
    r"MongoServerError",
    r"cannot use \$",
]

_TEMPLATE_ERROR_PATTERNS: list[str] = [
    r"jinja2\.exceptions",
    r"TemplateSyntaxError",
    r"UndefinedError",
    r"Twig[\\._]Error",
    r"Freemarker.*Exception",
    r"Velocity.*Exception",
    r"FreeMarkerException",
    r"Template.*not found",
    r"smarty.*error",
    r"ThymeleafException",
    r"Pebble.*Exception",
]

_XXE_PATTERNS: list[str] = [
    r"root:.*:0:0:",  # /etc/passwd
    r"\[boot loader\]",  # win.ini
    r"for 16-bit app support",
    r"DOCTYPE.*ENTITY",
    r"SYSTEM.*file://",
    r"\[global\]",  # win.ini section
    r"nss-softokn",  # Linux system file
    r"x11-common",
]

_PATH_TRAVERSAL_PATTERNS: list[str] = [
    r"root:.*:0:0:",
    r"\[boot loader\]",
    r"for 16-bit app support",
    r"win\.ini",
    r"\[fonts\]",
    r"x11-common",
    r"/bin/bash",
    r"daemon:.*:/usr/sbin",
]

_SHELL_OUTPUT_PATTERNS: list[str] = [
    r"uid=\d+\(\w+\)",
    r"gid=\d+\(\w+\)",
    r"total \d+\s+drw",
    r"Linux.*#\s*\d+",
    r"GNU coreutils",
    r"(?:^|\n)root\s+\d+",
    r"(?:^|\n)bin\s+\d+",
]

_DESERIALIZATION_PATTERNS: list[str] = [
    r"java\.io\..*Exception",
    r"ClassNotFoundException",
    r"ObjectInputStream",
    r"unserialize\(\)",
    r"PHP.*Notice.*unserialize",
    r"Deserialization.*error",
    r"pickle\.loads",
    r"cpickle",
    r"ObjectStreamException",
]


def _match_patterns(body: str, patterns: list[str], detection_type: str) -> DetectionResult:
    """Tente de matcher une liste de patterns regex dans le body."""
    for pattern in patterns:
        try:
            m = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if m:
                start = max(0, m.start() - 40)
                end = min(len(body), m.end() + 40)
                evidence = body[start:end].strip().replace("\n", " ")
                return DetectionResult(
                    matched=True,
                    pattern=pattern,
                    evidence=evidence,
                    detection_type=detection_type,
                )
        except re.error:
            continue
    return DetectionResult(matched=False)


def detect_sql_error(body: str) -> DetectionResult:
    """Détecte des erreurs SQL typiques dans le corps de réponse."""
    return _match_patterns(body, _SQL_ERROR_PATTERNS, "sql_error")


def detect_nosql_error(body: str) -> DetectionResult:
    """Détecte des erreurs NoSQL / Mongo dans le corps de réponse."""
    return _match_patterns(body, _NOSQL_ERROR_PATTERNS, "nosql_error")


def detect_template_error(body: str) -> DetectionResult:
    """Détecte des erreurs de moteur de template (SSTI) dans la réponse."""
    return _match_patterns(body, _TEMPLATE_ERROR_PATTERNS, "template_error")


def detect_xxe(body: str) -> DetectionResult:
    """Détecte des signaux d'XXE dans le corps de réponse."""
    return _match_patterns(body, _XXE_PATTERNS, "xxe")


def detect_path_traversal(body: str) -> DetectionResult:
    """Détecte des fuites liées à la traversée de chemins."""
    return _match_patterns(body, _PATH_TRAVERSAL_PATTERNS, "path_traversal")


def detect_shell_output(body: str) -> DetectionResult:
    """Détecte une sortie shell caractéristique (injection de commandes)."""
    return _match_patterns(body, _SHELL_OUTPUT_PATTERNS, "shell_output")


def detect_deserialization_error(body: str) -> DetectionResult:
    """Détecte des erreurs de désérialisation dans la réponse."""
    return _match_patterns(body, _DESERIALIZATION_PATTERNS, "deserialization_error")


def detect_reflection(body: str, marker: str) -> bool:
    """Vérifie si le marker est présent dans le body de la réponse."""
    return bool(marker) and marker in body


async def detect_time_based(
    probe_fn: Callable[[], Awaitable[float]],
    threshold_ms: float = 900.0,
    confirmations: int = 2,
) -> DetectionResult:
    """Détection time-based par répétition pour filtrer le bruit réseau.

    Args:
        probe_fn: Coroutine qui effectue la requête et retourne elapsed_ms.
        threshold_ms: Seuil de délai en millisecondes.
        confirmations: Nombre de succès consécutifs requis (anti-bruit).

    Returns:
        DetectionResult avec matched=True si confirmations atteint.
    """
    hits = 0
    for _ in range(max(confirmations, 2)):
        try:
            elapsed = await probe_fn()
            if elapsed >= threshold_ms:
                hits += 1
            else:
                hits = 0  # reset sur faux positif
        except Exception:
            hits = 0
        if hits >= confirmations:
            return DetectionResult(
                matched=True,
                evidence=f"Response delayed ≥{threshold_ms}ms (confirmed {confirmations}×)",
                detection_type="timing",
            )
        await asyncio.sleep(0.2)  # court délai entre les probes

    return DetectionResult(matched=False, detection_type="timing")


def diff_baseline(baseline: str, probe: str) -> float:
    """Retourne le ratio de différence entre réponse baseline et probe.

    Valeur 0.0 = identiques, 1.0 = totalement différentes.
    Utilise une comparaison par lignes pour robustesse aux variations mineures.
    """
    if not baseline and not probe:
        return 0.0
    if not baseline or not probe:
        return 1.0
    baseline_lines = set(baseline.splitlines())
    probe_lines = set(probe.splitlines())
    common = baseline_lines & probe_lines
    total = baseline_lines | probe_lines
    if not total:
        return 0.0
    return 1.0 - (len(common) / len(total))


def detect_ssti_eval(body: str) -> bool:
    """Détecte le résultat d'une évaluation SSTI (7*7=49)."""
    # Chercher "49" entouré de contexte non numérique (évite les faux positifs)
    return bool(re.search(r"(?<!\d)49(?!\d)", body))
