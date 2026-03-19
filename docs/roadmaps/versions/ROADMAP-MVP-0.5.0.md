# SecureOps — Roadmap MVP 0.5.0

Objectif : **tests d'intégration**, **docs/UX scanner**, **vérification d'autorisation**, **Scanner 2 (actif)**, **import doc API**, **scan paramétrable** et **infra/qualité** reportés depuis la v0.4.0.

**Prérequis :** MVP 0.4.0 livré (tests passifs complets, rate limiting et quotas, architecture deux scanners).

---

## Sommaire

- [1) Tests d'intégration et environnement](#1-tests-dintégration-et-environnement)
- [2) Scanner hub : docs et UX](#2-scanner-hub--docs-et-ux)
- [3) Affichage anomalies](#3-affichage-anomalies)
- [4) Vérification d'autorisation](#4-vérification-dautorisation)
- [5) Import documentation API (backend)](#5-import-documentation-api-backend)
- [6) Introduire les tests actifs (Scanner 2)](#6-introduire-les-tests-actifs-scanner-2)
- [7) Scan paramétrable](#7-scan-paramétrable)
- [8) Infra et qualité](#8-infra-et-qualité)

---

## 1) Tests d'intégration et environnement
*Périmètre : **backend** (environnements, CI, scénarios d'intégration scan/crawl)*

Reporté depuis la section 1.5 de la roadmap v0.4.0 (elle-même issue de la section 2 de la v0.3.0).

### 1.1 Environnements et serveurs de test

- [ ] Définir un environnement de test dédié au scan (Docker Compose minimal : scan-service + Postgres si nécessaire).
- [ ] Ajouter un ou plusieurs **serveurs cibles de démo** :
  - [ ] Serveur HTTP simple (cache/headers/cookies) — ex. `bad_cache_server.py`.
  - [ ] Serveur simulant des headers de sécurité variés (bonnes pratiques / mauvaises pratiques).
  - [ ] Serveur avec fichiers exposés / directory listing / robots.txt / sitemap de test.
  - [ ] **Serveur avec pages liées (même domaine)** pour les tests crawler : plusieurs pages HTML avec liens internes, pour valider le scénario crawl → liste → scan sur N URLs (voir 1.2).
  - [ ] (Optionnel) Serveur d'API de démo (Swagger/GraphQL/Content-Type).

### 1.2 Scénarios de tests d'intégration

- [ ] Scénario « happy path » : URL valide → scan complet → score cohérent → findings attendus.
- [ ] Scénarios d'erreur : DNS KO, timeout, TLS cassé, redirections excessives.
- [ ] Scénarios SSRF : URLs internes / localhost / IP privées bloquées en mode prod (`IS_PROD=true`).
- [ ] Scénarios de ports : ports non autorisés rejetés en prod, autorisés en dev (`IS_PROD=false` via `launch_dev.sh`).
- [ ] **Scénario crawler → liste → scan sur N URLs** : serveur de test avec pages liées (même domaine) ; lancer le crawler depuis une URL de départ, récupérer la liste d'URLs, lancer le scan sur un sous-ensemble ; vérifier agrégation des findings.
- [ ] Vérification des catégories de checks : TLS, headers, cookies, exposition fichiers, directory listing, robots/sitemap, cache, CORS, intégrité, info disclosure, methodes_http_et_redirections, apis_et_formats, etc.
- [ ] Vérification de l'écriture en historique (user-service) et de la génération PDF.
- [ ] Crawler — tests unitaires : parsing HTML → liste d'URLs attendue ; respect Disallow ; limites.
- [ ] Crawler — test d'intégration : crawl d'une page de test → vérifier la sortie et l'absence de fuite hors domaine.

### 1.3 Intégration dans la CI

- [ ] Ajouter un job **tests d'intégration scan-service** dans la pipeline (GitHub Actions).
- [ ] Démarrer les services nécessaires via Docker Compose dans le job.
- [ ] Lancer la suite de tests d'intégration (`pytest -m integration` ou répertoire dédié).
- [ ] Marquer le job comme requis pour les PR affectant le scan-service / gateway.

### 1.4 Observabilité et maintenance

- [ ] Logs clairs pour chaque scénario.
- [ ] Documentation dans `docs/` pour lancer les tests d'intégration en local.
- [ ] Stratégie de maintenance : couvrir les cas critiques (TLS, SSRF, cache, exposition fichiers, CORS, crawler + scan multi-URLs).

---

## 2) Scanner hub : docs et UX
*Périmètre : **frontend** (rapports, alertes, doc, liens contextuels)*

Reporté depuis la section 1.6.3 de la roadmap v0.4.0.

- [x] **Rapports et exports** — *Fait :* Accès aux PDF, CSV, JSON, XLSX (ScanResults export modal, endpoint `/api/scan/export/pdf`, `exportScan.ts`, `exportMultiScan.ts`).
- [x] **Alertes configurées** — *Fait :* Préférence `scan_alerts_enabled` par scan planifié (régression score, finding critique) ; toggle dans ScheduledScansBlock et ScheduleFormSection.
- [ ] Page/section doc regroupant : scan de posture (vérifications, crawling, interprétation), autres scanners, API publique (endpoints, clés API, exemples curl, CI/CD).

  > *Fait partiel :* Page `/scanner/docs` et `/scanner/docs/api` existent (auth, scan fake, gestion clés) ; contenu principal en placeholder « sera complétée prochainement ».
- [ ] Documentation contextuelle : lien doc depuis chaque page concernée (`/scanner/analyses/...`, `/scanner/cles-api`, etc.).

---

## 3) Affichage anomalies
*Périmètre : **frontend** (résumé, table, libellés)*

Reporté depuis la section 1.6.4 de la roadmap v0.4.0.

- [ ] Finaliser le rendu « anomalie détectée » : icône dédiée dans résumé/table + libellé explicite « Anomalie détectée » / « Trouvé ».

  > *Fait partiel :* Terminologie « anomalies » utilisée (ScanResultHeroCard, ScanSummarySection, locales `anomalies`/`anomalies_one`, `summaryNoAnomaliesBold`). Affinements possibles sur icône et libellé.

---

## 4) Vérification d'autorisation
*Périmètre : **backend** (vérification DNS, cache) ; **frontend** (flux utilisateur)*

> **Document dédié :** voir [VERIFICATION-AUTORISATION.md](../../VERIFICATION-AUTORISATION.md) pour la spécification complète.

Cette section est **requise uniquement pour le Scanner 2 (actif)**. Le Scanner 1 (passif) n'en a pas besoin.

- [ ] La vérification est **activée uniquement en production** (désactivée en dev/local)
- [ ] Seuls les domaines **vérifiés** par l'utilisateur peuvent être scannés avec le Scanner 2

### 4.1 Méthode : vérification DNS

- [ ] **Génération :** Token unique par domaine (`secureops-verify-abc123xyz`)
- [ ] **Enregistrement attendu :** `_secureops-verify.<domaine> TXT "secureops-verify-abc123xyz"`
- [ ] **Vérification :** Résolution TXT avant scan actif
- [ ] **Cache :** Stockage domaine + user_id + date (validité ex. 90 jours)
- [ ] **Environnement :** `AUTHORIZATION_CHECK_ENABLED=true` (production)

### 4.2 Flux utilisateur (Scanner 2 uniquement)

1. Utilisateur choisit Scanner 2 et saisit l'URL
2. Si domaine non vérifié : afficher « Ajoutez cet enregistrement DNS : `_secureops-verify.example.com TXT "votre-token"` »
3. Utilisateur ajoute l'enregistrement DNS
4. Clic « Vérifier » → résolution DNS → scan autorisé
5. Si domaine déjà vérifié (cache) : scan direct

### 4.3 Cas particuliers

- [ ] **Fallback :** En dev ou si DNS échoue : case à cocher + avertissement
- [ ] **API publique :** Domaine pré-vérifié ou acceptation préalable (doc + CGU)

---

## 5) Import documentation API (backend)
*Périmètre : **frontend** (formulaire, case à cocher, upload) ; **backend** (parsing spec)*

> **Prérequis avant le développement des tests actifs backend.**

### Comportement attendu (UI)

- [x] **Scan type backend** — *Fait :* Libellé « Scanner uniquement cet endpoint » (ScanTypeSelector, `scanOnlyThisEndpoint`).
- [x] **Section import doc** — *Fait :* Quand décoché (backend, multi-endpoints) : ApiDocImportZone avec drag-and-drop.
- [x] **Parsing OpenAPI / Postman** — *Fait :* parseApiDoc.ts (OpenAPI 2/3, Postman) ; extraction endpoints ; `.json`, `.yaml`, `.yml`.
- [x] **Flux parse → endpoints → validation** — *Fait :* EditableUrlList pour ajout/suppression ; base URL pour override ; envoi liste d'URLs au backend.
- [x] **Limite endpoints** — *Fait :* MAX_ENDPOINTS = 200 (parseApiDoc.ts).
- [ ] (Optionnel) Récupération spec par URL (GET `/openapi.json`, `/swagger.json`) — *Hors périmètre actuel.*

### Formats acceptés

| Format | Support | Source |
|--------|---------|--------|
| OpenAPI / Swagger | Fichier | Drag-and-drop `.json` ou `.yaml` |
| Postman Collection | Fichier | Drag-and-drop `.json` (v2.0, v2.1) |

---

## 6) Introduire les tests actifs (Scanner 2)
*Périmètre : selon le type — voir détail par sous-section*

> **Scanner 2 :** Ne fonctionne que pour les URLs dont le domaine a été vérifié (section 4). Option : inclure les tests passifs avant (défaut : oui).

### 6.1 Cadre et sécurité

- [ ] Choix utilisateur : tests passifs avant actifs (défaut : oui)
- [ ] Section « Tests actifs » dans le disclaimer
- [ ] Documenter chaque requête dans le rapport
- [ ] Rate limiting renforcé
- [ ] Contrôle d'accès : Scanner 2 refuse les URLs non vérifiées

### 6.2 Tests actifs — Redirections, Méthodes HTTP, CORS, Paramètres, etc.

(Voir sections détaillées 3.2 à 3.21 de la roadmap 0.4.0 pour le catalogue complet des tests actifs P0–P4, garde-fous et ordre de développement.)

---

## 7) Scan paramétrable
*Périmètre : **les deux** (frontend : UI ; backend : logique)*

### 7.1 Filtrage par gravité

- [ ] Mode « Uniquement critical »
- [ ] Mode « Critical + high »
- [ ] Mode « Complet » (défaut)
- [ ] Interface : sélecteur de mode avant lancement

### 7.2 Autres options (optionnel)

- [ ] Désactiver des catégories de tests
- [ ] Profondeur limitée (ex. uniquement passif)
- [ ] Préférences sauvegardées par utilisateur

---

## 8) Infra et qualité
*Périmètre : **backend** (config, tests unitaires)*

### 8.1 Mode asynchrone (optionnel)

- [ ] Si les tests actifs allongent le scan (> 30s), envisager le mode async

### 8.2 Tests unitaires

- [x] **Tests passifs** — *Fait :* Suite pytest existante pour checks TLS, headers, cookies, CORS, integrity, exposed files, directory listing, robots, sitemap, SSRF, scoring, etc. (backend/scan-service/tests/, backend/gateway/tests/, etc.)
- [ ] Tests pour chaque nouveau check actif
- [ ] Mocks des réponses HTTP pour les tests actifs

### 8.3 Configuration

- [ ] Option `active_scan_enabled` (défaut : true)
- [ ] Option `active_scan_max_requests_per_param`

---

## Synthèse MVP 0.5.0

| Domaine | Contenu |
|---------|---------|
| **Tests d'intégration** | Docker Compose, serveurs démo, scénarios scan/crawl, CI |
| **Docs/UX** | Rapports, alertes (déjà faits) ; doc complète et liens contextuels |
| **Affichage** | Finalisation libellé/icône « anomalie détectée » |
| **Vérification** | DNS TXT, cache, flux Scanner 2 |
| **Import API** | Déjà fait (drag-drop, OpenAPI/Postman, 200 endpoints) |
| **Tests actifs** | Cadre, redirections, méthodes HTTP, CORS, paramètres, path traversal, injection, DoS, etc. |
| **Scan paramétrable** | Mode par gravité (critical, critical+high, complet) |
| **Infra** | Tests unitaires passifs (faits) ; config et tests actifs |
