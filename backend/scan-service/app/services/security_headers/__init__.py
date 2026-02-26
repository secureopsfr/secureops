"""Vérifications Security Headers (roadmap §3.2) : CSP, HSTS, X-Frame-Options, etc."""

from app.services.security_headers.checks import SecurityHeadersCheckResult, check_security_headers_from_response

__all__ = ["SecurityHeadersCheckResult", "check_security_headers_from_response"]
