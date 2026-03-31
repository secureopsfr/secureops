"""Configuration du scan intrusif : scoring, budgets, garde-fous."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml

# Poids par catégorie pour le scoring intrusif (total = 100 pour normalisation)
_DEFAULT_INTRUSIVE_WEIGHTS: dict[str, int] = {
    "open_redirect": 3,
    "methodes_http": 2,
    "cors_actif": 5,
    "parametres_reflechis": 6,
    "sql_injection": 10,
    "path_traversal": 7,
    "csrf": 5,
    "idor": 8,
    "command_injection": 10,
    "nosql_injection": 7,
    "dos_rate_limit": 3,
    "auth_bruteforce": 7,
    "session_fixation": 6,
    "upload_abuse": 7,
    "mass_assignment": 5,
    "graphql_abuse": 4,
    "api_schema_abuse": 3,
    "ssrf": 8,
    "xxe": 7,
    "ssti": 8,
    "insecure_deserialization": 7,
    "lfi_rfi": 7,
    "host_header": 5,
    "cache_poisoning": 4,
    "request_smuggling": 6,
    "race_conditions": 4,
    "business_logic": 5,
    "websocket_authz": 4,
    "graphql_subscriptions": 3,
    "oauth_oidc": 6,
    "grpc_abuse": 3,
    "object_storage": 4,
    "service_mesh": 4,
}

_DEFAULT_INTRUSIVE_PENALTIES: dict[str, int] = {
    "critical": 100,
    "high": 50,
    "medium": 25,
    "low": 10,
    "info": 0,
}


@dataclass(frozen=True)
class IntrusiveScanSettings:
    """Configuration complète du scan intrusif."""

    category_weights: dict[str, int]
    severity_penalties: dict[str, int]
    # Budget de requêtes
    max_requests_per_param: int = 3
    budget_per_category: int = 30
    # Timeouts (secondes)
    probe_timeout: float = 8.0
    time_based_threshold_ms: float = 900.0
    time_based_confirmations: int = 2
    # Jitter entre requêtes (ms)
    jitter_min_ms: int = 50
    jitter_max_ms: int = 250
    # DoS P0 — burst sans sleep artificiel pour un signal réaliste
    dos_burst_count: int = 20  # nombre total de requêtes envoyées
    dos_burst_duration_s: float = 3.0  # durée max du burst (cap de sécurité)
    dos_min_requests_for_finding: int = 15  # seuil minimum avant de signaler l'absence
    # Mode destructif
    destructive_mode_enabled: bool = False


@lru_cache(maxsize=1)
def get_intrusive_scan_settings() -> IntrusiveScanSettings:
    """Charge la section intrusive_scan depuis config/settings.yml."""
    data = _load_settings_yml()
    s = data.get("intrusive_scan") or {}
    scoring = s.get("scoring") or {}
    cw = scoring.get("category_weights") or _DEFAULT_INTRUSIVE_WEIGHTS
    sp = scoring.get("severity_penalties") or _DEFAULT_INTRUSIVE_PENALTIES
    return IntrusiveScanSettings(
        category_weights={k: int(v) for k, v in cw.items()},
        severity_penalties={k: int(v) for k, v in sp.items()},
        max_requests_per_param=int(s.get("max_requests_per_param", 3)),
        budget_per_category=int(s.get("budget_per_category", 30)),
        probe_timeout=float(s.get("probe_timeout", 8.0)),
        time_based_threshold_ms=float(s.get("time_based_threshold_ms", 900.0)),
        time_based_confirmations=int(s.get("time_based_confirmations", 2)),
        jitter_min_ms=int(s.get("jitter_min_ms", 50)),
        jitter_max_ms=int(s.get("jitter_max_ms", 250)),
        dos_burst_count=int(s.get("dos_burst_count", 20)),
        dos_burst_duration_s=float(s.get("dos_burst_duration_s", 3.0)),
        dos_min_requests_for_finding=int(s.get("dos_min_requests_for_finding", 15)),
        destructive_mode_enabled=bool(s.get("destructive_mode_enabled", False)),
    )
