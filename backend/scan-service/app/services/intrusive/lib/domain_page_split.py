"""Constantes et helpers pour la séparation domain-phase / per-page.

Domain-phase : checks exécutés une seule fois par domaine (multi-URL).
Per-page     : checks exécutés sur chaque URL individuellement.

Ces constantes doivent rester en sync avec le roadmap §0.6.
"""

from __future__ import annotations

# Checks exécutés une fois par domaine (domain-phase)
DOMAIN_PHASE_CHECKS: frozenset[str] = frozenset(
    {
        "cors_actif",
        "methodes_http",
        "graphql_abuse",
        "api_schema_abuse",
        "mass_assignment",
        "ssrf",
        "xxe",
        "grpc_abuse",
        "object_storage",
        "service_mesh",
        "auth_bruteforce",
        "dos_p0",
    }
)

# Checks exécutés sur chaque page individuellement
PER_PAGE_CHECKS: frozenset[str] = frozenset(
    {
        "open_redirect",
        "parametres_reflechis",
        "sqli",
        "path_traversal",
        "csrf",
        "idor",
        "idor_complet",
        "command_injection",
        "nosqli",
        "upload_abuse",
        "ssti",
        "insecure_deserialization",
        "lfi_rfi",
        "host_header",
        "cache_poisoning",
        "request_smuggling",
        "race_conditions",
        "business_logic",
        "websocket_authz",
        "oauth_oidc",
        "session_fixation",
        "graphql_subscriptions",
    }
)


def is_domain_phase(check_name: str) -> bool:
    """Retourne True si le check doit tourner en domain-phase."""
    return check_name in DOMAIN_PHASE_CHECKS
