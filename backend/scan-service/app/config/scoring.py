"""Configuration du scoring (roadmap §5)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class ScoringSettings:
    """Configuration du scoring : pondération et pénalités."""

    category_weights: dict[str, int]
    severity_penalties: dict[str, int]


_DEFAULT_WEIGHTS: dict[str, int] = {
    "tls": 25,
    "headers": 25,
    "cache": 5,
    "integrity": 5,
    "cookies": 20,
    "exposed_files": 10,
    "directory_listing": 10,
    "robots_txt": 5,
    "sitemap": 5,
    "tech_fingerprinting": 5,
    "information_disclosure": 5,
    "cors_cross_origin": 5,
    "methodes_http_et_redirections": 5,
    "apis_et_formats": 5,
}
_DEFAULT_PENALTIES: dict[str, int] = {
    "critical": 100,
    "high": 50,
    "medium": 25,
    "low": 10,
    "info": 0,
}


@lru_cache(maxsize=1)
def get_scoring_settings() -> ScoringSettings:
    """Charge la section scoring depuis config/settings.yml."""
    data = _load_settings_yml()
    s = data.get("scoring") or {}
    cw = s.get("category_weights") or _DEFAULT_WEIGHTS
    sp = s.get("severity_penalties") or _DEFAULT_PENALTIES
    return ScoringSettings(
        category_weights={k: int(v) for k, v in cw.items()},
        severity_penalties={k: int(v) for k, v in sp.items()},
    )
