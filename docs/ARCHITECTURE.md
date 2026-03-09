# Architecture SecureOps

Ce document décrit l’architecture des services, le flux d’authentification et l’usage des bases de données.

## Vue d’ensemble

SecureOps est organisé en **microservices** derrière un **API Gateway** unique. Le frontend (Next.js) ne parle qu’au gateway ; le gateway authentifie les requêtes (JWT Cognito) et proxy vers les services backend.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                    Frontend (Next.js)                    │
                    │  Port 3000 • Cognito (Auth) • i18n fr/en • Tailwind     │
                    └───────────────────────────┬─────────────────────────────┘
                                                │
                                                │ HTTP (Bearer JWT pour API)
                                                ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                     API Gateway                         │
                    │  Port 8000 • Auth middleware • CORS • Proxy             │
                    │  Routes : /health, /admin/*, /user/*, /scan/*, /pdf/*   │
                    └───┬─────────┬─────────┬─────────┬─────────┬────────────┘
                        │         │         │         │         │
          ┌─────────────┘         │         │         │         └─────────────┐
          ▼                       ▼         ▼         ▼                        ▼
   ┌───────────────┐     ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐
   │ admin-service │     │ user-service  │ │ pdf-service   │ │ scan-service          │
   │ Port 8010     │     │ Port 8011     │ │ Port 8013     │ │ Port 8012             │
   │ PostgreSQL    │     │ PostgreSQL    │ │ (rapports PDF) │ │ (scan posture sécu)   │
   │ Alembic       │     │ Alembic       │ │ WeasyPrint    │ │                       │
   └───────┬───────┘     └──────┬───────┘ └───────────────┘ └───────────────────────┘
           │                    │
           └────────┬───────────┘
                    ▼
           ┌────────────────────┐
           │     PostgreSQL     │
           │  (PostGIS 15/17)   │
           │  template_db       │
           │  Port 5433 (host)  │
           └────────────────────┘
```

## Rôle des services

| Service | Port | Rôle | Base de données |
|--------|------|------|------------------|
| **gateway** | 8000 | Authentification JWT (Cognito), CORS, proxy vers les services. Ne stocke pas de données. | — |
| **admin-service** | 8010 | Administration : contacts, newsletter, emails, analytics, KPIs, alerting, gestion utilisateurs, upload d’images. | PostgreSQL (async), Alembic |
| **user-service** | 8011 | Utilisateurs : profil, préférences, abonnements, favoris, sécurité, confidentialité. | PostgreSQL, Alembic |
| **pdf-service** | 8013 | Génération de rapports PDF (WeasyPrint). Appelé par le scan-service pour l’export PDF ; pas de base de données. | — |
| **scan-service** | 8012 | Scanner de posture sécurité : TLS/HTTPS, headers, cookies, exposition fichiers, directory listing, robots.txt, fingerprinting. Score /100, findings normalisés. Export PDF via appel HTTP au pdf-service. | — |

Le **scan-service** expose `POST /api/scan` (SSE), `GET /api/scan/export/pdf` (proxy vers pdf-service) et `/api/health`. Protection SSRF, validation URL stricte, timeouts configurables.

Le **pdf-service** expose `POST /api/report/pdf` (body : payload scan + options lang/include_matrices) et `/api/health`. Optionnellement protégé par clé interne (`X-Internal-Api-Key`) si `PDF_SERVICE_INTERNAL_API_KEY` est définie.

## Routes du gateway

Le gateway expose :

- **`/health`** — Health check (public).
- **`/admin/*`** — Proxifié vers admin-service. Requiert **JWT + groupe Cognito `admin`** (sauf exceptions ci-dessous).
- **`/user/*`** — Proxifié vers user-service. Requiert **JWT** (utilisateur authentifié).
- **`/scan/*`** — Proxifié vers scan-service. `POST /scan/api/scan` est **public** (MVP) ; les autres routes requièrent **JWT**.
- **`/pdf/*`** — Proxifié vers pdf-service (génération de rapports PDF). Appelé en interne par le scan-service ; le gateway peut ajouter le header `X-Internal-Api-Key` si configuré.

Routes **publiques** (sans auth) :

- `GET /health`
- `GET /images/*`, `GET /admin/images/*` (accès aux images)
- `POST /api/contact` (formulaire de contact, protégé côté front par Turnstile)
- `POST /admin/api/analytics/ingest` (ingestion analytics depuis le front)
- `POST /scan/api/scan` (scanner de posture sécurité — MVP)
- `POST /user/api/user/init` (création/initialisation du compte utilisateur après première connexion)

**Exception lecture docs** (utilisateurs connectés, pas admin) : `GET /admin/api/docs` et `GET /admin/api/docs/*` — utilisateurs authentifiés peuvent lire la documentation (page Scanner → Documentation) sans être dans le groupe `admin`. Voir la note ci-dessous.

La configuration des URLs des services (Docker vs local) est dans `backend/gateway/config/settings.yml` (clés `services.docker` et `services.local`). Le mode est choisi via la variable d’environnement `IS_DOCKER`.

## Flux d’authentification

1. **Frontend** : l’utilisateur se connecte via **AWS Cognito** (Amplify UI : email/mot de passe ou Google OAuth).
2. **Frontend** : après connexion, le client récupère le **JWT** (idToken) via `fetchAuthSession()` et envoie les requêtes API avec l’en-tête `Authorization: Bearer <token>`.
3. **Gateway** : le middleware d’auth lit `Authorization`, appelle **common.common.jwt_verifier.verify_cognito_jwt(token)** (vérification JWKS Cognito, RS256, expiration, issuer, audience). Si la route est sous `/admin/*`, il vérifie en plus la présence du groupe Cognito `admin`.
4. **Gateway** : il transmet la requête au service backend concerné en repassant les headers (dont `Authorization`). Les services comme **user-service** peuvent à leur tour résoudre l’utilisateur (email depuis le JWT, puis `get_or_create_user` en base).

Les variables Cognito (User Pool ID, Client ID, région, domaine) sont configurées côté backend (gateway, user-service, admin-service) via les variables d’environnement décrites dans [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md).

## Bases de données

- **Une instance PostgreSQL** (image `postgis/postgis`) héberge la base **template_db**.
- **admin-service** et **user-service** utilisent cette même base avec des **schémas / tables distincts** (chaque service a son propre jeu de tables et ses migrations Alembic).
- Le **scan-service** n'utilise pas de base pour le MVP ; il peut être étendu pour persister des résultats si besoin.

Migrations :

- **admin-service** : `backend/admin-service/alembic/`, table de version `admin_alembic_version`.
- **user-service** : `backend/user-service/alembic/`, table de version `user_alembic_version`.

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
- Appels API via un client qui envoie le Bearer token (refresh sur 401).
- Pages : accueil, tarifs, contact, connexion, inscription, mot de passe oublié, confirmation, mon compte, admin (réservé aux utilisateurs du groupe `admin`), politique de confidentialité.

Pour plus de détails sur les pages et la config Amplify, voir [frontend/README.md](../frontend/README.md).

---

## ⚠️ Note — Documentation éditable (admin-service)

La **documentation des scanners** (scan frontend, crawler, etc.) est hébergée dans l’**admin-service** (`data/docs/`, router `doc_pages`), éditable via la Galerie admin et lisible par **tous les utilisateurs connectés** via `GET /admin/api/docs*`.

**Point d’attention** : cela implique des appels vers l’admin-service depuis des utilisateurs non-admin, ce qui brouille la frontière de responsabilité du service admin. Une approche plus rigoureuse consisterait à :

- héberger la doc du scan dans le **scan-service** (`/scan/api/docs/*`) ;
- héberger la doc du crawler dans le **crawl-service** (`/crawl/api/docs/*`).

Chaque service porterait sa propre doc, et la lecture par les users resterait sémantiquement cohérente. Pour l’instant, la solution centralisée dans l’admin est conservée par pragmatisme.
