# SecureOps — Roadmap MVP 0.4.0

Objectif : **finaliser tous les tests passifs** (section 5 de la v0.2.0), **introduire les tests actifs** (premiers pas), **rapports et analytics** (tendances, export, tableau de bord), **scan paramétrable** (ex. mode critical uniquement) et **explication du scoring** dans le frontend.

**Prérequis :** MVP 0.2.0 livré (API publique, clés API, scan avancé partiel, CI/CD).

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

- [ ] Requête OPTIONS : méthodes autorisées
- [ ] TRACE activé → finding (XST)
- [ ] PUT, DELETE, PATCH exposés sans nécessité → info
- [ ] HEAD supporté (bonne pratique)
- [ ] Détection open redirect (paramètres url/redirect/next)
- [ ] Chaînes de redirection excessives (> 5)
- [ ] Redirection HTTP→HTTPS : 301/302 vs 307/308

---

### 1.2 Intégrité et sous-ressources (5.6 — restant roadmap 0.2.0)

- [x] Scripts/CSS externes (CDN) sans attribut `integrity` → finding
- [x] Balises `<script>` sans nonce ou integrity (contexte CSP), uniquement lorsque l'en-tête CSP est présent (sinon, un message informe que les tests avancés ne sont pas appliqués)
- [x] Formulaires sans autocomplete adapté sur champs sensibles (password)
- [x] `target="_blank"` sans `rel="noopener noreferrer"`
- [x] Meta `robots` (noindex sur pages sensibles)

---

### 1.3 APIs et formats (ex-roadmap 5.7, voir A-PENSER-PLUS-TARD)

- [ ] GraphQL : introspection activée sur `/graphql` ou similaire
- [ ] Swagger/OpenAPI exposé sans auth
- [ ] Endpoints REST : listes non paginées (info)
- [ ] Content-Type incorrect (JSON servi en text/html)
- [ ] X-Content-Type-Options: nosniff sur tous les types
- [ ] Compression (gzip/brotli)

---

### 1.4 Tests passifs complémentaires

- [ ] Formulaires : détection de tokens CSRF (présence de champ csrf_token, _token, etc.)
- [ ] Métadonnées : analyse des balises `<meta>` (robots, generator)
- [ ] Mapping OWASP Top 10 : associer chaque finding à une catégorie OWASP (A01–A10)
- [ ] Rapport de conformité : synthèse par catégorie OWASP

---

### 1.5 Backlog tests reporté depuis la roadmap 0.3.0

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

## 2) Vérification d’autorisation (uniquement en production)

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

## 3) Introduire les tests actifs (Scanner 2)

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

- [ ] Open redirect : envoyer `?redirect=https://evil.com`, `?next=//evil.com`, `?url=...` et vérifier si redirection vers domaine externe
- [ ] Paramètres à tester : `redirect`, `url`, `next`, `return`, `redirect_uri`, `returnUrl`, `continue`, `destination`

---

### 3.3 Tests actifs — Méthodes HTTP

- [ ] Requête OPTIONS : récupérer Allow
- [ ] Requête TRACE : détecter XST (si 200 + écho de la requête)
- [ ] Requête HEAD : vérifier support

---

### 3.4 Tests actifs — CORS

- [ ] Envoyer requête avec `Origin: https://evil.com` (ou domaine de test)
- [ ] Vérifier si réponse contient `Access-Control-Allow-Origin: https://evil.com` + `Credentials: true` → réflexion non validée

---

### 3.5 Tests actifs — Paramètres (premiers pas)

- [ ] Détection de paramètres réfléchis : envoyer une chaîne unique (ex. `SecureOpsTest123`) dans les paramètres courants (`q`, `search`, `query`, `id`, `page`, etc.)
- [ ] Si la chaîne apparaît dans la réponse HTML → paramètre réfléchi (info, vecteur potentiel XSS)
- [ ] Ne pas envoyer de payload XSS à ce stade ; uniquement détection de réflexion

---

### 3.6 Tests actifs — Path traversal (léger)

- [ ] Tester `../` dans des paramètres de fichier courants (`file`, `path`, `document`, `template`, `include`)
- [ ] Exemple : `?file=../../../etc/passwd` — si erreur différente (500, message d’erreur) ou contenu suspect → finding
- [ ] Limiter à 1–2 requêtes par paramètre ; pas de fuzzing exhaustif

---

### 3.7 Tests actifs — Injection basique (erreurs révélatrices)

- [ ] SQL : envoyer `'` ou `"` dans paramètres (id, search, etc.) — détecter messages d’erreur SQL dans la réponse (MySQL, PostgreSQL, etc.)
- [ ] Pas d’exploitation ; uniquement détection d’erreur non gérée révélant une injection possible
- [ ] Liste de patterns d’erreur : `SQL syntax`, `mysql_fetch`, `PostgreSQL`, `ORA-`, `SQLite`, etc.

---

### 3.8 Tests actifs — DoS (single-source, pas DDoS)

> **Périmètre :** Tests depuis **une seule source** (le scanner) pour évaluer la résilience ou les indicateurs de vulnérabilité DoS. Pas de test DDoS (pas de volume distribué).

- [ ] **Détection d'absence de rate limiting** : envoi d'un petit nombre de requêtes rapprochées (ex. 5–10 req/s sur une courte fenêtre) ; si le serveur répond sans ralentir ni retourner 429/503 → finding info « Pas de rate limiting détecté » (indicateur de risque DoS).
- [ ] **Requêtes lentes (Slowloris-like, léger)** : ouvrir une ou deux connexions avec envoi très étalé des en-têtes (sans viser à saturer) ; si le serveur garde la connexion ouverte longtemps sans timeout côté serveur → info sur configuration des timeouts.
- [ ] **Seuils configurables** : nombre max de requêtes et durée du test DoS strictement limités (ex. 10 requêtes, 2 s) pour ne pas impacter la cible.
- [ ] **Documentation** : documenter dans le rapport les requêtes utilisées et le fait que le test est limité (single-source, pas d'exploitation).

---

### 3.9 Documentation et scoring

- [ ] Créer `docs/verifications/` pour chaque nouveau test actif
- [ ] Matrice de sévérité par test
- [ ] Adapter le scoring : pondération des findings actifs (souvent plus graves)
- [ ] Section « Requêtes envoyées » dans le rapport PDF (optionnel, pour transparence)

---

## 4) Rapports et analytics

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

---

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

**Recommandation :** À court terme, documenter cette limitation dans l'interface (tooltip ou notice). À moyen terme, implémenter l'option « URL backend optionnelle » pour étendre la couverture des tests.
