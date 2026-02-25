# Template Fullstack Immosphere

Template fullstack (backend Python/FastAPI + frontend Next.js) avec authentification Cognito, gateway API, services métier et base PostgreSQL. Utilisable comme base pour des applications SaaS (cybersécurité, gestion, etc.).

## Prérequis

- **Python** 3.11+
- **Node.js** 18+ (LTS recommandé)
- **Docker** et **Docker Compose** (pour PostgreSQL et/ou stack complète)
- **Git**

## Démarrage rapide

### 1. Cloner et configurer l’environnement

```bash
git clone <url-du-repo> .
cp .env.example .env
# Éditer .env et renseigner au minimum POSTGRES_*, puis optionnellement Cognito, etc.
```

Pour le **frontend** (Cognito, URL du gateway) :

```bash
cp frontend/.env.example frontend/.env.local
# Renseigner NEXT_PUBLIC_GATEWAY_URL, NEXT_PUBLIC_AWS_*, NEXT_PUBLIC_APP_URL
```

Voir [docs/VARIABLES-ENVIRONNEMENT.md](docs/VARIABLES-ENVIRONNEMENT.md) pour la liste des variables.

### 2. Démarrer la stack

**Option A — Script de dev (Linux/macOS, PostgreSQL dans Docker, reste en local)**

```bash
# Crée le volume pgdata et lance Postgres si besoin, puis tous les services en arrière-plan
./launch_dev.sh
```

Les logs sont dans `logs/`. Arrêt : `Ctrl+C` ou `pkill -f uvicorn; pkill -f npm`.

> **Si admin-service ou user-service affichent « Impossible de se connecter à la base »** : PostgreSQL n’est pas démarré. Soit relancez `./launch_dev.sh` (il démarre Postgres puis attend qu’il soit prêt), soit démarrez uniquement la base : `docker start postgres` (après un premier `./launch_dev.sh` ou `docker volume create pgdata && docker run -d --name postgres -p 5433:5432 -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=template_db -v pgdata:/var/lib/postgresql/data postgis/postgis:17-3.4`).

**Option B — Tout en Docker**

```bash
# Créer le volume PostgreSQL avant le premier run
docker volume create pgdata

docker compose up -d --build
```

- Frontend : http://localhost:3000
- Gateway API : http://localhost:8000
- Health gateway : http://localhost:8000/health

Arrêt : `docker compose down`. Données Postgres conservées dans le volume `pgdata`.

**Option C — Windows**

Le script `launch_dev.sh` affiche les commandes à lancer manuellement dans plusieurs terminaux (Postgres, gateway, admin-service, user-service, scan-service, frontend). Voir les messages à l’écran après exécution de `launch_dev.sh`.

## Structure du projet

```
template/
├── backend/
│   ├── common/                 # Package Python partagé (config, JWT, DB, logging, etc.)
│   ├── gateway/                # API Gateway (auth, proxy vers les services)
│   ├── admin-service/          # Service admin (contacts, analytics, emails, KPIs, etc.)
│   ├── user-service/           # Utilisateurs, profil, abonnements, favoris
│   └── scan-service/            # Service de scan (posture sécurité)
├── frontend/                   # Next.js 16 (App Router), i18n fr/en, Cognito, Tailwind
├── docs/                       # Documentation (architecture, déploiement, variables)
├── .github/workflows/          # CI (lint Python + JS)
├── docker-compose.yml          # Stack complète
├── launch_dev.sh               # Démarrage dev (Postgres + services locaux)
├── .env.example                # Variables d’environnement racine
└── pytest.ini                  # Config pytest (tests à venir)
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture des services, flux d’authentification, bases de données |
| [docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md) | Déploiement, migrations Alembic, healthchecks, bonnes pratiques |
| [docs/VARIABLES-ENVIRONNEMENT.md](docs/VARIABLES-ENVIRONNEMENT.md) | Référence des variables d’environnement (racine et frontend) |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Lint, pre-commit, conventions de code |
| [docs/AUDIT-TEMPLATE.md](docs/AUDIT-TEMPLATE.md) | Audit des manques et améliorations prioritaires |
| [frontend/README.md](frontend/README.md) | Détails du projet Next.js (pages, config Amplify) |

## Lint et qualité

- **Backend** : Black, isort, flake8 (config par service dans `backend/<service>/`).
- **Frontend** : ESLint, Prettier.
- **Pre-commit** : hooks pour Black, isort, flake8 (Python) et ESLint, Prettier (frontend). Voir [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

```bash
# Installer les hooks
pre-commit install

# Lancer le lint manuellement (ex. backend)
cd backend/gateway && black . && isort . && flake8 .

# Frontend
cd frontend && npm run lint && npm run format:check
```

## Migrations base de données

Les services **admin-service** et **user-service** utilisent Alembic. Les migrations sont appliquées au démarrage de l’app (voir [docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md)). Pour les lancer à la main :

```bash
# Admin
cd backend/admin-service && . venv/bin/activate && alembic upgrade head

# User
cd backend/user-service && . venv/bin/activate && alembic upgrade head
```

## Licence

Voir le fichier [LICENSE](LICENSE) s’il est présent, ou convenir avec l’équipe Immosphere.
