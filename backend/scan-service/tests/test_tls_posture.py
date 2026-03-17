"""Tests unitaires pour le calcul de la posture TLS (passive)."""

from app.services.passive.both.tls.checks import TlsCheckResult
from app.services.passive.both.tls.posture import POSTURE_CRITICAL, POSTURE_OK, POSTURE_WARNING, compute_tls_posture


def test_posture_ok_all_valid() -> None:
    """Posture OK quand HTTPS, redirect, cert valide, pas de TLS obsolète."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
    )
    assert compute_tls_posture(result) == POSTURE_OK


def test_posture_critical_https_disabled() -> None:
    """Posture critique quand HTTPS désactivé."""
    result = TlsCheckResult(
        https_enabled=False,
        http_redirects_to_https=None,
        certificate_status=None,
        tls_versions_obsolete=(),
        findings=("HTTPS non disponible",),
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_critical_fetch_failed() -> None:
    """Posture critique quand fetch a échoué."""
    result = TlsCheckResult(
        https_enabled=False,
        http_redirects_to_https=None,
        certificate_status=None,
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=False,
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_critical_no_redirect() -> None:
    """Posture critique quand pas de redirection HTTP→HTTPS."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=False,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=("Pas de redirection",),
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_critical_cert_expired() -> None:
    """Posture critique quand certificat expiré."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="expired",
        tls_versions_obsolete=(),
        findings=("Certificat expiré",),
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_critical_cert_self_signed() -> None:
    """Posture critique quand certificat auto-signé."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="self_signed",
        tls_versions_obsolete=(),
        findings=("Certificat auto-signé",),
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_critical_tls_obsolete() -> None:
    """Posture critique quand TLS 1.0/1.1 supporté."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=("1.0", "1.1"),
        findings=("TLS 1.0, 1.1 supportés",),
    )
    assert compute_tls_posture(result) == POSTURE_CRITICAL


def test_posture_warning_cert_expires_soon() -> None:
    """Posture avertissement quand certificat expire bientôt."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="expires_soon",
        tls_versions_obsolete=(),
        findings=("Certificat expire dans 15 jours",),
    )
    assert compute_tls_posture(result) == POSTURE_WARNING


def test_posture_warning_chain_incomplete() -> None:
    """Posture avertissement quand chaîne de certificats incomplète."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=("Chaîne incomplète",),
        chain_incomplete=True,
    )
    assert compute_tls_posture(result) == POSTURE_WARNING
