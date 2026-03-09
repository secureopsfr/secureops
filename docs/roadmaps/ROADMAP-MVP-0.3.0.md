# SecureOps — Roadmap MVP 0.3.0

## Sommaire

**Ordre recommandé pour la lecture et l’implémentation :** 0 (refactoring) → 1 (API + quotas) → 2 (tests) → 3 (GitHub Action) → 4–5 (placeholders) → 7 (crawler) → 8 (UX) → 6 (async, si besoin).

- [0) Refactoring de la base de code](#0-refactoring-de-la-base-de-code)
  - [0.1 Backend — Refactoring par dossier](#01-backend--refactoring-par-dossier)
  - [0.2 Frontend — Refactoring par dossier](#02-frontend--refactoring-par-dossier)
  - [0.3 Micro-service dédié à la génération PDF](#03-micro-service-dédié-à-la-génération-pdf)
- [1) API publique + clés API](#1-api-publique--clés-api)
  - [1.1 Modèle](#11-modèle)
  - [1.2 Authentification](#12-authentification)
  - [1.3 Quotas et rate limiting (web + API)](#13-quotas-et-rate-limiting-web--api)
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
- [4) Mode scan — synchrone uniquement (placeholder)](#4-mode-scan--synchrone-uniquement-placeholder)
- [5) Limites (renvoi vers 1.3)](#5-limites-renvoi-vers-13)
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

- [ ] `backend/common/`
  - [ ] `common/` (utils partagés : config, JWT, DB, logging, middleware, health, URL utils)
  - [ ] `pyproject.toml` / packaging du module commun

- [ ] `backend/gateway/`
  - [ ] `app/`
    - [ ] `routers/` (proxy, health, routes publiques)
    - [ ] `services/proxy/` (logique de proxy, métriques)
    - [ ] `config_loader.py` / settings
  - [ ] `config/` (YAML des services, CORS, timeouts)
  - [ ] `tests/`
  - [ ] `Dockerfile` / `requirements.txt`

- [ ] `backend/admin-service/`
  - [ ] `app/`
    - [ ] `routers/` (contact, newsletter, images, analytics, notifications, admin)
    - [ ] `models/` (events, audit, etc.)
    - [ ] `services/` (contact, mailing list, kpis, alerting, materialized views…)
    - [ ] `db.py` / `db_sync.py` / `email_config.py`
  - [ ] `config/settings.yml`
  - [ ] `alembic/` + `alembic.ini`
  - [ ] `tests/`
  - [ ] `Dockerfile` / `pyproject.toml` / `requirements.txt`

- [ ] `backend/user-service/`
  - [ ] `app/`
    - [ ] `routers/` (profil, préférences, sécurité, favoris, scans, scheduled scans, health)
    - [ ] `models/` (user, subscription, favorites, scans, scheduled_scans, alerts…)
    - [ ] `services/`
      - [ ] `user_repository.py`
      - [ ] `subscription_repository.py`
      - [ ] `favorite_repository.py`
      - [ ] `scan_repository.py`
      - [ ] `scan_alert_repository.py`
      - [ ] `scheduled_scan_repository.py`
      - [ ] `scheduled_scan_scheduler.py`
      - [ ] `scheduled_scan_utils.py`
      - [ ] `scan_alert_service.py`
      - [ ] `user_service.py`
      - [ ] `cognito_service.py`
    - [ ] `schemas/`
    - [ ] `utils/` (auth, URL utils)
    - [ ] `db.py` / `config_loader.py`
  - [ ] `config/settings.yml`
  - [ ] `alembic/` + `alembic.ini`
  - [ ] `scripts/` (cleanup, tâches ponctuelles)
  - [ ] `tests/`
  - [ ] `Dockerfile` / `requirements.txt`

- [ ] `backend/scan-service/`
  - [ ] `app/`
    - [ ] `routers/` (scan, health, export PDF via proxy vers pdf-service, endpoints internes)
    - [ ] `services/`
      - [ ] `tls/`
      - [ ] `security_headers/`
      - [ ] `cookies/`
      - [ ] `exposed_files/`
      - [ ] `directory_listing/`
      - [ ] `robots_txt/`
      - [ ] `sitemap/`
      - [ ] `tech_fingerprinting/`
      - [ ] `information_disclosure/`
      - [ ] `cache/`
      - [ ] `cors_cross_origin/`
      - [ ] `integrity/`
      - [ ] `subresources/`
      - [ ] `normalization/`
      - [ ] `scan_history_save/`
      - [ ] `scan_runner.py`
    - [ ] `catalogue/` (reco, matrices, catégories — hors PDF, voir pdf-service)
    - [ ] `config/` (TLS, cache, CORS, scoring, SSRS, timeouts, URL validation…)
    - [ ] `utils/` (url_validator, ssrf, url_helpers, headers, http_fetch, ssl_scan…)
    - [ ] `models/`, `schemas/`, `errors/`, `static/`
  - [ ] `tests/` (checks, scoring, router, SSRF, URL validator…)
  - [ ] `Dockerfile`

- [ ] `backend/` racine
  - [ ] Fichiers de configuration Docker / compose backend
  - [ ] Scripts divers (si présents)

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

Les sections suivantes de la roadmap v0.3.0 (nouvelles fonctionnalités, tests actifs, analytics, etc.) seront ajoutées après ce refactoring de base.

---

## 1) API publique + clés API

### 1.1 Modèle

- [ ] Schéma : `api_keys` (id, user_id, key_hash, name, created_at, last_used_at)
- [ ] Génération : clé aléatoire (ex. 32 caractères) ; stocker uniquement le hash

### 1.2 Authentification

- [ ] Header `X-API-Key` ou `Authorization: Bearer <api_key>`
- [ ] Middleware : vérifier la clé, résoudre l’utilisateur, appliquer quotas

### 1.3 Quotas et rate limiting (web + API)

Politique **unifiée** : mêmes principes pour les scans lancés depuis l’UI (compte utilisateur) et pour les appels API (clé). Les seuils peuvent être distincts (ex. quota par compte vs par clé) mais la mécanique (comptage, 429) est centralisée.

- [ ] **Quotas par compte (web)** : ex. nombre max de scans/jour par utilisateur connecté (à définir).
- [ ] **Quotas par clé API** : ex. 100 scans/jour par clé (ou aligné sur le quota compte).
- [ ] **Rate limiting** : ex. 10 req/min par clé ; par IP ou par compte pour l’UI (à définir).
- [ ] **Réponse 429** (Too Many Requests) en cas de dépassement, avec en-tête `Retry-After` si pertinent.
- [ ] Documenter les seuils retenus (section 5 ou doc dédiée) et les faire évoluer selon l’usage.

### 1.4 API

- [ ] `POST /api/keys` : créer une clé (nom, retourne la clé en clair une seule fois)
- [ ] `GET /api/keys` : liste des clés (sans valeur)
- [ ] `DELETE /api/keys/{id}` : révoquer une clé

### 1.5 Frontend

- [ ] Page « Clés API » dans Mon compte
- [ ] Création, affichage (une fois), révocation
- [ ] Documentation : exemple curl avec `X-API-Key`

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

## 4) Mode scan — synchrone uniquement (placeholder)

> **Note :** Ce n’est pas définitif ; cette section sert de **placeholder** pour formaliser le choix actuel et les évolutions possibles.

- [ ] Documenter explicitement que le scan reste **synchrone** en v0.3.0 (mode async reporté à la [section 6](#6-mode-asynchrone--queue)).
- [ ] Préciser dans la doc / release notes les limites (timeout, durée max) et le fait qu’un mode asynchrone pourra être envisagé en cas de scans longs.

---

## 5) Limites (renvoi vers 1.3)

Les **quotas et le rate limiting** (web + API) sont définis dans la [section 1.3](#13-quotas-et-rate-limiting-web--api). Cette section reste un **placeholder** pour d’éventuelles évolutions (seuils différenciés, périmètres spécifiques crawl/scan, abus — voir aussi [7.6](#76-gestion-des-urls-limites-et-prévention-des-abus)).

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

- [ ] **Limites d’usage du crawler** :
  - [ ] Nombre max de crawls/jour par utilisateur (ou par clé API), aligné ou dérivé des quotas 1.3 (ex. 1 crawl = 1 unité quota ou quota dédié crawl).
  - [ ] Option : limite par domaine cible (ex. pas plus de X crawls/jour vers le même host) pour éviter le harcèlement d’un même site.
- [x] **URLs interdites / SSRF** :
  - [x] Bloquer localhost, IP privées (RFC 1918), IP de bouclage pour l'**URL de départ** (`check_ssrf`) et les **URLs découvertes** (`is_hostname_blocked`). Réutilisation de la logique SSRF du scan-service.
  - [ ] Liste noire configurable (ex. dans `settings.yml`) : à implémenter ultérieurement.
- [ ] **Modération** (optionnel pour la v0.3.0) : possibilité d’ajouter a posteriori des domaines bloqués et de logger les tentatives (audit). À documenter comme évolution si non implémenté en 0.3.0.
- [ ] Documenter dans la doc crawler (7.5) et dans la doc limites/quotas : comportement en cas de dépassement (429), message utilisateur en cas d’URL refusée (liste noire ou interdite).

---

## 8) Réorganisation / amélioration de l’UX

**Objectif :** Revoir l’organisation des écrans et améliorer l’expérience utilisateur (navigation, lisibilité des résultats, parcours scanner / compte / admin).

### 8.1 Refonte de la landing page

- [ ] **Supprimer le contenu superflu** : retirer tout ce qui est « bullshit » (faux avis, témoignages factices, blocs marketing non essentiels).
- [ ] **Input scan directement sur la landing** : placer un champ URL + CTA pour lancer un **scan basique** depuis l’accueil (sans aller sur la page Scanner dédiée).
- [ ] **Parcours du scan basique** :
  - [ ] **Chargement de la page initiale uniquement** (pas de crawler : une seule URL récupérée), puis exécution d’un **scan basique** sur cette URL avec **uniquement les vérifications frontend** (TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, etc. — pas de tests actifs ni d’options avancées).
- [ ] **Connexion obligatoire pour les résultats** : réutiliser la même mécanique que sur la page Scanner — après le scan, l’utilisateur **doit se connecter** pour accéder aux résultats (gate « Connectez-vous pour accéder aux résultats », stockage temporaire en sessionStorage, restauration après connexion). Pas de résultats affichés sans auth.
- [ ] Message clair sur la landing : scan basique (une page) + vérifications frontend ; pour un scan avec découverte multi-pages (crawler) ou des options, redirection vers la page Scanner.
- [ ] À compléter selon les retours (ex. refonte page résultats, navigation Mon compte, onboarding, accessibilité).

### 8.2 Refonte de la page Scanner (hub connecté)

- [ ] **Accès réservé aux utilisateurs connectés** : la page Scanner n’est accessible qu’après connexion (sinon redirection vers login ou landing).
- [ ] **Page d’intro type hub** : une fois connecté, l’utilisateur arrive sur une page d’accueil « Scanner » qui présente les fonctionnalités sous forme de **cards** cliquables (pas directement le formulaire de scan).

#### Cards à prévoir

- [ ] **Card « Analyses »** (ou « Espace scan » / « Scans » — à trancher) : accès aux scanners disponibles.
  - [ ] Dedans : accès au **premier scanner** (scan de posture sécurité, URL + options + lancement) dans une sous-vue ou sous-page.
  - [ ] **Checkbox « Scanner uniquement cette page »** dans le formulaire : si cochée, pas de crawler (scan direct sur l’URL) ; si décochée, lancer le **crawler** (agent indépendant), réception du résultat au frontend, puis **étape de validation** (voir 7.3). Libellés clairs dans l’UI.
  - [ ] **Écran « Voici ce que le crawler a trouvé »** (quand crawler activé) : afficher la liste d’URLs ; permettre de supprimer des URLs, d’en ajouter manuellement ; bouton « Lancer le scan » sur la liste finale.
  - [ ] Possibilité d’ajouter plus tard d’autres types de scan (ex. scan actif, scan ciblé) dans la même rubrique.
- [ ] **Card « Gestion »** : renvoie vers un espace de gestion regroupant :
  - [ ] **Historique des scans** : liste des scans passés, filtres, détail, suppression.
  - [ ] **Évolution des failles** : tendances (évolution du score dans le temps, nombre de findings par sévérité, comparaison entre scans).
  - [ ] **Rapports et exports** : accès aux PDF, exports CSV/JSON si implémentés.
  - [ ] **Scans planifiés** : création, modification, pause des scans récurrents.
  - [ ] **Lien vers la gestion des clés API** : accès à la page « Clés API » (création, révocation, doc).
  - [ ] Autres éléments pertinents : résumé tableau de bord (nombre de scans ce mois, score moyen), alertes configurées, préférences de notification.
- [ ] **Card « Documentation »** : section sur la home du hub Scanner qui renvoie vers la documentation (scanners, API, etc.).
  - [ ] Liens vers une **page ou section doc** regroupant : doc du **scan de posture** (vérifications, crawling, interprétation des résultats), doc des **autres scanners** si présents, doc de l’**API publique** (endpoints, clés API, exemples curl, intégration CI/CD).
  - [ ] **Doc accessible depuis la page concernée** : la documentation d’un scanner en particulier (ex. scan de posture) doit aussi être disponible depuis la page de ce scanner (lien « Aide » ou « Documentation » sur la page `/scanner/analyses/posture`). De même, la doc de l’API doit être accessible depuis la page de gestion des clés API (lien « Documentation API »). Ainsi, l’utilisateur trouve la doc soit depuis le hub (section Documentation), soit depuis la page du sujet (scanner ou API).

#### Structure des routes (plusieurs pages)

- [ ] **Plusieurs pages obligatoires** : routes dédiées — `/scanner` (hub avec cards), `/scanner/analyses` ou `/scanner/analyses/posture` (premier scanner), `/scanner/gestion` (avec tabs ou sous-pages pour Historique, Évolution, Scans planifiés, Clés API). URLs claires, partageables, historique navigateur propre.
- [ ] **Convention** : `/scanner` = hub cards ; `/scanner/analyses` (ou `/scanner/analyses/posture`) = premier scanner ; `/scanner/gestion` = une seule page avec **tabs** (Historique | Évolution | Planifiés | Clés API) pour limiter le nombre de routes.

### 8.3 Header / navigation

- [ ] **Nav adaptée à l’état de connexion** : le header (barre de navigation) change selon que l’utilisateur est connecté ou non :
  - [ ] **Déconnecté** : liens type Accueil, Tarifs, Contact, Connexion / Inscription (pas d’entrée « Scanner » en tant que page hub réservée aux connectés, ou alors libellé du type « Découvrir le scanner » qui mène vers la landing avec l’input scan basique).
  - [ ] **Connecté** : ajout des entrées utiles (ex. Scanner [hub], Mon compte, Déconnexion) ; le lien « Scanner » mène vers le hub (page d’intro avec cards).
- [ ] **En mode Scanner (pages /scanner, /scanner/…)** : ne jamais afficher la nav en mode « déconnecté » pour ces URLs. Si l’utilisateur n’est pas connecté et atterrit sur une URL scanner (bookmark, lien direct), rediriger vers la connexion (ou la landing) au lieu d’afficher le hub avec un header déconnecté. Ainsi, dès qu’on est dans l’espace scanner, le header reflète toujours un utilisateur connecté (ou on n’a pas accès à la page).
- [ ] Cohérence : sur la landing, le header reste « déconnecté » (Accueil, Connexion, etc.) ; après connexion, le header bascule et inclut Scanner / Mon compte / Déconnexion.

### 8.4 Affichage du scanner : chargement et anomalies

**Objectif :** Lors du chargement ou de l’affichage des résultats du scan, ne pas utiliser le vert pour les points qui correspondent à une **anomalie détectée** ; indiquer clairement qu’**on a trouvé quelque chose** (alerte / attention), pour que l’utilisateur distingue immédiatement « vérification OK » vs « problème détecté ».

- [ ] **Réservoir le vert aux vérifications OK** : afficher en vert uniquement les points pour lesquels **aucune anomalie** n’a été trouvée (vérification passée).
- [ ] **Anomalies = « on a trouvé quelque chose »** : pour toute vérification qui remonte une anomalie, **ne pas** l’afficher comme un point « validé » (vert). Utiliser un traitement visuel dédié (icône, couleur, libellé du type « Anomalie détectée » / « Trouvé ») pour signaler qu’il y a un finding.
- [ ] **S’appliquer à toutes les anomalies sauf « info »** : ce comportement vaut pour tous les niveaux de sévérité d’anomalie (critique, haute, moyenne, basse). Le niveau **info** peut rester avec un traitement distinct (neutre ou informatif), sans être affiché comme « validé » en vert.
- [ ] Cohérence sur l’écran de chargement / progression et sur la page de résultats : même logique (vert = OK, pas d’anomalie ; autre traitement = quelque chose a été trouvé, pour toutes les anomalies hors info).

---

## 6) Mode asynchrone + queue

> **Contexte :** À réintégrer si les scans deviennent trop longs ou si les timeouts HTTP posent problème.

**Objectif :** Permettre des scans longs sans timeout : l’utilisateur lance un scan, reçoit immédiatement un `job_id`, puis consulte le statut et les résultats plus tard.

### 6.1 Choix technologique

- [ ] Choisir stack : SQS + worker Python **ou** Celery + Redis
- [ ] Documenter décision (pros/cons, coût, complexité)

### 6.2 Infrastructure queue

- [ ] Créer file SQS (ou Redis pour Celery)
- [ ] Configurer dead-letter queue (DLQ) pour échecs
- [ ] Timeout et retry policy (ex. 3 tentatives, backoff exponentiel)

### 6.3 Worker scan

- [ ] Worker dédié : consomme jobs de la queue, exécute le scan
- [ ] Réutiliser la logique existante (`scan_stream`, checks, normalisation)
- [ ] Stocker résultat en base (ex. PostgreSQL) avec `job_id`, `status`, `result`

### 6.4 API endpoints

- [ ] `POST /api/scan/async` : enqueue un job, retourne `job_id`
- [ ] `GET /api/scan/async/{job_id}` : statut du job (pending, running, completed, failed)
- [ ] `GET /api/scan/async/{job_id}/result` : résultat du scan (si completed)

### 6.5 Frontend

- [ ] Option : lancer scan en mode async si durée estimée > seuil
- [ ] Polling ou WebSocket pour afficher le statut
- [ ] Page résultats accessible via URL partageable (`/scan/{job_id}`)
