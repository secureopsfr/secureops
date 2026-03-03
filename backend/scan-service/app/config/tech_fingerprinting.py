"""Configuration tech fingerprinting (roadmap §5.1.7)."""

from functools import lru_cache

from app.config._base import _load_settings_yml

_DEFAULT_THRESHOLDS: dict[str, str] = {
    "nginx": "1.20.0",
    "apache": "2.4.50",
    "php": "8.0.0",
    "wordpress": "6.0.0",
    "drupal": "9.0.0",
}


@lru_cache(maxsize=1)
def get_tech_fingerprinting_thresholds() -> dict[str, str]:
    """Charge les seuils de versions vulnérables depuis config/settings.yml.

    Returns:
        dict[str, str]: product -> min_safe_version.
    """
    data = _load_settings_yml()
    tf = data.get("tech_fingerprinting") or {}
    custom = tf.get("vulnerable_thresholds") or {}
    if not custom:
        return _DEFAULT_THRESHOLDS
    result = dict(_DEFAULT_THRESHOLDS)
    for k, v in custom.items():
        if isinstance(v, str):
            result[str(k).lower()] = v
    return result
