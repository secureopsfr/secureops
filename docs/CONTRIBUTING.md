# Contribuer au template

Ce document décrit les conventions de code, le lint et les outils à utiliser pour contribuer au projet.

## Prérequis

- Python 3.11+, Node.js 18+, Docker (voir [README.md](../README.md))
- **Pre-commit** : `pip install pre-commit` puis `pre-commit install` à la racine du repo

## Pre-commit

Les hooks pre-commit assurent un formatage et un lint cohérent avant chaque commit.

```bash
pre-commit install
```

Lors d’un `git commit`, les hooks suivants s’exécutent automatiquement :

- **pre-commit-hooks** : trailing whitespace, fin de fichier, validation YAML/JSON
- **Black** : formatage Python (un hook par service backend)
- **isort** : tri des imports Python
- **flake8** : lint Python (règles par service)
- **ESLint** : lint du frontend Next.js (fichiers `frontend/**/*.{js,jsx,ts,tsx}`)
- **Prettier** : formatage du frontend (JS/TS/CSS/JSON/MD)

Pour lancer tous les hooks sur les fichiers suivis :

```bash
pre-commit run --all-files
```

## Backend (Python)

### Conventions

- **PEP 8** avec ligne max à **150 caractères** (règle E501 désactivée dans flake8).
- **Docstrings** en français sur chaque module, classe et fonction (description, Args, Returns, Raises le cas échéant).
- **Commentaires** en français, succincts.
- **Plugins flake8** : pytest-style (PT001, PT023), quotes, simplify, comprehensions.

### Outils par service

Chaque service (gateway, admin-service, user-service, scan-service) a sa propre config :

- **Black** : `backend/<service>/pyproject.toml`
- **isort** : profil `black`
- **flake8** : `backend/<service>/.flake8`

### Commandes manuelles

À exécuter depuis le répertoire du service (ex. `backend/gateway`) :

```bash
cd backend/gateway
python -m venv venv && . venv/bin/activate
pip install -e ../common -r requirements.txt

black .
isort .
flake8 .
```

Répéter pour chaque service modifié, ou utiliser pre-commit.

## Frontend (Next.js / TypeScript)

### Lint et formatage

```bash
cd frontend
npm install
npm run lint        # ESLint
npm run format:check  # Prettier (vérification)
npm run format      # Prettier (écriture)
```

Les hooks pre-commit appellent `npm run lint` et `npm run format` pour les fichiers du frontend.

### Build

Pour vérifier que le projet compile :

```bash
cd frontend
npm run build
```

En CI, un job de build peut être ajouté pour détecter les erreurs TypeScript ou d’import.

## CI (GitHub Actions)

Le workflow `.github/workflows/ci.yml` :

- Déclenché sur push/PR vers `master` et `develop`
- Lance la stack avec `docker-compose.ci.yml`
- Attend que PostgreSQL soit prêt
- Exécute Black (check), isort (check), flake8 pour chaque service backend
- Exécute `npm run lint` pour le frontend
- Teardown des conteneurs en fin de job

Il n’y a pas encore d’étape de tests ni de build frontend ; voir [AUDIT-TEMPLATE.md](AUDIT-TEMPLATE.md) pour les évolutions prévues.

## Branches et Pull Requests

- Travailler sur une branche dédiée (ex. `feature/xxx`, `fix/xxx`).
- Ouvrir une Pull Request vers `master` ou `develop` selon la convention du projet.
- S’assurer que la CI passe (lint) et que les modifications sont documentées si nécessaire (README, docs/, commentaires).

## Tests (à venir)

Le template prévoit une structure de tests (voir `pytest.ini` à la racine : `tests/unit`, `tests/integration`, `tests/e2e`) mais les répertoires et fichiers de tests ne sont pas encore en place. Quand ils le seront, la procédure sera :

- Backend : `pytest` depuis la racine ou depuis chaque service.
- Frontend : ajout d’un runner (Jest/Vitest) et d’un script `npm run test`.

Les contributeurs sont invités à ajouter des tests pour les parties qu’ils modifient, une fois le cadre en place.
