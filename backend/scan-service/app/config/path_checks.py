"""Configuration path checks : exposed_files et directory_listing (roadmap §3.4, §3.5)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class PathCheckConfig:
    """Configuration commune pour une vérification par chemin."""

    path: str
    severity: str
    message: str


ExposedFileConfig = PathCheckConfig
DirectoryListingConfig = PathCheckConfig

_DEFAULT_EXPOSED: tuple[tuple[str, str, str], ...] = (
    ("/.env", "critical", "Fichier .env exposé : credentials et secrets accessibles."),
    ("/.git/config", "critical", "Fichier .git/config exposé : dépôt Git accessible."),
    ("/backup.zip", "high", "Archive backup.zip exposée : sauvegarde accessible."),
    ("/phpinfo.php", "high", "phpinfo.php exposé : configuration PHP révélée."),
    ("/admin/", "medium", "Interface /admin/ exposée : à protéger par authentification."),
    ("/.DS_Store", "low", "Fichier .DS_Store exposé : structure des répertoires révélée."),
)
_DEFAULT_DIRECTORY: tuple[tuple[str, str, str], ...] = (
    ("/uploads/", "high", "Directory listing activé sur /uploads/ : fichiers utilisateurs énumérables."),
    ("/assets/", "medium", "Directory listing activé sur /assets/ : structure révélée."),
    ("/static/", "medium", "Directory listing activé sur /static/ : structure révélée."),
)
_DEFAULT_UPGRADE: tuple[str, ...] = ("/.git/config", "/.env")


def _get_path_check_settings(section: str, defaults: tuple[tuple[str, str, str], ...]) -> tuple[PathCheckConfig, ...]:
    """Charge une section YAML de type path check."""
    data = _load_settings_yml()
    block = data.get(section) or {}
    paths_raw = block.get("paths") or []
    if not paths_raw:
        return tuple(PathCheckConfig(p[0], p[1], p[2]) for p in defaults)
    result: list[PathCheckConfig] = []
    for item in paths_raw:
        if isinstance(item, dict):
            path = str(item.get("path", ""))
            severity = str(item.get("severity", "medium"))
            message = str(item.get("message", ""))
            result.append(PathCheckConfig(path=path, severity=severity, message=message))
    return tuple(result)


def _get_path_check_max_body(section: str, default: int) -> int:
    """Retourne la limite de lecture du corps (octets)."""
    data = _load_settings_yml()
    block = data.get(section) or {}
    return int(block.get("max_body_bytes", default))


@lru_cache(maxsize=1)
def get_exposed_files_settings() -> tuple[PathCheckConfig, ...]:
    """Charge la section exposed_files depuis config/settings.yml."""
    return _get_path_check_settings("exposed_files", _DEFAULT_EXPOSED)


@lru_cache(maxsize=1)
def get_exposed_files_max_body() -> int:
    """Retourne la limite de lecture du corps pour exposed_files."""
    return _get_path_check_max_body("exposed_files", 8192)


@lru_cache(maxsize=1)
def get_directory_listing_settings() -> tuple[PathCheckConfig, ...]:
    """Charge la section directory_listing depuis config/settings.yml."""
    return _get_path_check_settings("directory_listing", _DEFAULT_DIRECTORY)


@lru_cache(maxsize=1)
def get_directory_listing_max_body() -> int:
    """Retourne la limite de lecture du corps pour directory_listing."""
    return _get_path_check_max_body("directory_listing", 8192)


@lru_cache(maxsize=1)
def get_exposed_files_severity_upgrade() -> tuple[str, ...]:
    """Charge les chemins à upgrader en critical."""
    data = _load_settings_yml()
    ef = data.get("exposed_files") or {}
    paths = ef.get("severity_upgrade") or list(_DEFAULT_UPGRADE)
    return tuple(str(p) for p in paths)
