"""Tests unitaires de pseudonymisation des métriques."""

from app.services.proxy.pseudonymizer import _truncate_ip_address, pseudonymize_ip_address


def test_truncate_ipv4() -> None:
    """Doit tronquer le dernier octet IPv4."""
    assert _truncate_ip_address("192.168.1.123") == "192.168.1.0"


def test_truncate_ipv6_compressed() -> None:
    """Doit tronquer correctement une IPv6 compressée sur /64."""
    assert _truncate_ip_address("2001:db8::1") == "2001:db8::"


def test_pseudonymize_ip_returns_none_without_secret(monkeypatch) -> None:
    """Sans secret, la pseudonymisation doit retourner None."""
    monkeypatch.delenv("ADMIN_METRICS_USER_HASH_SECRET", raising=False)
    assert pseudonymize_ip_address("10.0.0.42") is None


def test_pseudonymize_ip_is_stable_with_secret(monkeypatch) -> None:
    """Avec secret, le hash IP doit être stable pour la même valeur tronquée."""
    monkeypatch.setenv("ADMIN_METRICS_USER_HASH_SECRET", "test-secret")
    first = pseudonymize_ip_address("192.168.1.10")
    second = pseudonymize_ip_address("192.168.1.99")
    assert first is not None
    assert first == second
