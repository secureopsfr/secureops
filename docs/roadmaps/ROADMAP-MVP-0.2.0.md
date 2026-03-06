# SecureOps — Roadmap MVP 0.2.0 (étape par étape)

Objectif : faire évoluer le scanner v0.1.0 vers une **plateforme** avec authentification, historique, export, monitoring et API publique.

**Prérequis :** MVP 0.1.0 livré (voir [ROADMAP-MVP.md](ROADMAP-MVP.md)).

---

## 0) Prérequis — Qualité, tests et release v0.1 (à compléter avant 0.2.0)

### 0.1 Backend CI
- [x] Lint (ruff/flake8)
- [x] Tests unitaires (pytest)
- [x] Coverage minimal

### 0.2 Frontend CI
- [x] Lint (eslint)
- [x] Build (npm run build)

### 0.3 Branch protection (main)
- [x] PR required
- [x] checks required

### 0.4 Tests finaux (avant annonce)
- [x] Tester sur sites de test (DVWA/Juice Shop en local)
- [x] Tester sur un vrai site vitrine simple
- [x] Tester cas d'erreurs : DNS, timeout, redirect, TLS broken
- [x] Vérifier que SSRF est impossible (tests IP privées)
- [x] Vérifier charge (10 scans rapides)

### 0.5 Release MVP v0.1
- [x] Tag `v0.1.0`
- [x] Release notes (fonctionnalités + limites)
- [x] Démo GIF / screenshots
- [x] Feedback form (Google Form / email)

---

## 1) Décisions MVP 0.2.0 (à figer avant de coder)

- [x] **Scope V2** : Auth + dashboard + historique + export PDF
- [x] **Auth** : Cognito (déjà en place) — connexion **après** le scan pour accéder aux résultats (comme 0.1.0 § 7.4), scanner restant public

---

## 2) Auth + dashboard + historique scans

### 2.1 Backend — persistance ✅
- [x] Schéma : `scans` (id, user_id, url, status, score, findings_json, timestamp, duration, created_at)
- [x] Migration Alembic (user-service) : `alembic/versions/0002_add_scans_table.py`
- [x] Associer chaque scan à l’utilisateur Cognito (via `user_id` ou `sub`)

### 2.2 Scanner public (inchangé vs 0.1.0) ✅
- [x] Conserver `POST /scan/api/scan` en route publique (scan sans login)
- [x] Connexion requise uniquement pour accéder aux résultats et à l’historique

### 2.3 API historique ✅
- [x] `POST /user/api/scans/history` : enregistrer un scan (auth requise)
- [x] `GET /user/api/scans/history` : liste des scans de l’utilisateur (pagination)
- [x] `GET /user/api/scans/history/{id}` : détail d’un scan passé
- [x] `DELETE /user/api/scans/history/{id}` : suppression

> **Fait (2.1-2.3) :** Modèle `app/models/scan.py`, migration 0002, `scan_repository.py`. Router `scan_history.py` dans user-service. Routes sous `/api/scans`. Gateway proxy `/user/*` → user-service. Pagination page/limit, tri `created_at DESC`. Scan-service appelle `/user/api/scans/history` via gateway en fin de scan si token présent.

### 2.4 Dashboard frontend ✅
- [x] Section « Historique des scans » dans Mon compte
- [x] Liste des scans : URL, date, score, badge, lien vers détail
- [x] Pagination (page, limit)
- [x] Détail : réutilisation du composant `ScanResults`

> **Fait :** `HistorySection` dans `components/user/sections/`. Service `scanHistoryService.ts` (getHistory, getScanDetail, deleteScan). Intégré dans `AccountLayout` et page Mon compte. Clic sur un scan → détail avec `ScanResults`.

### 2.5 UX ✅
- [x] Garder le flux 0.1.0 : scan sans login → gate « Connectez-vous pour accéder aux résultats » après scan
- [x] Message clair : « Connectez-vous pour sauvegarder vos résultats dans l'historique »

> **Fait :** `ScanResultsGate` affiche `gateHistoryDesc`. Si sauvegarde échoue (scan-service → gateway), événement SSE `save_failed` → toast d'erreur. Frontend envoie le token (`fetchAuthSession`) dans le POST scan si connecté.

### Architecture sauvegarde (une seule requête)
Le scan-service appelle le gateway (`GATEWAY_URL`) en fin de scan si `Authorization` présent. Flux : Frontend (token) → Gateway → Scan-service → scan → Scan-service → Gateway → User-service (POST /user/api/scans/history). Variable `GATEWAY_URL` (ex. `http://localhost:8000` en local, `http://gateway:8000` en Docker).

> **Fait (MVP 0.1.0) :** Gate « Connectez-vous pour accéder aux résultats » après scan. L’utilisateur peut lancer un scan sans être connecté ; les résultats sont stockés en `sessionStorage` et affichés après connexion. Voir [ROADMAP-MVP-0.1.0.md](ROADMAP-MVP-0.1.0.md) § 7.4.

---

## 3) Export PDF

### 3.1 Backend
- [x] Choisir librairie : WeasyPrint, ReportLab, ou pdfkit
  → **WeasyPrint** utilisé (`pdf_report.py`, `requirements.txt`)
- [x] Endpoint `GET /api/scan/{id}/export/pdf` : génère et retourne le PDF
  → `GET /api/scan/export/pdf?scan_id=...&lang=fr` dans `routers/scan.py`

### 3.2 Contenu du rapport
- [x] En-tête : logo, titre, date, URL scannée
  → Page de garde avec logo (ou SVG fallback), titre, date, URL scannée
- [x] Score global + badge
  → Jauge circulaire + nombre d'anomalies dans la section Synthèse
- [x] Résumé par catégorie
  → Tableaux « Tests effectués » et « Répartition par catégorie »
- [x] Liste des findings (titre, sévérité, preuve, recommandation)
  → Par catégorie, avec titre 2.1/2.2…, badge sévérité, Evidence, Détail, matrice, How to fix
- [x] Pied de page : disclaimer, lien SecureOps
  → Footer avec disclaimer et `https://secureops.example.com`

### 3.3 Frontend
- [x] Bouton « Télécharger PDF » sur la page résultats
  → Modal d'export dans `ScanResults.tsx`, option PDF via `downloadScanPdf(scanId, lang)`
- [x] Bouton « Télécharger PDF » sur la page détail d'un scan historique
  → Icône FileDown dans `ScanHistoryBlock`, à côté de la poubelle, télécharge le PDF sans ouvrir les résultats

### 3.4 Style
- [x] Template PDF professionnel (mise en page, couleurs)
  → Mise en page A4, sections avec titres bleus, sommaire cliquable, badges sévérité, matrices
- [x] Support i18n (fr/en) dans le PDF
  → Paramètre `lang` utilisé dans tout le rapport (libellés, catalogue `detail_fr`/`detail_en`)

### 3.5 Refactoring PDF (complété) ✅
- [x] Constantes centralisées : catégories (ordre, libellés, checked) dans `config/settings.yml`
- [x] CSS extrait : `app/static/pdf_report.css` (styles séparés du Python)
- [x] i18n centralisée : `pdf_i18n.py` (libellés UI) + catalogue `recommendations.json` (title, evidence, recommendation, detail fr/en)
- [x] Footer URL configurable : `pdf.footer_url` dans settings.yml
- [x] Découpage en modules : `app/services/pdf_report/` (cover, sommaire, synthese, findings, matrix, links, html_builder)
- [x] Validation schéma : `ScanForPdfSchema` avant génération
- [x] Tests unitaires : `tests/test_pdf_report.py`, `tests/test_catalogue.py`
- [x] Liens externes factorisés : `links.py` (build_ref_links, build_inline_ref_links)
- [x] Documentation : `docs/PDF-I18N.md` (architecture, ajout finding, nouvelle langue)

**Reste (optionnel) :**
- [x] Validation catalogue : test `test_all_risk_matrix_slugs_have_recommendation_en` vérifie que tous les slugs ont `recommendation_en`
- [x] i18n messages `settings.yml` : `message_absent_en` et `message_en` ajoutés (security_headers, exposed_files, directory_listing) ; le catalogue reste la source pour le PDF
- [x] Tests d'intégration : `test_pdf_integration_scan_to_pdf` (scan mocké → PDF, marqué `@pytest.mark.integration`)

---

## 4) Monitoring continu (scans planifiés)

### 4.1 Modèle de données ✅
- [x] Schéma : `scheduled_scans` (id, user_id, url, frequency, next_run_at, enabled)
  - **Fait :** `app/models/scheduled_scan.py`, migration `0004_add_scheduled_scans_table.py`
  - Colonnes étendues : `schedule_hour`, `schedule_minute`, `schedule_day_of_week`, `schedule_day_of_month` pour paramétrer l'heure (daily), le jour (weekly) et le jour du mois (monthly)
- [x] Fréquences : daily, weekly, monthly

### 4.2 Scheduler ✅
- [x] Boucle asyncio dans user-service : réveille les scans à exécuter toutes les 5 min (configurable via `SCHEDULED_SCAN_INTERVAL_SECONDS`)
  - **Fait :** `app/services/scheduled_scan_scheduler.py`, intégré dans `main.py` lifespan
- [x] Appel du scan : user-service appelle scan-service `POST /api/internal/scan/run` (retourne JSON, pas SSE)
  - **Fait :** `scan-service/app/services/scan_runner.py` + endpoint interne dans `routers/scan.py`
- [x] Mise à jour `next_run_at` après exécution **réussie** uniquement
  - En cas d'échec (site down, timeout) : pas de mise à jour → retry au prochain passage du scheduler

### 4.3 API ✅
- [x] `POST /user/api/scans/schedule` : créer un scan planifié
- [x] `GET /user/api/scans/schedule` : liste des scans planifiés
- [x] `PATCH /user/api/scans/schedule/{id}` : modifier (fréquence, horaire, pause)
- [x] `DELETE /user/api/scans/schedule/{id}` : supprimer
- **Fait :** `app/routers/scheduled_scan.py`, schémas `app/schemas/scheduled_scan.py`

### 4.4 Alertes (optionnel) ✅
- [x] Détection de régression (score chute vs dernier scan)
- [x] Email ou notification si finding critical détecté
- **Fait :** admin-service endpoint `/api/internal/notifications/scan-alert`, user-service `scan_alert_service.py`, préférence `scan_alerts_enabled`, toggle dans Settings

### 4.5 Frontend ✅
- [x] Bloc « Scans planifiés » sur la page Scanner (visible si connecté, comme l'historique)
  - **Fait :** `ScheduledScansBlock.tsx`, `scheduledScanService.ts`
- [x] Formulaire : URL, fréquence (daily/weekly/monthly), heure, minute, jour (weekly/monthly)
- [x] Indicateur : prochain scan prévu (`next_run_at` formaté)
- [x] Boutons : pause/reprise, suppression

---

## 5) Scan plus avancé (OWASP light, non intrusif)

> **Principe :** tests passifs uniquement — pas d’injection, pas de bruteforce, pas de fuzzing. Lecture et analyse des réponses HTTP/HTML.

---

### 5.1 Améliorations des tests existants

#### 5.1.1 TLS / HTTPS

**Existant (v0.1.0) :**
- HTTPS activé ? ✅
- Redirection HTTP→HTTPS ? ✅
- Certificat valide / expiré / auto-signé ? ✅
- Version TLS (détection 1.0/1.1) ✅

**En plus (v0.2.0) :**
- [x] Résumé « TLS posture » (synthèse lisible : OK / avertissements / critique)
  - **Fait :** Badge dans le résumé des résultats (OK / Avertissements / Critique) selon `compute_tls_posture`. Critères : HTTPS, redirect, certificat valide, pas de TLS obsolète, chaîne complète.
- [x] Vérification de la chaîne de certificats (intermédiaires manquants)
  - **Fait :** `openssl s_client -showcerts` pour récupérer la chaîne complète, `verify_certificate_chain` détecte les intermédiaires manquants. Finding `tls-chain-incomplete` si chaîne incomplète.
- [x] Alerte si certificat expire dans < 30 jours
  - **Fait :** Finding `tls-cert-expires-soon` avec gravité low (15–29 jours) ou medium (0–14 jours). Extraction du délai via `_extract_days_until_expiry` dans le message du certificat.
- [x] Support TLS 1.3 (détection si proposé)
  - **Fait :** `get_negotiated_tls_version` récupère la version TLS négociée (TLS 1.2 ou TLS 1.3). Affichée dans le résumé : « La connexion a été établie en **TLS 1.3**. »

#### 5.1.2 Security Headers

**Existant (v0.1.0) :**
- Vérifier présence : `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options` (nosniff), `Referrer-Policy`, `Permissions-Policy` ✅

**En plus (v0.2.0) :**
- [x] Vérifier `Content-Security-Policy` : présence de `report-uri` ou `report-to`
  - **Fait :** `_analyze_csp_header` détecte l'absence ; finding `headers-csp-no-report-uri` (low).
- [x] Vérifier directives CSP strictes (pas de `unsafe-inline`, `unsafe-eval` si possible)
  - **Fait :** `_analyze_csp_header` détecte unsafe-inline/unsafe-eval ; finding `headers-csp-unsafe-directives` (low).
- [x] Headers COEP/COOP (`Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy`)
  - **Fait :** Ajoutés dans settings.yml ; slugs `headers-coep-absent`, `headers-coop-absent` (low).
- [x] `Clear-Site-Data` pour déconnexion sécurisée
  - **Fait :** Ajouté dans settings.yml ; slug `headers-clear-site-data-absent` (low).
- [x] Sévérité différenciée selon le header manquant
  - **Fait :** `SecurityHeaderConfig.severity` ; CSP/HSTS=high, XFO/XCTO/Referrer/Permissions=medium, COEP/COOP/Clear-Site-Data=low.

#### 5.1.3 Cookies

**Existant (v0.1.0) :**
- Vérifier flags : `Secure`, `HttpOnly`, `SameSite` ✅
- Détecter cookies sans `Secure` si site HTTPS ✅

**En plus (v0.2.0) :**
- [x] Détecter préfixes `__Host-` et `__Secure-` (bonnes pratiques)
  - **Fait :** Finding `cookies-no-host-secure-prefix` (info) pour cookies sensibles sans préfixe.
- [x] Cookie `Partitioned` (CHIPS) pour cookies tiers
  - **Fait :** Finding `cookies-no-partitioned` (low) pour cookies analytics/tiers (`_ga`, `_gid`, etc.) sans Partitioned.
- [x] Alerte si cookie de session sans `HttpOnly` + `Secure` + `SameSite=Strict`
  - **Fait :** Finding `cookies-session-incomplete` (high) ; heuristique sur noms (session, auth, token, phpsessid, etc.).
- [x] Détection de cookies avec `Expires` trop lointain pour session
  - **Fait :** Finding `cookies-session-expires-long` (low) si Expires/Max-Age > 24h pour cookie session.

#### 5.1.4 Exposition fichiers

**Existant (v0.1.0) :**
- Liste fixe : `/.env`, `/.git/config`, `/backup.zip`, `/phpinfo.php`, `/admin/`, `/.DS_Store` ✅
- Signatures par chemin (KEY=value, [core], PK, etc.) ✅

**En plus (v0.2.0) :**
- [x] Liste étendue : `/.htaccess`, `/web.config`, `/.svn/entries`, `/composer.json`, `/package.json`, `/.npmrc`
- [x] Signatures améliorées (regex plus précises, faux positifs réduits)
- [x] Détection de fichiers de backup (`.bak`, `.old`, `.swp`, `~`)
- [x] Endpoints API docs exposés : `/swagger`, `/api-docs`, `/graphql` (introspection)

> **Fait :** Chemins et messages dans `config/settings.yml` (section `exposed_files.paths`) ; logique dans `app/services/path_checks/core.py` et normalisation `exposed_files` (signatures par chemin, severity_upgrade pour .env/.git/config).

#### 5.1.5 Directory listing

**Existant (v0.1.0) :**
- Répertoires : `/uploads/`, `/assets/`, `/static/` ✅
- Signatures Apache/Nginx (Index of, Parent Directory, [DIR], mod_autoindex, nginx, `<a href=`) ✅

**En plus (v0.2.0) :**
- [x] Chemins supplémentaires : `/tmp/`, `/logs/`, `/config/`, `/backup/`, `/data/`
  - **Fait :** `_DEFAULT_DIRECTORY` dans `app/config/path_checks.py` ; configurable via `directory_listing.paths` dans settings.yml.
- [x] Détection de listing partiel (réponse HTML avec liens vers fichiers)
  - **Fait :** `_is_partial_listing_body` dans `app/services/directory_listing/checks.py` (seuil de liens, extensions typiques).
- [x] Alerte si répertoire sensible retourne 403 (existence révélée)
  - **Fait :** `_SENSITIVE_FOR_403` (/config/, /backup/, /logs/, /tmp/, /data/) ; finding `directory_listing-sensitive-403` via normalizer.

#### 5.1.6 robots.txt

**Existant (v0.1.0) :**
- Lire `/robots.txt` ✅
- Extraire `Disallow` et signaler routes potentiellement sensibles (admin, api, backup, etc.) ✅

**En plus (v0.2.0) :**
- [x] Détecter `Crawl-delay` (non standard, info)
  - **Fait :** `_extract_crawl_delay` dans `app/services/robots_txt/checks.py` ; finding `robots_txt-crawl-delay` (info) via normalizer.
- [x] Analyser `Allow` en complément de `Disallow`
  - **Fait :** `_extract_allow_paths` dans `app/services/robots_txt/checks.py` ; `allow_paths` dans `RobotsTxtCheckResult`.

#### 5.1.6bis Sitemap

**Existant (v0.1.0) :** Aucun.

**En plus (v0.2.0) :**
- [x] Vérifier présence de `Sitemap:` dans robots.txt (bonne pratique SEO/sécurité)
  - **Fait :** `_extract_sitemap_urls` dans `app/services/robots_txt/checks.py` ; module `app/services/sitemap/checks.py` utilise `robots_txt_result.sitemap_urls`.
- [x] Fallback : chercher sitemap à l'emplacement classique (`/sitemap.xml`, `/sitemap_index.xml`) si non déclaré
  - **Fait :** `_SITEMAP_FALLBACK_PATHS` et `_resolve_sitemap_urls` dans `app/services/sitemap/checks.py` ; finding `sitemap-undeclared` si trouvé uniquement via fallback.
- [x] Analyser le contenu du sitemap : détecter URLs sensibles (admin, api, config, etc.) exposées dans le sitemap → finding
  - **Fait :** `_analyze_sitemap_urls` et `_url_path_matches_sensitive` ; patterns dans config ; finding `sitemap-sensitive-url` par URL sensible.

#### 5.1.7 Tech fingerprinting

**Existant (v0.1.0) :**
- Lire `Server`, `X-Powered-By`, `X-Generator`, `X-Drupal-Cache` ✅
- Heuristiques : Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal ✅
- Formulations indicatives (« probable », « détecté ») ✅

**En plus (v0.2.0) :**
- [x] Extraire versions dans `Server`, `X-Powered-By` (ex. `nginx/1.18.0`)
- [x] Base de données CPE/CVE : alerter si version connue vulnérable (lecture seule, seuils configurables)
- [x] Détection de technologies via balises HTML (`<meta generator>`, scripts)
- [x] Rapport « stack probable » avec niveaux de confiance

---

### 5.2 Nouveaux tests — Information disclosure

> **Fait :** module `app/services/information_disclosure/checks.py` ; étape `information_disclosure` dans la pipeline (après tech_fingerprinting). Analyse du corps (limite `information_disclosure.max_body_bytes` dans settings.yml) et des en-têtes. Findings : stack traces, mode debug, secrets (snippet masqué), headers de debug, Server/X-Powered-By/X-AspNet-Version avec version, X-Generator/X-Version/X-Drupal-Cache. Normalisation et catalogue i18n.

#### 5.2.1 Fuites dans les réponses
- [x] Détection de stack traces (PHP, Python, Java, .NET, Node) dans le body
- [x] Détection de messages d'erreur debug (mode dev activé)
- [x] Patterns sensibles : mots de passe, tokens, clés API dans le HTML/JSON
- [x] Headers révélant des infos : `X-AspNet-Version`, `X-Powered-By` avec version

#### 5.2.2 Headers de débogage
- [x] `X-Debug`, `X-Debug-Token`, `X-Runtime` (exposition temps d’exécution)
- [x] `Server` avec version complète (ex. `Apache/2.4.41`)
- [x] Headers custom révélant stack (ex. `X-Generator`)

---

### 5.3 Nouveaux tests — Cache et performances

#### 5.3.1 Headers de cache
#### 5.3.1 Headers de cache
- [x] `Cache-Control` : présence, directives (`max-age`, `no-store`, `private` pour données sensibles)
- [x] `Pragma: no-cache` (legacy, cohérence avec Cache-Control)
- [x] `ETag` et `Last-Modified` (validation conditionnelle)
- [x] `Vary` pour contenu négocié
- [x] Alerte si page sensible (login, admin) cacheable publiquement

> **Fait :** module `app/services/cache/checks.py` analysant les en-têtes de la **page principale** (`Cache-Control`, `Pragma`, `ETag`, `Last-Modified`, `Vary`). Les pages sensibles sont identifiées par leur **URL** (patterns configurables dans `cache.sensitive_paths`) et un finding de sévérité High est généré si elles sont cacheables publiquement (`public` ou `max-age` supérieur au seuil `cache.sensitive_max_age` sans `no-store`/`private`). Une absence de `Cache-Control` sur page sensible génère un finding Medium, et une incohérence `Pragma: no-cache` / `Cache-Control` permissif un finding Low.

#### 5.3.2 Cache des ressources statiques
#### 5.3.2 Cache des ressources statiques
- [x] Analyse des sous-requêtes (scripts, CSS, images) : headers Cache-Control
- [x] Recommandation : cache long pour assets immuables

> **Fait :** utilitaire générique `app/services/subresources.py` pour extraire les sous-ressources déclarées dans le HTML (`<script src>`, `<link rel="stylesheet" href>`, `<img src>`), normalisées par rapport à l’URL scannée et limitées à `cache.max_sub_resources`. Le check cache réutilise le **client HTTPX partagé** pour effectuer des requêtes `HEAD` (puis `GET` en fallback si nécessaire) et vérifie que les assets immuables (pattern `cache.immutable_pattern`, ex. `main.abc123.js`) bénéficient d’un cache long (`max-age >= cache.immutable_max_age` et présence de `immutable`). Un finding Info est émis (`cache-immutable-no-long-cache`) lorsque ce n’est pas le cas.

---

### 5.4 Nouveaux tests — CORS et cross-origin

#### 5.4.1 CORS
- [x] `Access-Control-Allow-Origin: *` sur endpoints sensibles → finding
  - **Fait :** Requêtes GET/OPTIONS avec Origin vers page + chemins sensibles (`cors_cross_origin.sensitive_paths`) ; finding `cors-allow-origin-star-sensitive` (high) si réponse type API.
- [x] `Access-Control-Allow-Credentials: true` + `Origin: *` → incohérence dangereuse
  - **Fait :** Finding `cors-credentials-origin-star` (critical). Réflexion d'origine non validée → `cors-credentials-origin-reflection` (critical).
- [x] Vérifier `Access-Control-Allow-Methods` (éviter PUT/DELETE si non nécessaire)
  - **Fait :** Finding `cors-allow-methods-dangerous` (info) si PUT/DELETE/PATCH exposés ; filtré par type de réponse (API) pour endpoints sensibles.
- [x] `Access-Control-Expose-Headers` : exposition d’headers sensibles
  - **Fait :** Liste `expose_headers_sensitive` dans settings ; finding `cors-expose-headers-sensitive` (medium) si en-tête sensible exposé.

#### 5.4.2 Cross-origin
- [x] Détection de ressources chargées en HTTP sur page HTTPS (mixed content)
  - **Fait :** Extraction sous-ressources via `subresources.py` ; finding `mixed-content-http-on-https` (high) pour chaque URL `http://` sur page HTTPS.
- [x] `Cross-Origin-Resource-Policy` manquant sur APIs
  - **Fait :** Finding `corp-missing` sur endpoint sensible (si réponse type API) et `corp-missing-main` sur page principale. Filtre « réponse = API » pour éviter faux positifs (page HTML « n'existe pas »).
- [x] `Referrer-Policy` trop permissif (`unsafe-url`, absence) — vérifié dans Security Headers (mention dans le résumé CORS)
  - **Fait :** Vérification dans la catégorie Security Headers ; résumé CORS et `category_summaries.json` indiquent que Referrer-Policy est vérifié côté headers.

---

### 5.6 Nouveaux tests — Intégrité et sous-ressources

#### 5.6.1 Subresource Integrity (SRI)

Détecter les ressources tierces (scripts, CSS) chargées sans garantie d’intégrité.

- [x] **Scripts/CSS externes (CDN) sans attribut `integrity`** → finding : balises `<script src="https://...">` et `<link href="https://...">` vers domaine externe sans attribut `integrity` (risque MITM / compromission CDN).
- [x] **Recommandation SRI pour tiers** : dans le rapport, recommander d’utiliser SRI pour toutes les ressources chargées depuis CDN ou domaines tiers.

> **Fait :** Implémenté dans `backend/scan-service/app/services/integrity/checks.py` via le parser HTML (`_IntegrityHTMLParser`) qui repère les scripts et CSS externes sans attribut `integrity` et génère un finding agrégé (`Ressources externes sans SRI détectées…`). Tests unitaires dans `backend/scan-service/tests/test_integrity_checks.py::test_check_integrity_sri_on_external_resources`.

#### 5.6.2 Analyse du HTML

Nouveaux checks passifs : parser le HTML de la page principale et signaler les bonnes pratiques manquantes.

- [x] **`<script>` sans `nonce` ou `integrity`** (contexte CSP) : balises script inline ou externes sans mécanisme d’intégrité ou nonce → finding (risque XSS / injection).
- [x] **Formulaires sans `autocomplete="off"`** sur champs sensibles (ex. `type="password"`, champs login) → finding (risque fuite par autocomplétion).
- [x] **`target="_blank"` sans `rel="noopener noreferrer"`** : liens ouvrant en nouvel onglet sans protection → finding (risque `window.opener`).
- [x] **Meta `robots`** : pages sensibles (login, admin, API) sans `noindex` quand approprié → finding ou info (exposition aux moteurs de recherche).

> **Fait :** Les mêmes modules d’intégrité analysent les scripts inline (nonces CSP), les champs `input type="password"` (autocomplete), les liens `target="_blank"` (absence de `rel="noopener"`), et les meta `robots` sur les chemins sensibles (configurés dans `integrity.sensitive_paths`). Couvert par `test_check_integrity_csp_absent_reports_skipped_advanced_checks`, `test_check_integrity_inline_scripts_without_nonce_when_csp_present`, `test_check_integrity_password_autocomplete_and_target_blank` et `test_check_integrity_meta_robots_on_sensitive_page`.

Référence : [integrite-et-sous-ressources.md](verifications/integrite-et-sous-ressources.md).

---

### 5.8 Documentation et scoring

#### 5.8.1 Documentation
- [x] Fichier `docs/verifications/` par catégorie de test
  - **Fait :** Un fichier par catégorie (tls-https, security-headers, cookies, exposition-fichiers, directory-listing, robots-txt, sitemap, tech-fingerprinting, information-disclosure, cache-et-performances, cors-et-cross-origin, integrite-et-sous-ressources, apis-et-formats, methodes-http-et-redirections).
- [x] Chaque check : risque, exemple, recommandation, référence OWASP/CWE
  - **Fait :** Structure commune dans les docs (objectif, explication, exemple, vulnérabilité/impact, matrice gravité) ; références OWASP/CWE selon les docs.
- [x] Matrice de sévérité (critical/high/medium/low/info)
  - **Fait :** `app/catalogue/risk_matrix.json` (gravite, vraisemblance par slug) ; `scoring.severity_penalties` dans settings.yml.

#### 5.8.2 Scoring
- [x] Adapter le scoring pour les nouveaux checks (pondération)
  - **Fait :** `app/config/scoring.py` et `app/services/scoring.py` ; `scoring.category_weights` dans settings.yml (tls, headers, cookies, exposed_files, directory_listing, robots_txt, sitemap, tech_fingerprinting, information_disclosure, cors_cross_origin).
- [x] Règles d’upgrade/downgrade pour les findings critiques
  - **Fait :** `get_exposed_files_severity_upgrade()` (path_checks.py) : chemins `.git/config`, `.env` → critical ; configurable via `exposed_files.severity_upgrade` dans settings.yml.

### Liste exhaustive des tests passifs frontend (MVP 0.2.0)

Tests qui concernent la **page principale** (URL scannée) et ses **sous-ressources** (HTML, headers, scripts/CSS/images extraits du HTML). Les blocs 5.5 (Méthodes HTTP / redirections) et 5.7 (APIs / formats) sont orientés backend/API et sont dans [A-PENSER-PLUS-TARD.md](A-PENSER-PLUS-TARD.md).

| Domaine | Détail | Statut |
|--------|--------|--------|
| **TLS / HTTPS** | Posture TLS, chaîne certificats, expiration &lt; 30 j, TLS 1.3 | ✅ Fait (5.1.1) |
| **Security Headers** | CSP, HSTS, XFO, XCTO, Referrer, Permissions, COEP, COOP, Clear-Site-Data, report-uri, unsafe-inline/eval | ✅ Fait (5.1.2) |
| **Cookies** | Secure, HttpOnly, SameSite, préfixes __Host-/__Secure-, Partitioned, session incomplète, Expires long | ✅ Fait (5.1.3) |
| **Exposition fichiers** | Liste étendue (.env, .git, .htaccess, swagger, graphql, backup…), signatures, API docs | ✅ Fait (5.1.4) |
| **Directory listing** | Chemins /tmp, /logs, /config…, listing partiel, 403 sur chemins sensibles | ✅ Fait (5.1.5) |
| **robots.txt** | Disallow, Allow, Crawl-delay, routes sensibles | ✅ Fait (5.1.6) |
| **Sitemap** | Sitemap: dans robots, fallback /sitemap.xml, URLs sensibles dans sitemap | ✅ Fait (5.1.6bis) |
| **Tech fingerprinting** | Server/X-Powered-By versions, CPE/CVE, meta/scripts HTML, stack probable | ✅ Fait (5.1.7) |
| **Information disclosure** | Stack traces, mode debug, secrets, headers debug, Server avec version | ✅ Fait (5.2) |
| **Cache** | Page : Cache-Control, Pragma, ETag, Last-Modified, Vary, pages sensibles non cacheables | ✅ Fait (5.3.1) |
| **Cache sous-ressources** | Scripts/CSS/images : Cache-Control, cache long pour assets immuables | ✅ Fait (5.3.2) |
| **CORS** | ACAO *, Credentials+*, Allow-Methods, Expose-Headers sensibles | ✅ Fait (5.4.1) |
| **Cross-origin** | Mixed content (HTTP sur HTTPS), CORP manquant, Referrer-Policy (via headers) | ✅ Fait (5.4.2) |
| **SRI** | Scripts/CSS externes (CDN) sans `integrity` → finding + recommandation SRI | ✅ Fait (5.6.1) |
| **Analyse HTML** | `<script>` sans nonce/integrity, autocomplete sur password, target="_blank" sans noopener, meta robots | ✅ Fait (5.6.2) |

**Conclusion :** Tous les tests passifs frontend listés ci‑dessus sont **faits** pour la v0.2.0, y compris **5.6** (SRI + Analyse du HTML).

### Ce qui manque dans les tests passifs (section 5)

Les blocs **5.5** (Méthodes HTTP et redirections) et **5.7** (APIs et formats) ont été déplacés dans [A-PENSER-PLUS-TARD.md](A-PENSER-PLUS-TARD.md) et restent à implémenter dans une version ultérieure.
Le bloc **5.6 — Intégrité et sous-ressources** est livré (voir [docs/verifications/integrite-et-sous-ressources.md](verifications/integrite-et-sous-ressources.md)).

---

## 6) Release MVP v0.2.0

- [ ] Tag `v0.2.0`
- [ ] Release notes (nouvelles fonctionnalités vs v0.1.0)
- [ ] Mise à jour de la documentation

---

# Notes importantes (MVP 0.2.0)

- L’authentification est requise **après** le scan pour accéder aux résultats et à l'historique ; le scanner reste public (comme 0.1.0).
- Les scans sont **persistés** : respecter les limites de rétention et RGPD.
- L’API publique : **rate limiting** et **quotas** obligatoires pour éviter les abus.
- La protection SSRF + timeout reste **non négociable**.
