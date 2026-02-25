# Documentation du template fullstack

Index de la documentation du projet.

## Démarrage et utilisation

- [**README.md**](../README.md) (racine) — Présentation du template, prérequis, démarrage rapide (`launch_dev.sh`, Docker), structure du projet, liens vers les docs.

## Architecture et technique

- [**ARCHITECTURE.md**](ARCHITECTURE.md) — Architecture des services (gateway, admin, user, metier-*), flux d’authentification (Cognito/JWT), bases de données, package commun backend, aperçu du frontend.

## Déploiement et opérations

- [**DEPLOIEMENT.md**](DEPLOIEMENT.md) — Variables d’environnement, build et exécution avec Docker, migrations Alembic, healthchecks, déploiement du frontend, bonnes pratiques et dépannage.

- [**VARIABLES-ENVIRONNEMENT.md**](VARIABLES-ENVIRONNEMENT.md) — Référence détaillée des variables d’environnement (racine et frontend).

## Contribution

- [**CONTRIBUTING.md**](CONTRIBUTING.md) — Conventions de code, pre-commit, lint backend (Black, isort, flake8) et frontend (ESLint, Prettier), CI, branches et PR.

## Audit et améliorations

- [**AUDIT-TEMPLATE.md**](AUDIT-TEMPLATE.md) — Audit des manques et améliorations recommandées (tests, rate limiting, CI, documentation, etc.), par ordre de priorité.

## Frontend

- [**frontend/README.md**](../frontend/README.md) — Détails du projet Next.js : pages disponibles, configuration AWS Amplify, structure des dossiers.
