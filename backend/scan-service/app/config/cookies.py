"""Configuration des heuristiques cookies."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_SESSION_LIKE_NAMES: tuple[str, ...] = (
    "session",
    "sess",
    "auth",
    "token",
    "csrf",
    "_token",
    "phpsessid",
    "jsessionid",
    "connect.sid",
    "asp.net_sessionid",
    "laravel_session",
    "symfony",
    "wordpress_logged_in",
    "wp-settings",
    "sid",
    "jwt",
    "access_token",
    "refresh_token",
)
_DEFAULT_THIRD_PARTY_LIKE_NAMES: tuple[str, ...] = ("_ga", "_gid", "_gat", "_fbp", "_gcl_au", "_gac_", "_dc")
_DEFAULT_SESSION_MAX_AGE_SECONDS = 86400


@dataclass(frozen=True)
class CookiesSettings:
    """Paramètres de détection des cookies sensibles."""

    session_like_names: tuple[str, ...]
    third_party_like_names: tuple[str, ...]
    session_max_age_seconds: int


@lru_cache(maxsize=1)
def get_cookies_settings() -> CookiesSettings:
    """Charge la section cookies_heuristics depuis config/settings.yml."""
    data = _load_settings_yml()
    c = data.get("cookies_heuristics") or {}
    session_like = tuple(str(v) for v in (c.get("session_like_names") or _DEFAULT_SESSION_LIKE_NAMES))
    third_party = tuple(str(v) for v in (c.get("third_party_like_names") or _DEFAULT_THIRD_PARTY_LIKE_NAMES))
    session_max_age = int(c.get("session_max_age_seconds", _DEFAULT_SESSION_MAX_AGE_SECONDS))
    return CookiesSettings(
        session_like_names=session_like,
        third_party_like_names=third_party,
        session_max_age_seconds=session_max_age,
    )
