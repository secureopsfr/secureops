# Documentation SecureOps

Index de la documentation du projet.

## Démarrage et utilisation

- [**README.md**](../README.md) (racine) — Présentation de SecureOps, prérequis, démarrage rapide (`launch_dev.sh`, Docker), structure du projet, liens vers les docs.

## Architecture et technique

- [**ARCHITECTURE.md**](ARCHITECTURE.md) — Architecture des services (gateway, admin, user, scan), flux d’authentification (Cognito/JWT), bases de données, package commun backend, aperçu du frontend.

## Déploiement et opérations

- [**DEPLOIEMENT.md**](DEPLOIEMENT.md) — Variables d’environnement, build et exécution avec Docker, migrations Alembic, healthchecks, déploiement du frontend, bonnes pratiques et dépannage.

- [**DEPLOIEMENT-AWS.md**](DEPLOIEMENT-AWS.md) — Guide pas à pas détaillé : domaine `.fr`, DNS (`secureops.fr`, `api.secureops.fr`), Amplify (frontend), Cognito, **EC2 unique** (Docker : gateway + microservices + **PostgreSQL/PostGIS**), TLS, CORS, emails (Microsoft Graph / SES), Cloudflare, sauvegardes EBS/`pg_dump`, secrets et ordre de déploiement ; option **RDS** en évolution.

- [**VARIABLES-ENVIRONNEMENT.md**](VARIABLES-ENVIRONNEMENT.md) — Référence détaillée des variables d’environnement (racine et frontend).

- [**RATE-LIMITING.md**](RATE-LIMITING.md) — Guide complet de protection anti-abus : stratégie de rate limiting, réponses 429, architecture Redis, observabilité et plan de déploiement progressif.

## Roadmaps et versions

- [**ROADMAP-MVP-0.1.0.md**](roadmaps/versions/ROADMAP-MVP-0.1.0.md) — Roadmap MVP 0.1.0 : scanner de posture sécurité (TLS, headers, cookies, exposition fichiers, etc.).

- [**ROADMAP-MVP-0.2.0.md**](roadmaps/versions/ROADMAP-MVP-0.2.0.md) — Roadmap MVP 0.2.0 : auth, historique, export PDF, API publique, monitoring.

- [**ROADMAP-MVP-0.3.0.md**](roadmaps/versions/ROADMAP-MVP-0.3.0.md) — Roadmap MVP 0.3.0 : refactoring plateforme, crawler indépendant, mode async scan/crawl, hub scanner.

- [**ROADMAP-MVP-1.0.0.md**](roadmaps/versions/ROADMAP-MVP-1.0.0.md) — Roadmap MVP 1.0.0 : finalisation tests passifs restants, premiers tests actifs, analytics et backlog reporté.

- [**ROADMAP-MVP-1.1.0.md**](roadmaps/versions/ROADMAP-MVP-1.1.0.md) — Roadmap MVP 1.1.0 : tests d’intégration, Scanner 2, vérification d’autorisation, backlog reporté depuis la 1.0.0.

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
