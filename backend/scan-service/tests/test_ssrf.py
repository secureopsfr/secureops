"""Tests unitaires de la protection SSRF (scan-service)."""

import pytest

from app.utils.ssrf import _resolve_host, check_ssrf, is_hostname_blocked, is_ip_blocked
from app.utils.url_validator import URLValidationError


def test_hostname_blocked_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    """Localhost et variantes sont bloqués (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    assert is_hostname_blocked("localhost") is True
    assert is_hostname_blocked("LOCALHOST") is True
    assert is_hostname_blocked("127.0.0.1") is True
    assert is_hostname_blocked("::1") is True
    assert is_hostname_blocked("[::1]") is True
    assert is_hostname_blocked("0.0.0.0") is True


def test_hostname_not_blocked() -> None:
    """Hostnames publics ne sont pas bloqués."""
    assert is_hostname_blocked("example.com") is False
    assert is_hostname_blocked("192.168.1.1") is False  # IP en string, pas encore résolue
    assert is_hostname_blocked(None) is False
    assert is_hostname_blocked("") is False


def test_ip_blocked_ipv4_private(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plages IPv4 privées / loopback sont bloquées (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("172.16.0.1") is True
    assert is_ip_blocked("192.168.1.1") is True
    assert is_ip_blocked("169.254.1.1") is True
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("0.0.0.0") is True


def test_ip_blocked_ipv6(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plages IPv6 loopback / link-local / ULA sont bloquées (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    assert is_ip_blocked("::1") is True
    assert is_ip_blocked("fe80::1") is True
    assert is_ip_blocked("fc00::1") is True


def test_ip_allowed_public() -> None:
    """IP publiques sont autorisées."""
    assert is_ip_blocked("8.8.8.8") is False
    assert is_ip_blocked("1.1.1.1") is False
    assert is_ip_blocked("2001:4860:4860::8888") is False


@pytest.mark.asyncio()
async def test_check_ssrf_rejects_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_ssrf refuse une URL vers localhost (sans SCAN_ALLOW_LOCALHOST)."""
    monkeypatch.delenv("SCAN_ALLOW_LOCALHOST", raising=False)
    with pytest.raises(URLValidationError, match="localhost|127.0.0.1|::1|autorisées"):
        await check_ssrf("http://localhost/")
    with pytest.raises(URLValidationError, match="localhost|127.0.0.1|::1|autorisées"):
        await check_ssrf("http://127.0.0.1/")


@pytest.mark.asyncio()
async def test_check_ssrf_rejects_private_ip_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_ssrf refuse si la résolution DNS retourne une IP privée."""

    def fake_resolve(host: str, port: int | None) -> list[str]:
        return ["192.168.1.1"]

    monkeypatch.setattr("app.utils.ssrf._resolve_host", fake_resolve)
    with pytest.raises(URLValidationError, match="privée|locale"):
        await check_ssrf("http://evil.internal/")


@pytest.mark.asyncio()
async def test_check_ssrf_accepts_public_ip_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_ssrf n'élève pas si la résolution retourne une IP publique."""

    def fake_resolve(host: str, port: int | None) -> list[str]:
        return ["8.8.8.8"]

    monkeypatch.setattr("app.utils.ssrf._resolve_host", fake_resolve)
    await check_ssrf("http://example.com/")  # ne lève pas


def test_resolve_host_returns_list() -> None:
    """_resolve_host retourne une liste (résolution DNS réelle si réseau dispo)."""
    ips = _resolve_host("example.com", 80)
    assert isinstance(ips, list)
    if ips:
        for ip in ips:
            assert is_ip_blocked(ip) is False


def test_allow_localhost_dev_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avec SCAN_ALLOW_LOCALHOST=1, localhost/127.0.0.1 ne sont pas bloqués (hostname)."""
    monkeypatch.setenv("SCAN_ALLOW_LOCALHOST", "1")
    assert is_hostname_blocked("localhost") is False
    assert is_hostname_blocked("127.0.0.1") is False
    assert is_hostname_blocked("::1") is False


def test_allow_localhost_dev_ip_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avec SCAN_ALLOW_LOCALHOST=1, les IP loopback ne sont pas bloquées."""
    monkeypatch.setenv("SCAN_ALLOW_LOCALHOST", "1")
    assert is_ip_blocked("127.0.0.1") is False
    assert is_ip_blocked("::1") is False


def test_allow_localhost_dev_ip_private_still_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avec SCAN_ALLOW_LOCALHOST=1, les IP privées non loopback restent bloquées."""
    monkeypatch.setenv("SCAN_ALLOW_LOCALHOST", "1")
    assert is_ip_blocked("192.168.1.1") is True
    assert is_ip_blocked("10.0.0.1") is True


@pytest.mark.asyncio()
async def test_check_ssrf_accepts_localhost_when_allow_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avec SCAN_ALLOW_LOCALHOST=1, check_ssrf accepte localhost et 127.0.0.1."""
    monkeypatch.setenv("SCAN_ALLOW_LOCALHOST", "1")
    await check_ssrf("http://localhost/")
    await check_ssrf("http://127.0.0.1/")
