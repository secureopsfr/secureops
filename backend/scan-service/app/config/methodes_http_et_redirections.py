"""Configuration des vérifications Méthodes HTTP et redirections.

Référence : docs/verifications/passive/methodes-http-et-redirections.md
"""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class MethodesHttpEtRedirectionsSettings:
    """Paramètres pour les vérifications Méthodes HTTP et redirections.

    Attributes:
        redirect_chain_max: Nombre max de redirections avant finding.
        trace_timeout: Timeout (s) pour requête TRACE.
        trace_max_urls: Limite URLs testées pour TRACE (page + chemins sensibles).
        form_sensitive_paths: Fragments de chemin pour formulaires sensibles (301/302 vs 307/308).
        check_trace: Activer le check TRACE.
        check_head: Activer le check HEAD.
        check_redirect_chain: Activer le check chaîne de redirections.
        check_redirect_301_302: Activer le check 301/302 vs 307/308.
    """

    redirect_chain_max: int
    trace_timeout: float
    trace_max_urls: int
    form_sensitive_paths: tuple[str, ...]
    check_trace: bool
    check_head: bool
    check_redirect_chain: bool
    check_redirect_301_302: bool


_DEFAULT_FORM_SENSITIVE_PATHS = ("/login", "/auth", "/signin", "/register", "/signup")


@lru_cache(maxsize=1)
def get_methodes_http_et_redirections_settings() -> MethodesHttpEtRedirectionsSettings:
    """Charge la section methodes_http_et_redirections depuis config/settings.yml."""
    data = _load_settings_yml()
    raw = data.get("methodes_http_et_redirections") or {}
    checks = raw.get("checks") or {}

    redirect_chain_max = int(raw.get("redirect_chain_max", 5))
    trace_timeout = float(raw.get("trace_timeout", 3.0))
    trace_max_urls = int(raw.get("trace_max_urls", 6))
    form_paths_raw = raw.get("form_sensitive_paths") or list(_DEFAULT_FORM_SENSITIVE_PATHS)
    form_sensitive_paths = tuple(str(p) for p in form_paths_raw)

    return MethodesHttpEtRedirectionsSettings(
        redirect_chain_max=redirect_chain_max,
        trace_timeout=trace_timeout,
        trace_max_urls=trace_max_urls,
        form_sensitive_paths=form_sensitive_paths,
        check_trace=bool(checks.get("trace", True)),
        check_head=bool(checks.get("head", True)),
        check_redirect_chain=bool(checks.get("redirect_chain", True)),
        check_redirect_301_302=bool(checks.get("redirect_301_302", True)),
    )
