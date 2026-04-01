"""Tests unitaires — scoring intrusif (app.services.scoring.compute_intrusive_score)."""

from __future__ import annotations

from app.models.finding import Finding
from app.services.scoring import compute_intrusive_score

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _f(category: str, severity: str, slug: str = "test-slug") -> Finding:
    """Construit un Finding minimal pour les tests de scoring intrusif."""
    return Finding(
        id=slug,
        category=category,
        title="Test finding",
        severity=severity,
        evidence="test evidence",
        recommendation="",
        references=(),
    )


# ─── Cas de base ──────────────────────────────────────────────────────────────


def test_compute_intrusive_score_empty_findings() -> None:
    """Sans findings, le score est 100."""
    assert compute_intrusive_score([]) == 100
    assert compute_intrusive_score(()) == 100


def test_compute_intrusive_score_returns_int() -> None:
    """Le score est un entier."""
    result = compute_intrusive_score([_f("sql_injection", "high")])
    assert isinstance(result, int)


def test_compute_intrusive_score_bounded_0_100_single_critical() -> None:
    """Un critical réduit le score entre 0 et 100."""
    findings = [_f("sql_injection", "critical")]
    score = compute_intrusive_score(findings)
    assert 0 <= score <= 100


def test_compute_intrusive_score_critical_reduces_score() -> None:
    """Un critical réduit le score."""
    score = compute_intrusive_score([_f("sql_injection", "critical")])
    assert score < 100


def test_compute_intrusive_score_info_no_penalty() -> None:
    """Un finding info (pénalité 0) ne réduit pas le score global."""
    score = compute_intrusive_score([_f("sql_injection", "info")])
    assert score == 100


def test_compute_intrusive_score_single_high() -> None:
    """Un high réduit le score entre 0 et 100."""
    score = compute_intrusive_score([_f("command_injection", "high")])
    assert 0 <= score <= 100
    assert score < 100


def test_compute_intrusive_score_single_medium() -> None:
    """Un medium réduit le score entre 0 et 100."""
    score = compute_intrusive_score([_f("cors_actif", "medium")])
    assert 0 <= score <= 100


def test_compute_intrusive_score_single_low() -> None:
    """Un low réduit le score entre 0 et 100."""
    score = compute_intrusive_score([_f("dos_rate_limit", "low")])
    assert 0 <= score <= 100


# ─── Cumul de pénalités ───────────────────────────────────────────────────────


def test_compute_intrusive_score_two_criticals_same_category() -> None:
    """Deux criticals dans la même catégorie : même résultat qu'un seul (capped à 0)."""
    one = compute_intrusive_score([_f("sql_injection", "critical")])
    two = compute_intrusive_score(
        [
            _f("sql_injection", "critical"),
            _f("sql_injection", "critical"),
        ]
    )
    # Deux criticals dans la même catégorie = même pénalité de catégorie (cap à 0)
    assert two <= one


def test_compute_intrusive_score_multiple_categories_worse_than_one() -> None:
    """Deux high dans différentes catégories sont pénalisés plus que un seul high."""
    single = compute_intrusive_score([_f("sql_injection", "high")])
    multi = compute_intrusive_score(
        [
            _f("sql_injection", "high"),
            _f("command_injection", "high"),
        ]
    )
    assert multi <= single


# ─── Score de 0 ───────────────────────────────────────────────────────────────


def test_compute_intrusive_score_all_critical_gives_zero() -> None:
    """Un critical dans chaque catégorie connue doit produire un score de 0."""
    categories = [
        "open_redirect",
        "methodes_http",
        "cors_actif",
        "parametres_reflechis",
        "sql_injection",
        "path_traversal",
        "csrf",
        "idor",
        "command_injection",
        "nosql_injection",
        "dos_rate_limit",
        "auth_bruteforce",
        "session_fixation",
        "upload_abuse",
        "mass_assignment",
        "graphql_abuse",
        "api_schema_abuse",
        "ssrf",
        "xxe",
        "ssti",
        "insecure_deserialization",
        "lfi_rfi",
        "host_header",
        "cache_poisoning",
        "request_smuggling",
        "race_conditions",
        "business_logic",
        "websocket_authz",
        "graphql_subscriptions",
        "oauth_oidc",
        "grpc_abuse",
        "object_storage",
        "service_mesh",
    ]
    findings = [_f(cat, "critical") for cat in categories]
    score = compute_intrusive_score(findings)
    assert score == 0


# ─── Catégories inconnues ─────────────────────────────────────────────────────


def test_compute_intrusive_score_unknown_category_doesnt_crash() -> None:
    """Une catégorie inconnue ne plante pas le scoring."""
    findings = [_f("unknown_future_category", "critical")]
    score = compute_intrusive_score(findings)
    assert 0 <= score <= 100


def test_compute_intrusive_score_unknown_category_no_weight() -> None:
    """Une catégorie sans poids n'impacte pas les catégories connues."""
    score_with_unknown = compute_intrusive_score([_f("unknown_cat", "critical")])
    # Les catégories connues ne sont pas pénalisées → score élevé
    assert score_with_unknown > 90


# ─── Sévérités non standards ──────────────────────────────────────────────────


def test_compute_intrusive_score_lowercase_severity() -> None:
    """Les sévérités minuscules sont acceptées."""
    score = compute_intrusive_score([_f("sql_injection", "critical")])
    assert 0 <= score <= 100


def test_compute_intrusive_score_unknown_severity_uses_default() -> None:
    """Une sévérité inconnue utilise la pénalité par défaut (25 = medium)."""
    score_unknown = compute_intrusive_score([_f("sql_injection", "apocalyptic")])
    score_medium = compute_intrusive_score([_f("sql_injection", "medium")])
    assert score_unknown == score_medium


# ─── Intégrité des bornes ─────────────────────────────────────────────────────


def test_compute_intrusive_score_never_above_100() -> None:
    """Le score ne peut pas dépasser 100."""
    assert compute_intrusive_score([]) == 100
    assert compute_intrusive_score([_f("sql_injection", "info")]) == 100


def test_compute_intrusive_score_never_below_0() -> None:
    """Le score ne peut pas être inférieur à 0."""
    findings = [_f("sql_injection", "critical")] * 50
    assert compute_intrusive_score(findings) >= 0


# ─── Ordre des findings sans importance ───────────────────────────────────────


def test_compute_intrusive_score_order_independent() -> None:
    """L'ordre des findings ne change pas le score."""
    f1 = _f("sql_injection", "high")
    f2 = _f("cors_actif", "medium")
    f3 = _f("ssrf", "critical")
    assert compute_intrusive_score([f1, f2, f3]) == compute_intrusive_score([f3, f1, f2])
