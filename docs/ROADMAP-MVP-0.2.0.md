# SecureOps — Roadmap MVP 0.2.0 (étape par étape)

Objectif : faire évoluer le scanner v0.1.0 vers une **plateforme** avec authentification, historique, export, monitoring et API publique.

**Prérequis :** MVP 0.1.0 livré (voir [ROADMAP-MVP.md](ROADMAP-MVP.md)).

---

## 0) Décisions MVP 0.2.0 (à figer avant de coder)

- [ ] **Scope V2** : Auth + dashboard + historique + export PDF + mode asynchrone + API publique
- [ ] **Auth** : Cognito (déjà en place) — scanner protégé pour utilisateurs connectés
- [ ] **Mode scan** : synchrone conservé pour scans rapides ; asynchrone pour scans longs (> 30s)
- [ ] **API publique** : clés API pour intégrations externes (CI/CD, scripts)
- [ ] **Limites** : quotas par utilisateur (ex. 50 scans/jour) ; rate limiting API

---

## 1) Mode asynchrone + queue

### 1.1 Choix technologique
- [ ] Choisir stack : SQS + worker Python **ou** Celery + Redis
- [ ] Documenter décision (pros/cons, coût, complexité)

### 1.2 Infrastructure queue
- [ ] Créer file SQS (ou Redis pour Celery)
- [ ] Configurer dead-letter queue (DLQ) pour échecs
- [ ] Timeout et retry policy (ex. 3 tentatives, backoff exponentiel)

### 1.3 Worker scan
- [ ] Worker dédié : consomme jobs de la queue, exécute le scan
- [ ] Réutiliser la logique existante (`scan_stream`, checks, normalisation)
- [ ] Stocker résultat en base (ex. PostgreSQL) avec `job_id`, `status`, `result`

### 1.4 API endpoints
- [ ] `POST /api/scan/async` : enqueue un job, retourne `job_id`
- [ ] `GET /api/scan/async/{job_id}` : statut du job (pending, running, completed, failed)
- [ ] `GET /api/scan/async/{job_id}/result` : résultat du scan (si completed)

### 1.5 Frontend
- [ ] Option : lancer scan en mode async si durée estimée > seuil
- [ ] Polling ou WebSocket pour afficher le statut
- [ ] Page résultats accessible via URL partageable (`/scan/{job_id}`)

---

## 2) Auth + dashboard + historique scans

### 2.1 Backend — persistance
- [ ] Schéma : `scans` (id, user_id, url, status, score, findings_json, created_at)
- [ ] Migration Alembic (user-service ou nouveau service scan-history)
- [ ] Associer chaque scan à l’utilisateur Cognito (via `user_id` ou `sub`)

### 2.2 Protection du scanner
- [ ] Retirer `POST /scan/api/scan` des routes publiques
- [ ] Exiger JWT pour lancer un scan

### 2.3 API historique
- [ ] `GET /api/scan/history` : liste des scans de l’utilisateur (pagination)
- [ ] `GET /api/scan/history/{id}` : détail d’un scan passé
- [ ] `DELETE /api/scan/history/{id}` : suppression (optionnel)

### 2.4 Dashboard frontend
- [ ] Page « Mon historique » (ou section dans Mon compte)
- [ ] Liste des scans : URL, date, score, lien vers détail
- [ ] Filtres : par date, par score
- [ ] Accès rapide au dernier scan

### 2.5 UX
- [ ] Redirection vers login si non connecté + tentative de scan
- [ ] Message clair : « Connectez-vous pour scanner et sauvegarder vos résultats »

> **Partiellement fait (MVP 0.1.0) :** Gate « Connectez-vous pour accéder aux résultats » après scan. L’utilisateur peut lancer un scan sans être connecté ; les résultats sont stockés en `sessionStorage` et affichés après connexion. Voir [ROADMAP-MVP-0.1.0.md](ROADMAP-MVP-0.1.0.md) § 7.4.

---

## 3) Export PDF

### 3.1 Backend
- [ ] Choisir librairie : WeasyPrint, ReportLab, ou pdfkit
- [ ] Endpoint `GET /api/scan/{id}/export/pdf` : génère et retourne le PDF

### 3.2 Contenu du rapport
- [ ] En-tête : logo, titre, date, URL scannée
- [ ] Score global + badge
- [ ] Résumé par catégorie
- [ ] Liste des findings (titre, sévérité, preuve, recommandation)
- [ ] Pied de page : disclaimer, lien SecureOps

### 3.3 Frontend
- [ ] Bouton « Télécharger PDF » sur la page résultats
- [ ] Bouton « Télécharger PDF » sur la page détail d’un scan historique

### 3.4 Style
- [ ] Template PDF professionnel (mise en page, couleurs)
- [ ] Support i18n (fr/en) dans le PDF

---

## 4) Monitoring continu (scans planifiés)

### 4.1 Modèle de données
- [ ] Schéma : `scheduled_scans` (id, user_id, url, frequency, next_run_at, enabled)
- [ ] Fréquences : daily, weekly, monthly

### 4.2 Scheduler
- [ ] Job cron (ou EventBridge) : réveille les scans à exécuter
- [ ] Enqueue les jobs dans la queue async
- [ ] Mise à jour `next_run_at` après exécution

### 4.3 API
- [ ] `POST /api/scan/schedule` : créer un scan planifié
- [ ] `GET /api/scan/schedule` : liste des scans planifiés
- [ ] `PATCH /api/scan/schedule/{id}` : modifier (fréquence, pause)
- [ ] `DELETE /api/scan/schedule/{id}` : supprimer

### 4.4 Alertes (optionnel)
- [ ] Détection de régression (score chute vs dernier scan)
- [ ] Email ou notification si finding critical détecté

### 4.5 Frontend
- [ ] Page « Scans planifiés » : liste, CRUD
- [ ] Formulaire : URL, fréquence (daily/weekly/monthly)
- [ ] Indicateur : prochain scan prévu

---

## 5) Scan plus avancé (OWASP light, non intrusif)

> **Principe :** tests passifs uniquement — pas d’injection, pas de bruteforce, pas de fuzzing. Lecture et analyse des réponses HTTP/HTML.

---

### 5.1 Améliorations des tests existants

#### 5.1.1 TLS / HTTPS

**Existant (v0.1.0) :**
- HTTPS activé ? ✅
- Redirection HTTP→HTTPS ? ✅
- Certificat valide / expiré / auto-signé ? ✅
- Version TLS (détection 1.0/1.1) ✅

**En plus (v0.2.0) :**
- [ ] Résumé « TLS posture » (synthèse lisible : OK / avertissements / critique)
- [ ] Vérification de la chaîne de certificats (intermédiaires manquants)
- [ ] Détection OCSP stapling (présent ou non)
- [ ] Alerte si certificat expire dans < 30 jours
- [ ] Support TLS 1.3 (détection si proposé)

#### 5.1.2 Security Headers

**Existant (v0.1.0) :**
- Vérifier présence : `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options` (nosniff), `Referrer-Policy`, `Permissions-Policy` ✅

**En plus (v0.2.0) :**
- [ ] Vérifier `Content-Security-Policy` : présence de `report-uri` ou `report-to`
- [ ] Vérifier directives CSP strictes (pas de `unsafe-inline`, `unsafe-eval` si possible)
- [ ] Headers COEP/COOP (`Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy`)
- [ ] `Clear-Site-Data` pour déconnexion sécurisée
- [ ] Sévérité différenciée selon le header manquant

#### 5.1.3 Cookies

**Existant (v0.1.0) :**
- Vérifier flags : `Secure`, `HttpOnly`, `SameSite` ✅
- Détecter cookies sans `Secure` si site HTTPS ✅

**En plus (v0.2.0) :**
- [ ] Détecter préfixes `__Host-` et `__Secure-` (bonnes pratiques)
- [ ] Cookie `Partitioned` (CHIPS) pour cookies tiers
- [ ] Alerte si cookie de session sans `HttpOnly` + `Secure` + `SameSite=Strict`
- [ ] Détection de cookies avec `Expires` trop lointain pour session

#### 5.1.4 Exposition fichiers

**Existant (v0.1.0) :**
- Liste fixe : `/.env`, `/.git/config`, `/backup.zip`, `/phpinfo.php`, `/admin/`, `/.DS_Store` ✅
- Signatures par chemin (KEY=value, [core], PK, etc.) ✅

**En plus (v0.2.0) :**
- [ ] Liste étendue : `/.htaccess`, `/web.config`, `/.svn/entries`, `/composer.json`, `/package.json`, `/.npmrc`
- [ ] Signatures améliorées (regex plus précises, faux positifs réduits)
- [ ] Détection de fichiers de backup (`.bak`, `.old`, `.swp`, `~`)
- [ ] Endpoints API docs exposés : `/swagger`, `/api-docs`, `/graphql` (introspection)

#### 5.1.5 Directory listing

**Existant (v0.1.0) :**
- Répertoires : `/uploads/`, `/assets/`, `/static/` ✅
- Signatures Apache/Nginx (Index of, Parent Directory, [DIR], mod_autoindex, nginx, `<a href=`) ✅

**En plus (v0.2.0) :**
- [ ] Chemins supplémentaires : `/tmp/`, `/logs/`, `/config/`, `/backup/`, `/data/`
- [ ] Détection de listing partiel (réponse HTML avec liens vers fichiers)
- [ ] Alerte si répertoire sensible retourne 403 (existence révélée)

#### 5.1.6 robots.txt

**Existant (v0.1.0) :**
- Lire `/robots.txt` ✅
- Extraire `Disallow` et signaler routes potentiellement sensibles (admin, api, backup, etc.) ✅

**En plus (v0.2.0) :**
- [ ] Vérifier présence de `Sitemap:` (bonne pratique SEO/sécurité)
- [ ] Détecter `Crawl-delay` (non standard, info)
- [ ] Analyser `Allow` en complément de `Disallow`
- [ ] Comparer chemins Disallow avec endpoints sensibles connus

#### 5.1.7 Tech fingerprinting

**Existant (v0.1.0) :**
- Lire `Server`, `X-Powered-By`, `X-Generator`, `X-Drupal-Cache` ✅
- Heuristiques : Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal ✅
- Formulations indicatives (« probable », « détecté ») ✅

**En plus (v0.2.0) :**
- [ ] Extraire versions dans `Server`, `X-Powered-By` (ex. `nginx/1.18.0`)
- [ ] Base de données CPE/CVE : alerter si version connue vulnérable (lecture seule)
- [ ] Détection de technologies via balises HTML (`<meta generator>`, scripts)
- [ ] Rapport « stack probable » avec niveaux de confiance

---

### 5.2 Nouveaux tests — Information disclosure

#### 5.2.1 Fuites dans les réponses
- [ ] Détection de stack traces (PHP, Python, Java, .NET, Node) dans le body
- [ ] Détection de messages d’erreur debug (mode dev activé)
- [ ] Patterns sensibles : mots de passe, tokens, clés API dans le HTML/JSON
- [ ] Headers révélant des infos : `X-AspNet-Version`, `X-Powered-By` avec version

#### 5.2.2 Headers de débogage
- [ ] `X-Debug`, `X-Debug-Token`, `X-Runtime` (exposition temps d’exécution)
- [ ] `Server` avec version complète (ex. `Apache/2.4.41`)
- [ ] Headers custom révélant stack (ex. `X-Generator`)

---

### 5.3 Nouveaux tests — Cache et performances

#### 5.3.1 Headers de cache
- [ ] `Cache-Control` : présence, directives (`max-age`, `no-store`, `private` pour données sensibles)
- [ ] `Pragma: no-cache` (legacy, cohérence avec Cache-Control)
- [ ] `ETag` et `Last-Modified` (validation conditionnelle)
- [ ] `Vary` pour contenu négocié
- [ ] Alerte si page sensible (login, admin) cacheable publiquement

#### 5.3.2 Cache des ressources statiques
- [ ] Analyse des sous-requêtes (scripts, CSS, images) : headers Cache-Control
- [ ] Recommandation : cache long pour assets immuables

---

### 5.4 Nouveaux tests — CORS et cross-origin

#### 5.4.1 CORS
- [ ] `Access-Control-Allow-Origin: *` sur endpoints sensibles → finding
- [ ] `Access-Control-Allow-Credentials: true` + `Origin: *` → incohérence dangereuse
- [ ] Vérifier `Access-Control-Allow-Methods` (éviter PUT/DELETE si non nécessaire)
- [ ] `Access-Control-Expose-Headers` : exposition d’headers sensibles

#### 5.4.2 Cross-origin
- [ ] Détection de ressources chargées en HTTP sur page HTTPS (mixed content)
- [ ] `Cross-Origin-Resource-Policy` manquant sur APIs
- [ ] `Referrer-Policy` trop permissif (`unsafe-url`, absence)

---

### 5.5 Nouveaux tests — Méthodes HTTP et redirections

#### 5.5.1 Méthodes HTTP
- [ ] Requête `OPTIONS` : lister les méthodes autorisées
- [ ] `TRACE` activé → finding (XST)
- [ ] `PUT`, `DELETE`, `PATCH` exposés sans nécessité → info
- [ ] `HEAD` supporté (bonne pratique)

#### 5.5.2 Redirections
- [ ] Détection open redirect (paramètre `url`/`redirect`/`next` redirigeant vers domaine externe)
- [ ] Chaînes de redirection excessives (> 5)
- [ ] Redirection HTTP→HTTPS avec code 301/302 (pas 307/308 pour préserver méthode)

---

### 5.6 Nouveaux tests — Intégrité et sous-ressources

#### 5.6.1 Subresource Integrity (SRI)
- [ ] Scripts/CSS externes (CDN) sans attribut `integrity` → finding
- [ ] Recommandation : utiliser SRI pour ressources tierces

#### 5.6.2 Analyse du HTML
- [ ] Balises `<script>` sans `nonce` ou `integrity` (contexte CSP)
- [ ] Formulaires sans `autocomplete="off"` sur champs sensibles (password)
- [ ] `target="_blank"` sans `rel="noopener noreferrer"`
- [ ] Meta `robots` (noindex sur pages sensibles)

---

### 5.7 Nouveaux tests — APIs et formats

#### 5.7.1 APIs exposées
- [ ] Détection GraphQL : introspection activée sur `/graphql` ou similaire
- [ ] Swagger/OpenAPI exposé sans auth
- [ ] Endpoints REST retournant des listes non paginées (info)

#### 5.7.2 Formats de réponse
- [ ] `Content-Type` incorrect (ex. JSON servi en `text/html`)
- [ ] `X-Content-Type-Options: nosniff` vérifié sur tous les types
- [ ] Compression (gzip/brotli) pour réduire surface

---

### 5.8 Documentation et scoring

#### 5.8.1 Documentation
- [ ] Fichier `docs/verifications/` par catégorie de test
- [ ] Chaque check : risque, exemple, recommandation, référence OWASP/CWE
- [ ] Matrice de sévérité (critical/high/medium/low/info)

#### 5.8.2 Scoring
- [ ] Adapter le scoring pour les nouveaux checks (pondération)
- [ ] Règles d’upgrade/downgrade pour les findings critiques

---

## 6) API publique + clés API

### 6.1 Modèle
- [ ] Schéma : `api_keys` (id, user_id, key_hash, name, created_at, last_used_at)
- [ ] Génération : clé aléatoire (ex. 32 caractères) ; stocker uniquement le hash

### 6.2 Authentification
- [ ] Header `X-API-Key` ou `Authorization: Bearer <api_key>`
- [ ] Middleware : vérifier la clé, résoudre l’utilisateur, appliquer quotas

### 6.3 Quotas et rate limiting
- [ ] Quotas par clé : ex. 100 scans/jour
- [ ] Rate limiting : ex. 10 req/min par clé
- [ ] Réponse 429 si dépassement

### 6.4 API
- [ ] `POST /api/keys` : créer une clé (nom, retourne la clé en clair une seule fois)
- [ ] `GET /api/keys` : liste des clés (sans valeur)
- [ ] `DELETE /api/keys/{id}` : révoquer une clé

### 6.5 Frontend
- [ ] Page « Clés API » dans Mon compte
- [ ] Création, affichage (une fois), révocation
- [ ] Documentation : exemple curl avec `X-API-Key`

---

## 7) Intégration CI/CD (GitHub Action)

### 7.1 Action GitHub
- [ ] Répo `secureops/actions` ou action dans le monorepo
- [ ] Inputs : `url`, `api_key` (secret), `fail_on_score_below` (optionnel)

### 7.2 Comportement
- [ ] Appel `POST /scan/api/scan` (ou async + poll) avec `X-API-Key`
- [ ] Parse le résultat (score, findings)
- [ ] Fail le job si `score < fail_on_score_below` ou si finding critical

### 7.3 Documentation
- [ ] README : exemple d’utilisation dans un workflow
- [ ] Badge optionnel : « Scan SecureOps » sur le README du projet

---

## 8) Qualité / CI (V2)

### 8.1 Backend
- [ ] Tests unitaires pour les nouveaux modules (queue, worker, export)
- [ ] Tests d’intégration pour l’API async (mock queue)
- [ ] Coverage maintenu

### 8.2 Frontend
- [ ] Tests unitaires pour les nouveaux composants (dashboard, historique)
- [ ] E2E tests (optionnel) : login → scan → historique

---

## 9) Déploiement AWS (V2)

### 9.1 Infra
- [ ] SQS (ou Redis pour Celery)
- [ ] Worker déployé (EC2, ECS, ou Lambda)
- [ ] Scaling du worker selon la charge

### 9.2 Base de données
- [ ] Tables `scans`, `scheduled_scans`, `api_keys` (user-service ou scan-service)
- [ ] Backups et migrations

---

## 10) Release MVP v0.2.0

- [ ] Tag `v0.2.0`
- [ ] Release notes (nouvelles fonctionnalités vs v0.1.0)
- [ ] Migration guide (changements breaking : auth requise pour scan)
- [ ] Mise à jour de la documentation

---

# Notes importantes (MVP 0.2.0)

- L’authentification devient **requise** pour le scanner (sauf si API publique avec clé).
- Les scans sont **persistés** : respecter les limites de rétention et RGPD.
- L’API publique : **rate limiting** et **quotas** obligatoires pour éviter les abus.
- La protection SSRF + timeout reste **non négociable**.
