"""Tests pour le mapping OWASP Top 10."""

from app.catalogue.owasp import get_owasp_categories


def test_get_owasp_categories_exact_match() -> None:
    """Correspondance exacte retourne les codes."""
    assert get_owasp_categories("tls-https-disabled") == ("A04",)
    assert get_owasp_categories("integrity-forms-post-without-csrf") == ("A01",)
    assert get_owasp_categories("cors-allow-origin-star-sensitive") == ("A01", "A02")


def test_get_owasp_categories_unmapped_returns_empty() -> None:
    """Slug non mappé retourne ()."""
    assert get_owasp_categories("unknown-slug-xyz") == ()


def test_get_owasp_categories_prefix_match() -> None:
    """Préfixe exposed_files ou directory_listing matche."""
    assert get_owasp_categories("exposed_files-.env") == ("A02",)
    assert get_owasp_categories("directory_listing-uploads") == ("A02",)
