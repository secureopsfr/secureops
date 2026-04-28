"""Configuration PDF : rendu, catégories, libellés i18n, footer (settings.yml)."""

from dataclasses import dataclass
from functools import lru_cache

from app.config._base import _load_settings_yml


@dataclass(frozen=True)
class PdfRenderSettings:
    """Paramètres de rendu du rapport PDF (limites de texte, seuils de score)."""

    evidence_max_len: int
    recommendation_max_len: int
    cover_url_max_len: int
    cover_logo_primary_color: str
    cover_logo_secondary_color: str
    score_good: int
    score_medium: int
    score_color_good: str
    score_color_medium: str
    score_color_low: str
    references_max_list: int
    references_max_inline: int
    severity_badges: dict[str, dict[str, str]]
    matrix_border_color: str
    matrix_cells: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class PdfCategoryConfig:
    """Configuration des catégories pour le rapport PDF."""

    order: tuple[str, ...]
    checked: tuple[str, ...]
    labels_fr: dict[str, str]
    labels_en: dict[str, str]


@dataclass(frozen=True)
class PdfSettings:
    """Configuration PDF : rendu, footer et catégories."""

    footer_url: str
    render: PdfRenderSettings
    categories: PdfCategoryConfig
    intrusive_categories: PdfCategoryConfig


# Mapping catégorie-check → macro-catégorie pour les scans intrusifs
INTRUSIVE_CATEGORY_MAPPING: dict[str, str] = {
    # injections
    "sql_injection": "injections",
    "nosql_injection": "injections",
    "command_injection": "injections",
    "ssti": "injections",
    "xxe": "injections",
    "lfi_rfi": "injections",
    "path_traversal": "injections",
    # access_control
    "cors_actif": "access_control",
    "csrf": "access_control",
    "host_header": "access_control",
    "open_redirect": "access_control",
    "ssrf": "access_control",
    "methodes_http": "access_control",
    # auth_sessions
    "auth_bruteforce": "auth_sessions",
    "session_fixation": "auth_sessions",
    "oauth_oidc": "auth_sessions",
    "idor": "auth_sessions",
    # client_injection
    "parametres_reflechis": "client_injection",
    # business_data
    "business_logic": "business_data",
    "race_conditions": "business_data",
    "dos_rate_limit": "business_data",
    "upload_abuse": "business_data",
    "insecure_deserialization": "business_data",
    "mass_assignment": "business_data",
    # api_protocols
    "graphql_abuse": "api_protocols",
    "graphql_subscriptions": "api_protocols",
    "api_schema_abuse": "api_protocols",
    "grpc_abuse": "api_protocols",
    "websocket_authz": "api_protocols",
    # infra_cache
    "cache_poisoning": "infra_cache",
    "request_smuggling": "infra_cache",
    "service_mesh": "infra_cache",
    "object_storage": "infra_cache",
}


_DEFAULT_RENDER = PdfRenderSettings(
    evidence_max_len=800,
    recommendation_max_len=800,
    cover_url_max_len=60,
    cover_logo_primary_color="#38bdf8",
    cover_logo_secondary_color="#0f172a",
    score_good=80,
    score_medium=50,
    score_color_good="#10b981",
    score_color_medium="#f59e0b",
    score_color_low="#ef4444",
    references_max_list=10,
    references_max_inline=3,
    severity_badges={
        "critical": {"bg": "#fef2f2", "text": "#dc2626"},
        "high": {"bg": "#fffbeb", "text": "#d97706"},
        "medium": {"bg": "#fffbeb", "text": "#d97706"},
        "low": {"bg": "#eff6ff", "text": "#2563eb"},
        "info": {"bg": "#eff6ff", "text": "#2563eb"},
    },
    matrix_border_color="#333333",
    matrix_cells=(
        ("#22c55e", "#22c55e", "#facc15", "#facc15"),
        ("#22c55e", "#facc15", "#f97316", "#f97316"),
        ("#facc15", "#f97316", "#ef4444", "#ef4444"),
        ("#f97316", "#ef4444", "#ef4444", "#ef4444"),
    ),
)
_DEFAULT_INTRUSIVE_ORDER = (
    "injections",
    "access_control",
    "auth_sessions",
    "client_injection",
    "business_data",
    "api_protocols",
    "infra_cache",
    "other",
)
_DEFAULT_INTRUSIVE_CHECKED = (
    "injections",
    "access_control",
    "auth_sessions",
    "client_injection",
    "business_data",
    "api_protocols",
    "infra_cache",
)
_DEFAULT_INTRUSIVE_LABELS_FR = {
    "injections": "Injections",
    "access_control": "Contrôle d'accès",
    "auth_sessions": "Authentification & Sessions",
    "client_injection": "Injections côté client",
    "business_data": "Logique métier & Données",
    "api_protocols": "APIs & Protocoles modernes",
    "infra_cache": "Infrastructure & Cache",
    "other": "Autres",
}
_DEFAULT_INTRUSIVE_LABELS_EN = {
    "injections": "Injections",
    "access_control": "Access Control",
    "auth_sessions": "Authentication & Sessions",
    "client_injection": "Client-side Injections",
    "business_data": "Business Logic & Data",
    "api_protocols": "APIs & Modern Protocols",
    "infra_cache": "Infrastructure & Cache",
    "other": "Other",
}

_DEFAULT_ORDER = (
    "tls",
    "headers",
    "cache",
    "integrity",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "sitemap",
    "tech_fingerprinting",
    "information_disclosure",
    "cors_cross_origin",
    "other",
)
_DEFAULT_CHECKED = (
    "tls",
    "headers",
    "cache",
    "integrity",
    "cookies",
    "exposed_files",
    "directory_listing",
    "robots_txt",
    "sitemap",
    "tech_fingerprinting",
    "information_disclosure",
    "cors_cross_origin",
)
_DEFAULT_LABELS_FR = {
    "tls": "TLS / HTTPS",
    "headers": "En-têtes de sécurité",
    "cache": "Cache et performances",
    "integrity": "Intégrité et sous-ressources",
    "cookies": "Cookies",
    "exposed_files": "Fichiers exposés",
    "directory_listing": "Listage de répertoires",
    "robots_txt": "robots.txt",
    "sitemap": "Plan du site",
    "tech_fingerprinting": "Empreinte technologique",
    "information_disclosure": "Divulgation d'information",
    "cors_cross_origin": "CORS et cross-origin",
    "other": "Autres",
}
_DEFAULT_LABELS_EN = {
    "tls": "TLS / HTTPS",
    "headers": "Security Headers",
    "cache": "Cache and performance",
    "integrity": "Integrity and subresources",
    "cookies": "Cookies",
    "exposed_files": "Exposed files",
    "directory_listing": "Directory listing",
    "robots_txt": "robots.txt",
    "sitemap": "Sitemap",
    "tech_fingerprinting": "Tech fingerprinting",
    "information_disclosure": "Information disclosure",
    "cors_cross_origin": "CORS and cross-origin",
    "other": "Other",
}


@lru_cache(maxsize=1)
def get_pdf_settings() -> PdfSettings:
    """Charge la section pdf depuis config/settings.yml."""
    data = _load_settings_yml()
    p = data.get("pdf") or {}
    footer_url = str(p.get("footer_url") or "https://secureops.example.com")

    r = p.get("render") or {}
    severity_badges = r.get("severity_badges") or _DEFAULT_RENDER.severity_badges
    matrix = r.get("matrix") or {}
    matrix_cells_raw = matrix.get("cells") or _DEFAULT_RENDER.matrix_cells
    matrix_cells = tuple(tuple(str(color) for color in row) for row in matrix_cells_raw)
    render = PdfRenderSettings(
        evidence_max_len=int(r.get("evidence_max_len") or _DEFAULT_RENDER.evidence_max_len),
        recommendation_max_len=int(r.get("recommendation_max_len") or _DEFAULT_RENDER.recommendation_max_len),
        cover_url_max_len=int(r.get("cover_url_max_len") or _DEFAULT_RENDER.cover_url_max_len),
        cover_logo_primary_color=str(r.get("cover_logo_primary_color") or _DEFAULT_RENDER.cover_logo_primary_color),
        cover_logo_secondary_color=str(r.get("cover_logo_secondary_color") or _DEFAULT_RENDER.cover_logo_secondary_color),
        score_good=int(r.get("score_good") or _DEFAULT_RENDER.score_good),
        score_medium=int(r.get("score_medium") or _DEFAULT_RENDER.score_medium),
        score_color_good=str(r.get("score_color_good") or _DEFAULT_RENDER.score_color_good),
        score_color_medium=str(r.get("score_color_medium") or _DEFAULT_RENDER.score_color_medium),
        score_color_low=str(r.get("score_color_low") or _DEFAULT_RENDER.score_color_low),
        references_max_list=int(r.get("references_max_list") or _DEFAULT_RENDER.references_max_list),
        references_max_inline=int(r.get("references_max_inline") or _DEFAULT_RENDER.references_max_inline),
        severity_badges={
            str(k): {
                "bg": str(v.get("bg", "")) if isinstance(v, dict) else "",
                "text": str(v.get("text", "")) if isinstance(v, dict) else "",
            }
            for k, v in severity_badges.items()
        },
        matrix_border_color=str(matrix.get("border_color") or _DEFAULT_RENDER.matrix_border_color),
        matrix_cells=matrix_cells,
    )

    cats = p.get("categories") or {}
    order = tuple(cats.get("order") or _DEFAULT_ORDER)
    checked = tuple(cats.get("checked") or _DEFAULT_CHECKED)
    labels_fr = dict(cats.get("labels_fr") or _DEFAULT_LABELS_FR)
    labels_en = dict(cats.get("labels_en") or _DEFAULT_LABELS_EN)

    icats = p.get("intrusive_categories") or {}
    intrusive_order = tuple(icats.get("order") or _DEFAULT_INTRUSIVE_ORDER)
    intrusive_checked = tuple(icats.get("checked") or _DEFAULT_INTRUSIVE_CHECKED)
    intrusive_labels_fr = dict(icats.get("labels_fr") or _DEFAULT_INTRUSIVE_LABELS_FR)
    intrusive_labels_en = dict(icats.get("labels_en") or _DEFAULT_INTRUSIVE_LABELS_EN)

    return PdfSettings(
        footer_url=footer_url,
        render=render,
        categories=PdfCategoryConfig(
            order=order,
            checked=checked,
            labels_fr=labels_fr,
            labels_en=labels_en,
        ),
        intrusive_categories=PdfCategoryConfig(
            order=intrusive_order,
            checked=intrusive_checked,
            labels_fr=intrusive_labels_fr,
            labels_en=intrusive_labels_en,
        ),
    )


def get_category_labels(lang: str, scan_mode: str = "passive") -> dict[str, str]:
    """Retourne les libellés de catégories pour la langue et le mode donnés."""
    settings = get_pdf_settings()
    cat_config = settings.intrusive_categories if scan_mode == "intrusive" else settings.categories
    return cat_config.labels_en if lang == "en" else cat_config.labels_fr


def get_category_config(scan_mode: str = "passive") -> PdfCategoryConfig:
    """Retourne la config catégories selon le mode de scan."""
    settings = get_pdf_settings()
    return settings.intrusive_categories if scan_mode == "intrusive" else settings.categories
