"""Configuration robots.txt (roadmap §3.6)."""

from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_PATTERNS: tuple[tuple[str, str], ...] = (
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
def get_robots_txt_settings() -> tuple[tuple[str, str], ...]:
    """Charge la section robots_txt depuis config/settings.yml."""
    data = _load_settings_yml()
    rt = data.get("robots_txt") or {}
    patterns_raw = rt.get("patterns") or []
    if not patterns_raw:
        return _DEFAULT_PATTERNS
    result: list[tuple[str, str]] = []
    for item in patterns_raw:
        if isinstance(item, dict):
            pattern = str(item.get("pattern", ""))
            severity = str(item.get("severity", "medium"))
            if pattern:
                result.append((pattern, severity))
    return tuple(result) if result else _DEFAULT_PATTERNS
