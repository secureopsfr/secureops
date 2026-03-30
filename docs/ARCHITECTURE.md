# Architecture SecureOps

Ce document décrit l’architecture des services, le flux d’authentification et l’usage des bases de données.

## Vue d’ensemble

SecureOps est organisé en **microservices** derrière un **API Gateway** unique. Le frontend (Next.js) ne parle qu’au gateway ; le gateway authentifie les requêtes (JWT Cognito ou clé API) et proxy vers les services backend.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Frontend (Next.js)                    │
                    │  Port 3000 • Cognito (Auth) • i18n fr/en • Tailwind     │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
                                                │ HTTP (Bearer JWT ou X-API-Key)
                                                ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                     API Gateway                         │
                    │  Port 8000 • Auth JWT + clés API • CORS • Proxy        │
                    │  Routes : /health, /admin/*, /user/*, /scan/*, /crawl/*… │
                    └───┬─────────┬─────────┬─────────┬─────────┬────────────┘
                        │         │         │         │         │
          ┌─────────────┘         │         │         │         └─────────────┐
          ▼                       ▼         ▼         ▼                        ▼
   ┌───────────────┐     ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐
   │ admin-service │     │ user-service  │ │ pdf-service   │ │ scan-service (API)    │
   │ Port 8010     │     │ Port 8011     │ │ Port 8013     │ │ Port 8012             │
   │ PostgreSQL    │     │ PostgreSQL    │ │ WeasyPrint    │ │ REST : création /     │
   │ Alembic       │     │ Alembic       │ │               │ │ statut / résultat job │
   └───────┬───────┘     └──────┬───────┘ └───────────────┘ └───────────┬───────────┘
           │                    │                                       │
           │                    │                                       ▼
           │                    │                            ┌───────────────────────┐
           │                    │                            │ scan-worker           │
           │                    │                            │ pas de port HTTP      │
           │                    │                            │ poll + exécution jobs │
           │                    │                            └───────────┬───────────┘
           │                    │                                        │
           └────────────────────┴────────────────────────────────────────┘
                                │
                                ▼
           ┌────────────────────┐  ┌───────────────────────┐
           │     PostgreSQL     │  │ crawl-service (API)   │
           │  (PostGIS 15/17)   │  │ Port 8014             │
           │  template_db       │  │ REST : création /     │
           │  tables file       │  │ statut / résultat job │
           │  d’attente async   │  └───────────┬───────────┘
           │  Port 5433 (host)  │              │
           └─────────┬──────────┘              ▼
                     │                ┌───────────────────────┐
                     │                │ crawl-worker          │
                     │                │ pas de port HTTP      │
                     │                │ poll + exécution jobs │
                     │                └───────────┬───────────┘
                     │                            │
                     └────────────────────────────┘
```

Les jobs asynchrones ne passent pas par une file Redis séparée : l’**API** enregistre une ligne en base (`scan_async_jobs`, `crawl_async_jobs`, etc.), et le **worker** dédié réclame puis exécute le travail (boucle de polling). Sous Docker Compose, **scan-worker** et **crawl-worker** sont des **conteneurs distincts**, même image Docker que l’API du service, avec une commande du type `python -m app.workers.async_scan_worker` / `async_crawl_worker`.

## Rôle des services

| Service | Port | Rôle | Base de données |
|--------|------|------|------------------|
| **gateway** | 8000 | Authentification JWT (Cognito) ou clé API (X-API-Key / Bearer), CORS, proxy vers les services. Ne stocke pas de données. | — |
| **admin-service** | 8010 | Administration : contacts, newsletter, emails, analytics, KPIs, alerting, gestion utilisateurs, upload d’images. | PostgreSQL (async), Alembic |
| **user-service** | 8011 | Utilisateurs : profil, préférences, abonnements, favoris, clés API, sécurité, confidentialité. Table `api_keys` pour l’API publique. | PostgreSQL, Alembic |
| **pdf-service** | 8013 | Génération de rapports PDF (WeasyPrint). Appelé par le scan-service pour l’export PDF ; pas de base de données. | — |
| **scan-service** | 8012 | Scanner de posture sécurité : TLS/HTTPS, headers, cookies, exposition fichiers, directory listing, robots.txt, fingerprinting. Score /100, findings normalisés. **Appels HTTP internes au gateway** (`GATEWAY_URL`, ex. `http://gateway:8000` en Docker) pour persister l’historique (`POST /user/api/scans/history`) et pour l’export PDF (lecture du détail scan puis `POST` au pdf-service). **API** des jobs async (création, progression, résultat). | PostgreSQL, Alembic |
| **scan-worker** | — | Processus / conteneur séparé : consomme la file **`scan_async_jobs`** en base (claim, exécution du scan, mise à jour statut / résultat). Pas d’exposition HTTP. | PostgreSQL (même instance) |
| **crawl-service** | 8014 | Crawler HTTP/SPA (html/playwright/both). **API** des jobs async avec progression persistée. | PostgreSQL, Alembic |
| **crawl-worker** | — | Processus / conteneur séparé : consomme **`crawl_async_jobs`** en base. Pas d’exposition HTTP. | PostgreSQL (même instance) |

Le **scan-service** expose `POST /api/scan/async`, `GET /api/scan/async/{job_id}`, `GET /api/scan/async/{job_id}/result`, `GET /api/scan/export/pdf` et `/api/health`. Protection SSRF, validation URL stricte, timeouts configurables. En **Docker**, définir **`GATEWAY_URL=http://gateway:8000`** sur le scan-service : sans cela, `localhost:8000` pointe vers le conteneur lui-même et les appels historique / PDF échouent (`ConnectError`).

Le **crawl-service** expose `POST /api/crawl/async`, `GET /api/crawl/async/{job_id}`, `GET /api/crawl/async/{job_id}/result` et `/api/health`.

Le **pdf-service** expose `POST /api/report/pdf` (body : payload scan + options lang/include_matrices) et `/api/health`. Optionnellement protégé par clé interne (`X-Internal-Api-Key`) si `PDF_SERVICE_INTERNAL_API_KEY` est définie.

## Routes du gateway

Le gateway expose :

- **`/health`** — Health check (public).
- **`/admin/*`** — Proxifié vers admin-service. Requiert **JWT + groupe Cognito `admin`** (sauf exceptions ci-dessous). Les clés API ne donnent **pas** accès aux routes admin.
- **`/user/*`** — Proxifié vers user-service. Requiert **JWT** (utilisateur authentifié). La gestion des clés (`POST/GET/DELETE /user/api/keys`) est réservée au JWT (interface web).
- **`/scan/*`** — Proxifié vers scan-service. `POST /scan/api/scan/async` est public pour `scan_type=frontend` (anonyme via `X-Job-Token`) et optionnellement authentifié. Les lectures status/result sont contrôlées par ownership user ou `X-Job-Token`.
- **`/crawl/*`** — Proxifié vers crawl-service. `POST /crawl/api/crawl/async` est public pour `scan_type=frontend` (anonyme via `X-Job-Token`) et optionnellement authentifié. Les lectures status/result sont contrôlées par ownership user ou `X-Job-Token`.
- **`/pdf/*`** — Proxifié vers pdf-service (génération de rapports PDF). Appelé en interne par le scan-service ; le gateway peut ajouter le header `X-Internal-Api-Key` si configuré.

**Authentification** : une requête peut être authentifiée soit par **JWT** (header `Authorization: Bearer <token>`), soit par **clé API** (`X-API-Key: sk_...` ou `Authorization: Bearer sk_...` si le token n’est pas un JWT). Le gateway appelle le user-service (`POST /api/internal/keys/verify`) pour valider les clés API. Voir [API-PUBLIQUE.md](API-PUBLIQUE.md) pour le détail.

Routes **publiques** (sans auth) :

- `GET /health`
- `GET /images/*`, `GET /admin/images/*` (accès aux images)
- `POST /api/contact` (formulaire de contact, protégé côté front par Turnstile)
- `POST /admin/api/analytics/ingest` (ingestion analytics depuis le front)
- `POST /scan/api/scan/async` (scan async frontend possible en anonyme)
- `POST /crawl/api/crawl/async` (crawl async frontend possible en anonyme)
- `POST /user/api/user/init` (création/initialisation du compte utilisateur après première connexion)

**Exception lecture docs** (utilisateurs connectés, pas admin) : `GET /admin/api/docs` et `GET /admin/api/docs/*` — utilisateurs authentifiés peuvent lire la documentation (page Scanner → Documentation) sans être dans le groupe `admin`. Voir la note ci-dessous.

La configuration des URLs des services (Docker vs local) est dans `backend/gateway/config/settings.yml` (clés `services.docker` et `services.local`). Le mode est choisi via la variable d’environnement `IS_DOCKER`.

**CORS** : les origines autorisées (navigateur → gateway) sont dans `backend/gateway/config/settings.yml` (`cors.allow_origins`, optionnel `allow_origin_regex` pour les URL Amplify `*.amplifyapp.com`). Avec `allow_credentials: true`, chaque origine (schéma + host + port) doit être listée ou couverte par la regex. Voir [DEPLOIEMENT-AWS.md](DEPLOIEMENT-AWS.md) § CORS.

## Flux d’authentification

1. **Frontend** : l’utilisateur se connecte via **AWS Cognito** (Amplify : email / mot de passe, etc.).
2. **Frontend** : après connexion, `fetchAuthSession()` fournit **access** et **id** tokens. Le client API (`getBearerToken`) envoie en général l’**access token** en `Authorization: Bearer`, avec repli sur l’**id token** si besoin. Les deux se vérifient avec la même JWKS / issuer Cognito (l’id token porte en plus `aud` = client id).
3. **Gateway** : le middleware d’auth tente d’abord l’auth par clé API (voir ci-dessous). Sinon, il lit `Authorization` et appelle **common.jwt_verifier.verify_cognito_jwt(token)** (JWKS, RS256, expiration, issuer, audience si le token porte `aud`). Si la route est sous `/admin/*`, il exige le groupe Cognito **`admin`** dans les claims (`cognito:groups`).
4. **Page admin (Next.js)** : `AdminGuard` contrôle le groupe `admin` sur le **access token** ; si `cognito:groups` n’y figure pas (selon la config du User Pool), l’utilisateur est renvoyé vers l’accueil **sans erreur visible**. Même contrainte côté API si seul un access token sans groupes est envoyé. Selon Cognito, inclure les groupes sur l’access token, ou faire transiter l’**id token** pour les appels admin et aligner `AdminGuard` sur les deux jetons.
5. **Gateway** : il transmet la requête au service backend concerné en repassant les headers (dont `Authorization`). Les services comme **user-service** résolvent l’utilisateur (claims JWT + éventuellement **Cognito AdminGetUser** si l’email est absent du token).

### user-service et AWS sur EC2

Pour **AdminGetUser** (email manquant du JWT), boto3 utilise soit le **rôle IAM de l’instance**, soit `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` si les deux sont définis dans l’environnement du conteneur. Des clés d’un **autre compte AWS** que le User Pool provoquent une erreur du type *User pool does not exist* alors que le pool est correct. Sur EC2 avec rôle dédié, le **docker-compose** du dépôt **n’injecte pas** ces clés dans le user-service pour forcer l’usage du rôle. Voir [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md).

### Auth clé API (intégrations, CI/CD)

1. Le client envoie `X-API-Key: sk_...` ou `Authorization: Bearer sk_...` (si le token n'est pas un JWT).
2. **Gateway** : le middleware appelle le user-service `POST /api/internal/keys/verify` avec la clé en clair. Protection par `X-Internal-Api-Key` si `USER_SERVICE_INTERNAL_API_KEY` est définie.
3. Le user-service vérifie le hash, met à jour `last_used_at` et retourne `user_id`, `email`, `sub`. Le gateway stocke `request.state.user` avec `auth_type: "api_key"`.
4. Pour les appels proxy, le gateway transmet la clé en `Authorization: Bearer <clé>`.

Les variables Cognito (User Pool ID, Client ID, région, domaine) sont configurées côté backend (gateway, user-service, admin-service) via les variables d’environnement décrites dans [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md). Pour les clés API : [API-PUBLIQUE.md](API-PUBLIQUE.md).

## Bases de données

- **Une instance PostgreSQL** (image `postgis/postgis`) héberge la base **template_db**.
- **admin-service**, **user-service**, **scan-service** et **crawl-service** utilisent cette même instance avec des tables et migrations séparées par service.
- Le **scan-service** persiste ses jobs async dans `scan_async_jobs`.
- Le **crawl-service** persiste ses jobs async dans `crawl_async_jobs`.

Migrations :

- **admin-service** : `backend/admin-service/alembic/`, table de version `admin_alembic_version`.
- **user-service** : `backend/user-service/alembic/`, table de version `user_alembic_version`.
- **scan-service** : `backend/scan-service/alembic/`, table de version `scan_alembic_version`.
- **crawl-service** : `backend/crawl-service/alembic/`, table de version `crawl_alembic_version`.

Au démarrage, chaque service applique ses migrations (voir [DEPLOIEMENT.md](DEPLOIEMENT.md)).

## Package commun (backend)

Le répertoire **backend/common** est un package Python installé en mode éditable (`pip install -e ../common`) par chaque service. Il fournit notamment :

- **config_base** : chargement de la config (YAML + env).
- **jwt_verifier** : vérification des JWT Cognito (JWKS, RS256).
- **cognito** : constantes Cognito (CLIENT_ID, ISSUER, JWKS_URL).
- **async_database** : connexion async SQLAlchemy (AsyncDatabase).
- **logging_config** : configuration des logs.
- **middleware** : CorrelationIdMiddleware (traçabilité).
- **error_handlers** : handlers d’exceptions HTTP communs (enregistrés dans chaque `main.py`).
- **health** : helpers pour les endpoints de health.
- **crud**, **schemas**, **datetime_utils** : utilitaires partagés.

## Frontend

- **Next.js 16** avec App Router, **i18n** (fr/en) et slugs localisés (ex. `/en/pricing` → route interne `/tarifs`).
- **AWS Amplify** (Cognito) pour l’auth ; formulaire de contact protégé par **Cloudflare Turnstile**.
- **Tailwind CSS** avec thème clair/sombre et variables CSS (design system).
- Appels API via un client qui envoie le Bearer (access token en priorité, repli sur id token ; refresh sur 401).
- Pages : accueil, tarifs, contact, connexion, inscription, mot de passe oublié, confirmation, mon compte, admin (réservé aux utilisateurs du groupe `admin`), politique de confidentialité. Section **Scanner** : hub, scan, historique, clés API (`/scanner/cles-api`), documentation API publique (`/scanner/docs/api`).

Pour plus de détails sur les pages et la config Amplify, voir [frontend/README.md](../frontend/README.md).

---

## ⚠️ Note — Documentation éditable (admin-service)

La **documentation des scanners** (scan frontend, crawler, etc.) est hébergée dans l’**admin-service** (`data/docs/`, router `doc_pages`), éditable via la Galerie admin et lisible par **tous les utilisateurs connectés** via `GET /admin/api/docs*`.

**Point d’attention** : cela implique des appels vers l’admin-service depuis des utilisateurs non-admin, ce qui brouille la frontière de responsabilité du service admin. Une approche plus rigoureuse consisterait à :

- héberger la doc du scan dans le **scan-service** (`/scan/api/docs/*`) ;
- héberger la doc du crawler dans le **crawl-service** (`/crawl/api/docs/*`).

Chaque service porterait sa propre doc, et la lecture par les users resterait sémantiquement cohérente. Pour l’instant, la solution centralisée dans l’admin est conservée par pragmatisme.
