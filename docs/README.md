# Documentation SecureOps

Index de la documentation du projet.

## Démarrage et utilisation

- [**README.md**](../README.md) (racine) — Présentation de SecureOps, prérequis, démarrage rapide (`launch_dev.sh`, Docker), structure du projet, liens vers les docs.

## Architecture et technique

- [**ARCHITECTURE.md**](ARCHITECTURE.md) — Architecture des services (gateway, admin, user, scan), flux d’authentification (Cognito/JWT), bases de données, package commun backend, aperçu du frontend.

## Déploiement et opérations

- [**DEPLOIEMENT.md**](DEPLOIEMENT.md) — Variables d’environnement, build et exécution avec Docker, migrations Alembic, healthchecks, déploiement du frontend, bonnes pratiques et dépannage.

- [**VARIABLES-ENVIRONNEMENT.md**](VARIABLES-ENVIRONNEMENT.md) — Référence détaillée des variables d’environnement (racine et frontend).

## Roadmaps et versions

- [**ROADMAP-MVP-0.1.0.md**](roadmaps/ROADMAP-MVP-0.1.0.md) — Roadmap MVP 0.1.0 : scanner de posture sécurité (TLS, headers, cookies, exposition fichiers, etc.).

- [**ROADMAP-MVP-0.2.0.md**](roadmaps/ROADMAP-MVP-0.2.0.md) — Roadmap MVP 0.2.0 : auth, historique, export PDF, API publique, monitoring.

- [**CHANGELOG.md**](../CHANGELOG.md) — Historique des modifications (format Keep a Changelog). Version courante dans [VERSION](../VERSION).

## Vérifications du scanner

Documentation détaillée des tests de posture sécurité implémentés :

- [**tls-https.md**](verifications/tls-https.md) — TLS, HTTPS, certificats, versions obsolètes
- [**security-headers.md**](verifications/security-headers.md) — Security headers (CSP, HSTS, etc.)
- [**cookies.md**](verifications/cookies.md) — Flags Secure, HttpOnly, SameSite
- [**exposition-fichiers.md**](verifications/exposition-fichiers.md) — Fichiers et endpoints sensibles exposés
- [**directory-listing.md**](verifications/directory-listing.md) — Directory listing
- [**robots-txt.md**](verifications/robots-txt.md) — robots.txt et routes Disallow
- [**crawler.md**](verifications/crawler.md) — Crawler HTTP : découverte des URLs, respect robots.txt, contrat API
- [**tech-fingerprinting.md**](verifications/tech-fingerprinting.md) — Détection de la stack technique

## Contribution

- [**CONTRIBUTING.md**](CONTRIBUTING.md) — Conventions de code, pre-commit, lint backend (Black, isort, flake8) et frontend (ESLint, Prettier), CI, branches et PR.

## Audit et améliorations

- [**AUDIT-TEMPLATE.md**](AUDIT-TEMPLATE.md) — Audit des manques et améliorations recommandées (tests, rate limiting, CI, documentation, etc.), par ordre de priorité.

## Frontend

- [**frontend/README.md**](../frontend/README.md) — Détails du projet Next.js : pages disponibles, configuration AWS Amplify, structure des dossiers.
