# Déploiement et opérations

Ce document décrit comment déployer la stack, gérer les migrations et surveiller les services.

## Variables d’environnement

Avant tout déploiement, configurer les variables d’environnement. Référence complète : [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md).

En résumé :

- **Racine / backend** : `.env` (copié depuis `.env.example`) — Postgres, `DATABASE_URL` / `ADMIN_DATABASE_URL`, Cognito, `ADMIN_METRICS_API_KEY`, Microsoft Graph (emails), URLs frontend.
- **Frontend** : `frontend/.env.local` (copié depuis `frontend/.env.example`) — `NEXT_PUBLIC_GATEWAY_URL`, `NEXT_PUBLIC_APP_URL`, variables Cognito (`NEXT_PUBLIC_AWS_*`), optionnellement Turnstile, Mapbox.

En production, ne jamais commiter de secrets ; utiliser les mécanismes du plateau (secrets, variables d’environnement du runtime).

## Build et exécution avec Docker

### Volume PostgreSQL

Le `docker-compose.yml` utilise un volume nommé **pgdata** avec `external: true`. Il doit exister avant le premier `docker compose up` :

```bash
docker volume create pgdata
```

### Lancer la stack

```bash
docker compose up -d --build
```

- Les images sont construites à partir des `Dockerfile` dans `backend/` (gateway, admin-service, user-service, scan-service, pdf-service) et `frontend/`.
- Les variables du fichier `.env` à la racine sont injectées dans les conteneurs (voir `docker-compose.yml`).
- Le frontend reçoit notamment `NEXT_PUBLIC_GATEWAY_URL=http://gateway:8000` pour appeler le gateway depuis le navigateur ; en production, adapter cette URL (domaine public du gateway).

### Arrêt et données

```bash
docker compose down
```

Les données PostgreSQL restent dans le volume `pgdata`. Pour tout supprimer (conteneurs + volumes) :

```bash
docker compose down -v
```

Le volume `pgdata` est déclaré `external: true`, donc `-v` ne le supprime pas ; pour le supprimer manuellement : `docker volume rm pgdata` (à faire uniquement si vous voulez repartir de zéro).

## Migrations Alembic

Les services **admin-service** et **user-service** appliquent leurs migrations au démarrage (dans le code d’initialisation de l’app). En environnement contrôlé (CI, déploiement manuel), on peut aussi les lancer explicitement.

### Admin-service

```bash
cd backend/admin-service
python -m venv venv  # si besoin
. venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -e ../common -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/template_db"
alembic upgrade head
```

### User-service

```bash
cd backend/user-service
. venv/bin/activate
export DATABASE_URL="postgresql://user:password@localhost:5433/template_db"
alembic upgrade head
```

En Docker, les variables sont déjà définies dans le `docker-compose.yml` ; les migrations sont en général exécutées au démarrage du processus Python. Si vous souhaitez un job dédié (ex. init container), appeler la même commande `alembic upgrade head` dans le conteneur du service concerné.

### Créer une nouvelle migration

```bash
cd backend/admin-service
alembic revision -m "description_courte"
# Éditer le fichier généré dans alembic/versions/
alembic upgrade head
```

Idem pour `backend/user-service`.

## Healthchecks

Chaque service expose un endpoint de santé utilisé par Docker et par le gateway :

| Service        | Endpoint santé        |
|----------------|------------------------|
| Gateway        | `GET http://gateway:8000/health` |
| Admin-service  | `GET http://admin-service:8010/api/health` |
| User-service   | `GET http://user-service:8011/api/health` |
| Scan-service   | `GET http://scan-service:8012/api/health` |
| Pdf-service    | `GET http://pdf-service:8013/api/health` |

Le `docker-compose.yml` définit des `healthcheck` et des `depends_on` avec `condition: service_healthy` pour que le gateway ne démarre qu’une fois les services et Postgres prêts.

En production, configurer un load balancer ou un outil de monitoring pour interroger ces URLs et alerter en cas d’échec.

## Déploiement du frontend (build Next.js)

En production, le frontend est en général servi après un build statique/SSR :

```bash
cd frontend
npm ci
npm run build
npm run start
```

Ou utilisation d’une image Docker construite à partir du `Dockerfile` du frontend (build + serve). Les variables `NEXT_PUBLIC_*` doivent être définies **au moment du build** pour être inlinées dans le bundle.

Sur une plateforme (Vercel, Netlify, etc.), renseigner les variables d’environnement dans le tableau de bord et lancer le build depuis la racine du frontend.

## Bonnes pratiques

- **Secrets** : ne jamais les mettre dans le code ni dans des fichiers versionnés. Utiliser des secrets du CI/CD et du runtime.
- **CORS** : en production, restreindre `cors.allow_origins` dans `backend/gateway/config/settings.yml` (ou via la config chargée depuis l’env) aux domaines du frontend.
- **HTTPS** : exposer le gateway et le frontend en HTTPS (reverse proxy, TLS).
- **Logs** : les services utilisent le logging Python standard et le `CorrelationIdMiddleware` ; en production, envoyer les logs vers un agrégateur (CloudWatch, Datadog, etc.) pour tracer les requêtes entre services.
- **Migrations** : toujours tester les migrations en staging avant la prod ; faire des sauvegardes de la base avant `alembic upgrade head` en production.

## Dépannage

- **Gateway 502/504** : vérifier que les services backend sont bien démarrés et que les URLs dans `gateway/config/settings.yml` (ou la config chargée) correspondent au mode (Docker vs local).
- **401 sur les API** : vérifier que le frontend envoie bien un JWT valide (Cognito) et que les variables Cognito côté backend (gateway) sont correctes (région, User Pool ID, Client ID).
- **Erreurs de migration** : vérifier que `DATABASE_URL` (ou `ADMIN_DATABASE_URL` pour admin en asyncpg) pointe vers la bonne base et que l’utilisateur a les droits CREATE/ALTER.
