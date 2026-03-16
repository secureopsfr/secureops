"""Tests unitaires pour la normalisation des résultats (passive)."""

from app.services.passive.both.cookies.checks import CookieCheckResult, CookieInfo
from app.services.passive.both.cors_cross_origin.checks import CorsCrossOriginCheckResult, CorsIssue
from app.services.passive.both.path_checks.core import PathCheckResult, PathFinding
from app.services.passive.both.robots_txt.checks import RobotsTxtCheckResult, SensitiveRoute
from app.services.passive.both.security_headers.checks import SecurityHeadersCheckResult
from app.services.passive.both.tech_fingerprinting.checks import TechFingerprintingCheckResult
from app.services.passive.both.tls.checks import TlsCheckResult
from app.services.passive.normalization import normalize_results


def test_normalize_results_empty_dict() -> None:
    """normalize_results avec dict vide retourne liste vide."""
    assert normalize_results({}) == []


def test_normalize_results_ignores_none_values() -> None:
    """normalize_results ignore les clés dont la valeur est None."""
    results = {"tls": None, "headers": None}
    assert normalize_results(results) == []


def test_normalize_tls_fetch_ok_false() -> None:
    """TLS avec fetch_ok=False produit tls-connection-failed."""
    result = TlsCheckResult(
        https_enabled=False,
        http_redirects_to_https=None,
        certificate_status=None,
        tls_versions_obsolete=(),
        findings=("HTTPS non activé (connexion refusée ou timeout).",),
        fetch_ok=False,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-connection-failed"
    assert findings[0].category == "tls"
    assert findings[0].severity == "high"


def test_normalize_tls_https_disabled() -> None:
    """TLS avec https_enabled=False produit tls-https-disabled."""
    result = TlsCheckResult(
        https_enabled=False,
        http_redirects_to_https=None,
        certificate_status=None,
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=True,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-https-disabled"
    assert findings[0].severity == "critical"


def test_normalize_tls_findings_redirect() -> None:
    """TLS finding sur redirection produit tls-no-redirect."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=False,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=("Pas de redirection HTTP→HTTPS.",),
        fetch_ok=True,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-no-redirect"
    assert findings[0].severity == "high"


def test_normalize_tls_findings_cert_expired() -> None:
    """TLS finding certificat expiré produit tls-cert-expired."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="expired",
        tls_versions_obsolete=(),
        findings=("Certificat expiré.",),
        fetch_ok=True,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-cert-expired"
    assert findings[0].severity == "critical"


def test_normalize_tls_findings_versions_obsolete() -> None:
    """TLS finding versions obsolètes produit tls-versions-obsolete."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=("1.0", "1.1"),
        findings=("TLS 1.0 et 1.1 encore accepté(s).",),
        fetch_ok=True,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-versions-obsolete"
    assert findings[0].severity == "medium"


def test_normalize_tls_expires_soon_severity_by_days() -> None:
    """tls-cert-expires-soon : gravité low si >= 15 jours, medium si < 15 jours."""
    result_15_days = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="expires_soon",
        tls_versions_obsolete=(),
        findings=("Certificat expire bientôt (dans 15 jour(s), notAfter: 2026-04-02). Renouveler avant expiration.",),
        fetch_ok=True,
    )
    findings_15 = normalize_results({"tls": result_15_days})
    assert len(findings_15) == 1
    assert findings_15[0].id == "tls-cert-expires-soon"
    assert findings_15[0].severity == "low"

    result_7_days = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="expires_soon",
        tls_versions_obsolete=(),
        findings=("Certificat expire bientôt (dans 7 jour(s), notAfter: 2026-03-25). Renouveler avant expiration.",),
        fetch_ok=True,
    )
    findings_7 = normalize_results({"tls": result_7_days})
    assert len(findings_7) == 1
    assert findings_7[0].severity == "medium"


def test_normalize_tls_chain_incomplete() -> None:
    """TLS finding chaîne incomplète produit tls-chain-incomplete."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(
            "Chaîne de certificats incomplète : le serveur n'envoie que le certificat feuille, "
            "sans les intermédiaires. Les navigateurs peuvent afficher des avertissements.",
        ),
        fetch_ok=True,
    )
    findings = normalize_results({"tls": result})
    assert len(findings) == 1
    assert findings[0].id == "tls-chain-incomplete"
    assert findings[0].severity == "medium"


def test_normalize_tls_no_findings() -> None:
    """TLS sans findings retourne liste vide."""
    result = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=True,
    )
    assert normalize_results({"tls": result}) == []


def test_normalize_headers_fetch_ok_false() -> None:
    """Headers avec fetch_ok=False produit headers-connection-failed."""
    result = SecurityHeadersCheckResult(
        headers_present=(),
        headers_missing=("Content-Security-Policy",),
        findings=("Impossible de récupérer les en-têtes (connexion refusée ou timeout).",),
        fetch_ok=False,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 1
    assert findings[0].id == "headers-connection-failed"
    assert findings[0].category == "headers"
    assert findings[0].severity == "high"


def test_normalize_headers_missing_csp() -> None:
    """Headers manquants produisent les slugs attendus avec sévérité différenciée."""
    result = SecurityHeadersCheckResult(
        headers_present=(),
        headers_missing=("Content-Security-Policy", "X-Frame-Options"),
        findings=(
            "Content-Security-Policy absent : risque XSS accru.",
            "X-Frame-Options absent : risque de clickjacking.",
        ),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 2
    ids = {f.id for f in findings}
    assert "headers-csp-absent" in ids
    assert "headers-xfo-absent" in ids
    csp_f = next(f for f in findings if f.id == "headers-csp-absent")
    xfo_f = next(f for f in findings if f.id == "headers-xfo-absent")
    assert csp_f.severity == "high"
    assert xfo_f.severity == "medium"


def test_normalize_headers_xcto_wrong_value() -> None:
    """X-Content-Type-Options valeur incorrecte produit headers-xcto-wrong-value."""
    result = SecurityHeadersCheckResult(
        headers_present=("X-Content-Type-Options",),
        headers_missing=(),
        findings=("X-Content-Type-Options présent mais valeur incorrecte (attendu : nosniff).",),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 1
    assert findings[0].id == "headers-xcto-wrong-value"


def test_normalize_headers_csp_no_report_uri() -> None:
    """CSP sans report-uri ni report-to produit headers-csp-no-report-uri."""
    result = SecurityHeadersCheckResult(
        headers_present=("Content-Security-Policy",),
        headers_missing=(),
        findings=("CSP présent mais sans report-uri ni report-to : violations non détectables.",),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 1
    assert findings[0].id == "headers-csp-no-report-uri"
    assert findings[0].severity == "low"


def test_normalize_headers_csp_unsafe_directives() -> None:
    """CSP avec unsafe-inline/unsafe-eval produit headers-csp-unsafe-directives."""
    result = SecurityHeadersCheckResult(
        headers_present=("Content-Security-Policy",),
        headers_missing=(),
        findings=("CSP contient unsafe-inline ou unsafe-eval : risque XSS accru.",),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 1
    assert findings[0].id == "headers-csp-unsafe-directives"
    assert findings[0].severity == "low"


def test_normalize_headers_coep_coop_clear_site_data() -> None:
    """COEP, COOP, Clear-Site-Data absents produisent les slugs attendus."""
    result = SecurityHeadersCheckResult(
        headers_present=(),
        headers_missing=(
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Clear-Site-Data",
        ),
        findings=(
            "Cross-Origin-Embedder-Policy absent : isolation cross-origin limitée.",
            "Cross-Origin-Opener-Policy absent : isolation cross-origin limitée.",
            "Clear-Site-Data absent : déconnexion sans purge des données.",
        ),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 3
    ids = {f.id for f in findings}
    assert "headers-coep-absent" in ids
    assert "headers-coop-absent" in ids
    assert "headers-clear-site-data-absent" in ids
    for f in findings:
        assert f.severity == "low"


def test_normalize_cookies_fetch_ok_false() -> None:
    """Cookies avec fetch_ok=False produit cookies-connection-failed."""
    result = CookieCheckResult(cookies=(), findings=("Impossible d'analyser les cookies.",), fetch_ok=False)
    findings = normalize_results({"cookies": result})
    assert len(findings) == 1
    assert findings[0].id == "cookies-connection-failed"


def test_normalize_cookies_no_secure() -> None:
    """Cookie sans Secure produit cookies-no-secure."""
    result = CookieCheckResult(
        cookies=(CookieInfo(name="lang", secure=False, httponly=True, samesite="Lax"),),
        findings=("Cookie 'lang' sans Secure sur site HTTPS : risque d'interception.",),
        fetch_ok=True,
    )
    findings = normalize_results({"cookies": result})
    assert len(findings) == 1
    assert findings[0].id == "cookies-no-secure"
    assert findings[0].severity == "high"


def test_normalize_cookies_session_incomplete() -> None:
    """Cookie de session sans triple protection produit cookies-session-incomplete."""
    result = CookieCheckResult(
        cookies=(CookieInfo(name="session_id", secure=False, httponly=False, samesite=None),),
        findings=("Cookie de session 'session_id' sans HttpOnly + Secure + SameSite=Strict : risque élevé.",),
        fetch_ok=True,
    )
    findings = normalize_results({"cookies": result})
    assert len(findings) == 1
    assert findings[0].id == "cookies-session-incomplete"
    assert findings[0].severity == "high"


def test_normalize_cookies_no_host_secure_prefix() -> None:
    """Cookie sensible sans préfixe __Host-/__Secure- produit cookies-no-host-secure-prefix."""
    # session_id a la triple protection mais pas les préfixes __Host-/__Secure-
    result = CookieCheckResult(
        cookies=(CookieInfo(name="session_id", secure=True, httponly=True, samesite="Strict"),),
        findings=("Cookie sensible 'session_id' sans préfixe __Host- ou __Secure- : bonne pratique recommandée.",),
        fetch_ok=True,
    )
    findings = normalize_results({"cookies": result})
    assert any(f.id == "cookies-no-host-secure-prefix" for f in findings)
    assert next(f for f in findings if f.id == "cookies-no-host-secure-prefix").severity == "info"


def test_normalize_cookies_no_partitioned() -> None:
    """Cookie tiers sans Partitioned produit cookies-no-partitioned."""
    # _ga est third-party-like (analytics), secure+httponly+samesite OK, partitioned=False
    result = CookieCheckResult(
        cookies=(CookieInfo(name="_ga", secure=True, httponly=True, samesite="Lax", partitioned=False),),
        findings=("Cookie '_ga' (analytics/tiers probable) sans Partitioned : recommandation CHIPS.",),
        fetch_ok=True,
    )
    findings = normalize_results({"cookies": result})
    assert any(f.id == "cookies-no-partitioned" for f in findings)
    assert next(f for f in findings if f.id == "cookies-no-partitioned").severity == "low"


def test_normalize_cookies_session_expires_long() -> None:
    """Cookie session avec Max-Age > 24h produit cookies-session-expires-long."""
    # session_id avec triple protection mais Max-Age = 48h (172800s > 86400s)
    result = CookieCheckResult(
        cookies=(CookieInfo(name="session_id", secure=True, httponly=True, samesite="Strict", max_age_seconds=172800),),
        findings=("Cookie de session 'session_id' avec Expires/Max-Age > 24h : session persistante non recommandée.",),
        fetch_ok=True,
    )
    findings = normalize_results({"cookies": result})
    assert any(f.id == "cookies-session-expires-long" for f in findings)
    assert next(f for f in findings if f.id == "cookies-session-expires-long").severity == "low"


def test_normalize_exposed_files_upgrade_critical() -> None:
    """exposed_files : .env et .git/config sont upgradés en critical."""
    pf_env = PathFinding(path="/.env", severity="high", message="Fichier .env exposé.")
    pf_git = PathFinding(path="/.git/config", severity="medium", message="Fichier .git/config exposé.")
    result = PathCheckResult(exposed=(pf_env, pf_git), findings=(pf_env.message, pf_git.message), fetch_ok=True)
    findings = normalize_results({"exposed_files": result})
    assert len(findings) == 2
    for f in findings:
        assert f.severity == "critical"
    ids = {f.id for f in findings}
    assert "exposed_files-env" in ids
    assert "exposed_files-git-config" in ids


def test_normalize_exposed_files_slug_from_path() -> None:
    """exposed_files : slug dérivé du path."""
    pf = PathFinding(path="/admin/", severity="medium", message="Interface /admin/ exposée.")
    result = PathCheckResult(exposed=(pf,), findings=(pf.message,), fetch_ok=True)
    findings = normalize_results({"exposed_files": result})
    assert len(findings) == 1
    assert findings[0].id == "exposed_files-admin"
    assert findings[0].category == "exposed_files"


def test_normalize_directory_listing() -> None:
    """directory_listing : PathCheckResult produit findings avec bon slug."""
    pf = PathFinding(path="/uploads/", severity="high", message="Directory listing activé.")
    result = PathCheckResult(exposed=(pf,), findings=(pf.message,), fetch_ok=True)
    findings = normalize_results({"directory_listing": result})
    assert len(findings) == 1
    assert findings[0].id == "directory_listing-uploads"
    assert findings[0].severity == "high"


def test_normalize_directory_listing_exposed_403() -> None:
    """directory_listing : exposed_403 produit finding directory_listing-sensitive-403."""
    pf_403 = PathFinding(path="/config/", severity="medium", message="Répertoire sensible /config/ retourne 403.")
    result = PathCheckResult(exposed=(), findings=(), fetch_ok=True, exposed_403=(pf_403,))
    findings = normalize_results({"directory_listing": result})
    assert len(findings) == 1
    assert findings[0].id == "directory_listing-sensitive-403"
    assert findings[0].title == "Répertoire sensible révélé : /config/"
    assert findings[0].severity == "medium"


def test_normalize_robots_txt_fetch_ok_false() -> None:
    """robots_txt avec fetch_ok=False produit robots_txt-connection-failed."""
    result = RobotsTxtCheckResult(
        disallow_paths=(),
        allow_paths=(),
        sensitive_routes=(),
        findings=("Impossible de récupérer robots.txt.",),
        fetch_ok=False,
        found=False,
        crawl_delay=None,
        sitemap_urls=(),
    )
    findings = normalize_results({"robots_txt": result})
    assert len(findings) == 1
    assert findings[0].id == "robots_txt-connection-failed"


def test_normalize_robots_txt_sensitive_routes() -> None:
    """robots_txt avec routes sensibles produit robots_txt-sensitive-route."""
    route = SensitiveRoute(path="/admin/", pattern="admin", severity="high")
    result = RobotsTxtCheckResult(
        disallow_paths=("/admin/",),
        allow_paths=(),
        sensitive_routes=(route,),
        findings=("Disallow: /admin/ (route potentiellement sensible : admin).",),
        fetch_ok=True,
        found=True,
        crawl_delay=None,
        sitemap_urls=(),
    )
    findings = normalize_results({"robots_txt": result})
    assert len(findings) == 1
    assert findings[0].id == "robots_txt-sensitive-route"
    assert findings[0].severity == "high"
    assert "admin" in findings[0].evidence


def test_normalize_robots_txt_crawl_delay() -> None:
    """robots_txt avec crawl_delay produit robots_txt-crawl-delay (info)."""
    result = RobotsTxtCheckResult(
        disallow_paths=(),
        allow_paths=(),
        sensitive_routes=(),
        findings=(),
        fetch_ok=True,
        found=True,
        crawl_delay=5,
        sitemap_urls=(),
    )
    findings = normalize_results({"robots_txt": result})
    assert len(findings) == 1
    assert findings[0].id == "robots_txt-crawl-delay"
    assert findings[0].severity == "info"


def test_normalize_sitemap_not_found() -> None:
    """Sitemap avec sitemap_found=False produit sitemap-not-found (info)."""
    from app.services.passive.frontend.sitemap.checks import SitemapCheckResult

    result = SitemapCheckResult(
        sitemap_found=False,
        sitemap_undeclared=False,
        sensitive_urls=(),
        fetch_ok=True,
    )
    findings = normalize_results({"sitemap": result})
    assert len(findings) == 1
    assert findings[0].id == "sitemap-not-found"
    assert findings[0].severity == "info"


def test_normalize_sitemap_sensitive_url() -> None:
    """Sitemap avec URL sensible produit sitemap-sensitive-url."""
    from app.services.passive.frontend.sitemap.checks import SensitiveSitemapUrl, SitemapCheckResult

    result = SitemapCheckResult(
        sitemap_found=True,
        sitemap_undeclared=False,
        sensitive_urls=(SensitiveSitemapUrl("https://ex.com/admin", "/admin", "admin", "high"),),
        fetch_ok=True,
    )
    findings = normalize_results({"sitemap": result})
    assert len(findings) == 1
    assert findings[0].id == "sitemap-sensitive-url"
    assert findings[0].severity == "high"


def test_normalize_tech_fingerprinting_fetch_ok_false() -> None:
    """tech_fingerprinting avec fetch_ok=False produit tech_fingerprinting-connection-failed (info)."""
    result = TechFingerprintingCheckResult(
        server=None,
        server_version=None,
        runtime=None,
        runtime_version=None,
        framework_cms=None,
        framework_cms_version=None,
        stack_entries=(),
        vulnerable_versions=(),
        findings=("Impossible d'analyser les en-têtes.",),
        fetch_ok=False,
    )
    findings = normalize_results({"tech_fingerprinting": result})
    assert len(findings) == 1
    assert findings[0].id == "tech_fingerprinting-connection-failed"
    assert findings[0].severity == "info"


def test_normalize_tech_fingerprinting_server_detected() -> None:
    """tech_fingerprinting avec serveur détecté produit tech_fingerprinting-server-detected."""
    result = TechFingerprintingCheckResult(
        server="nginx",
        server_version=None,
        runtime=None,
        runtime_version=None,
        framework_cms=None,
        framework_cms_version=None,
        stack_entries=(),
        vulnerable_versions=(),
        findings=("Serveur détecté : nginx",),
        fetch_ok=True,
    )
    findings = normalize_results({"tech_fingerprinting": result})
    assert len(findings) == 1
    assert findings[0].id == "tech_fingerprinting-server-detected"
    assert findings[0].severity == "info"


def test_normalize_tech_fingerprinting_vulnerable_version() -> None:
    """tech_fingerprinting avec version vulnérable produit tech_fingerprinting-vulnerable-version."""
    from app.services.passive.both.tech_fingerprinting.checks import VulnerableVersion

    result = TechFingerprintingCheckResult(
        server="nginx/1.18.0",
        server_version="1.18.0",
        runtime=None,
        runtime_version=None,
        framework_cms=None,
        framework_cms_version=None,
        stack_entries=(),
        vulnerable_versions=(VulnerableVersion("nginx", "1.18.0", "1.20.0"),),
        findings=("Serveur détecté : nginx/1.18.0", "Version potentiellement vulnérable : nginx 1.18.0 ..."),
        fetch_ok=True,
    )
    findings = normalize_results({"tech_fingerprinting": result})
    assert len(findings) >= 1
    vuln_findings = [f for f in findings if f.id == "tech_fingerprinting-vulnerable-version"]
    assert len(vuln_findings) == 1
    assert vuln_findings[0].severity == "medium"


def test_normalize_tech_fingerprinting_stack_unknown() -> None:
    """tech_fingerprinting sans stack produit tech_fingerprinting-stack-unknown."""
    result = TechFingerprintingCheckResult(
        server=None,
        server_version=None,
        runtime=None,
        runtime_version=None,
        framework_cms=None,
        framework_cms_version=None,
        stack_entries=(),
        vulnerable_versions=(),
        findings=("Stack : non identifiée (ou masquée)",),
        fetch_ok=True,
    )
    findings = normalize_results({"tech_fingerprinting": result})
    assert len(findings) == 1
    assert findings[0].id == "tech_fingerprinting-stack-unknown"


def test_normalize_cors_cross_origin_fetch_ok_false() -> None:
    """CORS avec fetch_ok=False produit cors-connection-failed."""
    result = CorsCrossOriginCheckResult(
        findings=("CORS et cross-origin inaccessibles : réponse HTTPS indisponible.",),
        fetch_ok=False,
    )
    findings = normalize_results({"cors_cross_origin": result})
    assert len(findings) == 1
    assert findings[0].id == "cors-connection-failed"
    assert findings[0].category == "cors_cross_origin"
    assert findings[0].severity == "high"


def test_normalize_cors_cross_origin_mixed_content() -> None:
    """CORS finding mixed content produit mixed-content-http-on-https."""
    result = CorsCrossOriginCheckResult(
        findings=("Mixed content : ressource chargée en HTTP sur page HTTPS : http://evil.com/lib.js.",),
        fetch_ok=True,
        issues=(CorsIssue(kind="mixed_content", message="Mixed content : ressource chargée en HTTP sur page HTTPS : http://evil.com/lib.js."),),
    )
    findings = normalize_results({"cors_cross_origin": result})
    assert len(findings) == 1
    assert findings[0].id == "mixed-content-http-on-https"
    assert findings[0].category == "cors_cross_origin"
    assert findings[0].severity == "high"


def test_normalize_cors_cross_origin_acao_star_sensitive() -> None:
    """CORS finding ACAO * sur endpoint sensible produit cors-allow-origin-star-sensitive."""
    result = CorsCrossOriginCheckResult(
        findings=("Access-Control-Allow-Origin: * sur endpoint sensible : https://example.com/api/.",),
        fetch_ok=True,
        issues=(CorsIssue(kind="acao_star_sensitive", message="Access-Control-Allow-Origin: * sur endpoint sensible : https://example.com/api/."),),
    )
    findings = normalize_results({"cors_cross_origin": result})
    assert len(findings) == 1
    assert findings[0].id == "cors-allow-origin-star-sensitive"
    assert findings[0].category == "cors_cross_origin"
    assert findings[0].severity == "high"


def test_normalize_results_full_pipeline() -> None:
    """normalize_results agrège tous les types de résultats."""
    tls = TlsCheckResult(
        https_enabled=True,
        http_redirects_to_https=True,
        certificate_status="valid",
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=True,
    )
    headers = SecurityHeadersCheckResult(
        headers_present=(),
        headers_missing=("Content-Security-Policy",),
        findings=("Content-Security-Policy absent : risque XSS accru.",),
        fetch_ok=True,
    )
    results = {"tls": tls, "headers": headers}
    findings = normalize_results(results)
    assert len(findings) == 1
    assert findings[0].category == "headers"
    assert findings[0].id == "headers-csp-absent"


def test_finding_has_recommendation_and_references() -> None:
    """Chaque Finding a recommendation et references depuis le catalogue."""
    result = SecurityHeadersCheckResult(
        headers_present=(),
        headers_missing=("Content-Security-Policy",),
        findings=("Content-Security-Policy absent : risque XSS accru.",),
        fetch_ok=True,
    )
    findings = normalize_results({"headers": result})
    assert len(findings) == 1
    f = findings[0]
    assert f.recommendation
    assert "Content-Security-Policy" in f.recommendation or "CSP" in f.recommendation
    assert isinstance(f.references, tuple)
    assert len(f.references) >= 0


def test_finding_to_dict_serializable() -> None:
    """Finding.to_dict() produit un dict sérialisable."""
    result = TlsCheckResult(
        https_enabled=False,
        http_redirects_to_https=None,
        certificate_status=None,
        tls_versions_obsolete=(),
        findings=(),
        fetch_ok=False,
    )
    findings = normalize_results({"tls": result})
    d = findings[0].to_dict()
    assert "id" in d
    assert "category" in d
    assert "title" in d
    assert "severity" in d
    assert "evidence" in d
    assert "recommendation" in d
    assert "references" in d
    assert isinstance(d["references"], list)
