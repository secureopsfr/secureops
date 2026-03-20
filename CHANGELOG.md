# Changelog

Toutes les modifications notables du projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et le projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [1.0.0] - 2026-03-19

Cette version **1.0.0** marque l’alignement de la version produit et de la documentation sur les jalons MVP. Ci-dessous : **synthèse de tout ce qui a été ajouté et consolidé depuis la [0.1.0]** (le détail inchangé par release reste dans les sections [0.3.0], [0.2.0] et [0.1.0] ci-dessous).

### Ajouté

#### Depuis [0.1.0] — MVP scanner (fondations)

- **Sécurité cible** : validation d’URL stricte, protection **SSRF** (localhost, IP privées, résolution DNS contrôlée), timeouts configurables
- **Tests passifs initiaux** : **TLS/HTTPS**, **security headers** (CSP, HSTS, XFO, XCTO, etc.), **cookies** (Secure, HttpOnly, SameSite), **exposition de fichiers** sensibles, **directory listing**, **robots.txt**, **tech fingerprinting**
- **Modèles** : findings typés, résultat de scan, **scoring** /100 avec pondération par catégorie
- **API** : `POST /scan/api/scan` en **SSE**, gestion d’erreurs structurée, logging avec `request_id`
- **Frontend** : landing, page résultats (score, catégories, recommandations), états de chargement, gate post-scan + sessionStorage, favicon du site scanné
- **Infra** : gateway exposant le scan, premières docs de vérifications

#### Depuis [0.2.0] — Compte, historique et scanner enrichi

- **Persistance** : table `scans`, API historique (création, liste paginée, suppression), affichage dans Mon compte, sauvegarde auto fin de scan si utilisateur connecté
- **Export** : **PDF** (WeasyPrint, i18n fr/en, page de garde, synthèse, findings)
- **Scans planifiés** : modèle `scheduled_scans`, scheduler user-service, API CRUD, alertes (régression, critical), UI sur le scanner
- **Tests passifs étendus** : TLS (posture, chaîne, expiration), headers (CSP avancé, COEP/COOP, etc.), cookies (__Host-, CHIPS, etc.), fichiers et listing élargis, robots/sitemap, fingerprinting (CPE/CVE, HTML), **information disclosure**, **cache**, **CORS / mixed content**, **SRI** et intégrité HTML (formulaires, meta, etc.)
- **UX** : résumés sur la page résultats, design chargement/scan, gestion durée de vie de l’historique
- **Documentation** : fiches par catégorie dans `docs/verifications/`, roadmaps versionnées dans `docs/roadmaps/`

#### Depuis [0.3.0] — Plateforme, PDF service et hub scanner

- **Socle commun** : package **`backend/common`** (config, JWT, middleware, health, validation URL, SSRF, schémas, etc.) avec tests et lint
- **Microservices** : refactoring gateway, admin-service, user-service, scan-service (Docker, deps, auth, async)
- **PDF** : microservice **`pdf-service`** (`POST /api/report/pdf`), intégration gateway/scan-service via `/pdf/*`
- **Crawler** : service dédié, découverte d’URLs, limites, robots.txt, validation côté UI avant scan
- **Async** : files d’attente DB pour **scan** et **crawl** (`/scan/async`, `/crawl/async`), workers, retries, contrôle d’accès aux jobs
- **API publique** : **clés API** (création, révocation, TTL, tags, restriction IP, usage via gateway)
- **Frontend** : refonte **landing + hub `/scanner`**, analyses/suivi/docs/clés API, tendances et KPIs, i18n et accessibilité renforcées

#### Spécifique à la release 1.0.0

- **Fichier `VERSION`** à **1.0.0** et **README** mis à jour (version affichée, liens roadmaps 1.0.0 / 1.1.0)
- **Roadmaps renommées** : anciennes `ROADMAP-MVP-0.4.0.md` → **`ROADMAP-MVP-1.0.0.md`**, `ROADMAP-MVP-0.5.0.md` → **`ROADMAP-MVP-1.1.0.md`** avec harmonisation des titres, liens et références (docs, vérifications intrusives, `ROADMAP-MVP-0.3.0.md`, etc.)

### Modifié

- **CHANGELOG** : cette entrée [1.0.0] regroupe la **vue cumulative** ; les sections [0.3.0] à [0.1.0] conservent le **journal détaillé** par version
- **Références « roadmap MVP 1.0.0 »** dans l’historique : alignement sur les nouveaux noms de fichiers et jalons (sans changer le fond des livraisons 0.1.0–0.3.0)

### Limites connues (à date 1.0.0)

- Backlog **roadmap MVP 1.0.0** : finalisation de certains tests passifs, premiers tests actifs (Scanner 2), rapports/analytics avancés, scan paramétrable, explication du scoring en UI — voir `docs/roadmaps/versions/ROADMAP-MVP-1.0.0.md`
- Reporté **roadmap MVP 1.1.0** : tests d’intégration dédiés, GitHub Action, compléments docs/UX scanner, vérification d’autorisation DNS, suite Scanner 2, etc. — voir `docs/roadmaps/versions/ROADMAP-MVP-1.1.0.md`
- Toujours en cours / partiel : alertes et exports avancés, rendu final « anomalie détectée », tests E2E/CI ciblés intégration scan/crawl

---

## [0.3.0] - 2026-03-12

### Ajouté

#### Refactoring backend et socle commun

- **Package partagé `backend/common`** consolidé (config, JWT, middleware, health, validation URL, SSRF, helpers URL, utilitaires schemas/datetime) avec tests et pipeline de lint dédiés
- **Refactoring structurel** des services `gateway`, `admin-service`, `user-service` et `scan-service` (séparation runtime/dev deps, Dockerfiles harmonisés, durcissements auth et robustesse async/sync)

#### PDF service dédié

- **Nouveau `pdf-service`** (endpoint `POST /api/report/pdf`) pour isoler la génération de rapports PDF (WeasyPrint, templates, i18n, assets)
- **Intégration gateway + scan-service** vers le service PDF via route `/pdf/*` et clés internes optionnelles
- **Qualité PDF** : schémas typés, constantes centralisées, options de rendu configurables, troncature explicite, nettoyage du code mort, couverture de tests renforcée

#### Scanner et plateforme

- **Crawler HTTP indépendant** (découverte d’URLs, limites, respect robots.txt, validation frontend avant scan)
- **Mode asynchrone scan + crawl** basé DB queue (`/scan/api/scan/async` et `/crawl/api/crawl/async`) avec workers dédiés, retries/backoff, contrôle d’accès job
- **API publique clés API** : création/liste/révocation, TTL, tags, restrictions IP, vérification interne via gateway/user-service

#### Frontend / UX scanner

- **Refonte landing + hub scanner** : parcours scan basique, espace connecté `/scanner`, pages dédiées analyses/suivi/docs/clé API
- **Historique, tendances et KPIs** alimentés par des endpoints dédiés
- **I18n et accessibilité** renforcées (FR/EN, labels, composants partagés, hooks SWR admin)

### Modifié

- **Architecture documentaire** et roadmaps : backlog non terminé de la v0.3.0 explicitement reporté dans la roadmap MVP 1.0.0
- **Pipeline scan-service** : unification du noyau d’exécution et homogénéisation des payloads (SSE + endpoint interne)

### Limites connues (MVP 0.3.0)

- Backlog d’intégration (tests E2E/CI), GitHub Action SecureOps, compléments docs/UX et gouvernance crawler reportés en roadmap MVP 1.0.0
- Alertes configurées, exports avancés et finalisation complète du rendu “anomalie détectée” restent à terminer

---

## [0.2.0] - 2025-03-05

### Ajouté

#### Auth, historique et dashboard

- **Persistance des scans** : table `scans` (user_id, url, score, findings_json, etc.), migration Alembic dans user-service
- **API historique** : `POST/GET/DELETE /user/api/scans/history` pour enregistrer, lister (pagination) et supprimer les scans
- **Dashboard** : section « Historique des scans » dans Mon compte, liste paginée avec score et badge, détail réutilisant `ScanResults`
- **Sauvegarde automatique** : scan-service appelle le gateway en fin de scan si token présent pour persister le résultat

#### Export PDF

- **Endpoint** `GET /api/scan/export/pdf` : génération de rapport PDF professionnel (WeasyPrint)
- **Contenu** : page de garde, score global, résumé par catégorie, liste des findings avec recommandations, footer configurable
- **Frontend** : bouton « Télécharger PDF » sur la page résultats et sur le détail d'un scan historique
- **i18n** : support fr/en dans le PDF via paramètre `lang`
- **Refactoring** : modules dédiés (cover, sommaire, synthese, findings, matrix), CSS externe, catalogue i18n centralisé

#### Monitoring continu (scans planifiés)

- **Modèle** `scheduled_scans` : url, fréquence (daily/weekly/monthly), horaire, jour, `next_run_at`
- **Scheduler** : boucle asyncio dans user-service (intervalle configurable), appel scan-service via endpoint interne
- **API** : `POST/GET/PATCH/DELETE /user/api/scans/schedule` pour créer, lister, modifier et supprimer les scans planifiés
- **Alertes** : détection de régression (chute de score), notification si finding critical ; préférence `scan_alerts_enabled` dans Settings
- **Frontend** : bloc « Scans planifiés » sur la page Scanner (si connecté), formulaire URL/fréquence/heure, indicateur prochain scan

#### Tests de posture sécurité — Améliorations

- **TLS** : résumé « TLS posture » (OK/Avertissements/Critique), chaîne de certificats, alerte expiration < 30 j, détection TLS 1.3
- **Security Headers** : CSP report-uri/unsafe-inline/unsafe-eval, COEP, COOP, Clear-Site-Data, sévérité différenciée par header
- **Cookies** : préfixes __Host-/__Secure-, Partitioned (CHIPS), session incomplète, Expires trop long pour session
- **Exposition fichiers** : liste étendue (.htaccess, web.config, .svn, composer.json, package.json, .npmrc, backups, swagger, graphql)
- **Directory listing** : chemins /tmp, /logs, /config, /backup, /data ; listing partiel ; 403 sur chemins sensibles
- **robots.txt** : Crawl-delay, Allow ; **Sitemap** : Sitemap dans robots, fallback /sitemap.xml, URLs sensibles dans sitemap
- **Tech fingerprinting** : versions dans Server/X-Powered-By, base CPE/CVE, meta/scripts HTML, stack probable

#### Nouveaux tests passifs

- **Information disclosure** : stack traces, mode debug, secrets dans HTML/JSON, headers X-Debug, X-Runtime, Server avec version
- **Cache** : Cache-Control, Pragma, ETag, Last-Modified, Vary ; pages sensibles non cacheables ; cache long pour assets immuables
- **CORS** : ACAO *, Credentials+*, Allow-Methods, Expose-Headers sensibles ; mixed content (HTTP sur HTTPS), CORP manquant
- **SRI** : scripts/CSS externes sans `integrity` ; analyse HTML : scripts sans nonce, autocomplete password, target="_blank" sans noopener, meta robots

#### UX et design

- Section « Résumé des vérifications » et « Liste des tests effectués » sur la page résultats
- Amélioration du design : page de chargement, bubble Nouveau scan, page de scan
- Gestion de la durée de vie de l'historique, suppression de tout l'historique en un clic
- Corrections : skeleton page connexion/inscription, shimmer header, PDF indisponible quand connexion forcée

#### Documentation

- Fichiers de vérification par catégorie dans `docs/verifications/` (tls-https, security-headers, cookies, exposition-fichiers, directory-listing, robots-txt, sitemap, tech-fingerprinting, information-disclosure, cache-et-performances, cors-et-cross-origin, integrite-et-sous-ressources, etc.)
- Roadmaps déplacées dans `docs/roadmaps/`, création roadmaps MVP 0.3.0 et 1.0.0

### Modifié

- Scoring adapté aux nouveaux checks (pondération par catégorie)
- Matrice de sévérité et règles d'upgrade pour findings critiques

### Limites connues (MVP 0.2.0)

- Pas de rate limiting sur l'endpoint de scan
- API publique : quotas et rate limiting à venir
- Blocs 5.5 (Méthodes HTTP/redirections) et 5.7 (APIs/formats) reportés à une version ultérieure

---

## [0.1.0] - 2025-03-02

### Ajouté

#### Backend — Sécurité et fondations

- **Validation URL** : autorisation uniquement `http`/`https`, refus des credentials dans l’URL, ports limités (80/443 par défaut, 1010/1011 pour badssl.com), normalisation (schéma/netloc en minuscules, fragment supprimé)
- **Protection SSRF** : blocage de localhost, 127.0.0.1, ::1, résolution DNS avec timeout 5s, blocage des IP privées (IPv4 et IPv6)
- **Timeouts** : connexion (3s), lecture (10s), durée globale du scan (60s), configurables via `settings.yml`

#### Backend — Tests de posture sécurité

- **TLS / HTTPS** : vérification HTTPS activé, redirection HTTP→HTTPS, validité du certificat (valide/expiré/auto-signé), détection TLS 1.0/1.1
- **Security Headers** : Content-Security-Policy, Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy
- **Cookies** : vérification des flags Secure, HttpOnly, SameSite ; détection des cookies sans Secure sur site HTTPS
- **Exposition fichiers** : tests GET sur `/.env`, `/.git/config`, `/backup.zip`, `/phpinfo.php`, `/admin/`, `/.DS_Store` avec signatures par chemin
- **Directory listing** : tests sur `/uploads/`, `/assets/`, `/static/` avec détection des signatures Apache/Nginx
- **robots.txt** : lecture et parsing des directives Disallow, signalement des routes potentiellement sensibles
- **Tech fingerprinting** : analyse des en-têtes Server, X-Powered-By, X-Generator, X-Drupal-Cache ; heuristiques pour Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal

#### Backend — Modèles et scoring

- **Schéma Finding** : id, category, title, severity, evidence, recommendation, references
- **Schéma ScanResult** : url, timestamp, duration, score, findings[]
- **Système de scoring** : score /100, pondération par catégorie (TLS 25, Headers 25, Cookies 20, Exposure 20, Fingerprinting 10), mapping sévérité (critical/high/medium/low/info), upgrade .git/config et .env → critical

#### Backend — API

- **Endpoint** `POST /scan/api/scan` : lance le scan et retourne le résultat via SSE
- **Gestion des erreurs** : URL invalide (400), site inaccessible / timeout / erreur TLS (503/504/502) avec classification (connection_failed, timeout, tls_error)
- **Logging structuré** : request_id (correlation_id), duration_seconds, nb_findings, status à la fin de chaque scan

#### Frontend

- **Landing** : hero, champ URL, CTA « Scan », disclaimer usage autorisé
- **Page résultats** : score global avec badge (🟢/🟡/🔴), résumé par catégorie, liste des findings triés par sévérité, bloc « How to fix » (recommandations)
- **UX** : loader pendant le scan, états idle/loading/success/error, responsive mobile
- **Gate authentification** : invitation à se connecter après scan si non authentifié ; stockage des résultats en sessionStorage, restauration après connexion
- **Favicon** : affichage du favicon du site scanné (Google Favicon API), fallback icône globe SVG

#### Infrastructure

- **Gateway** : route publique `POST /scan/api/scan` pour le scanner MVP
- **Documentation** : docs de vérifications (TLS/HTTPS, exposition fichiers, robots.txt, etc.)

### Limites connues (MVP 0.1.0)

- Pas de rate limiting sur l’endpoint de scan
- Pas de login requis pour lancer un scan (disclaimer côté front)
- Résumé « TLS posture » non implémenté
- Blocage des redirections vers IP privées non appliqué (à venir)
- Pas de tests CI exécutés (lint uniquement)

---

[1.0.0]: https://github.com/pierreglerant/secureops/releases/tag/v1.0.0
[0.3.0]: https://github.com/pierreglerant/secureops/releases/tag/v0.3.0
[0.2.0]: https://github.com/pierreglerant/secureops/releases/tag/v0.2.0
[0.1.0]: https://github.com/pierreglerant/secureops/releases/tag/v0.1.0
