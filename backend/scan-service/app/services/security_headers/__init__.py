"""Vérifications Security Headers (roadmap §3.2) : CSP, HSTS, X-Frame-Options, etc."""

from app.services.security_headers.checks import SecurityHeadersCheckResult, run_security_headers_checks

__all__ = ["SecurityHeadersCheckResult", "run_security_headers_checks"]
