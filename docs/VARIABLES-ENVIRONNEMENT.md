# Variables d’environnement

Référence des variables utilisées par le template (racine et frontend).

## Fichiers de configuration

- **Racine** : copier `.env.example` vers `.env`. Utilisé par `launch_dev.sh`, `docker-compose`, et les services backend (via `dotenv` ou injection Docker).
- **Frontend** : copier `frontend/.env.example` vers `frontend/.env.local`. Next.js charge automatiquement `.env.local` (et ne le commite pas).

---

## Racine (backend, Docker, Postgres)

| Variable | Obligatoire | Description | Exemple |
|----------|-------------|-------------|---------|
| `POSTGRES_USER` | Oui | Utilisateur PostgreSQL | `user` |
| `POSTGRES_PASSWORD` | Oui | Mot de passe PostgreSQL | `password` |
| `POSTGRES_DB` | Oui | Nom de la base | `template_db` |
| `DATABASE_URL` | Si hors Docker | URL de connexion synchrone (user-service, metier-*) | `postgresql://user:password@localhost:5433/template_db` |
| `ADMIN_DATABASE_URL` | Si hors Docker | URL async (admin-service, asyncpg) | `postgresql+asyncpg://user:password@localhost:5433/template_db` |
| `ADMIN_METRICS_API_KEY` | Recommandé | Clé pour l’endpoint métriques admin | `dev-admin-metrics-key` |
| `ADMIN_METRICS_USER_HASH_SECRET` | Optionnel | Secret pour pseudonymisation analytics | — |
| `COGNITO_REGION` | Pour auth | Région AWS Cognito | `eu-west-3` |
| `COGNITO_USER_POOL_ID` | Pour auth | User Pool ID Cognito | — |
| `COGNITO_CLIENT_ID` | Pour auth | Client ID de l’app Cognito | — |
| `TENANT_ID` | Optionnel (emails) | Microsoft Graph tenant | — |
| `CLIENT_ID` | Optionnel (emails) | App Azure / Graph | — |
| `CLIENT_SECRET` | Optionnel (emails) | Secret de l’app | — |
| `SENDER_EMAIL` | Optionnel (emails) | Email d’envoi | — |
| `NEXT_PUBLIC_GATEWAY_URL` | Optionnel racine | URL du gateway (pour doc / scripts) | `http://localhost:8000` |
| `FRONTEND_URL` | Optionnel | URL du frontend (callback, emails) | `http://localhost:3000` |
| `IS_DOCKER` | Auto (Docker) | `true` dans les conteneurs pour choisir les URLs des services | — |
| `DISABLE_AUTH_MIDDLEWARE` | Dev uniquement | Désactive l’auth au gateway si `true` | `false` |
| `IS_PROD` | Oui (scan-service) | Flag environnement pour le scan-service. Si `1`, `true` ou `yes` (valeur par défaut si non défini), les protections strictes sont activées : blocage localhost/127.0.0.1/::1 et IP privées, ports limités aux ports autorisés. Si `false`, localhost et les ports libres sont autorisés pour les tests locaux (ex. `bad_cache_server.py` sur 127.0.0.1:8001). | `false` en dev (forcé par `launch_dev.sh`), non défini ou `true` en prod |
| `PDF_SERVICE_URL` | scan-service | URL du pdf-service pour l’export PDF (scan-service appelle ce service en HTTP). | `http://localhost:8013` (dev), `http://pdf-service:8013` (Docker) |
| `PDF_SERVICE_INTERNAL_API_KEY` | Optionnel (prod) | Clé partagée pour les appels au pdf-service. Si définie : le **gateway** l’ajoute en header `X-Internal-Api-Key` lors du proxy vers `/pdf/*` ; le **scan-service** l’envoie lors de l’appel au pdf-service ; le **pdf-service** exige ce header. En dev (non définie), aucun contrôle. | En prod : une valeur secrète commune aux trois services |

En Docker, `DATABASE_URL` et `ADMIN_DATABASE_URL` sont construites à partir de `POSTGRES_*` dans le `docker-compose.yml`.

---

## Frontend (Next.js)

Toutes les variables exposées au navigateur doivent avoir le préfixe **`NEXT_PUBLIC_`**.

| Variable | Obligatoire | Description | Exemple |
|----------|-------------|-------------|---------|
| `NEXT_PUBLIC_GATEWAY_URL` | Oui | URL de l’API Gateway | `http://localhost:8000` (dev), `https://api.example.com` (prod) |
| `NEXT_PUBLIC_APP_URL` | Oui (SEO) | URL publique du site (canonicals, sitemap, OG) | `http://localhost:3000` (dev), `https://example.com` (prod) |
| `NEXT_PUBLIC_AWS_REGION` | Pour Cognito | Région Cognito | `eu-west-3` |
| `NEXT_PUBLIC_AWS_USER_POOL_ID` | Pour Cognito | User Pool ID | — |
| `NEXT_PUBLIC_AWS_CLIENT_ID` | Pour Cognito | Client ID | — |
| `NEXT_PUBLIC_IS_BETA_TEST` | Optionnel | Flag bêta | `true` / `false` |
| `NEXT_PUBLIC_IS_PROD` | Optionnel | Flag production | `false` (dev), `true` (prod) |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Optionnel | Clé site Cloudflare Turnstile (formulaire contact) | — |
| `NEXT_PUBLIC_TWITTER_SITE` | Optionnel | Twitter card `site` | — |
| `NEXT_PUBLIC_TWITTER_CREATOR` | Optionnel | Twitter card `creator` | — |
| `NEXT_PUBLIC_LOG_LEVEL` | Optionnel | Niveau de log client (debug, info, warn, error) | — |
| `NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL_URL` | Optionnel | URL du portail client Stripe (abonnements) | — |

Le frontend peut aussi accepter des alias (ex. `NEXT_PUBLIC_REGION` au lieu de `NEXT_PUBLIC_AWS_REGION`) selon `frontend/src/config/aws-exports.ts`.

---

## Résumé par environnement

- **Dev local (launch_dev.sh)** : `.env` à la racine avec au minimum `POSTGRES_*` ; optionnellement Cognito et autres. Frontend : `frontend/.env.local` avec `NEXT_PUBLIC_GATEWAY_URL`, `NEXT_PUBLIC_APP_URL` et les `NEXT_PUBLIC_AWS_*` si vous testez l’auth.
- **Docker Compose** : même `.env` à la racine ; le frontend en conteneur reçoit `NEXT_PUBLIC_GATEWAY_URL=http://gateway:8000` depuis le compose. Pour que le navigateur accède au gateway, utiliser l’URL hôte (ex. `http://localhost:8000`) dans `.env` ou dans un fichier d’env du frontend monté en prod.
- **Production** : ne pas utiliser de fichier `.env` versionné ; définir toutes les variables (et secrets) dans le plateau de déploiement. En prod, `NEXT_PUBLIC_APP_URL` et `NEXT_PUBLIC_GATEWAY_URL` doivent pointer vers les URLs HTTPS finales.
