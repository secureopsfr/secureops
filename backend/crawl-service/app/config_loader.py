"""Chargement de configuration pour crawl-service. Source unique : config/settings.yml."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from common.config_base import (
    BlacklistSettings,
    SsrfSettings,
    UrlValidationSettings,
    create_simple_settings,
    load_yaml,
    parse_blacklist_settings,
    parse_ssrf_settings,
    parse_url_validation_settings,
)

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_CFG_PATH = _SERVICE_ROOT / "config" / "settings.yml"


@lru_cache(maxsize=1)
def _get_data() -> dict:
    """Charge config/settings.yml une fois (mis en cache)."""
    return load_yaml(_CFG_PATH) or {}


# ---------------------------------------------------------------------------
# SSRF
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_ssrf_settings() -> SsrfSettings:
    """Charge la section SSRF depuis config/settings.yml."""
    data = _get_data()
    return parse_ssrf_settings(data.get("ssrf"))


# ---------------------------------------------------------------------------
# Blacklist
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_blacklist_settings() -> BlacklistSettings:
    """Charge la section blacklist depuis config/settings.yml."""
    data = _get_data()
    return parse_blacklist_settings(data.get("blacklist"))


# ---------------------------------------------------------------------------
# URL Validation
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_url_validation_settings() -> UrlValidationSettings:
    """Charge la section url_validation depuis config/settings.yml."""
    data = _get_data()
    return parse_url_validation_settings(data.get("url_validation"))


# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------


_DEFAULT_ROBOTS_PATTERNS: tuple[tuple[str, str], ...] = (
    ("admin", "high"),
    ("administrator", "high"),
    ("backend", "high"),
    ("manage", "high"),
    ("api", "medium"),
    ("config", "high"),
    ("configs", "high"),
    ("configuration", "high"),
    ("backup", "high"),
    ("backups", "high"),
    ("dump", "high"),
    ("private", "high"),
    ("internal", "high"),
    ("secret", "high"),
    ("cgi-bin", "medium"),
    ("/bin/", "medium"),
    ("upload", "medium"),
    ("uploads", "medium"),
    ("media", "medium"),
    ("files", "medium"),
    ("tmp", "medium"),
    ("temp", "medium"),
    ("cache", "medium"),
    ("/db/", "high"),
    ("database", "high"),
    ("sql", "high"),
    (".git", "critical"),
    (".env", "critical"),
    ("login", "medium"),
    ("auth", "medium"),
    ("signin", "medium"),
)


@lru_cache(maxsize=1)
def get_robots_txt_messages() -> dict[str, str]:
    """Charge les messages robots_txt depuis config/settings.yml."""
    data = _get_data()
    msg = (data.get("robots_txt") or {}).get("messages") or {}
    return {
        "unavailable": str(msg.get("unavailable", "Impossible de récupérer robots.txt (connexion refusée ou timeout).")),
    }


@lru_cache(maxsize=1)
def get_robots_txt_settings() -> tuple[tuple[str, str], ...]:
    """Charge la section robots_txt (patterns) depuis config/settings.yml."""
    data = _get_data()
    patterns_raw = (data.get("robots_txt") or {}).get("patterns") or []
    if not patterns_raw:
        return _DEFAULT_ROBOTS_PATTERNS
    result: list[tuple[str, str]] = []
    for item in patterns_raw:
        if isinstance(item, dict):
            pattern = str(item.get("pattern", ""))
            severity = str(item.get("severity", "medium"))
            if pattern:
                result.append((pattern, severity))
    return tuple(result) if result else _DEFAULT_ROBOTS_PATTERNS


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrawlerSettings:
    """Paramètres du crawler HTTP."""

    max_depth: int
    max_urls: int
    timeout_seconds: float
    stream_timeout_seconds: float
    respect_robots_txt: bool
    user_agent: str
    excluded_extensions: tuple[str, ...]
    excluded_path_prefixes: tuple[str, ...]
    playwright_page_timeout_ms: int
    playwright_network_idle_timeout_ms: int
    max_child_sitemaps: int
    consecutive_403_threshold: int
    api_patterns: tuple[str, ...]
    anti_bot_indicators: tuple[str, ...]


@dataclass(frozen=True)
class AsyncJobsSettings:
    """Paramètres async jobs pour crawl-service."""

    worker_poll_interval_seconds: float
    job_timeout_seconds: int
    max_attempts: int
    progress_batch_window_seconds: float


_DEFAULT_EXCLUDED = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".js",
    ".css",
)
_DEFAULT_PATH_PREFIXES = ("/_next/", "/__next/", "/static/")
_DEFAULT_API_PATTERNS = ("/api", "/graphql", "/v1", "/rest", "/swagger", "/api-docs")
_DEFAULT_ANTI_BOT = (
    "checking your browser",
    "cf-browser-verification",
    "challenge-running",
    "datadome",
    "blocked",
    "ak_bmsc",
    "bot manager",
    "g-recaptcha",
    "hcaptcha",
    "recaptcha",
    "access denied",
    "unusual traffic",
    "please enable javascript",
    "enable javascript",
    "cloudflare",
    "ddos protection",
    "ray id",
    "performance and security by cloudflare",
    "veuillez patienter",
    "vérification en cours",
    "just a moment",
    "human verification",
    "security check",
)


@lru_cache(maxsize=1)
def get_crawler_settings() -> CrawlerSettings:
    """Charge la section crawler depuis config/settings.yml."""
    data = _get_data()
    c = data.get("crawler") or {}
    ext = tuple(str(e).lower() for e in (c.get("excluded_extensions") or []))
    prefixes = tuple(str(p) for p in (c.get("excluded_path_prefixes") or []))
    api = tuple(str(p) for p in (c.get("api_patterns") or []))
    anti_bot = tuple(str(i).lower() for i in (c.get("anti_bot_indicators") or []))
    return CrawlerSettings(
        max_depth=int(c.get("max_depth", 2)),
        max_urls=int(c.get("max_urls", 50)),
        timeout_seconds=float(c.get("timeout_seconds", 60.0)),
        stream_timeout_seconds=float(c.get("stream_timeout_seconds", 120.0)),
        respect_robots_txt=bool(c.get("respect_robots_txt", True)),
        user_agent=str(c.get("user_agent", "SecureOps-Crawler/1.0")),
        excluded_extensions=ext if ext else _DEFAULT_EXCLUDED,
        excluded_path_prefixes=prefixes if prefixes else _DEFAULT_PATH_PREFIXES,
        playwright_page_timeout_ms=int(c.get("playwright_page_timeout_ms", 15000)),
        playwright_network_idle_timeout_ms=int(c.get("playwright_network_idle_timeout_ms", 5000)),
        max_child_sitemaps=int(c.get("max_child_sitemaps", 50)),
        consecutive_403_threshold=int(c.get("consecutive_403_threshold", 5)),
        api_patterns=api if api else _DEFAULT_API_PATTERNS,
        anti_bot_indicators=anti_bot if anti_bot else _DEFAULT_ANTI_BOT,
    )


@lru_cache(maxsize=1)
def get_async_jobs_settings() -> AsyncJobsSettings:
    """Charge la section async_jobs depuis config/settings.yml."""
    data = _get_data()
    cfg = data.get("async_jobs") or {}
    return AsyncJobsSettings(
        worker_poll_interval_seconds=float(cfg.get("worker_poll_interval_seconds", 2.0)),
        job_timeout_seconds=int(cfg.get("job_timeout_seconds", 300)),
        max_attempts=int(cfg.get("max_attempts", 3)),
        progress_batch_window_seconds=float(cfg.get("progress_batch_window_seconds", 0.2)),
    )


# ---------------------------------------------------------------------------
# Settings (general, server, database, routers) via create_simple_settings
# ---------------------------------------------------------------------------

settings = create_simple_settings("crawl-service", default_port=8014, caller_file=__file__)

__all__ = [
    "AsyncJobsSettings",
    "BlacklistSettings",
    "CrawlerSettings",
    "SsrfSettings",
    "UrlValidationSettings",
    "get_async_jobs_settings",
    "get_blacklist_settings",
    "get_crawler_settings",
    "get_robots_txt_messages",
    "get_robots_txt_settings",
    "get_ssrf_settings",
    "get_url_validation_settings",
    "settings",
]
