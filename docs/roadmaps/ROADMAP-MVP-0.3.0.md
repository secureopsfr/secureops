# SecureOps — Roadmap MVP 0.3.0

## Sommaire

**Ordre recommandé pour la lecture et l’implémentation :** 0 (refactoring) → 1 (API) → 2 (tests) → 3 (GitHub Action) → 5 (reporté) → 7 (crawler) → 8 (UX) → 6 (async).

- [0) Refactoring de la base de code](#0-refactoring-de-la-base-de-code)
  - [0.1 Backend — Refactoring par dossier](#01-backend--refactoring-par-dossier)
  - [0.2 Frontend — Refactoring par dossier](#02-frontend--refactoring-par-dossier)
  - [0.3 Micro-service dédié à la génération PDF](#03-micro-service-dédié-à-la-génération-pdf)
- [1) API publique + clés API](#1-api-publique--clés-api)
  - [1.1 Modèle](#11-modèle)
  - [1.2 Authentification](#12-authentification)
  - [1.4 API](#14-api)
  - [1.5 Frontend](#15-frontend)
- [2) Tests d'intégration pour la pipeline de scan](#2-tests-dintégration-pour-la-pipeline-de-scan)
  - [2.1 Environnements et serveurs de test](#21-environnements-et-serveurs-de-test)
  - [2.2 Scénarios de tests d'intégration](#22-scénarios-de-tests-dintégration)
  - [2.3 Intégration dans la CI](#23-intégration-dans-la-ci)
  - [2.4 Observabilité et maintenance des tests](#24-observabilité-et-maintenance-des-tests)
- [3) Intégration CI/CD (GitHub Action SecureOps)](#3-intégration-cicd-github-action-secureops)
  - [3.1 Action GitHub](#31-action-github)
  - [3.2 Comportement](#32-comportement)
  - [3.3 Documentation](#33-documentation)
- [5) Limites (reporté)](#5-limites-reporté)
- [7) Crawler HTTP — agent indépendant](#7-crawler-http--agent-indépendant)
  - [7.1 Noyau du crawler](#71-noyau-du-crawler)
  - [7.2 Suivi des routes (crawl en profondeur)](#72-suivi-des-routes-crawl-en-profondeur)
  - [7.3 Sortie du crawler, envoi au frontend et étape de validation](#73-sortie-du-crawler-envoi-au-frontend-et-étape-de-validation)
  - [7.4 Bonnes pratiques et suggestions](#74-bonnes-pratiques-et-suggestions)
  - [7.5 Documentation et tests](#75-documentation-et-tests)
  - [7.6 Gestion des URLs, limites et prévention des abus](#76-gestion-des-urls-limites-et-prévention-des-abus)
- [8) Réorganisation / amélioration de l'UX](#8-réorganisation--amélioration-de-lux)
  - [8.1 Refonte de la landing page](#81-refonte-de-la-landing-page)
  - [8.2 Refonte de la page Scanner (hub connecté)](#82-refonte-de-la-page-scanner-hub-connecté)
  - [8.3 Header / navigation](#83-header--navigation)
  - [8.4 Affichage du scanner : chargement et anomalies](#84-affichage-du-scanner--chargement-et-anomalies)
- [6) Mode asynchrone + queue](#6-mode-asynchrone--queue)
  - [6.1 Choix technologique](#61-choix-technologique)
  - [6.2 Infrastructure queue](#62-infrastructure-queue)
  - [6.3 Worker scan](#63-worker-scan)
  - [6.4 API endpoints](#64-api-endpoints)
  - [6.5 Frontend](#65-frontend)

---

## 0) Refactoring de la base de code

Objectif : **nettoyer et stabiliser l’existant** avant les nouvelles fonctionnalités de la v0.3.0, en clarifiant la structure des dossiers et en harmonisant les patterns backend / frontend.

---

## 0.1 Backend — Refactoring par dossier

- [x] `backend/common/`
  - [x] `common/` (utils partagés : config, JWT, DB, logging, middleware, health, URL utils)
    > **Fait :** Module complet avec config_base (load_yaml, create_simple_settings, create_load_settings_yml, SsrfSettings, UrlValidationSettings, parse_ssrf_settings, parse_url_validation_settings), jwt_verifier, cognito, async_database, logging_config, middleware (CorrelationIdMiddleware), health (create_health_router), url_utils, url_helpers (extract_host, extract_port, build_url_with_path, etc.), url_validator (validate_and_normalize_url), env_utils (is_prod_env), ssrf (check_ssrf, is_hostname_blocked, is_ip_blocked), schemas (make_pagination_meta), error_handlers, datetime_utils. Centralisation des duplications : SSRF (scan + crawl → common), url_helpers (scan + crawl → common), validate_and_normalize_url (scan + crawl → common), make_pagination_meta (admin → common). Wrappers minces restent dans scan-service et crawl-service pour la config locale.
  - [x] `pyproject.toml` / packaging du module commun
    > **Fait :** pyproject.toml avec dependencies, optional-dependencies [dev], [tool.black], [tool.isort], [tool.pytest.ini_options]. Pre-commit (Black, isort, Flake8), CI job lint-common (pip install -e backend/common[dev], black, isort, flake8, pytest), .flake8, requirements-dev.txt, Makefile (install, test, lint). Tests : test_url_utils, test_health, test_datetime_utils, test_schemas, test_config_base, test_env_utils, test_url_helpers.
  - [x] **Composants créés en plus** (centralisation des duplications)
    > **Fait :** `env_utils.py` (is_prod_env) ; `url_helpers.py` (extract_host_from_url, extract_port_from_url, build_url_with_path, build_https_url, build_http_url, get_host_from_url, get_https_port_from_url, get_scan_base_url, location_redirects_to_https) ; `url_validator.py` (validate_and_normalize_url avec validation des ports) ; `ssrf.py` (check_ssrf, is_hostname_blocked, is_ip_blocked, resolve_host) ; config_base : create_load_settings_yml, SsrfSettings, UrlValidationSettings, parse_ssrf_settings, parse_url_validation_settings ; schemas : make_pagination_meta. Fichiers config : .flake8, requirements-dev.txt, Makefile.

- [x] `backend/gateway/`
  - [x] `app/`
    - [x] `routers/` (proxy, health, routes publiques)
    - [x] `services/proxy/` (logique de proxy, métriques)
    - [x] `config_loader.py` / settings
  - [x] `config/` (YAML des services, CORS, timeouts)
  - [x] `tests/`
  - [x] `Dockerfile` / `requirements.txt`
  > **Fait :** Refactoring structurel du gateway avec nettoyage des artefacts legacy et consolidation des responsabilités dans `app/routers`, `app/services/proxy` et `config_loader`. Côté proxy : suppression des comportements hérités non utilisés (Mapbox/vector tiles, timeouts/services historiques), conservation du flux buffer/stream et normalisation des métriques (route extraction simplifiée). Côté config : simplification du schéma settings (`content_types` retiré), gestion d’erreur robuste (`ValueError` sur config invalide), et règles d’accès clarifiées dans le middleware (auth-only docs admin via constantes dédiées). Côté sécurité/maintenabilité : suppression du mock de package `app/__init__.py`, pseudonymisation IP IPv4/IPv6 fiabilisée via `ipaddress`, cache local de l’URL user-service pour l’auth API key. Côté qualité : ajout d’une vraie base de tests unitaires (`middleware`, `config_loader`, `metrics`, `api_key_auth`, `pseudonymizer`) en remplacement du placeholder seul. Côté build/deps : séparation runtime/dev (`requirements.txt` + `requirements-dev.txt`), Dockerfile gateway supportant l’installation optionnelle des dev deps via build arg, CI et `launch_dev.sh` adaptés pour installer les dépendances de dev uniquement dans les contextes lint/test.

- [x] `backend/admin-service/`
  - [x] `app/`
    - [x] `routers/` (contact, newsletter, images, analytics, notifications, admin)
    - [x] `models/` (events, audit, etc.)
    - [x] `services/` (contact, mailing list, kpis, alerting, materialized views…)
    - [x] `db.py` / `db_sync.py` / `email_config.py`
  - [x] `config/settings.yml`
  - [x] `alembic/` + `alembic.ini`
  - [x] `tests/`
  - [x] `Dockerfile` / `pyproject.toml` / `requirements.txt`
  > **Fait :** Refactoring admin-service finalisé avec durcissement sécurité, fiabilité, maintenabilité et base de tests. Côté sécurité : ajout d’une vérification JWT admin in-service (`require_admin_user`) et application au montage des routers admin principaux ; endpoint interne notifications mis en fail-closed si clé non configurée. Côté robustesse : correction `newsletter.schedule` (`scheduled_at` string), alignement contrat mailing list (`success=True`), correction de validation `kpis` (`window_minutes.ge`) et suppression des logs sensibles de préfixes de clé API. Côté async/sync : appels sync dans `newsletter`/`mailing_list`/`notification` déplacés via `run_in_threadpool` avec helpers dédiés pour éviter le blocage event loop. Côté qualité : ajout de tests ciblés (`auth`, `internal_notifications`, `mailing_list_router`, `mailing_list_service`, `newsletter_router`, `notification_router`) + smoke migrations. Côté build/deps : séparation runtime/dev (`requirements.txt` + `requirements-dev.txt`), Dockerfile avec installation optionnelle des dev deps via `INSTALL_DEV_DEPS`, activée en CI.

- [x] `backend/user-service/`
  - [x] `app/`
    - [x] `routers/` (profil, préférences, sécurité, favoris, scans, scheduled scans, health)
    - [x] `models/` (user, subscription, favorites, scans, scheduled_scans, alerts…)
    - [x] `services/`
      - [x] `user_repository.py`
      - [x] `subscription_repository.py`
      - [x] `favorite_repository.py`
      - [x] `scan_repository.py`
      - [x] `scan_alert_repository.py`
      - [x] `scheduled_scan_repository.py`
      - [x] `scheduled_scan_scheduler.py`
      - [x] `scheduled_scan_utils.py`
      - [x] `scan_alert_service.py`
      - [x] `user_service.py`
      - [x] `cognito_service.py`
    - [x] `schemas/`
    - [x] `utils/` (auth, URL utils)
    - [x] `db.py` / `config_loader.py`
  - [x] `config/settings.yml`
  - [x] `alembic/` + `alembic.ini`
  - [x] `scripts/` (cleanup, tâches ponctuelles)
  - [x] `tests/`
  - [x] `Dockerfile` / `requirements.txt`
  > **Fait :** Refactoring user-service finalisé avec corrections de sécurité, fiabilité et qualité. Sécurité : endpoints sensibles passés en JWT-only via `require_jwt_user` (security, privacy, profile, preferences, subscription, favorites), endpoint interne `/api/internal/keys/verify` en fail-closed (503 si clé interne absente). Fiabilité : bug scheduler corrigé (`scan_type` transmis à `create_scan`) et validation stricte des fuseaux horaires dans `scheduled_scan_utils` avec propagation explicite en `400` dans `scheduled_scan` pour fuseaux invalides. Auth : messages d’erreur JWT rendus génériques pour limiter l’exposition d’informations internes. Qualité : ajout de tests ciblés (`auth_jwt_only`, `internal_api_keys`, `scheduled_scan_scheduler`, `scheduled_scan_utils`) + smoke migrations, avec conformité `pytest-asyncio`. Côté build/deps : séparation runtime/dev (`requirements.txt` + `requirements-dev.txt`) et Dockerfile compatible `INSTALL_DEV_DEPS` en CI.

- [x] `backend/scan-service/`
  - [x] `app/`
    - [x] `routers/` (scan, health, export PDF via proxy vers pdf-service, endpoints internes)
    - [x] `services/`
      - [x] `tls/`
      - [x] `security_headers/`
      - [x] `cookies/`
      - [x] `exposed_files/`
      - [x] `directory_listing/`
      - [x] `robots_txt/`
      - [x] `sitemap/`
      - [x] `tech_fingerprinting/`
      - [x] `information_disclosure/`
      - [x] `cache/`
      - [x] `cors_cross_origin/`
      - [x] `integrity/`
      - [x] `subresources/`
      - [x] `normalization/`
      - [x] `scan_history_save.py`
      - [x] `scan_runner.py`
    - [x] `catalogue/` (reco, matrices, catégories — hors PDF, voir pdf-service)
    - [x] `config/` (TLS, cache, CORS, scoring, SSRS, timeouts, URL validation…)
    - [x] `utils/` (url_validator, ssrf, url_helpers, headers, http_fetch, ssl_scan…)
    - [x] `models/`, `schemas/`, `errors/`, `static/`
  - [x] `tests/` (checks, scoring, router, SSRF, URL validator…)
  - [x] `Dockerfile`
  > **Fait :** Refactoring scan-service finalisé avec amélioration de la maintenabilité, de la cohérence des payloads et du socle de configuration. **Noyau de scan mutualisé :** création de `app/services/_scan_core.py` (source de vérité unique pour `ScanContext`, `SCAN_STEPS` et construction du payload), suppression des duplications entre `scan_stream` et `scan_runner`. **Payload homogène :** alignement du format de sortie entre SSE et endpoint interne avec `status="success"` et `scan_type` dans les deux chemins. **Structure et séparation :** déplacement de `ScanForPdfSchema` vers `app/schemas/scan.py`, suppression des imports lazy dans les générateurs, déplacement de `subresources.py` vers `services/subresources/`. **Configuration :** ajout de `app/config/external_services.py`, branchement dans `config_loader`, centralisation des URLs/timeouts externes dans `settings.yml`, suppression de la section `database` résiduelle non utilisée. **Normalisation :** réduction du couplage aux messages texte dans `normalization/normalizers.py` (usage prioritaire des champs structurés des résultats de checks, fallback conservé pour compatibilité). **Catalogue :** labels de catégories surchargeables depuis `settings.yml` (`category_labels`) avec fallback JSON. **Qualité :** ajout de tests ciblés (`test_scan_runner.py`, `test_scan_stream.py`, `test_scan_history_save.py`) et adaptation des mocks existants ; suite non-intégration validée (`pytest -m "not integration"`).

---

## 0.2 Frontend — Refactoring par dossier

- [x] `frontend/` racine
  - [x] `package.json` / `package-lock.json`
  - [x] `next.config.ts`, `tsconfig.json`, `jest.config.mjs`, `eslint.config.mjs`, `postcss.config.mjs`
  - [x] `.env.example`
    > **Fait :** Configs présentes ; `turbopack.root` dans next.config ; middleware migré en proxy.ts ; .env.example allégé (variables inutiles supprimées).

- [x] `frontend/src/app/`
  - [x] Routing `[locale]/` (pages : accueil, tarifs, scanner, compte, admin, auth, politique de confidentialité…)
    > **Fait :** Toutes les routes sous `[locale]/` : accueil, tarifs, scanner, mon-compte, admin, connexion, inscription, mot-de-passe-oublie, confirmation, contact, politique-confidentialite, [...slug].
  - [x] Layouts (layout global, layout mon-compte, layout admin, loading/not-found)
    > **Fait :** `[locale]/layout.tsx` (global), `mon-compte/layout.tsx`, `admin/layout.tsx` ; `loading.tsx` et `not-found.tsx` présents à tous les niveaux concernés.
  - [x] Routes API (manifest, robots, sitemap)
    > **Fait :** `api/manifest/[locale]/route.ts` (PWA i18n), `robots.ts` (allow/disallow, sitemap), `sitemap.ts` (pages publiques × locales, alternates).
  - [x] `proxy.ts` (auth / i18n, ex-middleware)

- [x] `frontend/src/components/`
  - [x] Composants UI génériques (Header, Footer, cards, badges, modals, skeletons…)
    > **Fait :** Création du dossier `components/ui/` et regroupement des composants génériques : Header, Footer, Modal, Badge, cards/, skeletons/. Imports mis à jour dans tout le projet.
  - [x] Composants scanner (`scan/` : ScannerContent, ScanResults, ScanHistoryBlock, etc.)
    > **Fait :** `scan/` : ScannerContent, ScanResults, ScanHistoryBlock, ScanLoader, FindingCard, AlertHistoryBlock, ScheduledScansBlock, ScanResultsGate, FakeScanResultsBlurred, scanConstants.
  - [x] Composants compte utilisateur (`user/sections/` : settings, sécurité, confidentialité, abonnement…)
    > **Fait :** `user/sections/` : ProfileSection, SecuritySection, PrivacySection, SettingsSection, SubscriptionSection ; `user/AccountLayout`, SectionSkeleton.
  - [x] Composants admin (gestion users, contacts, analytics, abonnements, emails…)
    > **Fait :** `admin/` : UserManagement, ContactManagement, EmailManagement, email/, SiteAnalytics, ApiMetrics, RouteMetrics, SubscriptionEditModal, SubscriptionChart, AdminGuard, AdminHeader, AuditLog, etc.
  - [x] StructuredContentEditor / inputs / forms / schedule / tables virtualisées
    > **Fait :** StructuredContentEditor/, inputs/ (DatePicker, Checkbox, ToggleSwitch…), forms/ (FormSelect), schedule/ (ScheduleFormPanel, RecurrenceScheduleFields…), VirtualizedTable.

- [x] `frontend/src/services/`
  - [x] Services `scanHistoryService`, `userService`
  - [x] Services admin (`admin*Service.ts`)
  - [x] Client HTTP (`apiClient.ts`, helpers d’export)
  > **Fait :** scanHistoryService, userService, scanService, scheduledScanService, contactService, analyticsTracker ; admin/ (adminUsersService, adminContactService, adminEmailsService, adminMetricsService, adminAnalyticsService, adminAuditService, adminAlertsService, adminSubscriptionsService, adminMediaService) ; apiClient et exportScan dans utils/.

- [x] `frontend/src/hooks/`
  - [x] Hooks génériques (pagination, filtres, loading states, auth user, page view…)
  - [x] Hooks SWR (clés, data fetching)
  > **Fait :** usePagination, useFilters, useLoadingStates, useAuthUser, usePageView, useDebounce, useModal, useDropdown, useInView, useVisibleSection, useAccountPage, useConfirmDelete ; swr/keys.ts.

- [x] `frontend/src/utils/`
  - [x] Helpers (logger, dates, URLs, metrics, admin helpers, scanStorage…)
  > **Fait :** logger, dateFormat, urlFormat, scanUrl, metricsHelpers, adminHelpers, scanStorage, exportScan, apiClient, numberFormatter, toastNotifications, renderWithBold.

- [x] `frontend/src/locales/`
  - [x] Fichiers i18n `fr.json` / `en.json`
  - [x] `i18n/server.ts`
  > **Fait :** locales/fr.json, locales/en.json ; i18n/server.ts (getTranslation) et i18n/config.ts.

- [x] `frontend/public/`
  - [x] `manifest.json`, assets publics (favicons, images, etc.)
  > **Fait :** manifest.json, favicon.ico, favicon-96x96.png, apple-touch-icon.png, logo.png, logo.svg, blue_logo.svg.

- [x] `frontend/tests/`
  - [x] Tests unitaires / placeholders à compléter
  > **Fait :** structure présente (placeholder.test.ts). Tests frontend réels (services, hooks, composants) à ajouter plus tard ; voir section 2 pour les tests d’intégration backend.

**Améliorations réalisées (0.2) :**
- **Services :** gestion d’erreur uniformisée avec `fetchJsonWithAuth` dans tous les services admin concernés : adminUsersService, adminContactService, adminAuditService, **adminAlertsService**, **adminEmailsService**, **adminMediaService** (méthodes JSON uniquement ; upload image reste en FormData), **adminSubscriptionsService** ; et dans **scheduledScanService**. Non modifiés (volontairement) : adminMetricsService, adminAnalyticsService (retournent `{ success, error }`), userService (helper `apiCall`), scanService (SSE pour `runScan`).
- **Hooks SWR :** hooks dédiés dans `hooks/swr/` : `useAdminUsers`, `useAdminUsersStats`, `useAdminContacts` ; **useAdminAuditLogs**, **useAdminAuditStats** ; **useAdminImages**, **useAdminImageStats** ; **useAdminTemplates**, **useAdminTemplateContent** ; **useAdminAlertRules**, **useAdminAlertEvents**, **useAdminAlertSummary**. Export via `hooks/swr/index.ts`. Les composants **AuditLog**, **AlertingDashboard** et **ImageGallery** (sections Images + Templates) utilisent ces hooks à la place de `useSWR` + services directs.
- **React.memo :** **KpiGrid** et **SubscriptionChart** enveloppés avec `React.memo` pour limiter les re-renders (KpiCard était déjà mémoïsée).
- **Public :** rôle du manifest clarifié dans `public/README.md` : manifest statique = fallback FR ; manifest dynamique i18n = `api/manifest/[locale]` (priorité).
- **i18n (traductions FR/EN) :** suppression des chaînes en dur et harmonisation des aria-labels. Nouvelles clés dans `fr.json` / `en.json` : `common.noData`, `pagination`, `errorBoundary`, `modal`, `datePicker`, `contact.ariaPage` / `ariaForm`, `scanner.ariaHeader` / `ariaForm`, `admin.ariaTabs`, `admin.gallery.viewGrid` / `viewList` / `templatePreview`, `admin.overview.registrationsEvolution12`, `admin.chart.free` / `premium`, `editor.*` (barre d’outils), `imageModal.*`, `routeMetrics.*`. Composants mis à jour : SubscriptionChart, admin/page (loading + aria tabs), SearchToolbar, Pagination, ConfirmModal, GenericButton, Table, VirtualizedTable, AdminSectionLoading / AdminInlineLoading (messageKey), ErrorBoundary (fallback traduit via ErrorBoundaryFallback + renderFallback, ErrorBoundary déplacé dans LanguageProvider), ContactForm, ScannerContent, Modal, DatePicker, ImageGallery (templatePreview), StructuredContentEditor, ImageModal, RouteMetrics. En locale EN, tous ces textes suivent désormais la langue choisie.

---

## 0.3 Micro-service dédié à la génération PDF

**Objectif :** extraire la génération de rapports PDF du scan-service vers un **micro-service à part** (ex. `pdf-service` ou `report-service`), pour isoler les dépendances lourdes (WeasyPrint, polices, etc.) et permettre de scaler ou de faire évoluer le rendu sans toucher au scanner.

**Comment s’y prendre (résumé) :**

1. **Créer le service**
   - Nouveau répertoire `backend/pdf-service/` (ou `report-service/`) avec structure type : `app/` (routers, services), `config/`, `tests/`, `Dockerfile`, `requirements.txt` (WeasyPrint + dépendances actuelles du PDF).

2. **Déplacer la logique**
   - Migrer le code de `scan-service/app/services/pdf_report/`, le catalogue et les assets (CSS, i18n) vers le pdf-service.
   - Exposer un endpoint unique, par ex. `POST /api/report/pdf` (body : payload du scan + `lang`), qui retourne le PDF en binaire (ou un lien temporaire).

3. **Intégration**
   - **Option A :** Le scan-service appelle le pdf-service en HTTP (après un scan ou sur demande) : envoi du résultat de scan en JSON, récupération du PDF.
   - **Option B :** Le gateway expose une route (ex. `/user/api/scan/export/pdf` ou `/pdf/api/export`) qui proxy vers le pdf-service ; le frontend et le scan-service appellent cette URL.
   - Configurer l’URL du pdf-service dans le gateway (comme pour admin/user/scan) et, si besoin, une route interne pour le scan-service.

4. **Données et auth**
   - Le pdf-service ne nécessite pas de base de données : entrée = payload scan + options (lang) ; sortie = fichier.
   - Authentification : soit le gateway vérifie le JWT et transmet la requête au pdf-service, soit le pdf-service est appelé uniquement en interne (scan-service / user-service) avec une clé ou un réseau isolé.

5. **Livrables**
   - [x] Créer `backend/pdf-service/` avec endpoint de génération PDF.
     > **Fait :** Répertoire `backend/pdf-service/` avec `app/` (main, routers/report, services/pdf_report, config, schemas, utils), `config/settings.yml`, `tests/`, `Dockerfile`, `requirements.txt` (WeasyPrint). Endpoint `POST /api/report/pdf` (body : url, score, timestamp, duration, findings ; query : lang, include_matrices) et `GET /api/health`.
   - [x] Déplacer la logique et les assets (catalogue, CSS, i18n) depuis le scan-service.
     > **Fait :** Migration de `pdf_report/` (cover, sommaire, synthese, findings, matrix, links, pdf_i18n, html_builder), `config/pdf.py`, `static/pdf_report.css` et `logo.png`, `catalogue/` (recommendations, risk_matrix, category_summaries + JSON) vers pdf-service. Suppression de tout le code PDF du scan-service.
   - [x] Adapter le gateway (route vers pdf-service) et le scan-service ou user-service (appel au pdf-service au lieu de générer en local).
     > **Fait :** Gateway : route `/pdf/*` → pdf-service (port 8013) dans `config/settings.yml` ; si `PDF_SERVICE_INTERNAL_API_KEY` définie, header `X-Internal-Api-Key` ajouté au proxy. Scan-service : `GET /api/scan/export/pdf` appelle le pdf-service en POST avec le payload scan ; variables `PDF_SERVICE_URL` et `PDF_SERVICE_INTERNAL_API_KEY`. Pdf-service : vérification optionnelle du header `X-Internal-Api-Key` si clé définie.
   - [x] Mettre à jour le docker-compose et la doc (ARCHITECTURE.md, VARIABLES-ENVIRONNEMENT.md).
     > **Fait :** docker-compose (principal, CI, betatest) : service pdf-service, variables `PDF_SERVICE_URL` et `PDF_SERVICE_INTERNAL_API_KEY` pour gateway et scan-service. `launch_dev.sh` : vérification et démarrage du pdf-service. ARCHITECTURE.md : schéma, table des services, route `/pdf/*`, endpoints scan/pdf. VARIABLES-ENVIRONNEMENT.md et `.env.example` (racine, pdf-service, gateway) : documentation des variables PDF. DEPLOIEMENT.md et PDF-I18N.md adaptés.
   - [x] Refactoring qualité du pdf-service (maintenabilité, rigueur, type-safety).
     > **Fait :** Refactoring complet de la base de code du pdf-service pour améliorer la maintenabilité et la rigueur. **Schémas Pydantic :** création de `app/schemas/finding.py` (modèle `Finding` avec validation de la sévérité : normalisation en minuscules, fallback sur `info`, `extra="ignore"` pour absorber les champs futurs) et `app/schemas/report.py` (`ReportPdfBody` extrait du router) ; `ReportPdfBody.findings` est désormais `list[Finding]` — la validation entrante se fait à la frontière HTTP, les fonctions de rendu reçoivent des objets typés. **Constantes centralisées :** nouveau module `app/services/pdf_report/constants.py` (`SEVERITY_LIST`, `SEVERITY_ORDER`, `severity_index()`) partagé entre `findings.py` et `sommaire.py` — suppression des deux copies locales identiques. **Paramètres de rendu configurables :** nouveau bloc `pdf.render` dans `config/settings.yml` (`evidence_max_len: 800`, `recommendation_max_len: 800`, `score_good: 80`, `score_medium: 50`) et nouveau dataclass `PdfRenderSettings` dans `app/config/pdf.py` — les seuils de score et les limites de texte ne sont plus des magic numbers dans le code. **Troncature explicite :** remplacement du slicing silencieux `[:800]` par `_truncate()` qui ajoute `…` en fin de texte et émet un `logger.warning` avec le slug et la longueur — le PDF est honnête et les dépassements sont traçables. **Source de vérité unique pour les labels :** suppression des champs `label_fr` / `label_en` redondants des 12 entrées de `catalogue/category_summaries.json` (labels déjà définis dans `settings.yml`). **Suppression du code mort :** `build_category_summaries()`, `CategorySummaryEntry`, `_CATEGORY_ORDER` retirés de `catalogue/category_summaries.py` (fonction appartenant au scan-service, jamais appelée dans le pdf-service). **Tests :** suite étendue de 5 à 26 tests — ajout de tests unitaires ciblés par module (`Finding` validation, `severity_index`, troncature avec `…`, échappement HTML sur URL et titres, builders HTML `cover`/`sommaire`/`synthese`/`build_html`, endpoint avec sévérité en majuscules, champs inconnus ignorés). 0 régression, 0 erreur lint flake8.
   - [x] Hardening final du socle de configuration et des constantes de rendu.
     > **Fait :** Finalisation du hardening pour éliminer les derniers points de dette. **Configuration commune (`backend/common`) :** `create_simple_settings()` accepte désormais `require_database_url` (défaut `True`) pour supporter proprement les services sans base ; le `pdf-service` l’utilise avec `False` et le hack `DATABASE_URL` factice a été supprimé de `app/config_loader.py`. **Constantes cover externalisées :** ajout de `cover_url_max_len`, `cover_logo_primary_color`, `cover_logo_secondary_color` dans `pdf.render` et utilisation directe dans `cover.py` (URL tronquée configurable + SVG fallback paramétrable). **API simplifiée :** suppression du paramètre `lang` inutilisé dans `links.py`, signatures allégées et appels mis à jour dans `findings.py`. **Validation qualité :** exécution complète des tests et du lint sur `pdf-service` et `common` (`pytest` + `flake8`) sans régression.

Les sections suivantes de la roadmap v0.3.0 (nouvelles fonctionnalités, tests actifs, analytics, etc.) seront ajoutées après ce refactoring de base.

---

## 1) API publique + clés API

### 1.1 Modèle

- [x] Schéma : `api_keys` (id, user_id, key_hash, name, prefix, created_at, last_used_at, expires_at, tags, allowed_ips)
  > **Fait :** Table `api_keys`, migrations 0011–0013. Contrainte unique (user_id, name) et key_hash unique. Préfixe `sk_`, hash SHA-256. Colonnes optionnelles : `expires_at` (TIMESTAMPTZ), `tags` (JSONB), `allowed_ips` (JSONB).
- [x] Génération : clé aléatoire (ex. 32 caractères) ; stocker uniquement le hash
  > **Fait :** `secrets.token_urlsafe(24)` → ~32 caractères. Hash SHA-256 hex. Préfixe affiché `sk_xxx...` pour la liste.

### 1.2 Authentification

- [x] Header `X-API-Key` ou `Authorization: Bearer <api_key>`
  > **Fait :** Gateway extrait la clé depuis X-API-Key ou Bearer si non-JWT. User-service : endpoint interne POST /api/internal/keys/verify protégé par X-Internal-Api-Key.
- [x] Middleware : vérifier la clé, résoudre l’utilisateur (quotas reportés)
  > **Fait :** Gateway appelle user-service pour vérifier ; request.state.user avec auth_type api_key. Proxy transmet Authorization Bearer aux backends. Quotas et rate limiting reportés → [A-PENSER-PLUS-TARD.md](../A-PENSER-PLUS-TARD.md).
- [x] Expiration des clés : vérifier `expires_at` ; rejeter si dépassée (401 « Clé API expirée »)
  > **Fait :** Par défaut TTL 30 jours ; options 90, 180, 365, ou 0 (jamais). Config `api_keys.default_ttl_days`, `allowed_ttl_days`.
- [x] Restriction IP : si `allowed_ips` défini, vérifier l'IP client (X-Forwarded-For, X-Real-IP) ; 401 « Clé API : IP non autorisée » si hors whitelist
  > **Fait :** Gateway transmet `client_ip` au verify ; user-service vérifie contre les plages CIDR ou IP autorisées.

### 1.3 Quotas et rate limiting (reporté)

Quotas, rate limiting et réponse 429 sont reportés à plus tard. Voir [A-PENSER-PLUS-TARD.md](../A-PENSER-PLUS-TARD.md) pour le détail (quotas par compte/clé, limites crawler, doc 429).

### 1.4 API

- [x] `POST /api/keys` : créer une clé (nom, options, retourne la clé en clair une seule fois)
  > **Fait :** POST /user/api/keys. Body { name, ttl_days?, tags?, allowed_ips? }. Réponse { id, key, name, created_at, expires_at }. Erreurs 403 limite, 409 nom existant.
- [x] `GET /api/keys` : liste des clés (sans valeur)
  > **Fait :** GET /user/api/keys. Réponse { items: [{ id, name, prefix, created_at, last_used_at, expires_at, tags, allowed_ips }] }.
- [x] `DELETE /api/keys/{id}` : révoquer une clé
  > **Fait :** DELETE /user/api/keys/{id}. 204 No Content. Erreur 404 si non trouvée.

### 1.5 Frontend

- [x] Page « Clés API » dans Mon compte
  > **Fait :** Page /scanner/cles-api (hub Scanner). Composant ApiKeysContent.
- [x] Création, affichage (une fois), révocation
  > **Fait :** Modal création : nom, durée de validité (1 mois défaut, 3/6/12 mois, jamais), tags (optionnel), restriction IP (optionnel). Modal clé avec Copier + avertissement « Ne sera plus visible ». Modal confirmation révocation.
- [x] Liste : affichage de expires_at, tags, allowed_ips par clé
  > **Fait :** Chaque clé affiche créée le, expire le, tags (badges), IP autorisées. Dernière utilisation si renseignée.
- [x] Documentation : exemple curl avec `X-API-Key`
  > **Fait :** Page /scanner/docs/api avec auth, exemple curl pour POST /scan/api/scan/async, lien vers clés.

---

## 2) Tests d’intégration pour la pipeline de scan

Objectif : **valider de bout en bout** la pipeline de scan (validation URL → protections SSRF → fetch HTTP/TLS → exécution des checks → scoring → sauvegarde historique et PDF) via des tests d’intégration automatisés, avec de vrais serveurs de test et une exécution dans la CI.

### 2.1 Environnements et serveurs de test

- [ ] Définir un environnement de test dédié au scan (Docker Compose minimal : scan-service + Postgres si nécessaire).
- [ ] Ajouter un ou plusieurs **serveurs cibles de démo** :
  - [ ] Serveur HTTP simple (cache/headers/cookies) — ex. `bad_cache_server.py`.
  - [ ] Serveur simulant des headers de sécurité variés (bonnes pratiques / mauvaises pratiques).
  - [ ] Serveur avec fichiers exposés / directory listing / robots.txt / sitemap de test.
  - [ ] **Serveur avec pages liées (même domaine)** pour les tests crawler : plusieurs pages HTML avec liens internes, pour valider le scénario crawl → liste → scan sur N URLs (voir 2.2).
  - [ ] (Optionnel) Serveur d’API de démo (Swagger/GraphQL/Content-Type).

### 2.2 Scénarios de tests d’intégration

- [ ] Scénario « happy path » : URL valide → scan complet → score cohérent → findings attendus.
- [ ] Scénarios d’erreur : DNS KO, timeout, TLS cassé, redirections excessives.
- [ ] Scénarios SSRF : URLs internes / localhost / IP privées bloquées en mode prod (`IS_PROD=true`).
- [ ] Scénarios de ports : ports non autorisés rejetés en prod, autorisés en dev (`IS_PROD=false` via `launch_dev.sh`).
- [ ] **Scénario crawler → liste → scan sur N URLs** : serveur de test avec pages liées (même domaine) ; lancer le crawler depuis une URL de départ, récupérer la liste d’URLs (via l’API crawler retenue en 7.3), lancer le scan sur un sous-ensemble (ex. 2–3 URLs) ; vérifier que les résultats agrègent les findings par URL ou produisent un rapport cohérent (historique, PDF si applicable).
- [ ] Vérification des catégories de checks : TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, info disclosure, etc.
- [ ] Vérification de l’écriture en historique (user-service) et de la génération PDF.

### 2.3 Intégration dans la CI

- [ ] Ajouter un job **tests d’intégration scan-service** dans la pipeline (GitHub Actions).
- [ ] Démarrer les services nécessaires (scan-service + serveurs de test) via Docker Compose dans le job.
- [ ] Lancer la suite de tests d’intégration (`pytest -m integration` ou répertoire dédié).
- [ ] Marquer le job comme requis pour les PR affectant le scan-service / gateway.

### 2.4 Observabilité et maintenance des tests

- [ ] Logs clairs pour chaque scénario (URL cible, findings principaux).
- [ ] Documentation rapide dans `docs/` pour expliquer comment lancer les tests d’intégration en local.
- [ ] Stratégie de maintenance : limiter le nombre de scénarios mais couvrir les cas critiques (TLS, SSRF, cache, exposition fichiers, CORS, crawler + scan multi-URLs).

---

## 3) Intégration CI/CD (GitHub Action SecureOps)

Objectif : proposer aux utilisateurs une **GitHub Action** officielle pour intégrer SecureOps dans leurs propres pipelines CI/CD.

### 3.1 Action GitHub

- [ ] Créer la répo `secureops/actions` ou une action dans le monorepo.
- [ ] Définir les inputs : `url`, `api_key` (secret), `fail_on_score_below` (optionnel).

### 3.2 Comportement

- [ ] Appeler `POST /scan/api/scan` avec `X-API-Key` (API publique SecureOps).
- [ ] Parser le résultat (score, findings).
- [ ] Faire échouer le job si `score < fail_on_score_below` ou si finding `critical`.

### 3.3 Documentation

- [ ] Rédiger un README avec un exemple d’utilisation dans un workflow GitHub Actions.
- [ ] (Optionnel) Fournir un badge « Scan SecureOps » pour le README des projets utilisateurs.

---

## 5) Limites (reporté)

Quotas, rate limiting et limites crawler sont reportés. Voir [A-PENSER-PLUS-TARD.md](../A-PENSER-PLUS-TARD.md). La section [7.6](#76-gestion-des-urls-limites-et-prévention-des-abus) couvre les URLs interdites / SSRF (implémenté).

---

## 7) Crawler HTTP — agent indépendant

> **Implémenté (v0.3.0).** Documentation détaillée : [docs/verifications/crawler.md](../verifications/crawler.md).

**Objectif :** Le **crawler** est un **agent indépendant des scans** : il s’exécute à part, produit une liste d’URLs (et métadonnées), et **envoie ce résultat au frontend**. Le frontend affiche ensuite une étape de validation/édition avant tout scan. Le crawler ne déclenche pas lui‑même le scan ; il alimente l’utilisateur qui valide puis lance le scan sur la liste finale.

**Fonctionnement :** télécharger la page initiale, parser le DOM, extraire liens et endpoints, produire une **liste d’URLs et de métadonnées** ; renvoyer cette liste au frontend. Le frontend présente : « Voici ce que le crawler a trouvé. C’est OK ? Tu veux supprimer des URLs ? Tu veux en ajouter manuellement ? » — l’utilisateur confirme ou édite la liste, puis lance le scan sur cette liste. Le crawler est entièrement implémenté dans la v0.3.0.

### 7.1 Noyau du crawler

- [x] **Téléchargement** : récupérer la page HTML de l’URL de départ (réutiliser le client HTTP existant, timeouts, suivi des redirections).
- [x] **Parsing DOM** : parser le HTML (HTMLParser natif Python) pour extraire les éléments utiles.
- [x] **Extraction des liens** :
  - [x] Liens `<a href="...">` (URLs absolues et relatives, normalisées).
  - [x] Formulaires `<form action="...">` (méthode, action, champs).
  - [x] Scripts `<script src="...">` et feuilles `<link rel="stylesheet" href="...">` (déjà partiellement fait pour SRI/cache ; les réutiliser ou les intégrer au flux crawler).
  - [x] Iframes `src` si pertinent (optionnel, avec limite).
- [x] **Détection d’endpoints type API** : repérer dans les liens ou attributs des patterns comme `/api`, `/graphql`, `/v1`, `/rest`, `/swagger`, etc. → marquer ces URLs comme « endpoint API » pour la phase scan (ex. CORS, headers, Content-Type).
- [x] **Normalisation et dédoublonnage** : normaliser les URLs (schéma, host, slash trailing, fragment), dédupliquer, filtrer les types inutiles (mailto:, tel:, ancres pures).

### 7.2 Suivi des routes (crawl en profondeur)

- [x] **Politique de suivi** : suivre les liens **même domaine** (et optionnellement sous-domaines configurables) pour découvrir d’autres pages.
- [x] **Limites** :
  - [x] Profondeur max (2 niveaux par défaut à partir de l’URL de départ).
  - [x] Nombre max d’URLs à crawler (ex. 50–100) pour rester dans les timeouts et coûts raisonnables.
  - [x] Timeout global du crawl (30 s par défaut).
- [x] **File d’URLs** : traiter les URLs en file (BFS ou DFS), en évitant de re-visiter une URL déjà vue.
- [x] **Respect de robots.txt** : avant de crawler une URL, vérifier qu’elle n’est pas interdite par `Disallow` (réutiliser la logique robots.txt existante). Option : respecter aussi `Crawl-delay` si présent (attente entre requêtes).

### 7.3 Sortie du crawler, envoi au frontend et étape de validation

- [x] **Structure de sortie** : liste d’entrées `{ url, type?, depth? }` (type = page, formulaire, script, api_endpoint, etc.) avec métadonnées utiles.
- [x] **Réception du résultat crawler par le frontend** — à préciser pour l’implémentation, documenter le choix en 7.5 :
  - **Option A (crawl court)** : endpoint synchrone type `POST /api/crawl` (ou équivalent) : body = `{ url }`, réponse = liste d’URLs après crawl (timeout côté client ex. 30–60 s). Le frontend attend la réponse puis affiche l’étape de validation.
  - **Option B (crawl long)** : `POST /api/crawl` retourne un `crawl_job_id` ; le frontend poll `GET /api/crawl/{crawl_job_id}` jusqu’à statut `completed` (ou `failed`), puis récupère la liste via `GET /api/crawl/{crawl_job_id}/result`. Adapter si usage de SSE/WebSocket plutôt que polling.
  - Choisir A ou B selon durée attendue du crawl et contraintes timeout ; documenter le contrat (payload, format de la liste, codes erreur) dans la doc technique (7.5).
- [x] **Envoi du résultat au frontend** : le crawler (agent indépendant) renvoie sa liste d’URLs au frontend via le mécanisme retenu ci‑dessus. Aucun scan n’est lancé automatiquement après le crawl.
- [x] **Option utilisateur « Scanner uniquement cette page »** (checkbox dans le formulaire du scanner) :
  - [x] Si **coché** : **aucun crawler** — pas d’étape de découverte ; scan directement sur l’URL saisie. Indiquer dans l’UI : « Scanner uniquement cette page (pas de découverte des autres pages du site) ».
  - [x] Si **décoché** (comportement par défaut) : **lancer le crawler** ; le résultat est envoyé au frontend ; le frontend affiche l’étape de validation (voir ci‑dessous) ; le scan ne s’exécute qu’après validation par l’utilisateur. Indiquer dans l’UI : « Découvrir les pages du même domaine puis choisir les URLs à scanner » (ou équivalent).
- [x] **Étape frontend après réception du résultat du crawler** :
  - [x] Afficher : « Voici ce que le crawler a trouvé. C’est OK ? Tu veux supprimer des URLs ? Tu veux en ajouter manuellement ? »
  - [x] Liste des URLs découvrables (avec type/depth si utile) : cases à cocher ou bouton « supprimer » par ligne pour retirer des URLs.
  - [x] Champ ou bouton pour **ajouter des URLs manuellement** (une ou plusieurs).
  - [x] Bouton type « Lancer le scan » (ou « C’est bon, scanner ces URLs ») : envoi de la **liste finale** (validée/éditée) au backend pour exécution du scan sur cet ensemble.
- [x] **Alimentation du scan** : le scan s’exécute sur la liste validée par l’utilisateur (URL initiale + URLs conservées/ajoutées). L’URL de départ reste la cible principale ; les autres URLs sont traitées selon la politique (checks ciblés, rapport « URLs découvertes », etc.).

### 7.4 Bonnes pratiques et suggestions

- [x] **User-Agent** : envoyer un User-Agent identifié (ex. `SecureOps-Crawler/1.0`) pour transparence côté serveur cible.
- [x] **Même domaine strict** par défaut : ne pas suivre les liens vers d’autres domaines (éviter crawl sauvage et SSRF).
- [x] **Exclusion des ressources binaires** : ne pas mettre en file les URLs dont l’extension ou le type suggère un binaire (images, PDF, ZIP, etc.) sauf si configuré.
- [x] **Détection d’URL « backend »** : si une URL crawlé ressemble à une API (pattern `api.`, `backend.`, chemin `/api`, `/graphql`), la marquer pour la feature « scanner aussi le backend » (option future ou option utilisateur « URL backend »).
- [x] **Logs et observabilité** : nombre d’URLs découvertes, nombre crawlé, durée, erreurs (timeout, 403, etc.) pour le rapport ou les métriques.
- [x] **Configuration** : paramètres dans `settings.yml` (profondeur max, max URLs, timeout, respect robots.txt on/off, domaines autorisés).

### 7.5 Documentation et tests

- [x] Documenter dans `docs/verifications/crawler.md` : objectif, limites, respect robots.txt, impact sur le scan, choix techniques.
- [x] Documenter le **contrat API crawler** (option A synchrone, payload, format de la liste, codes erreur) dans la doc.
- [ ] Tests unitaires : parsing HTML → liste d’URLs attendue ; respect Disallow ; limites (profondeur, max URLs).
- [ ] Test d’intégration : crawl d’une page de test (ex. `bad_crawl_server` ou fixture HTML) → vérifier la sortie et l’absence de fuite hors domaine.

### 7.6 Gestion des URLs, limites et prévention des abus

**Objectif :** Limiter les abus (crawl sauvage, ciblage de domaines sensibles) et sécuriser l’usage du crawler et du scan (URLs interdites, listes noires).


- [x] **URLs interdites / SSRF** :
  - [x] Bloquer localhost, IP privées (RFC 1918), IP de bouclage pour l'**URL de départ** (`check_ssrf`) et les **URLs découvertes** (`is_hostname_blocked`). Réutilisation de la logique SSRF du scan-service.
  - [ ] Liste noire configurable (ex. dans `settings.yml`) : à implémenter ultérieurement.
- [ ] **Modération** (optionnel) : possibilité d’ajouter a posteriori des domaines bloqués et de logger les tentatives (audit). À documenter comme évolution si non implémenté.
- [ ] **Quotas crawler, rate limiting, 429** : reportés → [A-PENSER-PLUS-TARD.md](../A-PENSER-PLUS-TARD.md).

---

## 8) Réorganisation / amélioration de l’UX

**Objectif :** Revoir l’organisation des écrans et améliorer l’expérience utilisateur (navigation, lisibilité des résultats, parcours scanner / compte / admin).

### 8.1 Refonte de la landing page

- [x] **Supprimer le contenu superflu** : retirer tout ce qui est « bullshit » (faux avis, témoignages factices, blocs marketing non essentiels).
  > **Fait :** Suppression du badge « 4.9/5 — 120+ équipes » (faux avis), de la section logos partenaires (`TRUSTED_LOGOS`), de la section témoignages (`TestimonialCard` × 3), du bloc CTA redondant, et de la section features (« Une sécurité pensée pour les équipes modernes », Détection continue, Priorisation intelligente, Conformité intégrée). Landing réduite au hero (titre, sous-titre, CTA démo/docs).
- [x] **Input scan directement sur la landing** : placer un champ URL + CTA pour lancer un **scan basique** depuis l’accueil (sans aller sur la page Scanner dédiée).
  > **Fait :** Composant `LandingScanBlock` : champ URL + bouton « Lancer le scan » dans le hero. Message `home.scanDesc` : scan basique, pour multi-pages → Scanner.
- [x] **Parcours du scan basique** :
  - [x] **Chargement de la page initiale uniquement** (pas de crawler : une seule URL récupérée), puis exécution d'un **scan basique** sur cette URL avec **uniquement les vérifications frontend** (TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, etc. — pas de tests actifs ni d'options avancées).
  > **Fait :** Appel direct à `runScan(url)` sans crawler. Même pipeline que la page Scanner en mode « scanner uniquement cette page ». (pas de crawler : une seule URL récupérée), puis exécution d’un **scan basique** sur cette URL avec **uniquement les vérifications frontend** (TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, etc. — pas de tests actifs ni d’options avancées).
- [x] **Connexion obligatoire pour les résultats** : réutiliser la même mécanique que sur la page Scanner — après le scan, l’utilisateur **doit se connecter** pour accéder aux résultats (gate « Connectez-vous pour accéder aux résultats », stockage temporaire en sessionStorage, restauration après connexion). Pas de résultats affichés sans auth.
  > **Fait :** `ScanResultsGate` + `FakeScanResultsBlurred`, sessionStorage, `returnTo=/`, sauvegarde historique au retour.
- [x] Message clair sur la landing : scan basique (une page) + vérifications frontend ; pour crawler ou options, redirection vers la page Scanner.
  > **Fait :** Intro `home.scanIntro` au-dessus de l’input, texte `home.scanDesc` sous le formulaire. Refonte résultats, nav Mon compte, onboarding, accessibilité : à traiter selon les retours.

### 8.2 Refonte de la page Scanner (hub connecté)

- [x] **Accès réservé aux utilisateurs connectés** : la page Scanner n'est accessible qu'après connexion (sinon redirection vers login ou landing).
  > **Fait :** `ScannerGuard` dans `scanner/layout.tsx` ; redirection vers `/connexion?returnTo=/scanner` si non authentifié.
- [x] **Page d’intro type hub** : une fois connecté, l’utilisateur arrive sur une page d’accueil « Scanner » qui présente les fonctionnalités sous forme de **cards** cliquables (pas directement le formulaire de scan).
  > **Fait :** `ScannerHub` avec deux sections (Gestion, Scanner) et cartes cliquables.

#### Cards à prévoir

- [x] **Card « Analyses »** (ou « Espace scan » / « Scans » — à trancher) : accès aux scanners disponibles.
  > **Fait :** Card « Scan frontend » → `/scanner/analyses`.
  - [x] Dedans : accès au **premier scanner** (scan de posture sécurité, URL + options + lancement) dans une sous-vue ou sous-page.
  - [x] **Checkbox « Scanner uniquement cette page »** dans le formulaire : si cochée, pas de crawler (scan direct sur l’URL) ; si décochée, lancer le **crawler** (agent indépendant), réception du résultat au frontend, puis **étape de validation** (voir 7.3). Libellés clairs dans l’UI.
  - [x] **Écran « Voici ce que le crawler a trouvé »** (quand crawler activé) : afficher la liste d’URLs ; permettre de supprimer des URLs, d’en ajouter manuellement ; bouton « Lancer le scan » sur la liste finale.
  - [x] Possibilité d’ajouter plus tard d’autres types de scan (ex. scan actif, scan ciblé) dans la même rubrique : card « Scans personnalisés » (placeholder en construction).
- [x] **Section « Vue d'ensemble » – card « Suivi des scans »** : renvoie vers un espace regroupant :
  > **Fait :** Section « Vue d'ensemble », card « Suivi des scans » → `/scanner/vue-d-ensemble` ; card « Clés API » → `/scanner/cles-api` (placeholder).
  - [x] **Historique des scans** : liste des scans passés, filtres, détail, suppression.
  - [x] **Évolution des failles** : tendances (évolution du score dans le temps, nombre de findings par sévérité). Graphique avec **données réelles** : barres = nombre de scans par jour, courbe = score ou anomalies (toggle). Données agrégées via endpoint `GET /user/api/scans/history/overview`, filtres (URL, type de scan, période) appliqués.
  - [ ] **Rapports et exports** : accès aux PDF, exports CSV/JSON si implémentés.
  - [x] **Scans planifiés** : création, modification, pause des scans récurrents.
  - [x] **Lien vers la gestion des clés API** : accès à la page « Clés API » (création, révocation, doc). Card dédiée sur le hub.
  - [x] **KPIs tableau de bord** : Total scans, Score moyen, Anomalies critiques, Planifiés actifs, Dernier scan. **Données réelles** via l’endpoint overview, mises à jour lors des changements de filtres (URL, type, période).
  - [ ] Alertes configurées, préférences de notification.
- [x] **Card « Documentation »** : section sur la home du hub Scanner qui renvoie vers la documentation (scanners, API, etc.).
  > **Fait :** Card → `/scanner/docs` (page placeholder). Cards additionnelles : Crawlers, Scan backend (placeholders).
  - [ ] Liens vers une **page ou section doc** regroupant : doc du **scan de posture** (vérifications, crawling, interprétation des résultats), doc des **autres scanners** si présents, doc de l’**API publique** (endpoints, clés API, exemples curl, intégration CI/CD). Page doc à compléter.
  - [ ] **Doc accessible depuis la page concernée** : la documentation d’un scanner en particulier (ex. scan de posture) doit aussi être disponible depuis la page de ce scanner (lien « Aide » ou « Documentation » sur la page `/scanner/analyses/posture`). De même, la doc de l’API doit être accessible depuis la page de gestion des clés API (lien « Documentation API »). Ainsi, l’utilisateur trouve la doc soit depuis le hub (section Documentation), soit depuis la page du sujet (scanner ou API).

#### Structure des routes (plusieurs pages)

- [x] **Plusieurs pages obligatoires** : routes dédiées — `/scanner` (hub avec cards), `/scanner/analyses` ou `/scanner/analyses/posture` (premier scanner), `/scanner/vue-d-ensemble` (suivi des scans : Historique, Évolution, Scans planifiés, Clés API). URLs claires, partageables, historique navigateur propre.
  > **Fait :** `/scanner` (hub), `/scanner/analyses`, `/scanner/vue-d-ensemble`, `/scanner/docs`, `/scanner/crawlers`, `/scanner/backend`, `/scanner/cles-api`, `/scanner/scans-personnalises`.
- [x] **Convention** : `/scanner` = hub cards ; `/scanner/analyses` (ou `/scanner/analyses/posture`) = premier scanner ; `/scanner/vue-d-ensemble` = une seule page « Suivi des scans » avec contenu (évolution, scans planifiés, historiques) sans tabs.
  > **Fait :** Page gestion en scroll unique (évolution, planifiés, 2 historiques côte à côte). Pas de tabs.

### 8.3 Header / navigation

- [x] **Nav adaptée à l’état de connexion** : le header (barre de navigation) change selon que l’utilisateur est connecté ou non :
  > **Fait :** `navLinks` filtrés selon `isAuthenticated` ; lien « Scanner » masqué si déconnecté.
  - [x] **Déconnecté** : liens type Accueil, Tarifs, Contact, Connexion / Inscription (pas d’entrée « Scanner » en tant que page hub réservée aux connectés, ou alors libellé du type « Découvrir le scanner » qui mène vers la landing avec l’input scan basique).
  - [x] **Connecté** : ajout des entrées utiles (ex. Scanner [hub], Mon compte, Déconnexion) ; le lien « Scanner » mène vers le hub (page d’intro avec cards).
- [x] **En mode Scanner (pages /scanner, /scanner/…)** : ne jamais afficher la nav en mode « déconnecté » pour ces URLs. Si l’utilisateur n’est pas connecté et atterrit sur une URL scanner (bookmark, lien direct), rediriger vers la connexion (ou la landing) au lieu d’afficher le hub avec un header déconnecté. Ainsi, dès qu’on est dans l’espace scanner, le header reflète toujours un utilisateur connecté (ou on n’a pas accès à la page).
  > **Fait :** `ScannerGuard` redirige vers `/connexion?returnTo=/scanner` si non authentifié.
- [x] Cohérence : sur la landing, le header reste « déconnecté » (Accueil, Connexion, etc.) ; après connexion, le header bascule et inclut Scanner / Mon compte / Déconnexion.

### 8.4 Affichage du scanner : chargement et anomalies

**Objectif :** Lors du chargement ou de l’affichage des résultats du scan, ne pas utiliser le vert pour les points qui correspondent à une **anomalie détectée** ; indiquer clairement qu’**on a trouvé quelque chose** (alerte / attention), pour que l’utilisateur distingue immédiatement « vérification OK » vs « problème détecté ».

- [x] **Réservoir le vert aux vérifications OK** : afficher en vert uniquement les points pour lesquels **aucune anomalie** n’a été trouvée (vérification passée).
- [ ] **Anomalies = « on a trouvé quelque chose »**
  > **En cours :** Couleurs dédiées (error, warning) pour les sévérités. Libellé « anomalie(s) » présent. Manque : icône dédiée dans le résumé/table ; libellé explicite « Anomalie détectée »/« Trouvé ».
- [x] **S’appliquer à toutes les anomalies sauf « info »** : ce comportement vaut pour tous les niveaux de sévérité d’anomalie (critique, haute, moyenne, basse). Le niveau **info** peut rester avec un traitement distinct (neutre ou informatif), sans être affiché comme « validé » en vert.
- [x] Cohérence sur l’écran de chargement / progression et sur la page de résultats : même logique (vert = OK, pas d’anomalie ; autre traitement = quelque chose a été trouvé, pour toutes les anomalies hors info).

---

## 6) Mode asynchrone + queue

> **Contexte :** Implémente pour `scan-service` et `crawl-service` en mode DB queue (V1).

**Objectif :** Permettre des scans longs sans timeout : l’utilisateur lance un scan, reçoit immédiatement un `job_id`, puis consulte le statut et les résultats plus tard.

Documentation detaillee: [Queue asynchrone scan + crawl](../verifications/async-queue.md)

### 6.1 Choix technologique

- [x] Choisir stack : SQS + worker Python **ou** Celery + Redis
  > **Fait :** V1 retenue en **DB queue only** (pas SQS/Celery). Les jobs sont persistes dans PostgreSQL et traites par workers dedies.
- [x] Documenter décision (pros/cons, coût, complexité)
  > **Fait :** Decision et plan detailles dans `docs/roadmaps/ROADMAP-ASYNC-SCAN-CRAWL-IMPLEMENTATION.md`.

### 6.2 Infrastructure queue

- [x] Créer file SQS (ou Redis pour Celery)
  > **Fait :** Infrastructure V1 basee sur tables SQL service-owned: `scan_async_jobs` et `crawl_async_jobs`.
- [x] Configurer dead-letter queue (DLQ) pour échecs
  > **Fait :** En V1 DB queue, pas de DLQ externe. Les jobs terminent en `failed` avec `error_json` et `attempt_count=max_attempts` apres echec final.
- [x] Timeout et retry policy (ex. 3 tentatives, backoff exponentiel)
  > **Fait :** `max_attempts=3`, backoff `15s/60s/180s`, timeout job `300s` (scan+crawl), configuration via `async_jobs` dans `settings.yml`.

### 6.3 Worker scan

- [x] Worker dédié : consomme jobs de la queue, exécute le scan
  > **Fait :** `scan-worker` et `crawl-worker` en processus separes des APIs, ajoutes dans docker-compose.
- [x] Réutiliser la logique existante (`scan_stream`, checks, normalisation)
  > **Fait :** Les executors async reutilisent la logique metier existante (`scan_stream_generator` / `crawl_stream_generator`) et ajoutent le support `scan_type` (`frontend` reel, `backend/custom` fake complete).
- [x] Stocker résultat en base (ex. PostgreSQL) avec `job_id`, `status`, `result`
  > **Fait :** Resultats et erreurs stockes dans `result_json` / `error_json`, progression dans `progress_log_json`, etats dans `status`.

### 6.4 API endpoints

- [x] `POST /api/scan/async` : enqueue un job, retourne `job_id`
- [x] `GET /api/scan/async/{job_id}` : statut du job (pending, running, completed, failed)
- [x] `GET /api/scan/async/{job_id}/result` : résultat du scan (si completed)
  > **Fait :** Meme contrat implemente pour scan **et** crawl:
  > - `POST /scan/api/scan/async`, `GET /scan/api/scan/async/{job_id}`, `GET /scan/api/scan/async/{job_id}/result`
  > - `POST /crawl/api/crawl/async`, `GET /crawl/api/crawl/async/{job_id}`, `GET /crawl/api/crawl/async/{job_id}/result`
  >
  > Ownership gere via user authentifie ou `X-Job-Token` anonyme (token stocke en hash seulement).

### 6.5 Frontend

- [x] Option : lancer scan en mode async si durée estimée > seuil
  > **Fait :** Le frontend utilise le flux async comme mode principal pour scan et crawl.
- [x] Polling ou WebSocket pour afficher le statut
  > **Fait :** Polling implemente avec progression en base (`progress_log`) et affichage etape par etape.
- [x] Page résultats accessible via URL partageable (`/scan/{job_id}`)
  > **Fait :** Non implantee telle quelle. Le flux actuel est `create -> polling status -> result` dans les ecrans scanner existants.

### 6.6 Hardening et refactoring (post-implementation)

- [x] Factoriser la logique commune queue scan/crawl
  > **Fait :** Helpers communs centralises dans `backend/common/common/async_jobs.py` (repository generic, progress batcher, retry helpers).
- [x] Sortir la logique d'access control des routers
  > **Fait :** `app/use_cases/async_job_access.py` introduit dans scan-service et crawl-service (exceptions metier + mapping HTTP en router).
- [x] Rendre la fenetre de batch de progression configurable
  > **Fait :** `async_jobs.progress_batch_window_seconds` ajoute dans `settings.yml` scan/crawl et utilise par les workers.
