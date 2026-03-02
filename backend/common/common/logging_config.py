"""Configuration centralisée du logging pour tous les micro-services.

Usage dans chaque service :

    from common.logging_config import setup_logging, get_logger

    setup_logging(service_name="admin-service")
    logger = get_logger(__name__)

Le module fournit :
- Un format JSON structuré pour la production (activé via ``LOG_FORMAT=json``)
- Un format texte lisible pour le développement (par défaut)
- Un *correlation_id* automatique injecté dans chaque log via le middleware
  ``CorrelationIdMiddleware``
- Un filtre automatique de sanitisation des données sensibles (emails, tokens,
  secrets, URLs de base de données) pour éviter les fuites de PII dans les logs.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Optional

# ────────────────────────── Context Variables ──────────────────────────

correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


# ────────────────────────── Sanitisation ──────────────────────────

# Patterns compilés une seule fois au chargement du module.
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}")
_DB_URL_RE = re.compile(r"(?:postgresql|mysql|sqlite)(?:\+\w+)?://[^\s]+")
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE)
_SECRET_KEY_RE = re.compile(
    r"(?:secret|api[_-]?key|access[_-]?key|private[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?",
    re.IGNORECASE,
)


def mask_email(email: str) -> str:
    """Masque un email pour les logs : ``jean.dupont@example.com`` → ``j***t@e***.com``.

    Args:
        email: adresse email à masquer.

    Returns:
        str: version masquée.
    """
    if not email or "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    parts = domain.rsplit(".", 1)
    domain_name = parts[0] if len(parts) > 1 else domain
    tld = f".{parts[1]}" if len(parts) > 1 else ""
    masked_local = f"{local[0]}***{local[-1]}" if len(local) > 1 else f"{local[0]}***"
    masked_domain = f"{domain_name[0]}***{tld}" if domain_name else "***"
    return f"{masked_local}@{masked_domain}"


def _sanitize_message(message: str) -> str:
    """Applique toutes les règles de sanitisation à un message de log.

    Args:
        message: message brut.

    Returns:
        str: message nettoyé.
    """
    # JWT tokens (avant les emails car les JWT peuvent contenir des '.')
    message = _JWT_RE.sub("[TOKEN_REDACTED]", message)
    # Bearer tokens
    message = _BEARER_RE.sub("Bearer [REDACTED]", message)
    # Database URLs (masquer les credentials)
    message = _DB_URL_RE.sub(lambda m: _mask_db_url(m.group(0)), message)
    # Emails
    message = _EMAIL_RE.sub(lambda m: mask_email(m.group(0)), message)
    # Clés secrètes
    message = _SECRET_KEY_RE.sub(
        lambda m: m.group(0).replace(m.group(1), "[REDACTED]") if m.group(1) else m.group(0),
        message,
    )
    return message


def _mask_db_url(url: str) -> str:
    """Masque les credentials dans une URL de base de données.

    ``postgresql+asyncpg://user:password@host:5432/db``
    → ``postgresql+asyncpg://***:***@host:5432/db``
    """
    match = re.match(r"(\w+(?:\+\w+)?://)([^@]+)@(.+)", url)
    if match:
        return f"{match.group(1)}***:***@{match.group(3)}"
    return "[DB_URL_REDACTED]"


class SensitiveDataFilter(logging.Filter):
    """Filtre de logging qui masque automatiquement les données sensibles.

    S'applique au message formaté ainsi qu'aux arguments du message
    avant leur interpolation.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Modifie le record en place pour masquer les données sensibles.

        Args:
            record: enregistrement de log à filtrer.

        Returns:
            bool: toujours True (on ne supprime jamais le log, on le nettoie).
        """
        # Sanitiser le message principal
        if isinstance(record.msg, str):
            record.msg = _sanitize_message(record.msg)

        # Sanitiser les arguments du message (cas f-string déjà interpolée ou % formatting)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _sanitize_message(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(_sanitize_message(str(a)) if isinstance(a, str) else a for a in record.args)

        return True


# ────────────────────────── JSON Formatter ──────────────────────────


class JSONFormatter(logging.Formatter):
    """Formatteur de logs en JSON structuré (une ligne par enregistrement)."""

    def __init__(self, service_name: str = "unknown") -> None:
        """Initialise le formatteur JSON avec le nom du service."""
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Formate un enregistrement de log en JSON structuré."""
        import json

        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Ajouter le correlation_id s'il est présent
        cid = correlation_id_ctx.get()
        if cid:
            log_entry["correlation_id"] = cid

        # Ajouter les extras pertinents (requête HTTP, scan, etc.)
        extra_keys = (
            "path",
            "status_code",
            "method",
            "duration_ms",
            "user_id",
            "request_id",
            "duration_seconds",
            "nb_findings",
            "status",
        )
        for key in extra_keys:
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        # Ajouter l'exception si présente
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ────────────────────────── Text Formatter ──────────────────────────


class TextFormatter(logging.Formatter):
    """Formatteur lisible pour le développement, avec correlation_id."""

    def __init__(self, service_name: str = "unknown") -> None:
        """Initialise le formatteur texte avec le nom du service."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        """Formate un enregistrement de log en texte lisible."""
        cid = correlation_id_ctx.get()
        if cid:
            record.msg = f"[{cid[:8]}] {record.msg}"
        return super().format(record)


# ────────────────────────── Setup ──────────────────────────


def setup_logging(
    service_name: str = "unknown",
    level: str | None = None,
) -> None:
    """Configure le logging racine pour un micro-service.

    La variable d'environnement ``LOG_FORMAT`` contrôle le format :
    - ``json`` → JSON structuré (recommandé en production)
    - toute autre valeur ou absente → texte lisible

    La variable d'environnement ``LOG_LEVEL`` permet de surcharger le niveau.

    Args:
        service_name: nom du service (apparaît dans chaque log).
        level: niveau de log (DEBUG, INFO, WARNING, …). Si None, utilise LOG_LEVEL ou INFO.
    """
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    log_level = level or os.getenv("LOG_LEVEL", "INFO")

    root = logging.getLogger()

    # Éviter d'ajouter des handlers en double (hot-reload)
    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(JSONFormatter(service_name=service_name))
    else:
        handler.setFormatter(TextFormatter(service_name=service_name))

    # Filtre de sanitisation des données sensibles (emails, tokens, secrets)
    handler.addFilter(SensitiveDataFilter())

    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.addHandler(handler)

    # Réduire le bruit des bibliothèques tierces
    for noisy_logger in ("uvicorn.access", "botocore", "boto3", "urllib3", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Raccourci pour obtenir un logger nommé.

    Args:
        name: nom du logger (typiquement ``__name__``).

    Returns:
        logging.Logger: logger configuré.
    """
    return logging.getLogger(name)
