"""Tests unitaires pour l'analyse des certificats TLS (app.services.tls.certificate)."""

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID

from app.services.tls.certificate import CertificateStatus, analyze_certificate, verify_certificate_chain


def _make_cert_der(
    not_before: datetime,
    not_after: datetime,
    self_signed: bool = False,
) -> bytes:
    """Génère un certificat DER avec les dates spécifiées."""
    ca_key = rsa.generate_private_key(65537, 2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")])
    leaf_key = rsa.generate_private_key(65537, 2048)
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])
    issuer_name = leaf_name if self_signed else ca_name
    sign_key = leaf_key if self_signed else ca_key
    cert = (
        x509.CertificateBuilder()
        .subject_name(leaf_name)
        .issuer_name(issuer_name)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(sign_key, hashes.SHA256())
    )
    return cert.public_bytes(Encoding.DER)


def test_analyze_certificate_valid() -> None:
    """Certificat valide (dates OK, non auto-signé) retourne valid."""
    now = datetime.now(timezone.utc)
    cert_der = _make_cert_der(
        not_before=now - timedelta(days=1),
        not_after=now + timedelta(days=365),
        self_signed=False,
    )
    status, findings = analyze_certificate(cert_der, "example.com")
    assert status == CertificateStatus.VALID
    assert len(findings) == 0


def test_analyze_certificate_expires_soon() -> None:
    """Certificat qui expire dans moins de 30 jours retourne expires_soon."""
    now = datetime.now(timezone.utc)
    cert_der = _make_cert_der(
        not_before=now - timedelta(days=365),
        not_after=now + timedelta(days=15),
        self_signed=False,
    )
    status, findings = analyze_certificate(cert_der, "example.com")
    assert status == CertificateStatus.EXPIRES_SOON
    assert len(findings) == 1
    assert "expire bientôt" in findings[0]
    assert "jour(s)" in findings[0]


def test_verify_certificate_chain_self_signed_ok() -> None:
    """Chaîne avec certificat auto-signé (1 seul) : OK."""
    now = datetime.now(timezone.utc)
    cert_der = _make_cert_der(
        not_before=now - timedelta(days=1),
        not_after=now + timedelta(days=365),
        self_signed=True,
    )
    ok, findings = verify_certificate_chain([cert_der], leaf_is_self_signed=True)
    assert ok is True
    assert len(findings) == 0


def test_verify_certificate_chain_single_non_self_signed_incomplete() -> None:
    """Un seul certificat non auto-signé : chaîne incomplète."""
    now = datetime.now(timezone.utc)
    cert_der = _make_cert_der(
        not_before=now - timedelta(days=1),
        not_after=now + timedelta(days=365),
        self_signed=False,
    )
    ok, findings = verify_certificate_chain([cert_der], leaf_is_self_signed=False)
    assert ok is False
    assert len(findings) == 1
    assert "incomplète" in findings[0]
