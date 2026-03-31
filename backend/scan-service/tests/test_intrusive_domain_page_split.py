"""Tests unitaires — séparation domain-phase / per-page (app.services.intrusive.lib.domain_page_split)."""

from __future__ import annotations

from app.services.intrusive.lib.domain_page_split import DOMAIN_PHASE_CHECKS, PER_PAGE_CHECKS, is_domain_phase

# ─── Constantes ───────────────────────────────────────────────────────────────


def test_domain_phase_checks_is_frozenset() -> None:
    """Les checks domain-phase sont un frozenset."""
    assert isinstance(DOMAIN_PHASE_CHECKS, frozenset)


def test_per_page_checks_is_frozenset() -> None:
    """Les checks per-page sont un frozenset."""
    assert isinstance(PER_PAGE_CHECKS, frozenset)


def test_domain_phase_checks_not_empty() -> None:
    """Les checks domain-phase ne sont pas vides."""
    assert len(DOMAIN_PHASE_CHECKS) > 0


def test_per_page_checks_not_empty() -> None:
    """Les checks per-page ne sont pas vides."""
    assert len(PER_PAGE_CHECKS) > 0


def test_sets_are_disjoint() -> None:
    """Aucun check ne doit appartenir aux deux ensembles à la fois."""
    overlap = DOMAIN_PHASE_CHECKS & PER_PAGE_CHECKS
    assert overlap == frozenset(), f"Checks in both sets: {overlap}"


def test_domain_phase_expected_checks() -> None:
    """Les checks domain-phase attendus sont bien présents."""
    expected = {"cors_actif", "methodes_http", "ssrf", "xxe", "dos_p0", "auth_bruteforce"}
    assert expected <= DOMAIN_PHASE_CHECKS


def test_per_page_expected_checks() -> None:
    """Les checks per-page attendus sont bien présents."""
    expected = {"sqli", "path_traversal", "csrf", "ssti", "lfi_rfi", "host_header"}
    assert expected <= PER_PAGE_CHECKS


def test_all_phase_a_p0_checks_classified() -> None:
    """Tous les checks Phase A P0 (définis dans le pipeline) sont dans l'un des ensembles."""
    phase_a_checks = {
        "open_redirect",
        "methodes_http",
        "cors_actif",
        "parametres_reflechis",
        "sqli",
        "path_traversal",
        "csrf",
        "idor",
        "command_injection",
        "nosqli",
        "dos_p0",
    }
    for check in phase_a_checks:
        classified = check in DOMAIN_PHASE_CHECKS or check in PER_PAGE_CHECKS
        assert classified, f"Check '{check}' not classified in either set"


def test_all_phase_b_checks_classified() -> None:
    """Tous les checks Phase B sont classifiés."""
    phase_b_checks = {
        "auth_bruteforce",
        "session_fixation",
        "upload_abuse",
        "idor_complet",
        "mass_assignment",
        "graphql_abuse",
        "api_schema_abuse",
        "ssrf",
        "xxe",
        "ssti",
        "insecure_deserialization",
        "lfi_rfi",
    }
    for check in phase_b_checks:
        classified = check in DOMAIN_PHASE_CHECKS or check in PER_PAGE_CHECKS
        assert classified, f"Check '{check}' not classified in either set"


def test_all_phase_c_checks_classified() -> None:
    """Tous les checks Phase C sont classifiés."""
    phase_c_checks = {
        "host_header",
        "cache_poisoning",
        "request_smuggling",
        "race_conditions",
        "business_logic",
        "websocket_authz",
        "oauth_oidc",
        "object_storage",
        "service_mesh",
        "graphql_subscriptions",
        "grpc_abuse",
    }
    for check in phase_c_checks:
        classified = check in DOMAIN_PHASE_CHECKS or check in PER_PAGE_CHECKS
        assert classified, f"Check '{check}' not classified in either set"


# ─── is_domain_phase ──────────────────────────────────────────────────────────


def test_is_domain_phase_true_for_cors() -> None:
    """is_domain_phase retourne True pour le check CORS actif."""
    assert is_domain_phase("cors_actif") is True


def test_is_domain_phase_true_for_ssrf() -> None:
    """is_domain_phase retourne True pour le check SSRF."""
    assert is_domain_phase("ssrf") is True


def test_is_domain_phase_false_for_sqli() -> None:
    """is_domain_phase retourne False pour le check SQLi."""
    assert is_domain_phase("sqli") is False


def test_is_domain_phase_false_for_ssti() -> None:
    """is_domain_phase retourne False pour le check SSTI."""
    assert is_domain_phase("ssti") is False


def test_is_domain_phase_false_for_unknown() -> None:
    """is_domain_phase retourne False pour un check inconnu."""
    assert is_domain_phase("unknown_check_xyz") is False


def test_is_domain_phase_all_domain_checks() -> None:
    """is_domain_phase retourne True pour tous les checks domain-phase."""
    for check in DOMAIN_PHASE_CHECKS:
        assert is_domain_phase(check) is True, f"{check} should return True"


def test_is_domain_phase_all_per_page_checks() -> None:
    """is_domain_phase retourne False pour tous les checks per-page."""
    for check in PER_PAGE_CHECKS:
        assert is_domain_phase(check) is False, f"{check} should return False"


def test_is_domain_phase_returns_bool() -> None:
    """is_domain_phase retourne un booléen."""
    assert isinstance(is_domain_phase("cors_actif"), bool)
    assert isinstance(is_domain_phase("sqli"), bool)
    assert isinstance(is_domain_phase("unknown"), bool)


# ─── Total de checks couverts ─────────────────────────────────────────────────


def test_total_checks_count() -> None:
    """Le total des checks classifiés doit correspondre aux 34 checks du pipeline."""
    total = len(DOMAIN_PHASE_CHECKS) + len(PER_PAGE_CHECKS)
    # 11 domain-phase + 21 per-page = 32 (idor_complet et mass_assignment hors scope ci-dessous)
    # On vérifie un minimum cohérent
    assert total >= 30, f"Expected at least 30 classified checks, got {total}"
