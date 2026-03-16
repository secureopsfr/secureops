# SecureOps — Roadmap MVP 0.4.0

Objectif : **finaliser tous les tests passifs** (section 5 de la v0.2.0), **introduire les tests actifs** (premiers pas), **rapports et analytics** (tendances, export, tableau de bord), **scan paramétrable** (ex. mode critical uniquement) et **explication du scoring** dans le frontend.

**Prérequis :** MVP 0.2.0 livré (API publique, clés API, scan avancé partiel, CI/CD).

**Périmètre des tests :** Pour chaque section, le périmètre est indiqué en *italique* sous le titre : **frontend** (UI, affichage, pages web cibles), **backend** (APIs, moteur scan, services), ou **les deux**.

## Sommaire

**Ordre recommandé pour la lecture et l'implémentation :** 0 (architecture) -> 1 (passif restant) -> 2 (vérification d'autorisation + 2.4 backend/doc API) -> 3 (actif MVP + backlog intrusif) -> 4 (rapports/analytics) -> 5 (scan paramétrable) -> 6 (infra/qualité) -> 7 (release).

- [0) Architecture : deux scanners](#0-architecture--deux-scanners)
  - [0.1 Rappel : passif vs actif](#01-rappel--passif-vs-actif)
- [1) Finaliser les tests passifs restants](#1-finaliser-les-tests-passifs-restants)
  - [1.1 Méthodes HTTP et redirections](#11-méthodes-http-et-redirections-ex-roadmap-55-voir-a-penser-plus-tard)
  - [1.2 Intégrité et sous-ressources](#12-intégrité-et-sous-ressources-56--restant-roadmap-020)
  - [1.3 APIs et formats](#13-apis-et-formats-ex-roadmap-57-voir-a-penser-plus-tard)
  - [1.4 Tests passifs complémentaires](#14-tests-passifs-complémentaires)
  - [1.5 Backlog tests reporté depuis la roadmap 0.3.0](#15-backlog-tests-reporté-depuis-la-roadmap-030)
  - [1.6 Backlog reporté depuis la roadmap 0.3.0 (hors section tests)](#16-backlog-reporté-depuis-la-roadmap-030-hors-section-tests)
  - [1.7 Adaptation des tests passifs pour scan_type backend](#17-adaptation-des-tests-passifs-pour-scan_type-backend)
- [2) Vérification d'autorisation (uniquement en production)](#2-vérification-dautorisation-uniquement-en-production)
  - [2.1 Méthode : vérification DNS](#21-méthode--vérification-dns)
  - [2.2 Flux utilisateur (Scanner 2 uniquement)](#22-flux-utilisateur-scanner-2-uniquement)
  - [2.3 Cas particuliers](#23-cas-particuliers)
- [2.4 Option backend et import de documentation API](#24-option-backend-et-import-de-documentation-api) *(prérequis avant tests actifs backend)*
- [3) Introduire les tests actifs (Scanner 2)](#3-introduire-les-tests-actifs-scanner-2)
  - [3.1 Cadre et sécurité](#31-cadre-et-sécurité)
  - [3.2 Tests actifs — Redirections](#32-tests-actifs--redirections-déjà-partiellement-actif)
  - [3.3 Tests actifs — Méthodes HTTP](#33-tests-actifs--méthodes-http)
  - [3.4 Tests actifs — CORS](#34-tests-actifs--cors)
  - [3.5 Tests actifs — Paramètres (premiers pas)](#35-tests-actifs--paramètres-premiers-pas)
  - [3.6 Tests actifs — Path traversal (léger)](#36-tests-actifs--path-traversal-léger)
  - [3.7 Tests actifs — Injection basique (erreurs révélatrices)](#37-tests-actifs--injection-basique-erreurs-révélatrices)
  - [3.8 Tests actifs — DoS (single-source, pas DDoS)](#38-tests-actifs--dos-single-source-pas-ddos)
  - [3.9 Documentation et scoring](#39-documentation-et-scoring)
  - [3.10 Backlog intrusif exhaustif](#310-backlog-intrusif-exhaustif-au-dela-du-mvp-strict)
  - [3.11 Garde-fous obligatoires](#311-garde-fous-obligatoires-toutes-phases)
  - [3.12 P0 — Indispensable](#312-p0--indispensable-common-forte-valeur)
  - [3.13 P1 — Très recommandé](#313-p1--tres-recommande)
  - [3.14 P2 — Avancé](#314-p2--avance-moins-frequent-impact-eleve-potentiel)
  - [3.15 P3 — Spécialisés](#315-p3--specialises)
  - [3.16 P4 — Rare/recherche](#316-p4--rarerecherche-mode-expert-explicite)
  - [3.17 Exigences techniques minimales](#317-exigences-techniques-minimales-moteur-intrusif)
  - [3.18 Ordre de développement recommandé](#318-ordre-de-developpement-recommande)
  - [3.19 Exhaustive checklist](#319-exhaustive-checklist-families-a-couvrir)
  - [3.20 Désactivé par défaut](#320-desactive-par-defaut-mode-expert-uniquement)
  - [3.21 Documentation cible](#321-documentation-cible)
- [4) Rapports et analytics](#4-rapports-et-analytics)
- [5) Scan paramétrable](#5-scan-paramétrable)
- [6) Infra et qualité](#6-infra-et-qualité)
- [7) Release MVP v0.4.0](#7-release-mvp-v040)
- [Synthèse](#synthèse)
- [Notes importantes (MVP 0.4.0)](#notes-importantes-mvp-040)
- [Périmètre des tests : URL frontend vs backend](#périmètre-des-tests--url-frontend-vs-backend)

---

## 0) Architecture : deux scanners

| Scanner | Tests | Vérification DNS | URLs autorisées |
|---------|-------|------------------|-----------------|
| **Scanner 1 (passif)** | Tests passifs uniquement | Non requise | Toutes les URLs |
| **Scanner 2 (actif)** | Tests passifs (optionnel) + tests actifs | **Obligatoire** | Uniquement les URLs dont le domaine a été vérifié par l’utilisateur |

### Scanner 1 — Passif

- Premier scanner, celui qui existe déjà (étendu avec tous les tests passifs).
- Fonctionne sur **n’importe quelle URL**.
- Aucune vérification d’autorisation requise.

### Scanner 2 — Actif

- Deuxième scanner, nouveau.
- **Ne fonctionne que pour les URLs dont le domaine a été vérifié** par l’utilisateur (voir section 2).
- **Option :** Inclure les tests passifs en premier (choix utilisateur, **défaut : oui**). Si activé : exécution des tests passifs puis des tests actifs. Si désactivé : tests actifs uniquement.
- Vérification DNS obligatoire avant tout scan.

---

## 0.1 Rappel : passif vs actif

| Type | Définition | Exemple |
|------|------------|---------|
| **Passif** | Lecture et analyse des réponses. Aucune requête « provocante ». | Lire les headers, analyser le HTML, détecter des patterns |
| **Actif** | Envoi de requêtes ou paramètres **craftés** pour provoquer un comportement révélateur. | Envoyer `?redirect=evil.com`, tester TRACE, envoyer un payload dans un paramètre |

> **Attention :** Les tests actifs peuvent déclencher des actions côté serveur (logs, alertes, blocages). Le disclaimer « usage autorisé uniquement » est **obligatoire**. Documenter les requêtes envoyées dans le rapport.

---

## 1) Finaliser les tests passifs restants

> Les tests passifs des sections 5.1 à 5.4 et 5.8 de la roadmap 0.2.0 sont livrés (TLS, headers, cookies, exposition fichiers, directory listing, robots, sitemap, tech fingerprinting, information disclosure, cache, CORS et cross-origin). Il reste à implémenter pour le Scanner 1 (passif) :

### 1.1 Méthodes HTTP et redirections (ex-roadmap 5.5, voir A-PENSER-PLUS-TARD)
*Périmètre : **les deux** (frontend et backend)*

- [ ] Requête OPTIONS : méthodes autorisées
- [ ] TRACE activé → finding (XST)
- [ ] PUT, DELETE, PATCH exposés sans nécessité → info
- [ ] HEAD supporté (bonne pratique)
- [ ] Détection open redirect (paramètres url/redirect/next)
- [ ] Chaînes de redirection excessives (> 5)
- [ ] Redirection HTTP→HTTPS : 301/302 vs 307/308

---

### 1.2 Intégrité et sous-ressources (5.6 — restant roadmap 0.2.0)
*Périmètre : **frontend** (HTML, scripts, formulaires)*

- [x] Scripts/CSS externes (CDN) sans attribut `integrity` → finding
- [x] Balises `<script>` sans nonce ou integrity (contexte CSP), uniquement lorsque l'en-tête CSP est présent (sinon, un message informe que les tests avancés ne sont pas appliqués)
- [x] Formulaires sans autocomplete adapté sur champs sensibles (password)
- [x] `target="_blank"` sans `rel="noopener noreferrer"`
- [x] Meta `robots` (noindex sur pages sensibles)

---

### 1.3 APIs et formats (ex-roadmap 5.7, voir A-PENSER-PLUS-TARD)
*Périmètre : **backend** (APIs, endpoints)*

- [ ] GraphQL : introspection activée sur `/graphql` ou similaire
- [ ] Swagger/OpenAPI exposé sans auth
- [ ] Endpoints REST : listes non paginées (info)
- [ ] Content-Type incorrect (JSON servi en text/html)
- [ ] X-Content-Type-Options: nosniff sur tous les types
- [ ] Compression (gzip/brotli)

---

### 1.4 Tests passifs complémentaires
*Périmètre : **frontend** (formulaires, meta) ; **les deux** (OWASP mapping, rapport conformité)*

- [ ] Formulaires : détection de tokens CSRF (présence de champ csrf_token, _token, etc.)
- [ ] Métadonnées : analyse des balises `<meta>` (robots, generator)
- [ ] Mapping OWASP Top 10 : associer chaque finding à une catégorie OWASP (A01–A10)
- [ ] Rapport de conformité : synthèse par catégorie OWASP

---

### 1.5 Backlog tests reporté depuis la roadmap 0.3.0
*Périmètre : **backend** (environnements, CI, scénarios d'intégration scan/crawl)*

Objectif : finaliser la couverture de tests d’intégration de la pipeline scan/crawl, reportée depuis la section 2 de la roadmap v0.3.0.

#### 1.5.1 Environnements et serveurs de test

- [ ] Définir un environnement de test dédié au scan (Docker Compose minimal : scan-service + Postgres si nécessaire).
- [ ] Ajouter un ou plusieurs **serveurs cibles de démo** :
  - [ ] Serveur HTTP simple (cache/headers/cookies) — ex. `bad_cache_server.py`.
  - [ ] Serveur simulant des headers de sécurité variés (bonnes pratiques / mauvaises pratiques).
  - [ ] Serveur avec fichiers exposés / directory listing / robots.txt / sitemap de test.
  - [ ] **Serveur avec pages liées (même domaine)** pour les tests crawler : plusieurs pages HTML avec liens internes, pour valider le scénario crawl → liste → scan sur N URLs (voir 1.5.2).
  - [ ] (Optionnel) Serveur d’API de démo (Swagger/GraphQL/Content-Type).

#### 1.5.2 Scénarios de tests d’intégration

- [ ] Scénario « happy path » : URL valide → scan complet → score cohérent → findings attendus.
- [ ] Scénarios d’erreur : DNS KO, timeout, TLS cassé, redirections excessives.
- [ ] Scénarios SSRF : URLs internes / localhost / IP privées bloquées en mode prod (`IS_PROD=true`).
- [ ] Scénarios de ports : ports non autorisés rejetés en prod, autorisés en dev (`IS_PROD=false` via `launch_dev.sh`).
- [ ] **Scénario crawler → liste → scan sur N URLs** : serveur de test avec pages liées (même domaine) ; lancer le crawler depuis une URL de départ, récupérer la liste d’URLs (via l’API crawler retenue en 7.3 de la v0.3.0), lancer le scan sur un sous-ensemble (ex. 2–3 URLs) ; vérifier que les résultats agrègent les findings par URL ou produisent un rapport cohérent (historique, PDF si applicable).
- [ ] Vérification des catégories de checks : TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, info disclosure, etc.
- [ ] Vérification de l’écriture en historique (user-service) et de la génération PDF.
- [ ] Crawler — tests unitaires : parsing HTML → liste d’URLs attendue ; respect Disallow ; limites (profondeur, max URLs).
- [ ] Crawler — test d’intégration : crawl d’une page de test (ex. `bad_crawl_server` ou fixture HTML) → vérifier la sortie et l’absence de fuite hors domaine.

#### 1.5.3 Intégration dans la CI

- [ ] Ajouter un job **tests d’intégration scan-service** dans la pipeline (GitHub Actions).
- [ ] Démarrer les services nécessaires (scan-service + serveurs de test) via Docker Compose dans le job.
- [ ] Lancer la suite de tests d’intégration (`pytest -m integration` ou répertoire dédié).
- [ ] Marquer le job comme requis pour les PR affectant le scan-service / gateway.

#### 1.5.4 Observabilité et maintenance des tests

- [ ] Logs clairs pour chaque scénario (URL cible, findings principaux).
- [ ] Documentation rapide dans `docs/` pour expliquer comment lancer les tests d’intégration en local.
- [ ] Stratégie de maintenance : limiter le nombre de scénarios mais couvrir les cas critiques (TLS, SSRF, cache, exposition fichiers, CORS, crawler + scan multi-URLs).

---

### 1.6 Backlog reporté depuis la roadmap 0.3.0 (hors section tests)
*Périmètre : **backend** (GitHub Action, gouvernance crawler) ; **frontend** (docs/UX, affichage anomalies)*

Objectif : centraliser dans la v0.4.0 les éléments non faits de la v0.3.0 liés à l’intégration CI/CD, au crawler, à la doc/UX scanner et au rendu d’anomalies.

#### 1.6.1 GitHub Action SecureOps (ex-section 3 de la v0.3.0)

- [ ] Créer la répo `secureops/actions` ou une action dans le monorepo.
- [ ] Définir les inputs : `url`, `api_key` (secret), `fail_on_score_below` (optionnel).
- [ ] Appeler `POST /scan/api/scan` avec `X-API-Key` (API publique SecureOps).
- [ ] Parser le résultat (score, findings).
- [ ] Faire échouer le job si `score < fail_on_score_below` ou si finding `critical`.
- [ ] Rédiger un README avec un exemple d’utilisation dans un workflow GitHub Actions.
- [ ] (Optionnel) Fournir un badge « Scan SecureOps » pour le README des projets utilisateurs.

#### 1.6.2 Gouvernance crawler (ex-section 7.6 de la v0.3.0)

- [ ] Liste noire configurable (ex. dans `settings.yml`) pour bloquer des domaines/cibles.
- [ ] Modération (optionnel) : ajouter a posteriori des domaines bloqués et logger les tentatives (audit).
- [ ] Quotas crawler, rate limiting, réponses 429 (aligné avec `A-PENSER-PLUS-TARD.md`).

#### 1.6.3 Scanner hub: docs/UX (ex-section 8.2 de la v0.3.0)

- [ ] Rapports et exports : accès aux PDF, exports CSV/JSON si implémentés.
- [ ] Alertes configurées, préférences de notification.
- [ ] Page/section doc regroupant : scan de posture (vérifications, crawling, interprétation), autres scanners, API publique (endpoints, clés API, exemples curl, CI/CD).
- [ ] Documentation contextuelle : lien doc depuis chaque page concernée (`/scanner/analyses/...`, `/scanner/cles-api`, etc.).

#### 1.6.4 Affichage anomalies (ex-section 8.4 de la v0.3.0)

- [ ] Finaliser le rendu “anomalie détectée” : icône dédiée dans résumé/table + libellé explicite “Anomalie détectée” / “Trouvé”.

---

### 1.7 Adaptation des tests passifs pour scan_type backend
*Périmètre : **backend** (moteur scan passif, pipeline)*

> **Contexte :** Lorsqu'un utilisateur lance un scan en mode **backend** (cible API, endpoint JSON/XML plutôt que page HTML), certaines étapes des tests passifs dépendent du **HTML** pour fonctionner (extraction de sous-ressources, meta generator, mixed content). Ces étapes sont sans pertinence ou non applicables sur une réponse API. On **ne supprime pas** le code : on ne l'exécute simplement pas quand `scan_type == "backend"`.

#### Propagation de scan_type dans la pipeline

- [x] **ScanContext** (`_scan_core.py`) : ajout du champ `scan_type` (défaut `"frontend"`).
- [x] **scan_stream_generator** (`scan_stream.py`) : paramètre keyword-only `scan_type` propagé à `_run_pipeline_steps` puis `_run_checks_with_client`.
- [x] **async_scan_executor** : lorsqu'on utilise le flux passive, passage explicite de `scan_type` (issu du job) au générateur.
- [x] Les lambdas des étapes SCAN_STEPS reçoivent `ctx.scan_type` et le transmettent aux fonctions de check concernées.

#### Comportement par check (backend vs frontend)

| Check | Comportement frontend | Comportement backend |
|-------|------------------------|----------------------|
| **cache** | Analyse des headers de la page **+** analyse des sous-ressources (JS/CSS/images extraites du HTML) | Analyse des headers de la page uniquement ; **pas** d'analyse des sous-ressources |
| **cors_cross_origin** | Vérifications CORS (ACAO, credentials, CORP) **+** contrôle mixed content (ressources HTTP sur page HTTPS) | Vérifications CORS uniquement ; **pas** de contrôle mixed content |
| **tech_fingerprinting** | Analyse des headers (Server, X-Powered-By) **+** détection via HTML (meta generator, scripts) | Analyse des headers uniquement ; **pas** de `_detect_from_html` |
| **sitemap** | Vérification Sitemap (robots.txt, sitemap.xml, URLs sensibles) | **Étape entière ignorée** (non pertinente pour une API) |
| **integrity** | Intégrité HTML (SRI, scripts, formulaires, target="_blank", meta robots) | **Étape entière ignorée** (réponse JSON/XML, pas de HTML) |
| **robots_txt** | Présence et contenu de robots.txt (Disallow, Sitemap) | **Étape entière ignorée** (non pertinent pour une API) |

#### Implémentation technique

- [x] **cache** (`both/cache/checks.py`) : `check_cache_from_response(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_analyze_subresources`.
- [x] **cors_cross_origin** (`both/cors_cross_origin/checks.py`) : `run_cors_cross_origin_checks(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_check_mixed_content`.
- [x] **tech_fingerprinting** (`both/tech_fingerprinting/checks.py`) : `check_tech_fingerprinting_from_response(..., scan_type="frontend")` ; si `scan_type == "backend"`, on n'appelle pas `_detect_from_html`.
- [x] **robots_txt**, **sitemap** et **integrity** : étapes entièrement ignorées quand `scan_type == "backend"` (voir `_FRONTEND_ONLY_STEPS` dans `scan_stream.py`). Ces catégories sont exclues des `category_summaries` et du `total_tests_count` pour les scans backend (voir `build_findings_bundle` avec `_FRONTEND_ONLY_CATEGORIES`).

#### Restructuration frontend

- [x] **robots_txt** déplacé de `both/` vers `frontend/` pour cohérence avec sitemap et integrity (ces trois checks sont frontend-only). Imports mis à jour dans `_scan_core`, `multi_scan_orchestrator`, `normalization` et les tests.

#### Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `passive/_scan_core.py` | `ScanContext.scan_type` ; lambdas cache, cors, tech_fingerprinting ; `_FRONTEND_ONLY_CATEGORIES` ; `build_findings_bundle(..., scan_type)` ; import `frontend.robots_txt` |
| `passive/scan_stream.py` | `scan_type` dans `_run_checks_with_client`, `_run_pipeline_steps`, `scan_stream_generator` ; `_FRONTEND_ONLY_STEPS` (robots_txt, sitemap, integrity) |
| `async_scan_executor.py` | Appel `passive_scan_stream_generator(url, authorization=None, scan_type=scan_type)` |
| `both/cache/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_analyze_subresources` |
| `both/cors_cross_origin/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_check_mixed_content` |
| `both/tech_fingerprinting/checks.py` | Paramètre `scan_type` ; condition `if scan_type != "backend"` avant `_detect_from_html` |
| `passive/frontend/robots_txt/` | **Nouveau** — module déplacé depuis `both/` (checks, normalizer, __init__) |
| `passive/normalization.py` | Import `frontend.robots_txt` |
| `passive/multi_scan_orchestrator.py` | Import `frontend.robots_txt` |

---

## 2) Vérification d’autorisation (uniquement en production)
*Périmètre : **backend** (vérification DNS, cache) ; **frontend** (flux utilisateur, affichage token)*

> **Document dédié :** voir [VERIFICATION-AUTORISATION.md](VERIFICATION-AUTORISATION.md) pour la spécification complète.

Cette section est une **partie à part** de la roadmap. La vérification DNS est **requise uniquement pour le Scanner 2 (actif)**. Le Scanner 1 (passif) n’en a pas besoin.

- [ ] La vérification est **activée uniquement en production** (désactivée en dev/local)
- [ ] Seuls les domaines **vérifiés** par l’utilisateur peuvent être scannés avec le Scanner 2

### 2.1 Méthode : vérification DNS

Comme pour Let's Encrypt, Google Search Console : l’utilisateur ajoute un enregistrement DNS **TXT** pour prouver qu’il contrôle le domaine.

- [ ] **Génération :** Pour chaque domaine à scanner, générer un token unique (ex. `secureops-verify-abc123xyz`)
- [ ] **Enregistrement attendu :** `_secureops-verify.<domaine> TXT "secureops-verify-abc123xyz"`
- [ ] **Vérification :** Avant le scan actif, résoudre le TXT du sous-domaine et vérifier que la valeur correspond au token
- [ ] **Cache :** Une fois un domaine vérifié pour un utilisateur, stocker la preuve (domaine + user_id + date) — validité ex. 90 jours
- [ ] **Environnement :** Vérification activée uniquement si `AUTHORIZATION_CHECK_ENABLED=true` (production)

### 2.2 Flux utilisateur (Scanner 2 uniquement)

1. L’utilisateur choisit le **Scanner 2 (actif)** et saisit l’URL
2. Si le domaine n’est pas encore vérifié : le système affiche « Ajoutez cet enregistrement DNS : `_secureops-verify.example.com TXT "votre-token"` »
3. L’utilisateur ajoute l’enregistrement dans le gestionnaire DNS de son domaine
4. Clic sur « Vérifier » → résolution DNS → si OK, le scan est autorisé
5. Si le domaine est déjà vérifié (cache), le scan peut démarrer directement

### 2.3 Cas particuliers

- [ ] **Fallback :** En dev/local, ou si la vérification DNS échoue (timeout, DNS privé), option de fallback : case à cocher + avertissement
- [ ] **API publique :** Domaine pré-vérifié dans le compte, ou acceptation préalable (doc + CGU)

---

### 2.4 Option backend et import de documentation API
*Périmètre : **frontend** (formulaire, case à cocher, upload) ; **backend** (parsing spec)*

> **Prérequis avant le développement des tests actifs backend.** À implémenter avant ou en parallèle des tests IDOR, mass assignment, GraphQL, etc.

#### Contexte : crawler et scan frontend vs backend

- **Cible frontend** : le crawler agit comme actuellement. Checkbox « Scanner uniquement cette page » : si **coché** → pas de crawl, scan direct sur l'URL ; si **décoché** → crawler (découverte des pages du site) puis scan multi-URL.
- **Cible backend** : pas de crawler (une API n'est pas parcourue comme un site HTML). La checkbox change de libellé et de sens :
  - **Coché** : « Scanner uniquement cet endpoint » — scan direct sur l'URL API saisie.
  - **Décoché** : « Scanner plusieurs endpoints » — affichage d'une zone d'**import de documentation API** (drag-and-drop de fichier). Les endpoints sont extraits de la doc fournie par l'utilisateur ; **pas de recherche automatique** (bruteforce de chemins de doc exclu pour l'instant).
- **Sans doc** (backend, multi-endpoints) : les tests se limitent à la liste fixe configurée dans `settings.yml` (`sensitive_paths`, `exposed_files`).

#### Comportement attendu (UI)

- [ ] **Scan type backend** : le libellé de la checkbox devient « Scanner uniquement cet endpoint » (ou équivalent).
- [ ] **Quand décoché (backend)** : affichage d'une section « Fournissez la documentation API pour scanner plusieurs endpoints » avec :
  1. **Drag-and-drop de fichier** : OpenAPI (`.json`, `.yaml`), Postman Collection (`.json`).
- [ ] **Avec doc** : le scanner parse la spec et extrait la liste des endpoints (méthode, chemin, paramètres) pour le scan multi-URL.
- [ ] **Sans doc** : scan sur la liste fixe de chemins uniquement.

#### Formats acceptés pour l'import

| Format | Support | Source |
|--------|---------|--------|
| **OpenAPI / Swagger** | Fichier | Drag-and-drop `.json` ou `.yaml` |
| **Postman Collection** | Fichier | Drag-and-drop `.json` (v2.0, v2.1) |

> **Hors périmètre pour l'instant** : bruteforce automatique des chemins de doc (`/swagger`, `/openapi.json`, etc.) sur l'URL backend. La liste d'endpoints provient uniquement de l'import utilisateur ou de la liste fixe.

#### Décisions d'implémentation

- [ ] **Flux** : identique au crawler — parse doc → affichage des endpoints → étape de validation (ajout/suppression) → bouton « Lancer le scan » → scan passif multi-URL.
- [ ] **Parsing** : côté frontend (libs JS pour OpenAPI, Postman). Le frontend envoie une **liste d'URLs** au backend, pas le fichier.
- [ ] **Limite endpoints** : 200 max (aligné sur la limite crawler).
- [ ] **Formats** : OpenAPI/Swagger, Postman Collection dès le début.

#### Tests concernés

Les tests actifs orientés backend (IDOR, mass assignment, GraphQL abuse, injection sur API, etc.) s'appuient sur la liste d'endpoints issue de la doc importée ou de la liste fixe.

---

## 3) Introduire les tests actifs (Scanner 2)
*Périmètre des tests : selon le type — voir détail par sous-section*

> **Principe :** Tests actifs **légers** au départ. Pas de fuzzing massif, pas de bruteforce. Requêtes ciblées pour détecter des vulnérabilités courantes.

> **Scanner 2 :** Ce scanner ne fonctionne que pour les URLs dont le domaine a été vérifié par l’utilisateur (section 2). Option : inclure les tests passifs en premier (défaut : oui).

### 3.1 Cadre et sécurité

- [ ] **Choix utilisateur :** Inclure les tests passifs avant les tests actifs (défaut : **oui**). Si oui : exécution passif → actif. Si non : actif uniquement.
- [ ] Définir une section « Tests actifs » dans le disclaimer (avertissement renforcé)
- [ ] Documenter chaque requête envoyée dans le rapport (transparence)
- [ ] Rate limiting renforcé pour les tests actifs (éviter surcharge cible)
- [ ] **Contrôle d’accès :** Le Scanner 2 refuse toute URL dont le domaine n’a pas été vérifié par l’utilisateur

---

### 3.2 Tests actifs — Redirections (déjà partiellement actif)
*Périmètre : **les deux** (pages frontend avec redirect ; endpoints backend avec redirect_uri)*

- [ ] Open redirect : envoyer `?redirect=https://evil.com`, `?next=//evil.com`, `?url=...` et vérifier si redirection vers domaine externe
- [ ] Paramètres à tester : `redirect`, `url`, `next`, `return`, `redirect_uri`, `returnUrl`, `continue`, `destination`

---

### 3.3 Tests actifs — Méthodes HTTP
*Périmètre : **les deux** (toute URL peut exposer OPTIONS, TRACE, HEAD)*

- [ ] Requête OPTIONS : récupérer Allow
- [ ] Requête TRACE : détecter XST (si 200 + écho de la requête)
- [ ] Requête HEAD : vérifier support

---

### 3.4 Tests actifs — CORS
*Périmètre : **les deux** (frontend et API peuvent mal configurer CORS)*

- [ ] Envoyer requête avec `Origin: https://evil.com` (ou domaine de test)
- [ ] Vérifier si réponse contient `Access-Control-Allow-Origin: https://evil.com` + `Credentials: true` → réflexion non validée

---

### 3.5 Tests actifs — Paramètres (premiers pas)
*Périmètre : **les deux** (pages web avec paramètres réfléchis ; APIs avec paramètres dans les réponses)*

- [ ] Détection de paramètres réfléchis : envoyer une chaîne unique (ex. `SecureOpsTest123`) dans les paramètres courants (`q`, `search`, `query`, `id`, `page`, etc.)
- [ ] Si la chaîne apparaît dans la réponse HTML → paramètre réfléchi (info, vecteur potentiel XSS)
- [ ] Ne pas envoyer de payload XSS à ce stade ; uniquement détection de réflexion

---

### 3.6 Tests actifs — Path traversal (léger)
*Périmètre : **backend** (paramètres file, path, document sur endpoints)*

- [ ] Tester `../` dans des paramètres de fichier courants (`file`, `path`, `document`, `template`, `include`)
- [ ] Exemple : `?file=../../../etc/passwd` — si erreur différente (500, message d’erreur) ou contenu suspect → finding
- [ ] Limiter à 1–2 requêtes par paramètre ; pas de fuzzing exhaustif

---

### 3.7 Tests actifs — Injection basique (erreurs révélatrices)
*Périmètre : **backend** (formulaires/APIs qui interrogent la BDD)*

- [ ] SQL : envoyer `'` ou `"` dans paramètres (id, search, etc.) — détecter messages d’erreur SQL dans la réponse (MySQL, PostgreSQL, etc.)
- [ ] Pas d’exploitation ; uniquement détection d’erreur non gérée révélant une injection possible
- [ ] Liste de patterns d’erreur : `SQL syntax`, `mysql_fetch`, `PostgreSQL`, `ORA-`, `SQLite`, etc.

---

### 3.8 Tests actifs — DoS (single-source, pas DDoS)
*Périmètre : **les deux** (tout endpoint peut être ciblé)*

> **Périmètre :** Tests depuis **une seule source** (le scanner) pour évaluer la résilience ou les indicateurs de vulnérabilité DoS. Pas de test DDoS (pas de volume distribué).

- [ ] **Détection d'absence de rate limiting** : envoi d'un petit nombre de requêtes rapprochées (ex. 5–10 req/s sur une courte fenêtre) ; si le serveur répond sans ralentir ni retourner 429/503 → finding info « Pas de rate limiting détecté » (indicateur de risque DoS).
- [ ] **Requêtes lentes (Slowloris-like, léger)** : ouvrir une ou deux connexions avec envoi très étalé des en-têtes (sans viser à saturer) ; si le serveur garde la connexion ouverte longtemps sans timeout côté serveur → info sur configuration des timeouts.
- [ ] **Seuils configurables** : nombre max de requêtes et durée du test DoS strictement limités (ex. 10 requêtes, 2 s) pour ne pas impacter la cible.
- [ ] **Documentation** : documenter dans le rapport les requêtes utilisées et le fait que le test est limité (single-source, pas d'exploitation).

---

### 3.9 Documentation et scoring
*Périmètre : **backend** (matrice sévérité, pondération) ; **frontend** (section rapport PDF)*

- [ ] Créer `docs/verifications/` pour chaque nouveau test actif
- [ ] Matrice de sévérité par test
- [ ] Adapter le scoring : pondération des findings actifs (souvent plus graves)
- [ ] Section « Requêtes envoyées » dans le rapport PDF (optionnel, pour transparence)

---

### 3.10 Backlog intrusif exhaustif (au-dela du MVP strict)
*Périmètre : **backend** (P0-P4) ; **frontend** (XSS réfléchi) ; **les deux** (open redirect, CORS, méthodes HTTP, rate limiting)*

> Cette section migre le catalogue des tests intrusifs complets dans la roadmap v0.4.0 afin de centraliser la trajectoire Scanner 2.
> Les items ci-dessous sont priorises P0 -> P4 et complete la section 3 (premiers tests actifs).

### 3.11 Garde-fous obligatoires (toutes phases)
*Périmètre : **backend** (moteur scanner)*

- [ ] Autorisation forte : preuve de controle du domaine (DNS TXT), audit trail, acceptation explicite
- [ ] Kill switch global : arret immediat d'un scan actif en cours
- [ ] Rate limit strict par hote, endpoint, categorie
- [ ] Budget de requetes par test / endpoint / scan
- [ ] Timeouts courts + retries limites + jitter
- [ ] Methodes interdites par defaut : `PUT`, `PATCH`, `DELETE`, `POST` non idempotent (sauf opt-in explicite)
- [ ] Payload safety : pas d'ecriture irreversible, pas d'exfiltration reelle
- [ ] Journalisation complete : requete redigee, cible, timestamp, statut, evidence
- [ ] Scopes explicites (frontend, backend optionnel, exclusions)
- [ ] Protection SSRF non negociable cote scanner

---

### 3.12 P0 — Indispensable (common, forte valeur)
*Périmètre : **backend** (auth, session, IDOR, SQLi, path traversal, command injection, CSRF, rate limiting) ; **frontend** (XSS réfléchi) ; **les deux** (open redirect, CORS, méthodes HTTP)*

#### Authentification et session

- [ ] Bruteforce protection login (lockout, backoff, captcha, 429)
- [ ] Enumeration utilisateur (messages differencies)
- [ ] Session fixation (rotation post-login)
- [ ] Invalidation session (logout effectif token/cookie)
- [ ] JWT basique (alg, exp, nbf, aud, iss)

#### Autorisation (IDOR / BOLA / BFLA)

- [ ] Escalade horizontale (`/users/{id}` ou equivalent)
- [ ] Escalade verticale (routes admin acces role non admin)
- [ ] Controle objet/fonction manquant sur API

#### Injections frequentes

- [ ] SQLi error-based + time-based leger
- [ ] NoSQLi basique (operateurs/injection de structure JSON)
- [ ] XSS reflechi (detection de reflexion + contexte)
- [ ] Path traversal (variantes encodees)
- [ ] Command injection basique (erreurs/comportements anormaux)

#### Web/API classiques

- [ ] Open redirect actif
- [ ] CORS actif (origin reflection + credentials)
- [ ] Methodes HTTP (OPTIONS/TRACE/HEAD)
- [ ] CSRF presence + enforcement
- [ ] Rate limiting endpoint (burst court controle)

---

### 3.13 P1 — Tres recommande
*Périmètre : **backend** (upload, GraphQL, mass assignment, SSRF, XXE, SSTI, deserialization)*

#### Upload et contenu utilisateur

- [ ] Upload type non autorise (MIME spoof, double extension, malforme)
- [ ] Execution de fichier upload (acces direct + execution serveur)
- [ ] Traversal via nom de fichier

#### APIs modernes

- [ ] GraphQL actif (introspection, depth, alias, batching abuse)
- [ ] Mass assignment (champs sensibles acceptes sans whitelist)
- [ ] Validation schema (type confusion, champs inattendus, arrays excessifs)
- [ ] Pagination abuse (`limit` excessif, bornes absentes)

#### SSRF applicative

- [ ] SSRF via parametres URL (parsing/schemas/redirections)
- [ ] Metadata cloud probes en safe mode (sans exfiltration)

#### XML/Template/Deserialize

- [ ] XXE
- [ ] SSTI
- [ ] Insecure deserialization (selon techno)

---

### 3.14 P2 — Avance (moins frequent, impact eleve potentiel)
*Périmètre : **backend** (request smuggling, cache poisoning, host header, race conditions, business logic)*

#### HTTP/cache avances

- [ ] HTTP request smuggling / desync (`CL`/`TE`)
- [ ] Cache poisoning (en-tetes non normalises)
- [ ] Web cache deception
- [ ] Host header injection (reset password poisoning, liens absolus)

#### Conditions de course

- [ ] Double spend / double action
- [ ] TOCTOU (check/use)

#### Business logic abuse

- [ ] Bypass workflow metier
- [ ] Abuse coupons/credits
- [ ] Actions hors fenetre metier

---

### 3.15 P3 — Specialises
*Périmètre : **backend** (WebSocket, GraphQL subscriptions, gRPC, OAuth/OIDC, SSO, object storage)*

#### Temps reel et protocoles

- [ ] WebSocket authz
- [ ] GraphQL subscriptions abuse
- [ ] gRPC abuse

#### Infra/cloud ciblee

- [ ] Object storage exposure test actif
- [ ] Service mesh/internal API exposure

#### Auth avancee

- [ ] OAuth/OIDC misconfig (`redirect_uri`, `state`, PKCE)
- [ ] SSO relay state abuse

---

### 3.16 P4 — Rare/recherche (mode expert explicite)
*Périmètre : **backend** (tous ces tests ciblent des endpoints)*

- [ ] DoS applicatif controle (burst, slow request/headers, amplification)
- [ ] HTTP/2 abuse patterns
- [ ] Unicode normalization confusion sur authz
- [ ] DNS rebinding applicatif
- [ ] Parser differential attacks multi-proxy

---

### 3.17 Exigences techniques minimales (moteur intrusif)
*Périmètre : **backend** (moteur de scan)*

#### Moteur de requetes

- [ ] Rejouer methodes, headers, query, body
- [ ] Support encodages URL/double URL/unicode/JSON
- [ ] Session stateful (cookies/tokens), isolation entre tests
- [ ] Retry intelligent + jitter

#### Moteur de payloads

- [ ] Payloads parametrables par categorie
- [ ] Mutations auto (case, encodings, wrappers)
- [ ] Payload IDs uniques pour tracer la reflexion

#### Detection

- [ ] Signatures regex (SQL/template/parser/errors)
- [ ] Diff baseline/probe
- [ ] Detection temporelle robuste au bruit
- [ ] Heuristiques anti faux positifs

#### Reporting

- [ ] Requete redigee, endpoint, parametre, payload_id
- [ ] Observation brute + interpretation
- [ ] Reproduction minimale
- [ ] Recommandation concrete

---

### 3.18 Ordre de developpement recommande
*Périmètre : mix **frontend** + **backend** selon la famille de test (voir 3.12-3.16)*

#### Phase A (MVP intrusif)

- [ ] Open redirect
- [ ] Methodes HTTP
- [ ] CORS actif
- [ ] Reflection params
- [ ] SQL error-based basique
- [ ] Path traversal basique
- [ ] CSRF enforcement basique
- [ ] IDOR simple

#### Phase B

- [ ] NoSQLi, SSTI, XXE
- [ ] Upload abuse
- [ ] Mass assignment
- [ ] Rate limiting/auth abuse (lockout, enumeration)
- [ ] Session tests (fixation/invalidation)

#### Phase C

- [ ] Request smuggling/desync
- [ ] Cache poisoning/deception
- [ ] Race conditions
- [ ] WebSocket/gRPC/OAuth avances
- [ ] DoS controle (toujours borne)

---

### 3.19 Exhaustive checklist (families a couvrir)
*Périmètre : **backend** (majorité) ; **frontend** (XSS) ; **les deux** (CORS, open redirect, méthodes HTTP)*

- [ ] Auth brute force / lockout / enumeration
- [ ] Session fixation / invalidation / token lifecycle
- [ ] Horizontal + vertical authorization (IDOR/BOLA/BFLA)
- [ ] CSRF enforcement
- [ ] CORS actif (origin reflection, credentials)
- [ ] Open redirect
- [ ] Methodes HTTP (OPTIONS/TRACE/HEAD)
- [ ] SQLi (error/time)
- [ ] NoSQLi
- [ ] XSS reflechi (detection)
- [ ] Command injection basique
- [ ] Path traversal
- [ ] File inclusion (LFI/RFI selon techno)
- [ ] XXE
- [ ] SSTI
- [ ] Insecure deserialization
- [ ] Upload abuse (MIME, extension, execution)
- [ ] Mass assignment
- [ ] GraphQL abuse (introspection/depth/alias/batch)
- [ ] GraphQL subscriptions abuse (sous-categorie GraphQL)
- [ ] API schema validation abuse
- [ ] Pagination abuse (limit excessif, bornes absentes — sous-categorie API schema)
- [ ] SSRF applicative
- [ ] Host header injection
- [ ] Cache poisoning / web cache deception
- [ ] HTTP request smuggling / desync
- [ ] Race conditions
- [ ] Business logic abuse
- [ ] WebSocket authz
- [ ] OAuth/OIDC misuse
- [ ] DoS controle (borne) — P0 leger (rate limiting) ; P4 mode expert

---

### 3.20 Desactive par defaut (mode expert uniquement)
*Périmètre : **backend** (exécution) ; **frontend** (opt-in UI)*

- [ ] Tests potentiellement destructifs
- [ ] Scenarios impliquant ecriture irreversible
- [ ] Flood haute frequence longue duree
- [ ] Exploitation complete (RCE, exfiltration)

Activation uniquement en mode expert, avec opt-in explicite et limites strictes.

---

### 3.21 Documentation cible
*Périmètre : **backend** (docs techniques)*

- [ ] Toutes les specs intrusives detaillees dans `docs/verifications/intrusive/`
- [x] Catalogue complet intrusif versionne et maintenu dans `docs/verifications/intrusive/catalogue-complet-tests-intrusifs.md`
- [x] Architecture et mutualisation : `docs/verifications/intrusive/architecture-mutualisation.md`

---

## 4) Rapports et analytics
*Périmètre : **backend** (calcul, agrégation, export) ; **frontend** (affichage, graphiques, tableau de bord, explication scoring)*

### 4.1 Tendances

- [ ] Évolution du score dans le temps (par URL)
- [ ] Graphique de tendance sur la page détail d'un scan
- [ ] Comparaison entre deux scans (diff des findings)

### 4.2 Export

- [ ] Export CSV des findings (pour analyse)
- [ ] Export JSON structuré (pour intégrations)

### 4.3 Frontend

- [ ] Page « Tableau de bord » avec métriques
- [ ] Graphiques de tendance

### 4.4 Explication du scoring

- [ ] Afficher dans le frontend comment est calculé le score (formule, pondération par gravité)
- [ ] Tooltip ou lien « Comment est calculé le score ? » à proximité du score affiché
- [ ] Explication des niveaux de gravité (critical, high, medium, low, info) et de leur impact sur le score
- [ ] Page ou modal dédiée décrivant le système de scoring (optionnel)

---

## 5) Scan paramétrable
*Périmètre : **les deux** (frontend : UI sélecteur de mode ; backend : logique de filtrage par gravité/catégorie)*

Rendre le scan **simple à paramétrer** pour adapter la profondeur et le périmètre selon les besoins.

### 5.1 Filtrage par gravité

- [ ] Mode « Uniquement critical » : n’exécuter que les checks dont les findings seraient en gravité critical
- [ ] Mode « Critical + high » : limiter aux findings critical et high
- [ ] Mode « Complet » (défaut) : tous les checks
- [ ] Interface simple : sélecteur de mode (ex. liste déroulante ou boutons radio) avant le lancement du scan

### 5.2 Autres options (optionnel)

- [ ] Désactiver des catégories de tests (ex. désactiver « Exposition fichiers »)
- [ ] Profondeur limitée (ex. pas de tests actifs, uniquement passif)
- [ ] Préférences sauvegardées par utilisateur

---

## 6) Infra et qualité
*Périmètre : **backend** (mode async, config, tests unitaires)*

### 6.1 Mode asynchrone (optionnel)

- [ ] Si les tests actifs allongent le scan (> 30s), envisager le mode async (voir A-PENSER-PLUS-TARD.md)

### 6.2 Tests unitaires

- [ ] Tests pour chaque nouveau check passif et actif
- [ ] Mocks des réponses HTTP pour les tests actifs

### 6.3 Configuration

- [ ] Option `active_scan_enabled` dans la config (défaut : true)
- [ ] Option `active_scan_max_requests_per_param` pour limiter les requêtes

---

## 7) Release MVP v0.4.0

- [ ] Tag `v0.4.0`
- [ ] Release notes : tests passifs complets + premiers tests actifs + rapports et analytics + scan paramétrable + explication du scoring
- [ ] Mise à jour du disclaimer (tests actifs)
- [ ] Documentation : liste des requêtes envoyées en mode actif

# Synthèse

| Version | Tests |
|---------|-------|
| **0.1.0** | Tests passifs de base (TLS, headers, cookies, fichiers, directory listing, robots, fingerprinting) |
| **0.2.0** | Améliorations + nouveaux tests passifs (5.1–5.7 partiels) + API publique, export, monitoring |
| **0.4.0** | **Scanner 1 (passif)** : tous les tests passifs finalisés, toute URL. **Scanner 2 (actif)** : tests passifs (optionnel, défaut oui) + premiers tests actifs, **uniquement URLs vérifiées** (DNS). **Rapports et analytics** : tendances, export CSV/JSON, tableau de bord. **Scan paramétrable** : mode par gravité (ex. critical uniquement). **Scoring** : explication dans le frontend. |

---

# Notes importantes (MVP 0.4.0)

- Les tests actifs envoient des requêtes **craftées**. Le disclaimer « usage autorisé uniquement » doit être explicite.
- **Deux scanners :** Scanner 1 (passif) = toute URL. Scanner 2 (actif) = uniquement les URLs dont le domaine a été vérifié via DNS. La vérification DNS est activée uniquement en production.
- Commencer par des tests actifs **légers** ; pas de fuzzing, pas de bruteforce.
- Documenter chaque requête pour la transparence et l’audit.
- La protection SSRF côté scanner reste **non négociable** (les tests actifs ne doivent pas permettre de scanner des IP internes).

---

## Périmètre des tests : URL frontend vs backend

Certains tests (exposition fichiers, API docs, directory listing, etc.) s'exécutent **uniquement sur l'URL saisie par l'utilisateur**, qui correspond généralement au **frontend** (site web public). Or, les endpoints sensibles (Swagger, GraphQL, fichiers de config, répertoires de backup) sont souvent hébergés sur une **URL backend** distincte (ex. `api.example.com`, `backend.example.com`).

**État actuel :** Les tests d'exposition fichiers, API docs, directory listing et similaires ne s'exécutent que sur l'URL frontend. Si le backend est sur un autre domaine/sous-domaine, ces tests ne le couvrent pas.

**Améliorations envisagées :**

1. **Détection automatique du backend** : tenter d'inférer l'URL backend à partir du frontend (ex. analyse des requêtes XHR/fetch dans le HTML, liens vers des APIs, patterns courants `api.`, `backend.`, `*.api.`).
2. **URL backend optionnelle** : proposer à l'utilisateur de saisir une **URL backend** en option lors du scan. Si fournie, exécuter ces tests sur les deux URLs (frontend + backend).
3. **Autres tests concernés** : exposition fichiers, directory listing, endpoints API docs (Swagger, GraphQL), information disclosure (stack traces, headers debug), éventuellement CORS et méthodes HTTP sur les endpoints API.

**Recommandation :** À court terme, documenter cette limitation dans l'interface (tooltip ou notice). À moyen terme, implémenter l'option « URL backend optionnelle » pour étendre la couverture des tests. Voir [section 2.4](#24-option-backend-et-import-de-documentation-api) pour l'option backend et l'import de documentation API.
