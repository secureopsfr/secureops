"""Tests unitaires de la liste noire (common)."""

import pytest

from common.blacklist import is_domain_blacklisted
from common.config_base import BlacklistSettings


def test_is_domain_blacklisted_exact_match() -> None:
    """Exact match : host == domain."""
    settings = BlacklistSettings(domains=("secureops.fr",))
    assert is_domain_blacklisted("secureops.fr", settings) is True


def test_is_domain_blacklisted_subdomain() -> None:
    """Sous-domaine : host.endswith('.domain')."""
    settings = BlacklistSettings(domains=("secureops.fr",))
    assert is_domain_blacklisted("www.secureops.fr", settings) is True
    assert is_domain_blacklisted("app.secureops.fr", settings) is True
    assert is_domain_blacklisted("staging.secureops.fr", settings) is True


def test_is_domain_blacklisted_not_matched() -> None:
    """Domaine non listé."""
    settings = BlacklistSettings(domains=("secureops.fr",))
    assert is_domain_blacklisted("example.com", settings) is False
    assert is_domain_blacklisted("secureops.fr.evil.com", settings) is False


def test_is_domain_blacklisted_empty() -> None:
    """Liste vide = aucun blocage."""
    settings = BlacklistSettings(domains=())
    assert is_domain_blacklisted("secureops.fr", settings) is False


def test_is_domain_blacklisted_none_host() -> None:
    """Host None = non bloqué."""
    settings = BlacklistSettings(domains=("secureops.fr",))
    assert is_domain_blacklisted(None, settings) is False


@pytest.mark.asyncio()
async def test_check_blacklist_raises() -> None:
    """check_blacklist lève URLValidationError pour domaine interdit."""
    from common.blacklist import check_blacklist
    from common.url_utils import URLValidationError

    settings = BlacklistSettings(domains=("secureops.fr",))
    with pytest.raises(URLValidationError, match="interdit"):
        await check_blacklist("https://www.secureops.fr/", settings)


@pytest.mark.asyncio()
async def test_check_blacklist_accepts() -> None:
    """check_blacklist n'élève pas pour domaine autorisé."""
    from common.blacklist import check_blacklist

    settings = BlacklistSettings(domains=("secureops.fr",))
    await check_blacklist("https://example.com/", settings)  # ne lève pas
