"""Tests unitaires — moteur de payloads intrusif (app.services.intrusive.lib.payload_engine)."""

from __future__ import annotations

import pytest

from app.services.intrusive.lib.payload_engine import (
    Payload,
    PayloadCategory,
    get_mass_assignment_fields,
    get_nosql_qs_payloads,
    get_payloads,
    make_ssti_payloads,
    make_xss_marker,
    mutate,
)

# ─── PayloadCategory ──────────────────────────────────────────────────────────


def test_payload_categories_exist() -> None:
    """Les catégories de payloads existent."""
    expected = {"SQL", "NOSQL", "TEMPLATE", "XML", "SHELL", "PATH", "REDIRECT", "XSS_MARKER", "SSRF", "MASS_ASSIGNMENT"}
    actual = {m.name for m in PayloadCategory}
    assert expected <= actual


# ─── Payload dataclass ────────────────────────────────────────────────────────


def test_payload_dataclass_frozen() -> None:
    """Le payload est immutable."""
    p = Payload(raw="test", category=PayloadCategory.SQL, payload_id="abc")
    try:
        p.raw = "changed"  # type: ignore[misc]
        assert pytest.fail("Should have raised FrozenInstanceError")
    except Exception:
        pass


def test_payload_default_encoding() -> None:
    """L'encodage par défaut est none."""
    p = Payload(raw="x", category=PayloadCategory.SQL, payload_id="id1")
    assert p.encoding == "none"


def test_payload_custom_description() -> None:
    """Le description est custom."""
    p = Payload(raw="x", category=PayloadCategory.SHELL, payload_id="id2", description="cmd_probe")
    assert p.description == "cmd_probe"


# ─── get_payloads ─────────────────────────────────────────────────────────────


def test_get_payloads_sql_returns_list() -> None:
    """get_payloads retourne une liste de payloads pour la catégorie SQL."""
    payloads = get_payloads(PayloadCategory.SQL)
    assert isinstance(payloads, list)
    assert len(payloads) > 0


def test_get_payloads_budget_limits_count() -> None:
    """Le budget limite le nombre de payloads."""
    payloads = get_payloads(PayloadCategory.SQL, budget=2)
    assert len(payloads) <= 2


def test_get_payloads_budget_zero_returns_empty() -> None:
    """Un budget de 0 retourne une liste vide."""
    payloads = get_payloads(PayloadCategory.SQL, budget=0)
    assert payloads == []


def test_get_payloads_each_has_unique_id() -> None:
    """Chaque payload a un ID unique."""
    payloads = get_payloads(PayloadCategory.SQL, budget=5)
    ids = [p.payload_id for p in payloads]
    assert len(ids) == len(set(ids)), "IDs should be unique"


def test_get_payloads_correct_category() -> None:
    """Les payloads sont de la bonne catégorie."""
    payloads = get_payloads(PayloadCategory.SHELL, budget=3)
    for p in payloads:
        assert p.category == PayloadCategory.SHELL


def test_get_payloads_all_categories() -> None:
    """Les payloads de toutes les catégories existent."""
    for cat in [
        PayloadCategory.SQL,
        PayloadCategory.NOSQL,
        PayloadCategory.TEMPLATE,
        PayloadCategory.XML,
        PayloadCategory.SHELL,
        PayloadCategory.PATH,
        PayloadCategory.REDIRECT,
        PayloadCategory.SSRF,
    ]:
        payloads = get_payloads(cat, budget=3)
        assert isinstance(payloads, list)
        assert len(payloads) > 0, f"No payloads for {cat}"


def test_get_payloads_unknown_category_returns_empty() -> None:
    """MASS_ASSIGNMENT n'est pas dans la dispatch table de get_payloads."""
    payloads = get_payloads(PayloadCategory.MASS_ASSIGNMENT, budget=3)
    assert payloads == []


def test_get_payloads_raw_strings_non_empty() -> None:
    """Les payloads ont une chaîne non vide."""
    for p in get_payloads(PayloadCategory.SQL, budget=5):
        assert p.raw, "Payload raw string must not be empty"


# ─── get_nosql_qs_payloads ────────────────────────────────────────────────────


def test_get_nosql_qs_payloads_returns_list() -> None:
    """get_nosql_qs_payloads retourne une liste de payloads."""
    payloads = get_nosql_qs_payloads()
    assert isinstance(payloads, list)
    assert len(payloads) > 0


def test_get_nosql_qs_payloads_budget() -> None:
    """Le budget limite le nombre de payloads."""
    payloads = get_nosql_qs_payloads(budget=1)
    assert len(payloads) == 1


def test_get_nosql_qs_payloads_category() -> None:
    """Les payloads sont de la bonne catégorie."""
    for p in get_nosql_qs_payloads(budget=4):
        assert p.category == PayloadCategory.NOSQL


def test_get_nosql_qs_payloads_description() -> None:
    """Le description est correct."""
    for p in get_nosql_qs_payloads(budget=2):
        assert p.description == "nosql_qs"


# ─── get_mass_assignment_fields ───────────────────────────────────────────────


def test_get_mass_assignment_fields_returns_list() -> None:
    """get_mass_assignment_fields retourne une liste de payloads."""
    fields = get_mass_assignment_fields()
    assert isinstance(fields, list)
    assert len(fields) > 0


def test_get_mass_assignment_fields_tuples() -> None:
    """Les items sont des tuples."""
    for item in get_mass_assignment_fields():
        assert isinstance(item, tuple)
        assert len(item) == 2


def test_get_mass_assignment_fields_contains_admin() -> None:
    """Les noms contiennent admin ou role."""
    names = [f[0] for f in get_mass_assignment_fields()]
    assert any("admin" in n or "role" in n for n in names)


# ─── make_xss_marker ──────────────────────────────────────────────────────────


def test_make_xss_marker_returns_payload() -> None:
    """make_xss_marker retourne un payload."""
    marker = make_xss_marker()
    assert isinstance(marker, Payload)


def test_make_xss_marker_category() -> None:
    """Le payload est de la catégorie XSS_MARKER."""
    marker = make_xss_marker()
    assert marker.category == PayloadCategory.XSS_MARKER


def test_make_xss_marker_unique_per_call() -> None:
    """Les marqueurs sont uniques par appel."""
    m1 = make_xss_marker()
    m2 = make_xss_marker()
    assert m1.raw != m2.raw


def test_make_xss_marker_prefix_in_raw() -> None:
    """Le préfixe est dans la chaîne de caractères."""
    marker = make_xss_marker(prefix="testpfx")
    assert marker.raw.startswith("testpfx-")


def test_make_xss_marker_default_prefix() -> None:
    """Le préfixe par défaut est sec0p5."""
    marker = make_xss_marker()
    assert marker.raw.startswith("sec0p5-")


def test_make_xss_marker_description() -> None:
    """Le description est correct."""
    marker = make_xss_marker()
    assert marker.description == "xss_reflection_marker"


# ─── mutate ───────────────────────────────────────────────────────────────────


def test_mutate_returns_three_variants() -> None:
    """Mutate retourne trois variantes."""
    variants = mutate("'")
    assert len(variants) == 3


def test_mutate_first_is_raw() -> None:
    """La première variante est le payload brut."""
    variants = mutate("' OR 1=1--")
    assert variants[0] == "' OR 1=1--"


def test_mutate_second_is_url_encoded() -> None:
    """La deuxième variante est url-encoded."""
    variants = mutate("'")
    assert "%" in variants[1]


def test_mutate_third_is_double_encoded() -> None:
    """La troisième variante est double-encodée."""
    variants = mutate("'")
    # Double encoding : le % lui-même est encodé en %25
    assert "%25" in variants[2]


def test_mutate_all_strings() -> None:
    """Toutes les variantes sont des chaînes de caractères."""
    for v in mutate("<script>"):
        assert isinstance(v, str)


# ─── make_ssti_payloads ───────────────────────────────────────────────────────


def test_make_ssti_payloads_returns_list() -> None:
    """make_ssti_payloads retourne une liste de payloads."""
    payloads = make_ssti_payloads()
    assert isinstance(payloads, list)
    assert len(payloads) > 0


def test_make_ssti_payloads_template_category() -> None:
    """Les payloads sont de la catégorie TEMPLATE."""
    for p in make_ssti_payloads():
        assert p.category == PayloadCategory.TEMPLATE


def test_make_ssti_payloads_description() -> None:
    """Le description est correct."""
    for p in make_ssti_payloads():
        assert p.description == "ssti_eval"


def test_make_ssti_payloads_contains_7x7() -> None:
    """Les payloads contiennent 7*7."""
    raws = [p.raw for p in make_ssti_payloads()]
    assert any("7*7" in r for r in raws)
