# Audit SecureOps (backend + frontend)

Analyse détaillée des manques et améliorations recommandées, **par ordre de priorité**.

> **Note :** Certains points (ex. documentation) ont été mis à jour depuis la création de cet audit. Voir [README.md](README.md) et [ROADMAP-MVP-0.1.0.md](ROADMAP-MVP-0.1.0.md) pour l'état actuel.

---

## Priorité 1 — Critique (sécurité, qualité, livraison)

### 1.1 Tests absents

- **Backend**
  - `pytest.ini` à la racine définit `testpaths = tests/unit, tests/integration, tests/e2e` mais **aucun répertoire `tests/`** n’existe (ni à la racine ni dans les services).
  - Aucun fichier `test_*.py` ou `*_test.py` dans le backend.
  - **Action :** Créer une arborescence `tests/` (unit / integration / e2e) par service ou partagée, ajouter des tests unitaires sur les routes critiques (auth, user, admin), des tests d’intégration sur la base et le gateway, et exécuter `pytest` dans la CI.

- **Frontend**
  - Aucun runner de tests (Jest, Vitest) dans `package.json`, pas de script `test`, pas de dépendances de test.
  - **Action :** Introduire Vitest (ou Jest) + React Testing Library, ajouter un script `npm run test`, couvrir au minimum les composants critiques (auth, formulaires, appels API) et les faire tourner en CI.

### 1.2 Rate limiting non implémenté

- La doc et les commentaires (ex. `gateway/app/middleware.py`, `admin-service/app/routers/analytics.py`) indiquent que le rate limiting est prévu « au niveau du reverse proxy / gateway », mais **aucun rate limiting n’est en place** dans le gateway ni dans les services.
- Les endpoints publics (`/api/contact`, `POST /admin/api/analytics/ingest`, `POST /scan/api/scan`) sont donc exposés aux abus (spam, surcharge).
- **Action :** Ajouter un rate limiter au gateway (ex. `slowapi` ou middleware custom avec Redis/in-memory) pour les routes publiques et/ou par IP, et documenter la politique (ex. 10 req/min par IP pour `/scan/api/scan`, 100 req/min pour `/api/contact`, 50 req/min pour analytics ingest).

### 1.3 CI sans exécution des tests

- Le workflow `.github/workflows/ci.yml` lance la stack avec `docker-compose.ci.yml`, fait le lint Python (black, isort, flake8) et le lint JS (ESLint), mais **ne lance aucun test** (ni backend ni frontend).
- **Action :** Après mise en place des tests (1.1), ajouter un job CI qui exécute `pytest` pour le backend et `npm run test` pour le frontend (et optionnellement un build Next.js `npm run build` pour détecter les erreurs de build).

### 1.4 Page d’erreur globale et erreur 500

- **Frontend :** Il existe `app/not-found.tsx` (404) et un composant `ErrorBoundary.tsx`, mais **pas de `error.tsx`** (erreur segment) ni de **`global-error.tsx`** (erreur racine) dans l’App Router.
- En cas d’erreur non gérée (500, crash React), l’utilisateur peut voir l’UI par défaut de Next.js au lieu d’une page cohérente avec le template.
- **Action :** Ajouter `app/[locale]/error.tsx` et `app/global-error.tsx` avec un message clair et un lien « Retour à l’accueil », en restant accessible (i18n si possible pour global-error).

---

## Priorité 2 — Haute (maintenabilité, opérations, onboarding)

### 2.1 Documentation projet

- **Fait :** README à la racine, ARCHITECTURE.md, DEPLOIEMENT.md, VARIABLES-ENVIRONNEMENT.md, ROADMAP-MVP-0.1.0.md, ROADMAP-MVP-0.2.0.md, CHANGELOG.md, docs de vérifications (TLS, headers, cookies, etc.).
- **À compléter :** Mettre à jour régulièrement la doc lors des évolutions ; ajouter un runbook opérationnel si besoin.

### 2.2 Makefile ou scripts de référence

- Aucun **Makefile** à la racine pour standardiser les commandes (lint, test, build, migrations, démarrage stack).
- Les développeurs s’appuient sur `launch_dev.sh` et des commandes docker-compose manuelles.
- **Action :** Ajouter un `Makefile` (ou un `package.json` racine avec scripts) avec des cibles du type : `up`, `down`, `lint`, `test`, `test-backend`, `test-frontend`, `migrate-admin`, `migrate-user`, `build-frontend`. Documenter ces cibles dans le README.

### 2.3 Volume Docker `pgdata` en `external: true`

- Dans `docker-compose.yml`, le volume **`pgdata`** est déclaré avec **`external: true`**. Si le volume n’est pas créé avant le premier `docker compose up`, le démarrage échoue.
- **Action :** Documenter dans le README ou dans `docs/` la nécessité de faire `docker volume create pgdata` (ou équivalent) avant la première utilisation ; ou proposer un compose de dev où `pgdata` n’est pas external pour simplifier le premier run.

### 2.4 Pas de build frontend en CI

- La CI ne fait pas de **build Next.js** (`npm run build`). Les erreurs de build (imports manquants, erreurs TypeScript bloquantes) ne sont détectées qu’en local ou en déploiement.
- **Action :** Ajouter une étape « Build frontend » dans la CI (après lint) pour exécuter `npm run build` dans le conteneur ou en local avec les variables d’environnement nécessaires (ex. celles de `.env.example`).

---

## Priorité 3 — Moyenne (robustesse, observabilité, cohérence)

### 3.1 Observabilité et monitoring

- Aucune intégration explicite de **métriques** (Prometheus, StatsD) ou de **tracing** (OpenTelemetry, X-Ray) dans le gateway ou les services.
- Les healthchecks Docker sont en place ; les logs sont gérés via `common.logging_config` et le **CorrelationIdMiddleware**, mais il n’y a pas de tableau de bord ou d’alertes sur les performances ou les erreurs.
- **Action :** Documenter la stratégie de monitoring (logs, métriques, traces) et, si pertinent, ajouter un endpoint `/metrics` (Prometheus) au gateway et une page ou doc pour les alertes (admin-service a déjà des alertes métier ; les lier à un runbook dans `docs/`).

### 3.2 Vérification des dépendances (audit)

- Aucune étape **`npm audit`** (frontend) ou **`pip audit`** / **`safety`** (backend) en CI pour détecter les vulnérabilités connues.
- **Action :** Ajouter en CI (ou en pre-commit) une étape d’audit des dépendances et documenter la procédure de mise à jour des paquets vulnérables.

### 3.3 Not-found et locale

- La page **`app/not-found.tsx`** propose un lien « Retour à l’accueil » codé en dur vers **`/fr`**. En environnement multilingue, il serait préférable de renvoyer vers la locale courante ou la page d’accueil par défaut.
- **Action :** Utiliser la locale détectée (middleware, cookie ou en-tête) pour générer le lien d’accueil (ex. `/${locale}`) ou rediriger vers la home sans forcer `fr`.

### 3.4 Service scan (scan-service)

- Le service **scan-service** expose un health check et une config ; la logique de scan (posture sécurité) est à implémenter selon la roadmap MVP.
- **Action :** Étendre le service avec les endpoints et la logique décrits dans `docs/ROADMAP-MVP.md`.

---

## Priorité 4 — Basse (confort, bonnes pratiques)

### 4.1 Pre-commit sans exécution des tests

- Le **pre-commit** configure black, isort, flake8 (Python) et ESLint, Prettier (frontend), mais **ne lance pas les tests**. Les développeurs peuvent committer du code qui casse les tests.
- **Action :** Une fois les tests en place (1.1), ajouter optionnellement un hook pre-commit pour lancer les tests rapides (ex. tests unitaires uniquement) ou rappeler dans la doc de lancer `make test` avant push.

### 4.2 Changelog et versioning

- Aucun **CHANGELOG.md** (ou équivalent) pour décrire les changements entre versions du template.
- **Action :** Ajouter un `CHANGELOG.md` à la racine (ou dans `docs/`) et y documenter les évolutions majeures (sécurité, nouvelles features, breaking changes). Optionnel : taguer les releases (Git tags) et les lier au changelog.

### 4.3 Fichier `.env.example` racine vs frontend

- Il existe un **`.env.example`** à la racine et un **`frontend/.env.example`**. Les variables frontend sont partiellement dupliquées. Ce n’est pas bloquant mais peut créer des confusions.
- **Action :** Documenter dans le README ou dans `docs/` quelle env utiliser où (racine pour docker-compose / backend, frontend pour Next.js) et éventuellement un seul `.env.example` à la racine avec des sections clairement séparées (Backend / Frontend / DB).

### 4.4 Contributeurs et licence

- Pas de **CONTRIBUTING.md** ni de **LICENSE** visible à la racine. Pour un template réutilisable, une licence claire et des consignes de contribution aident les contributeurs.
- **Action :** Ajouter une licence (MIT, Apache 2.0, etc.) et un court CONTRIBUTING.md (comment lancer le projet, linter, tests, format des PR).

---

## Synthèse des actions par priorité

| Priorité | Thème              | Actions principales |
|----------|--------------------|----------------------|
| **1**    | Critique           | Tests backend + frontend ; rate limiting gateway ; CI avec tests ; `error.tsx` + `global-error.tsx` |
| **2**    | Haute              | README racine + docs (architecture, déploiement) ; Makefile ; doc volume `pgdata` ; build frontend en CI |
| **3**    | Moyenne            | Stratégie monitoring ; audit dépendances ; not-found avec locale ; doc services métier stubs |
| **4**    | Basse              | Pre-commit + tests (optionnel) ; CHANGELOG ; clarification .env ; CONTRIBUTING + LICENSE |

---

## Points déjà bien couverts (à conserver)

- **Auth :** Cognito + JWT (gateway + user-service), middleware d’auth et groupe admin.
- **Sécurité frontend :** Headers CSP, X-Frame-Options, HSTS, etc. dans `next.config.ts`.
- **Base de données :** PostgreSQL + PostGIS ; Alembic pour admin-service et user-service ; healthchecks.
- **i18n :** Locales (fr/en), sitemap, robots.txt, slugs localisés.
- **Qualité de code :** Black, isort, flake8 (backend) ; ESLint, Prettier (frontend) ; pre-commit.
- **Stack :** Docker Compose, gateway avec proxy et CORS, séparation nette des services.

Ce document peut servir de feuille de route pour rendre le template prêt pour la production et l’utilisation en équipe.
