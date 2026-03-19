# SecureOps — Roadmap MVP 0.4.0

Objectif : **finaliser tous les tests passifs** (section 5 de la v0.2.0), **introduire les tests actifs** (premiers pas), **rapports et analytics** (tendances, export, tableau de bord), **scan paramétrable** (ex. mode critical uniquement) et **explication du scoring** dans le frontend.

**Prérequis :** MVP 0.2.0 livré (API publique, clés API, scan avancé partiel, CI/CD).

**Périmètre des tests :** Pour chaque section, le périmètre est indiqué en *italique* sous le titre : **frontend** (UI, affichage, pages web cibles), **backend** (APIs, moteur scan, services), ou **les deux**.

## Sommaire

**Ordre recommandé :** 0 (architecture) → 1 (passif + backlog) → [2, 3, 5, 6 reportés en 0.5.0](ROADMAP-MVP-0.5.0.md) → 4 (rapports/analytics) → 7 (release).

- [0) Architecture : deux scanners](#0-architecture--deux-scanners)
  - [0.1 Rappel : passif vs actif](#01-rappel--passif-vs-actif)
- [1) Finaliser les tests passifs restants](#1-finaliser-les-tests-passifs-restants)
  - [1.1 Méthodes HTTP et redirections](#11-méthodes-http-et-redirections-ex-roadmap-55-voir-a-penser-plus-tard)
  - [1.2 Intégrité et sous-ressources](#12-intégrité-et-sous-ressources-56--restant-roadmap-020)
  - [1.3 APIs et formats](#13-apis-et-formats-ex-roadmap-57-voir-a-penser-plus-tard)
  - [1.4 Tests passifs complémentaires](#14-tests-passifs-complémentaires)
  - [1.5 Backlog tests reporté — déplacé en 0.5.0](#15-backlog-tests-reporté--déplacé-en-roadmap-050)
  - [1.6 Backlog reporté depuis la roadmap 0.3.0 (hors section tests)](#16-backlog-reporté-depuis-la-roadmap-030-hors-section-tests)
  - [1.7 Adaptation des tests passifs pour scan_type backend](#17-adaptation-des-tests-passifs-pour-scan_type-backend)
- [2) Vérification d'autorisation — déplacé en 0.5.0](#2-vérification-dautorisation--déplacé-en-roadmap-050)
- [3) Introduire les tests actifs — déplacé en 0.5.0](#3-introduire-les-tests-actifs--déplacé-en-roadmap-050)
- [4) Rapports et analytics](#4-rapports-et-analytics)
- [5) Scan paramétrable — déplacé en 0.5.0](#5-scan-paramétrable--déplacé-en-roadmap-050)
- [6) Infra et qualité — déplacé en 0.5.0](#6-infra-et-qualité--déplacé-en-roadmap-050)
- [7) Release MVP v0.4.0](#7-release-mvp-v040)
- [Synthèse](#synthèse)
- [Notes importantes (MVP 0.4.0)](#notes-importantes-mvp-040)
- [Périmètre des tests : URL frontend vs backend](#périmètre-des-tests--url-frontend-vs-backend)

---

## 0) Architecture : deux scanners

| Scanner | Tests | Vérification DNS | URLs autorisées |
|---------|-------|------------------|-----------------|
| **Scanner 1 (passif)** | Tests passifs uniquement | Non requise | Toutes les URLs |
| **Scanner 2 (actif)** | Tests passifs (optionnel) + tests actifs | **Obligatoire** | Uniquement les URLs dont le domaine a été vérifié par l’utilisateur |

### Scanner 1 — Passif

- Premier scanner, celui qui existe déjà (étendu avec tous les tests passifs).
- Fonctionne sur **n’importe quelle URL**.
- Aucune vérification d’autorisation requise.

### Scanner 2 — Actif

- Deuxième scanner, nouveau.
- **Ne fonctionne que pour les URLs dont le domaine a été vérifié** par l’utilisateur (voir section 2).
- **Option :** Inclure les tests passifs en premier (choix utilisateur, **défaut : oui**). Si activé : exécution des tests passifs puis des tests actifs. Si désactivé : tests actifs uniquement.
- Vérification DNS obligatoire avant tout scan.

---

## 0.1 Rappel : passif vs actif

| Type | Définition | Exemple |
|------|------------|---------|
| **Passif** | Lecture et analyse des réponses. Aucune requête « provocante ». | Lire les headers, analyser le HTML, détecter des patterns |
| **Actif** | Envoi de requêtes ou paramètres **craftés** pour provoquer un comportement révélateur. | Envoyer `?redirect=evil.com`, tester TRACE, envoyer un payload dans un paramètre |

> **Attention :** Les tests actifs peuvent déclencher des actions côté serveur (logs, alertes, blocages). Le disclaimer « usage autorisé uniquement » est **obligatoire**. Documenter les requêtes envoyées dans le rapport.

---

## 1) Finaliser les tests passifs restants

> Les tests passifs des sections 5.1 à 5.4 et 5.8 de la roadmap 0.2.0 sont livrés (TLS, headers, cookies, exposition fichiers, directory listing, robots, sitemap, tech fingerprinting, information disclosure, cache, CORS et cross-origin). Il reste à implémenter pour le Scanner 1 (passif) :

### 1.1 Méthodes HTTP et redirections (ex-roadmap 5.5, voir A-PENSER-PLUS-TARD)
*Périmètre : **les deux** (frontend et backend)*

- [x] Requête OPTIONS : méthodes autorisées — *Info* — Réutilisation des OPTIONS CORS (Allow + Access-Control-Allow-Methods) ; pas de requête supplémentaire.
- [x] TRACE activé → finding (XST) — *Medium à High* — Requête TRACE sur page + chemins sensibles (limite `trace_max_urls`), finding si 200 + écho.
- [x] PUT, DELETE, PATCH exposés sans nécessité → info — *Info à Low* — Depuis Allow/ACAM ; distinction frontend (Low) / backend (Info) via `scan_type`.
- [x] HEAD supporté (bonne pratique) — *Info* — Requête HEAD sur la page ; finding si 4xx/5xx.
- [x] Chaînes de redirection excessives (> 5) — *Info à Low* — Analyse de `response.history` (fetch initial) ; seuil configurable `redirect_chain_max`.
- [x] Redirection HTTP→HTTPS : 301/302 vs 307/308 — *Info* — Finding si 301/302 dans la chaîne et URL finale sur chemin formulaire sensible (`form_sensitive_paths`).

---

### 1.2 Intégrité et sous-ressources (5.6 — restant roadmap 0.2.0)
*Périmètre : **frontend** (HTML, scripts, formulaires)*

- [x] Scripts/CSS externes (CDN) sans attribut `integrity` → finding
- [x] Balises `<script>` sans nonce ou integrity (contexte CSP), uniquement lorsque l'en-tête CSP est présent (sinon, un message informe que les tests avancés ne sont pas appliqués)
- [x] Formulaires sans autocomplete adapté sur champs sensibles (password)
- [x] `target="_blank"` sans `rel="noopener noreferrer"`
- [x] Meta `robots` (noindex sur pages sensibles)

---

### 1.3 APIs et formats (ex-roadmap 5.7, voir [apis-et-formats.md](../../verifications/passive/apis-et-formats.md))
*Périmètre : **backend** (APIs exposées) ; **les deux** (formats de réponse)*

- [x] GraphQL : introspection activée sur `/graphql` ou similaire — *Backend* — Phase domaine : POST `{"query":"{ __schema { types { name } } }"}` sur chemins `graphql_paths` ; finding si 200 + schéma JSON retourné.
- [x] Swagger/OpenAPI exposé sans auth — *Backend* — Phase domaine : GET sur `swagger_paths` (`/swagger`, `/api-docs`, `/openapi.json`, etc.) ; finding si 200 + corps contient `openapi`/`swagger` (JSON) ou Swagger UI (HTML).
- [x] Endpoints REST : listes non paginées (info) — *Backend* — Phase domaine : GET sur `api_list_paths` ; phase page : analyse de chaque réponse JSON (multi-URL) ; finding si tableau ≥ 50 éléments sans `page`/`limit`/`offset` dans la réponse ; seuil `unpaginated_list_threshold: 50`.
- [x] Content-Type incorrect (JSON servi en text/html) — *Les deux* — Analyse de la réponse (page + réponses API) : si corps ressemble à JSON (`{` ou `[`) et `Content-Type` ≠ `application/json` → finding Medium.
- [x] X-Content-Type-Options: nosniff sur tous les types — *Les deux* — Vérifié sur les **réponses API uniquement** (phase domaine) ; la page principale reste couverte par `security_headers` pour éviter doublon.
- [x] Compression (gzip/brotli) — *Les deux* — Sur page (phase page) et sur chaque réponse API (phase domaine) ; finding Info si corps textuel > `compression_min_body_bytes` (1024) et absence de `Content-Encoding: gzip` ou `br`.

#### Architecture : backend vs both

| Module | Périmètre | Phase | Contenu |
|--------|-----------|-------|---------|
| `passive/backend/api/` | Backend | Domaine (1× par base) | GraphQL, Swagger, REST listes ; appelle `check_formats_from_response` sur chaque réponse API (Content-Type, X-CTO, compression) |
| `passive/both/formats/` | Les deux | Page (par URL) | `check_formats_from_response(page_response, check_xcto=False)` — Content-Type, compression uniquement sur la page (X-CTO déjà dans security_headers) |

#### Implémentation technique

- [x] **backend/api** : `run_api_checks(base_url, client)` — probes en séquence GraphQL (POST introspection), Swagger (GET), REST listes (GET) ; pour chaque réponse 200, appelle `check_formats_from_response(..., check_xcto=True)`.
- [x] **both/formats** : `check_formats_from_response(response, url, check_xcto, compression_min_body_bytes)` — fonction pure, appelée par page checks (page) et par backend/api (réponses API).
- [x] **REST listes** : `check_rest_from_response(url, response, threshold)` — appelé en phase page pour chaque URL scannée ; détecte JSON avec array ou clé `items`/`users`/`data` ≥ 50 éléments sans pagination.
- [x] **exposed_files** : retrait des chemins `/swagger`, `/swagger.json`, `/api-docs`, `/api-docs.json`, `/graphql` — centralisés dans apis_et_formats.

#### Fichiers créés / modifiés

| Fichier | Modification |
|---------|--------------|
| `passive/backend/api/` | **Nouveau** — checks (GraphQL, Swagger, REST), normalizer, `check_rest_from_response` pour phase page |
| `passive/both/formats/` | **Nouveau** — checks (Content-Type, X-CTO, compression), normalizer |
| `config/apis_et_formats.py` | **Nouveau** — chargement `graphql_paths`, `swagger_paths`, `api_list_paths`, `unpaginated_list_threshold`, `compression_min_body_bytes` |
| `config/settings.yml` | Section `apis_et_formats` ; retrait `/swagger`, `/graphql`, `/api-docs` de `exposed_files` |
| `both/exposed_files/checks.py` | Retrait des checkers `/swagger`, `/graphql`, `/api-docs` |
| `passive/_page_checks_runner.py` | Ajout `formats` (check_formats_from_response, check_xcto=False) et `api_page` (check_rest_from_response) |
| `passive/_scan_core.py` | Ajout étapes `api_checks`, `formats`, `api_page` |
| `passive/multi_scan_orchestrator.py` | `_run_domain_api` : run_api_checks en phase domaine |
| `passive/normalization.py` | Normalizers `api_checks`, `formats`, `api_page` → catégorie `apis_et_formats` |
| `passive/scan_stream.py` | Étapes SSE `api_checks`, `formats`, `api_page` |
| `catalogue/category_summaries.json` | Entrée `apis_et_formats` ; mise à jour `exposed_files` (retrait swagger/graphql) |
| `catalogue/recommendations.json` | Slugs api-graphql-introspection, api-swagger-exposed, api-rest-unpaginated, formats-* |
| `scoring` / `category_labels` | Pondération 5 ; label FR/EN |

---

### 1.4 Tests passifs complémentaires
*Périmètre : **frontend** (formulaires, meta) ; **les deux** (OWASP mapping)*

- [x] Formulaires : détection de tokens CSRF (présence de champ csrf_token, _token, etc.)

  > **Fait :** Parser HTML dans `frontend/integrity/checks.py` : détection des `<form method="post">` sans champ hidden dont le nom figure dans `integrity.csrf_field_names` (configurable dans `settings.yml` : csrf_token, _token, authenticity_token, _csrf, __RequestVerificationToken, etc.). Un seul finding agrégé avec le nombre de formulaires concernés. Sévérité Low. Normalizer + slug `integrity-forms-post-without-csrf` + recommandation dans le catalogue.

- [x] Métadonnées : analyse des balises `<meta>` (robots, generator)

  > **Fait :** Meta robots : déjà couvert par integrity (présence de `<meta name="robots">` et directive noindex sur pages sensibles). Meta generator : ajout dans `information_disclosure/checks.py` — détection de `<meta name="generator" content="...">` dans le body HTML, finding `info-disclosure-meta-generator` (sévérité info). Le module `tech_fingerprinting` utilise déjà meta generator pour le fingerprinting CMS et la détection de versions vulnérables.

- [x] Mapping OWASP Top 10 : associer chaque finding à une catégorie OWASP (A01–A10)

  > **Fait :** Mapping OWASP Top 10:2025 dans `catalogue/owasp_mapping.json` (fichier dédié). Module `catalogue/owasp.py` avec `get_owasp_categories(slug)` — correspondance exacte + préfixe pour slugs dynamiques (exposed_files-*, directory_listing-*). Pas de fallback : slugs non mappés retournent (). Champ `owasp_categories: tuple[str, ...]` ajouté au modèle Finding et à `to_dict()`. Tous les normalizers passifs peuplent ce champ. Affichage dans le PDF (après le badge sévérité) et dans l'UI (FindingCard).

---

### 1.5 Backlog tests reporté — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §1 — Tests d'intégration : Docker Compose, serveurs de démo, scénarios, CI.

---

### 1.6 Backlog reporté depuis la roadmap 0.3.0 (hors section tests)
*Périmètre : **backend** (GitHub Action, gouvernance crawler) ; **frontend** (docs/UX, affichage anomalies)*

Objectif : centraliser dans la v0.4.0 les éléments non faits de la v0.3.0 liés à l’intégration CI/CD, au crawler, à la doc/UX scanner et au rendu d’anomalies.

#### 1.6.1 GitHub Action SecureOps (ex-section 3 de la v0.3.0)

- [ ] Créer la répo `secureops/actions` ou une action dans le monorepo.
- [ ] Définir les inputs : `url`, `api_key` (secret), `fail_on_score_below` (optionnel).
- [ ] Appeler `POST /scan/api/scan` avec `X-API-Key` (API publique SecureOps).
- [ ] Parser le résultat (score, findings).
- [ ] Faire échouer le job si `score < fail_on_score_below` ou si finding `critical`.
- [ ] Rédiger un README avec un exemple d’utilisation dans un workflow GitHub Actions.
- [ ] (Optionnel) Fournir un badge « Scan SecureOps » pour le README des projets utilisateurs.

#### 1.6.2 Gouvernance crawler (ex-section 7.6 de la v0.3.0)

- [x] **Liste noire configurable** — *Fait :* section `blacklist.domains` dans `settings.yml` (scan-service, crawl-service) ; blocage scan/crawl si hostname exact ou sous-domaine (ex. `secureops.fr` bloque `www.secureops.fr`). Par défaut : `secureops.fr`. Voir `common/blacklist.py`, `common/config_base.py`.
- [x] **Quotas et rate limiting** — *Fait :* rate limiting court terme (10 req/60s user, 3 req/60s anon) et quota journalier fusionné (50 scans+crawls/jour par user) sur `scan/async` et `crawl/async` ; réponses 429 + `Retry-After` ; scans planifiés consomment le quota ; affichage `X / 50` dans le hub Scanner. Voir `docs/RATE-LIMITING.md`.

#### 1.6.3 Scanner hub: docs/UX — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §2.

#### 1.6.4 Affichage anomalies — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §3.

---

### 1.7 Adaptation des tests passifs pour scan_type backend
*Périmètre : **backend** (moteur scan passif, pipeline)*

> **Contexte :** Lorsqu'un utilisateur lance un scan en mode **backend** (cible API, endpoint JSON/XML plutôt que page HTML), certaines étapes des tests passifs dépendent du **HTML** pour fonctionner (extraction de sous-ressources, meta generator, mixed content). Ces étapes sont sans pertinence ou non applicables sur une réponse API. On **ne supprime pas** le code : on ne l'exécute simplement pas quand `scan_type == "backend"`.

#### Propagation de scan_type dans la pipeline

- [x] **ScanContext** (`_scan_core.py`) : ajout du champ `scan_type` (défaut `"frontend"`).
- [x] **scan_stream_generator** (`scan_stream.py`) : paramètre keyword-only `scan_type` propagé à `_run_pipeline_steps` puis `_run_checks_with_client`.
- [x] **async_scan_executor** : lorsqu'on utilise le flux passive, passage explicite de `scan_type` (issu du job) au générateur.
- [x] Les lambdas des étapes SCAN_STEPS reçoivent `ctx.scan_type` et le transmettent aux fonctions de check concernées.

#### Comportement par check (backend vs frontend)

| Check | Comportement frontend | Comportement backend |
|-------|------------------------|----------------------|
| **cache** | Analyse des headers de la page **+** analyse des sous-ressources (JS/CSS/images extraites du HTML) | Analyse des headers de la page uniquement ; **pas** d'analyse des sous-ressources |
| **cors_cross_origin** | Vérifications CORS (ACAO, credentials, CORP) **+** contrôle mixed content (ressources HTTP sur page HTTPS) | Vérifications CORS uniquement ; **pas** de contrôle mixed content |
| **tech_fingerprinting** | Analyse des headers (Server, X-Powered-By) **+** détection via HTML (meta generator, scripts) | Analyse des headers uniquement ; **pas** de `_detect_from_html` |
| **sitemap** | Vérification Sitemap (robots.txt, sitemap.xml, URLs sensibles) | **Étape entière ignorée** (non pertinente pour une API) |
| **integrity** | Intégrité HTML (SRI, scripts, formulaires CSRF, autocomplete, target="_blank", meta robots) | **Étape entière ignorée** (réponse JSON/XML, pas de HTML) |
| **robots_txt** | Présence et contenu de robots.txt (Disallow, Sitemap) | **Étape entière ignorée** (non pertinent pour une API) |
| **methodes_http_et_redirections** | TRACE, HEAD, Allow/ACAM, PUT/DELETE/PATCH, redirections | Même exécution ; sévérité `dangerous_methods` : backend→Info, frontend→Low |
| **apis_et_formats** | GraphQL, Swagger, REST listes, Content-Type, X-CTO, compression | Même exécution ; phase domaine (api_checks) + phase page (formats, api_page) |

#### Implémentation technique

- [x] **cache** (`both/cache/checks.py`) : `check_cache_from_response(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_analyze_subresources`.
- [x] **cors_cross_origin** (`both/cors_cross_origin/checks.py`) : `run_cors_cross_origin_checks(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_check_mixed_content`.
- [x] **tech_fingerprinting** (`both/tech_fingerprinting/checks.py`) : `check_tech_fingerprinting_from_response(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_detect_from_html`.
- [x] **robots_txt**, **sitemap** et **integrity** : étapes entièrement ignorées quand `scan_type == "backend"` (voir `_FRONTEND_ONLY_STEPS` dans `scan_stream.py`). Ces catégories sont exclues des `category_summaries` et du `total_tests_count` pour les scans backend (voir `build_findings_bundle` avec `_FRONTEND_ONLY_CATEGORIES`).

#### Restructuration frontend

- [x] **robots_txt** déplacé de `both/` vers `frontend/` pour cohérence avec sitemap et integrity (ces trois checks sont frontend-only). Imports mis à jour dans `_scan_core`, `multi_scan_orchestrator`, `normalization` et les tests.

#### Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `passive/_scan_core.py` | `ScanContext.scan_type` ; lambdas cache, cors, tech_fingerprinting ; `_FRONTEND_ONLY_CATEGORIES` ; `build_findings_bundle(..., scan_type)` ; import `frontend.robots_txt` |
| `passive/scan_stream.py` | `scan_type` dans `_run_checks_with_client`, `_run_pipeline_steps`, `scan_stream_generator` ; `_FRONTEND_ONLY_STEPS` (robots_txt, sitemap, integrity) |
| `async_scan_executor.py` | Appel `passive_scan_stream_generator(url, authorization=None, scan_type=scan_type)` |
| `both/cache/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_analyze_subresources` |
| `both/cors_cross_origin/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_check_mixed_content` |
| `both/tech_fingerprinting/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_detect_from_html` |
| `passive/frontend/robots_txt/` | **Nouveau** — module déplacé depuis `both/` (checks, normalizer, __init__) |
| `passive/normalization.py` | Import `frontend.robots_txt` ; ajout `methodes_http_et_redirections` |
| `passive/multi_scan_orchestrator.py` | Import `frontend.robots_txt` |
| `passive/both/methodes_http_et_redirections/` | **Nouveau** — checks (OPTIONS/Allow/ACAM via CORS, TRACE, HEAD, redirections), normalizer, config |
| `both/cors_cross_origin/checks.py` | `methodes_data` (Allow/ACAM par URL), retrait finding `dangerous_methods` (déplacé vers methodes_http) |
| `config/settings.yml` | Section `methodes_http_et_redirections` (redirect_chain_max, trace_*, form_sensitive_paths) |

---

## 2) Vérification d'autorisation — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §4 (vérification DNS) et §5 (import doc API).

---

## 3) Introduire les tests actifs — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §6.

---

## 4) Rapports et analytics
*Périmètre : **backend** (calcul, agrégation, export) ; **frontend** (affichage, graphiques, tableau de bord, explication scoring)*

### 4.1 Tendances

- [x] Évolution du score dans le temps (par URL) — *Fait :* ScannerEvolutionChart dans ScannerGestion (vue d'ensemble, séries score/anomalies).
- [x] Graphique de tendance sur la page détail d'un scan — *Fait :* idem, données agrégées par URL.
- [x] Comparaison entre deux scans — *Fait partiel :* onglet « Comparaison » dans MultiScanResults (`multiTabCompare`). Diff détaillée des findings à préciser.

### 4.2 Export

- [x] Export CSV des findings (pour analyse) — *Fait :* `exportScan.ts`, `exportMultiScan.ts` (CSV, JSON, XLSX).
- [x] Export JSON structuré (pour intégrations) — *Fait :* idem + endpoint PDF `/api/scan/export/pdf`.

### 4.3 Frontend

- [x] Page « Tableau de bord » avec métriques — *Fait :* ScannerGestion (Mon compte) avec graphique d'évolution.
- [x] Graphiques de tendance — *Fait :* ScannerEvolutionChart (score, anomalies).

### 4.4 Explication du scoring

- [ ] Afficher dans le frontend comment est calculé le score (formule, pondération par gravité)
- [ ] Tooltip ou lien « Comment est calculé le score ? » à proximité du score affiché
- [ ] Explication des niveaux de gravité (critical, high, medium, low, info) et de leur impact sur le score
- [ ] Page ou modal dédiée décrivant le système de scoring (optionnel)

---

## 5) Scan paramétrable — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §7.

---

## 6) Infra et qualité — déplacé en roadmap 0.5.0

> **Reporté :** [ROADMAP-MVP-0.5.0.md](ROADMAP-MVP-0.5.0.md) §8. *Fait (tests passifs) :* suite pytest existante pour checks TLS, headers, cookies, CORS, integrity, etc.

---

## 7) Release MVP v0.4.0

- [ ] Tag `v0.4.0`
- [ ] Release notes : tests passifs complets + premiers tests actifs + rapports et analytics + scan paramétrable + explication du scoring + rate limiting et quotas (scan/crawl/planifiés)
- [ ] Mise à jour du disclaimer (tests actifs)
- [ ] Documentation : liste des requêtes envoyées en mode actif

# Synthèse

| Version | Tests |
|---------|-------|
| **0.1.0** | Tests passifs de base (TLS, headers, cookies, fichiers, directory listing, robots, fingerprinting) |
| **0.2.0** | Améliorations + nouveaux tests passifs (5.1–5.7 partiels) + API publique, export, monitoring |
| **0.4.0** | **Scanner 1 (passif)** : tous les tests passifs finalisés, toute URL. **Scanner 2 (actif)** : tests passifs (optionnel, défaut oui) + premiers tests actifs, **uniquement URLs vérifiées** (DNS). **Rate limiting et quotas** : limite court terme + quota 50 scans+crawls/jour (UI, API, scans planifiés cumulés), affichage dans le hub. **Rapports et analytics** : tendances, export CSV/JSON, tableau de bord. **Scan paramétrable** : mode par gravité (ex. critical uniquement). **Scoring** : explication dans le frontend. |

---

# Notes importantes (MVP 0.4.0)

- **Rate limiting et quotas** : implémentés (voir `docs/RATE-LIMITING.md`) — rate limit court terme + quota journalier 50 scans/crawls (scans manuels, API, scans planifiés cumulés), affichage dans le hub Scanner.
- Les tests actifs envoient des requêtes **craftées**. Le disclaimer « usage autorisé uniquement » doit être explicite.
- **Deux scanners :** Scanner 1 (passif) = toute URL. Scanner 2 (actif) = uniquement les URLs dont le domaine a été vérifié via DNS. La vérification DNS est activée uniquement en production.
- Commencer par des tests actifs **légers** ; pas de fuzzing, pas de bruteforce.
- Documenter chaque requête pour la transparence et l’audit.
- La protection SSRF côté scanner reste **non négociable** (les tests actifs ne doivent pas permettre de scanner des IP internes).

---

## Périmètre des tests : URL frontend vs backend

Certains tests (exposition fichiers, API docs, directory listing, etc.) s'exécutent **uniquement sur l'URL saisie par l'utilisateur**, qui correspond généralement au **frontend** (site web public). Or, les endpoints sensibles (Swagger, GraphQL, fichiers de config, répertoires de backup) sont souvent hébergés sur une **URL backend** distincte (ex. `api.example.com`, `backend.example.com`).

**État actuel :** Les tests d'exposition fichiers, API docs, directory listing et similaires ne s'exécutent que sur l'URL frontend. Si le backend est sur un autre domaine/sous-domaine, ces tests ne le couvrent pas.

**Améliorations envisagées :**

1. **Détection automatique du backend** : tenter d'inférer l'URL backend à partir du frontend (ex. analyse des requêtes XHR/fetch dans le HTML, liens vers des APIs, patterns courants `api.`, `backend.`, `*.api.`).
2. **URL backend optionnelle** : proposer à l'utilisateur de saisir une **URL backend** en option lors du scan. Si fournie, exécuter ces tests sur les deux URLs (frontend + backend).
3. **Autres tests concernés** : exposition fichiers, directory listing, endpoints API docs (Swagger, GraphQL), information disclosure (stack traces, headers debug), éventuellement CORS et méthodes HTTP sur les endpoints API.

**Recommandation :** À court terme, documenter cette limitation dans l'interface (tooltip ou notice). À moyen terme, implémenter l'option « URL backend optionnelle » pour étendre la couverture des tests. Voir [ROADMAP-MVP-0.5.0 §5](ROADMAP-MVP-0.5.0.md#5-import-documentation-api-backend) pour l'option backend et l'import de documentation API.
