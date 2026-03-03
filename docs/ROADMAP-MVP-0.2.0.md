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

- [ ] **Scope V2** : Auth + dashboard + historique + export PDF + API publique
- [ ] **Auth** : Cognito (déjà en place) — connexion **après** le scan pour accéder aux résultats (comme 0.1.0 § 7.4), scanner restant public
- [ ] **Mode scan** : synchrone uniquement (mode async reporté, voir [A-PENSER-PLUS-TARD.md](A-PENSER-PLUS-TARD.md))
- [ ] **API publique** : clés API pour intégrations externes (CI/CD, scripts)
- [ ] **Limites** : quotas par utilisateur (ex. 50 scans/jour) ; rate limiting API

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

#### 5.1.5 Directory listing

**Existant (v0.1.0) :**
- Répertoires : `/uploads/`, `/assets/`, `/static/` ✅
- Signatures Apache/Nginx (Index of, Parent Directory, [DIR], mod_autoindex, nginx, `<a href=`) ✅

**En plus (v0.2.0) :**
- [ ] Chemins supplémentaires : `/tmp/`, `/logs/`, `/config/`, `/backup/`, `/data/`
- [ ] Détection de listing partiel (réponse HTML avec liens vers fichiers)
- [ ] Alerte si répertoire sensible retourne 403 (existence révélée)

#### 5.1.6 robots.txt

**Existant (v0.1.0) :**
- Lire `/robots.txt` ✅
- Extraire `Disallow` et signaler routes potentiellement sensibles (admin, api, backup, etc.) ✅

**En plus (v0.2.0) :**
- [ ] Vérifier présence de `Sitemap:` (bonne pratique SEO/sécurité)
- [ ] Détecter `Crawl-delay` (non standard, info)
- [ ] Analyser `Allow` en complément de `Disallow`
- [ ] Comparer chemins Disallow avec endpoints sensibles connus

#### 5.1.7 Tech fingerprinting

**Existant (v0.1.0) :**
- Lire `Server`, `X-Powered-By`, `X-Generator`, `X-Drupal-Cache` ✅
- Heuristiques : Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal ✅
- Formulations indicatives (« probable », « détecté ») ✅

**En plus (v0.2.0) :**
- [ ] Extraire versions dans `Server`, `X-Powered-By` (ex. `nginx/1.18.0`)
- [ ] Base de données CPE/CVE : alerter si version connue vulnérable (lecture seule)
- [ ] Détection de technologies via balises HTML (`<meta generator>`, scripts)
- [ ] Rapport « stack probable » avec niveaux de confiance

---

### 5.2 Nouveaux tests — Information disclosure

#### 5.2.1 Fuites dans les réponses
- [ ] Détection de stack traces (PHP, Python, Java, .NET, Node) dans le body
- [ ] Détection de messages d’erreur debug (mode dev activé)
- [ ] Patterns sensibles : mots de passe, tokens, clés API dans le HTML/JSON
- [ ] Headers révélant des infos : `X-AspNet-Version`, `X-Powered-By` avec version

#### 5.2.2 Headers de débogage
- [ ] `X-Debug`, `X-Debug-Token`, `X-Runtime` (exposition temps d’exécution)
- [ ] `Server` avec version complète (ex. `Apache/2.4.41`)
- [ ] Headers custom révélant stack (ex. `X-Generator`)

---

### 5.3 Nouveaux tests — Cache et performances

#### 5.3.1 Headers de cache
- [ ] `Cache-Control` : présence, directives (`max-age`, `no-store`, `private` pour données sensibles)
- [ ] `Pragma: no-cache` (legacy, cohérence avec Cache-Control)
- [ ] `ETag` et `Last-Modified` (validation conditionnelle)
- [ ] `Vary` pour contenu négocié
- [ ] Alerte si page sensible (login, admin) cacheable publiquement

#### 5.3.2 Cache des ressources statiques
- [ ] Analyse des sous-requêtes (scripts, CSS, images) : headers Cache-Control
- [ ] Recommandation : cache long pour assets immuables

---

### 5.4 Nouveaux tests — CORS et cross-origin

#### 5.4.1 CORS
- [ ] `Access-Control-Allow-Origin: *` sur endpoints sensibles → finding
- [ ] `Access-Control-Allow-Credentials: true` + `Origin: *` → incohérence dangereuse
- [ ] Vérifier `Access-Control-Allow-Methods` (éviter PUT/DELETE si non nécessaire)
- [ ] `Access-Control-Expose-Headers` : exposition d’headers sensibles

#### 5.4.2 Cross-origin
- [ ] Détection de ressources chargées en HTTP sur page HTTPS (mixed content)
- [ ] `Cross-Origin-Resource-Policy` manquant sur APIs
- [ ] `Referrer-Policy` trop permissif (`unsafe-url`, absence)

---

### 5.5 Nouveaux tests — Méthodes HTTP et redirections

#### 5.5.1 Méthodes HTTP
- [ ] Requête `OPTIONS` : lister les méthodes autorisées
- [ ] `TRACE` activé → finding (XST)
- [ ] `PUT`, `DELETE`, `PATCH` exposés sans nécessité → info
- [ ] `HEAD` supporté (bonne pratique)

#### 5.5.2 Redirections
- [ ] Détection open redirect (paramètre `url`/`redirect`/`next` redirigeant vers domaine externe)
- [ ] Chaînes de redirection excessives (> 5)
- [ ] Redirection HTTP→HTTPS avec code 301/302 (pas 307/308 pour préserver méthode)

---

### 5.6 Nouveaux tests — Intégrité et sous-ressources

#### 5.6.1 Subresource Integrity (SRI)
- [ ] Scripts/CSS externes (CDN) sans attribut `integrity` → finding
- [ ] Recommandation : utiliser SRI pour ressources tierces

#### 5.6.2 Analyse du HTML
- [ ] Balises `<script>` sans `nonce` ou `integrity` (contexte CSP)
- [ ] Formulaires sans `autocomplete="off"` sur champs sensibles (password)
- [ ] `target="_blank"` sans `rel="noopener noreferrer"`
- [ ] Meta `robots` (noindex sur pages sensibles)

---

### 5.7 Nouveaux tests — APIs et formats

#### 5.7.1 APIs exposées
- [ ] Détection GraphQL : introspection activée sur `/graphql` ou similaire
- [ ] Swagger/OpenAPI exposé sans auth
- [ ] Endpoints REST retournant des listes non paginées (info)

#### 5.7.2 Formats de réponse
- [ ] `Content-Type` incorrect (ex. JSON servi en `text/html`)
- [ ] `X-Content-Type-Options: nosniff` vérifié sur tous les types
- [ ] Compression (gzip/brotli) pour réduire surface

---

### 5.8 Documentation et scoring

#### 5.8.1 Documentation
- [ ] Fichier `docs/verifications/` par catégorie de test
- [ ] Chaque check : risque, exemple, recommandation, référence OWASP/CWE
- [ ] Matrice de sévérité (critical/high/medium/low/info)

#### 5.8.2 Scoring
- [ ] Adapter le scoring pour les nouveaux checks (pondération)
- [ ] Règles d’upgrade/downgrade pour les findings critiques

---

## 6) API publique + clés API

### 6.1 Modèle
- [ ] Schéma : `api_keys` (id, user_id, key_hash, name, created_at, last_used_at)
- [ ] Génération : clé aléatoire (ex. 32 caractères) ; stocker uniquement le hash

### 6.2 Authentification
- [ ] Header `X-API-Key` ou `Authorization: Bearer <api_key>`
- [ ] Middleware : vérifier la clé, résoudre l’utilisateur, appliquer quotas

### 6.3 Quotas et rate limiting
- [ ] Quotas par clé : ex. 100 scans/jour
- [ ] Rate limiting : ex. 10 req/min par clé
- [ ] Réponse 429 si dépassement

### 6.4 API
- [ ] `POST /api/keys` : créer une clé (nom, retourne la clé en clair une seule fois)
- [ ] `GET /api/keys` : liste des clés (sans valeur)
- [ ] `DELETE /api/keys/{id}` : révoquer une clé

### 6.5 Frontend
- [ ] Page « Clés API » dans Mon compte
- [ ] Création, affichage (une fois), révocation
- [ ] Documentation : exemple curl avec `X-API-Key`

---

## 7) Intégration CI/CD (GitHub Action)

### 7.1 Action GitHub
- [ ] Répo `secureops/actions` ou action dans le monorepo
- [ ] Inputs : `url`, `api_key` (secret), `fail_on_score_below` (optionnel)

### 7.2 Comportement
- [ ] Appel `POST /scan/api/scan` avec `X-API-Key`
- [ ] Parse le résultat (score, findings)
- [ ] Fail le job si `score < fail_on_score_below` ou si finding critical

### 7.3 Documentation
- [ ] README : exemple d’utilisation dans un workflow
- [ ] Badge optionnel : « Scan SecureOps » sur le README du projet

---

## 8) Qualité / CI (V2)

### 8.1 Backend
- [ ] Tests unitaires pour les nouveaux modules (export, historique)
- [ ] Coverage maintenu

### 8.2 Frontend
- [ ] Tests unitaires pour les nouveaux composants (dashboard, historique)
- [ ] E2E tests (optionnel) : login → scan → historique

---

## 9) Release MVP v0.2.0

- [ ] Tag `v0.2.0`
- [ ] Release notes (nouvelles fonctionnalités vs v0.1.0)
- [ ] Migration guide (changements : historique, export PDF — scan reste public)
- [ ] Mise à jour de la documentation

---

# Notes importantes (MVP 0.2.0)

- L’authentification est requise **après** le scan pour accéder aux résultats et à l'historique ; le scanner reste public (comme 0.1.0).
- Les scans sont **persistés** : respecter les limites de rétention et RGPD.
- L’API publique : **rate limiting** et **quotas** obligatoires pour éviter les abus.
- La protection SSRF + timeout reste **non négociable**.
