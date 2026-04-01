"""Category summaries dedicated to non-passive scan modes."""

from __future__ import annotations

from app.models.finding import Finding


def _entry(
    *,
    category: str,
    label_fr: str,
    label_en: str,
    description_fr: str,
    description_en: str,
    checks_fr: list[str],
    checks_en: list[str],
    anomaly_count: int,
    checks_count: int,
    granular_categories: list[str] | None = None,
) -> dict:
    entry: dict = {
        "category": category,
        "label_fr": label_fr,
        "label_en": label_en,
        "description_fr": description_fr,
        "description_en": description_en,
        "checks_fr": checks_fr,
        "checks_en": checks_en,
        "anomaly_count": anomaly_count,
        "checks_count": checks_count,
    }
    if granular_categories is not None:
        entry["granular_categories"] = granular_categories
    return entry


def _count_by_category(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.category] = counts.get(finding.category, 0) + 1
    return counts


def build_intrusive_category_summaries(findings: list[Finding], scan_type: str = "frontend") -> list[dict]:
    """Build summaries for intrusive checks grouped into 8 macro-categories.

    scan_type filtre les checks non applicables avant agrégation :
    - backend  : skip parametres_reflechis
    - frontend : skip mass_assignment, graphql_abuse, api_schema_abuse, grpc_abuse, graphql_subscriptions
    """
    by_cat = _count_by_category(findings)

    _FRONTEND_ONLY = {"parametres_reflechis"}
    _BACKEND_ONLY = {"mass_assignment", "graphql_abuse", "api_schema_abuse", "grpc_abuse", "graphql_subscriptions"}

    def _inc(cat: str) -> bool:
        if scan_type == "backend" and cat in _FRONTEND_ONLY:
            return False
        if scan_type == "frontend" and cat in _BACKEND_ONLY:
            return False
        return True

    # Définition granulaire de chaque check (source de vérité)
    _CHECKS: list[dict] = [
        # ── injections ────────────────────────────────────────────────────────
        {
            "macro": "injections",
            "cat": "sql_injection",
            "checks_fr": ["Probe SQL error-based", "Probe SQL time-based"],
            "checks_en": ["SQL error-based probe", "SQL time-based probe"],
            "n": 2,
        },
        {
            "macro": "injections",
            "cat": "nosql_injection",
            "checks_fr": ["Probe opérateurs NoSQL QS", "Probe body JSON NoSQL"],
            "checks_en": ["NoSQL QS operator probe", "NoSQL JSON body probe"],
            "n": 2,
        },
        {
            "macro": "injections",
            "cat": "command_injection",
            "checks_fr": ["Probe shell error-based", "Probe shell time-based"],
            "checks_en": ["Shell error-based probe", "Shell time-based probe"],
            "n": 2,
        },
        {
            "macro": "injections",
            "cat": "ssti",
            "checks_fr": ["Probe SSTI (7*7=49) et erreurs de template"],
            "checks_en": ["SSTI probe (7*7=49) and template errors"],
            "n": 2,
        },
        {
            "macro": "injections",
            "cat": "xxe",
            "checks_fr": ["Probe entité XML externe sur endpoints XML"],
            "checks_en": ["XML external entity probe on XML endpoints"],
            "n": 1,
        },
        {
            "macro": "injections",
            "cat": "lfi_rfi",
            "checks_fr": ["Probe path traversal LFI", "PHP wrapper probe"],
            "checks_en": ["LFI path traversal probe", "PHP wrapper probe"],
            "n": 2,
        },
        {
            "macro": "injections",
            "cat": "path_traversal",
            "checks_fr": ["Probe path traversal sur paramètres fichier"],
            "checks_en": ["Path traversal probe on file parameters"],
            "n": 1,
        },
        # ── access_control ────────────────────────────────────────────────────
        {
            "macro": "access_control",
            "cat": "cors_actif",
            "checks_fr": ["Probe CORS avec Origin externe"],
            "checks_en": ["CORS probe with external Origin"],
            "n": 1,
        },
        {
            "macro": "access_control",
            "cat": "csrf",
            "checks_fr": ["Replay POST sans token CSRF", "Vérification SameSite"],
            "checks_en": ["POST replay without CSRF token", "SameSite verification"],
            "n": 2,
        },
        {
            "macro": "access_control",
            "cat": "host_header",
            "checks_fr": ["Probe Host/X-Forwarded-Host avec domaine externe"],
            "checks_en": ["Host/X-Forwarded-Host probe with external domain"],
            "n": 1,
        },
        {
            "macro": "access_control",
            "cat": "open_redirect",
            "checks_fr": ["Probe redirection ouverte sur paramètres communs et détectés"],
            "checks_en": ["Open redirect probe on common and detected parameters"],
            "n": 1,
        },
        {
            "macro": "access_control",
            "cat": "ssrf",
            "checks_fr": ["Probe IMDS / localhost sur paramètres URL/webhook"],
            "checks_en": ["IMDS / localhost probe on URL/webhook parameters"],
            "n": 1,
        },
        {
            "macro": "access_control",
            "cat": "methodes_http",
            "checks_fr": ["OPTIONS + TRACE probe"],
            "checks_en": ["OPTIONS + TRACE probe"],
            "n": 2,
        },
        # ── auth_sessions ─────────────────────────────────────────────────────
        {
            "macro": "auth_sessions",
            "cat": "auth_bruteforce",
            "checks_fr": ["5 tentatives avec credentials invalides"],
            "checks_en": ["5 attempts with invalid credentials"],
            "n": 1,
        },
        {
            "macro": "auth_sessions",
            "cat": "session_fixation",
            "checks_fr": ["Test de logout et réutilisation de session", "Vérification claims JWT"],
            "checks_en": ["Logout and session reuse test", "JWT claims verification"],
            "n": 2,
        },
        {
            "macro": "auth_sessions",
            "cat": "oauth_oidc",
            "checks_fr": ["redirect_uri externe probe", "Vérification paramètre state"],
            "checks_en": ["External redirect_uri probe", "State parameter verification"],
            "n": 2,
        },
        {
            "macro": "auth_sessions",
            "cat": "idor",
            "checks_fr": ["Incrémentation d'ID séquentiel", "Accès routes admin", "Escalade de privilèges"],
            "checks_en": ["Sequential ID increment", "Admin route access", "Privilege escalation"],
            "n": 3,
        },
        # ── client_injection ─────────────────────────────────────────────────
        {
            "macro": "client_injection",
            "cat": "parametres_reflechis",
            "checks_fr": ["Marker de réflexion sur paramètres query string et formulaires"],
            "checks_en": ["Reflection marker on query string and form parameters"],
            "n": 1,
        },
        # ── business_data ─────────────────────────────────────────────────────
        {
            "macro": "business_data",
            "cat": "business_logic",
            "checks_fr": ["Montants/quantités négatifs", "Manipulation d'état"],
            "checks_en": ["Negative amounts/quantities", "State manipulation"],
            "n": 2,
        },
        {
            "macro": "business_data",
            "cat": "race_conditions",
            "checks_fr": ["3 requêtes simultanées sur endpoints sensibles"],
            "checks_en": ["3 simultaneous requests on sensitive endpoints"],
            "n": 1,
        },
        {
            "macro": "business_data",
            "cat": "dos_rate_limit",
            "checks_fr": ["Burst contrôlé (5 req)"],
            "checks_en": ["Controlled burst (5 req)"],
            "n": 1,
        },
        {
            "macro": "business_data",
            "cat": "upload_abuse",
            "checks_fr": ["Upload fichier PHP/double extension", "Upload path traversal"],
            "checks_en": ["PHP/double extension upload", "Path traversal upload"],
            "n": 2,
        },
        {
            "macro": "business_data",
            "cat": "insecure_deserialization",
            "checks_fr": ["Analyse cookies sérialisés", "Probe Java magic bytes"],
            "checks_en": ["Serialized cookie analysis", "Java magic bytes probe"],
            "n": 2,
        },
        {
            "macro": "business_data",
            "cat": "mass_assignment",
            "checks_fr": ["PUT/PATCH avec champs sensibles (role, admin, price)"],
            "checks_en": ["PUT/PATCH with sensitive fields (role, admin, price)"],
            "n": 1,
        },
        # ── api_protocols ─────────────────────────────────────────────────────
        {
            "macro": "api_protocols",
            "cat": "graphql_abuse",
            "checks_fr": ["Introspection probe", "Depth query probe"],
            "checks_en": ["Introspection probe", "Depth query probe"],
            "n": 2,
        },
        {
            "macro": "api_protocols",
            "cat": "graphql_subscriptions",
            "checks_fr": ["Probe souscription anonyme"],
            "checks_en": ["Anonymous subscription probe"],
            "n": 1,
        },
        {
            "macro": "api_protocols",
            "cat": "api_schema_abuse",
            "checks_fr": ["Type confusion probe", "Limit=99999 probe"],
            "checks_en": ["Type confusion probe", "Limit=99999 probe"],
            "n": 2,
        },
        {
            "macro": "api_protocols",
            "cat": "grpc_abuse",
            "checks_fr": ["Probe gRPC Reflection Service"],
            "checks_en": ["gRPC Reflection Service probe"],
            "n": 1,
        },
        {
            "macro": "api_protocols",
            "cat": "websocket_authz",
            "checks_fr": ["Probe WebSocket upgrade anonyme"],
            "checks_en": ["Anonymous WebSocket upgrade probe"],
            "n": 1,
        },
        # ── infra_cache ───────────────────────────────────────────────────────
        {
            "macro": "infra_cache",
            "cat": "cache_poisoning",
            "checks_fr": ["X-Forwarded-Host poisoning", "Web Cache Deception probe"],
            "checks_en": ["X-Forwarded-Host poisoning", "Web Cache Deception probe"],
            "n": 2,
        },
        {
            "macro": "infra_cache",
            "cat": "request_smuggling",
            "checks_fr": ["Probe CL/TE contradictoires", "Probe TE.TE obfusqué"],
            "checks_en": ["Contradictory CL/TE probe", "Obfuscated TE.TE probe"],
            "n": 2,
        },
        {
            "macro": "infra_cache",
            "cat": "service_mesh",
            "checks_fr": ["Probe actuator, debug, health, env"],
            "checks_en": ["Actuator, debug, health, env probe"],
            "n": 1,
        },
        {
            "macro": "infra_cache",
            "cat": "object_storage",
            "checks_fr": ["Probe listing S3/GCS/Azure Blob"],
            "checks_en": ["S3/GCS/Azure Blob listing probe"],
            "n": 1,
        },
    ]

    _MACRO_META: dict[str, dict] = {
        "injections": {
            "label_fr": "Injections",
            "label_en": "Injections",
            "description_fr": (
                "SQLi, NoSQLi, injection de commande OS, SSTI, XXE, LFI/RFI et traversée de répertoire. "
                "Ces vecteurs permettent d'exécuter du code arbitraire, d'exfiltrer des données ou de "
                "prendre le contrôle du serveur."
            ),
            "description_en": (
                "SQLi, NoSQLi, OS command injection, SSTI, XXE, LFI/RFI and path traversal. "
                "These vectors allow arbitrary code execution, data exfiltration or server takeover."
            ),
        },
        "access_control": {
            "label_fr": "Contrôle d'accès",
            "label_en": "Access Control",
            "description_fr": (
                "CORS actif (réflexion + credentials), CSRF (token et SameSite), Host Header injection, "
                "Open Redirect, SSRF in-band et méthodes HTTP dangereuses (TRACE, PUT, DELETE)."
            ),
            "description_en": (
                "Active CORS (reflection + credentials), CSRF (token and SameSite), Host Header injection, "
                "Open Redirect, in-band SSRF and dangerous HTTP methods (TRACE, PUT, DELETE)."
            ),
        },
        "auth_sessions": {
            "label_fr": "Authentification & Sessions",
            "label_en": "Authentication & Sessions",
            "description_fr": (
                "IDOR/BOLA/BFLA (accès direct à un objet par identifiant), absence de verrouillage de compte "
                "(bruteforce), non-invalidation de session après déconnexion, absence d'expiration JWT, "
                "failles OAuth/OIDC."
            ),
            "description_en": (
                "IDOR/BOLA/BFLA (insecure direct object reference), missing account lockout (bruteforce), "
                "session not invalidated after logout, missing JWT expiration, OAuth/OIDC flaws."
            ),
        },
        "client_injection": {
            "label_fr": "Injections côté client",
            "label_en": "Client-side Injections",
            "description_fr": (
                "Paramètres GET/POST réfléchis sans encodage dans les réponses HTML, pouvant mener à des "
                "attaques XSS réfléchi. Frontend uniquement."
            ),
            "description_en": (
                "GET/POST parameters reflected without encoding in HTML responses, which can lead to " "reflected XSS attacks. Frontend only."
            ),
        },
        "business_data": {
            "label_fr": "Logique métier & Données",
            "label_en": "Business Logic & Data",
            "description_fr": (
                "Manipulation de montants négatifs, manipulation d'état de workflow, race conditions, "
                "absence de rate limiting (DoS), abus d'upload de fichiers, désérialisation non sécurisée "
                "et mass assignment."
            ),
            "description_en": (
                "Negative amount manipulation, workflow state manipulation, race conditions, "
                "missing rate limiting (DoS), file upload abuse, insecure deserialization and mass assignment."
            ),
        },
        "api_protocols": {
            "label_fr": "APIs & Protocoles modernes",
            "label_en": "APIs & Modern Protocols",
            "description_fr": (
                "Introspection GraphQL exposée, abus de profondeur GraphQL, souscriptions sans "
                "authentification, gRPC Reflection exposé, WebSocket sans authentification, schéma OpenAPI "
                "sans validation. Backend uniquement."
            ),
            "description_en": (
                "Exposed GraphQL introspection, GraphQL query depth abuse, unauthenticated subscriptions, "
                "exposed gRPC Reflection, WebSocket without authentication, OpenAPI schema without validation. "
                "Backend only."
            ),
        },
        "infra_cache": {
            "label_fr": "Infrastructure & Cache",
            "label_en": "Infrastructure & Cache",
            "description_fr": (
                "Cache poisoning (X-Forwarded-Host), web cache deception, request smuggling (CL/TE et "
                "TE.TE), exposition d'endpoints internes (actuator, debug, health) et listing public de "
                "buckets d'object storage."
            ),
            "description_en": (
                "Cache poisoning (X-Forwarded-Host), web cache deception, request smuggling (CL/TE and "
                "TE.TE), internal endpoint exposure (actuator, debug, health) and public object storage "
                "bucket listing."
            ),
        },
    }

    # Agrégation par macro-catégorie
    agg: dict[str, dict] = {}
    for check in _CHECKS:
        if not _inc(check["cat"]):
            continue
        macro = check["macro"]
        if macro not in agg:
            agg[macro] = {
                "anomaly_count": 0,
                "checks_count": 0,
                "checks_fr": [],
                "checks_en": [],
                "granular_categories": [],
            }
        agg[macro]["anomaly_count"] += by_cat.get(check["cat"], 0)
        agg[macro]["checks_count"] += check["n"]
        agg[macro]["checks_fr"].extend(check["checks_fr"])
        agg[macro]["checks_en"].extend(check["checks_en"])
        agg[macro]["granular_categories"].append(check["cat"])

    # Ordre fixe des macro-catégories
    _ORDER = ["injections", "access_control", "auth_sessions", "client_injection", "business_data", "api_protocols", "infra_cache"]

    result = []
    for macro in _ORDER:
        if macro not in agg:
            continue
        meta = _MACRO_META[macro]
        data = agg[macro]
        result.append(
            _entry(
                category=macro,
                label_fr=meta["label_fr"],
                label_en=meta["label_en"],
                description_fr=meta["description_fr"],
                description_en=meta["description_en"],
                checks_fr=data["checks_fr"],
                checks_en=data["checks_en"],
                anomaly_count=data["anomaly_count"],
                checks_count=data["checks_count"],
                granular_categories=data["granular_categories"],
            )
        )
    return result


def build_custom_category_summaries(findings: list[Finding] | None = None) -> list[dict]:
    """Build summaries for custom scan mode."""
    by_cat = _count_by_category(findings or [])
    return [
        _entry(
            category="custom",
            label_fr="Scénario custom",
            label_en="Custom Scenario",
            description_fr="Résultats du scénario custom défini par l'utilisateur.",
            description_en="Results from the user-defined custom scenario.",
            checks_fr=["Exécution du scénario custom"],
            checks_en=["Custom scenario execution"],
            anomaly_count=by_cat.get("custom", 0),
            checks_count=1,
        ),
    ]


def build_destructive_category_summaries(findings: list[Finding] | None = None) -> list[dict]:
    """Build summaries for destructive P4 checks."""
    by_cat = _count_by_category(findings or [])
    return [
        _entry(
            category="dos_aggressive",
            label_fr="DoS agressif (P4)",
            label_en="Aggressive DoS (P4)",
            description_fr="Burst agressif pour tester l'absence de rate limiting. Requiert opt_in explicite.",
            description_en="Aggressive burst to test missing rate limiting. Requires explicit opt_in.",
            checks_fr=["Burst 20 req + détection 429"],
            checks_en=["20 req burst + 429 detection"],
            anomaly_count=by_cat.get("dos_aggressive", 0),
            checks_count=1,
        ),
        _entry(
            category="http2_abuse",
            label_fr="HTTP/2 Abuse (P4)",
            label_en="HTTP/2 Abuse (P4)",
            description_fr="Tests d'abus HTTP/2 : streams parallèles, rapid reset.",
            description_en="HTTP/2 abuse tests: parallel streams, rapid reset.",
            checks_fr=["10 streams HTTP/2 simultanés"],
            checks_en=["10 simultaneous HTTP/2 streams"],
            anomaly_count=by_cat.get("http2_abuse", 0),
            checks_count=1,
        ),
        _entry(
            category="unicode_normalization",
            label_fr="Unicode Confusion (P4)",
            label_en="Unicode Confusion (P4)",
            description_fr="Bypass d'autorisation via confusion de normalisation Unicode.",
            description_en="Authorization bypass via Unicode normalization confusion.",
            checks_fr=["Variantes Unicode sur routes protégées"],
            checks_en=["Unicode variants on protected routes"],
            anomaly_count=by_cat.get("unicode_normalization", 0),
            checks_count=1,
        ),
        _entry(
            category="dns_rebinding",
            label_fr="DNS Rebinding (P4)",
            label_en="DNS Rebinding (P4)",
            description_fr="Détection des vulnérabilités DNS rebinding applicatif.",
            description_en="Detection of applicative DNS rebinding vulnerabilities.",
            checks_fr=["Validation Host header"],
            checks_en=["Host header validation"],
            anomaly_count=by_cat.get("dns_rebinding", 0),
            checks_count=1,
        ),
        _entry(
            category="parser_differential",
            label_fr="Parser Differential (P4)",
            label_en="Parser Differential (P4)",
            description_fr="Attaques par différence de parsing entre proxies.",
            description_en="Parser differential attacks between proxies.",
            checks_fr=["Confusion de chemin URL"],
            checks_en=["URL path confusion"],
            anomaly_count=by_cat.get("parser_differential", 0),
            checks_count=1,
        ),
    ]


def count_total_tests(category_summaries: list[dict]) -> int:
    """Compute total tests count from mode-specific category summaries."""
    return sum(int(entry.get("checks_count", 0)) for entry in category_summaries)
