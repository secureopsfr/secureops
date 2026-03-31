# SecureOps — Roadmap MVP 1.1.0 (Scanner 2 — tests intrusifs)

**Périmètre v1.1.0 :** mise en œuvre complète du **scan intrusif** (Scanner 2), avec socle technique, lib mutualisée, **34 checks réels**, scoring, PDF / exports, UX scanner et documentation — **hors vérification DNS** du domaine (prévue en **1.2.0**).

**Prérequis :** [ROADMAP-MVP-1.0.0.md](./ROADMAP-MVP-1.0.0.md) livré (passif, quotas, hub scanner de base).

**Référence catalogue :** [catalogue-complet-tests-intrusifs.md](../../verifications/intrusive/catalogue-complet-tests-intrusifs.md)

---

## Sommaire

- [0.3 Adaptation des tests intrusifs (frontend / backend)](#03-adaptation-des-tests-intrusifs-frontend--backend)
- [Bloc 0 — Socle](#bloc-0--socle)
- [Bloc 1 — Composants mutualisables (`lib/`)](#bloc-1--composants-mutualisables-lib)
- [Bloc 2 — Phase A (P0)](#bloc-2--phase-a-p0)
- [Bloc 3 — Phase B (P0–P1)](#bloc-3--phase-b-p0p1)
- [Bloc 4 — Phase C (P2–P3)](#bloc-4--phase-c-p2p3)
- [Bloc 5 — Modes destructif + custom](#bloc-5--modes-destructif--custom)
- [Bloc 6 — Finalisation produit](#bloc-6--finalisation-produit)
- [7) Scoring des findings intrusifs](#7-scoring-des-findings-intrusifs)
- [8) Configuration intrusive](#8-configuration-intrusive)
- [Reporté en 1.2.0 ou hors périmètre 1.1.0](#reporté-en-120-ou-hors-périmètre-110)
- [Limitations connues (MVP 1.1.0)](#limitations-connues-mvp-110)
- [Synthèse](#synthèse-mvp-110)

---

## 0.3 Adaptation des tests intrusifs (frontend / backend)

- [x] **Gestion `scan_type` (`frontend` / `backend`)** — *Fait :* skips explicites (`_INTRUSIVE_FRONTEND_ONLY_STEPS`, `_INTRUSIVE_BACKEND_ONLY_STEPS`), même logique en multi-URL (`multi_scan_orchestrator`).
- [x] **Credentials cible (`ScanCredentials`)** — *Fait :* cookie / bearer propagés dans le pipeline ; **non persistés** (y compris scans planifiés : limitation connue).
- [x] **Cohérence UX** — *Fait :* formulaire scanner, modes, imports API, résultats et exports alignés sur le flux passif où pertinent.

---

## Bloc 0 — Socle

- [x] **Schéma `ScanCredentials` + propagation** — *Fait :* `async_job`, exécuteur async, `scan_stream` / orchestrateur multi.
- [x] **Auth SecureOps pour modes actifs** — *Fait :* accès intrusif / custom protégé (gateway + JWT comme le reste du hub).
- [x] **`compute_intrusive_score()`** — *Fait :* `scoring.py`, poids / pénalités dans `config` + `settings.yml` (`intrusive_scan`).
- [x] **Budgets, timeouts, jitter** — *Fait :* `intrusive_scan.py` / `settings.yml`, alignés avec le worker async.
- [x] **Domaine / page split** — *Fait :* `domain_page_split.py`, orchestration cohérente multi-URL.

---

## Bloc 1 — Composants mutualisables (`lib/`)

- [x] **Client HTTP intrusif** — *Fait :* `lib/http_client.py` (credentials, probes).
- [x] **Extraction paramètres** — *Fait :* `lib/param_extractor.py`.
- [x] **Moteur de payloads** — *Fait :* `lib/payload_engine.py`.
- [x] **Détecteurs (SQL, NoSQL, SSTI, etc.)** — *Fait :* `lib/detector.py`.
- [x] **Redirections / signatures** — *Fait :* modules dédiés dans `lib/` selon besoins des checks.

---

## Bloc 2 — Phase A (P0)

Checks réels (ordre pipeline) : `open_redirect`, `methodes_http`, `cors_actif`, `parametres_reflechis` (frontend), `sqli`, `path_traversal`, `csrf`, `idor`, `command_injection`, `nosqli`, `dos_p0`.

- [x] Implémentation par module sous `checks/frontend/`, `checks/backend/`, `checks/both/`.
- [x] Catalogue / résumés / OWASP : fichiers JSON côté scan-service + pdf-service (macro-catégories rapport).
- [x] **Tests unitaires** — *Fait :* `test_intrusive_*.py` (détecteur, payloads, params, scoring, checks, domain/page split).

---

## Bloc 3 — Phase B (P0–P1)

`auth_bruteforce`, `session_fixation`, `upload_abuse`, `idor_complet`, `mass_assignment`, `graphql_abuse`, `api_schema_abuse`, `ssrf`, `xxe`, `ssti`, `insecure_deserialization`, `lfi_rfi`.

- [x] Même structure que bloc 2 (modules + intégration pipeline + tests).

---

## Bloc 4 — Phase C (P2–P3)

`host_header`, `cache_poisoning`, `request_smuggling`, `race_conditions`, `business_logic`, `websocket_authz`, `oauth_oidc`, `object_storage`, `service_mesh`, `graphql_subscriptions`, `grpc_abuse`.

- [x] Même structure ; **34 checks** au total dans `INTRUSIVE_STEPS`.

---

## Bloc 5 — Modes destructif + custom

- [x] **Mode `destructive`** — *Fait :* retiré / neutralisé pour cette branche ; contenu reporté (pas de checks destructifs actifs en prod pour l’instant).
- [x] **Mode `custom`** — *Fait :* moteur de scénarios (`scenario_engine.py`) pour enchaînement contrôlé via config JSON.

---

## Bloc 6 — Finalisation produit

- [x] **PDF** — *Fait :* rapport intrusif, macro-catégories, badge mode, textes i18n PDF ; regroupement des catégories fines.
- [x] **Frontend résultats** — *Fait :* répartition par macro-catégories (alignée PDF), cartes findings, exports (CSV, JSON, XLSX, PDF).
- [x] **Scanner hub / doc** — *Fait :* pages `/scanner/docs`, doc statique intrusif/passif (admin CMS + `lang`), lien contextuel depuis le formulaire selon le mode.
- [x] **Affichage anomalies** — *Fait :* icônes + libellés cohérents (cartes / résumé ; i18n).
- [x] **Import documentation API (OpenAPI / Postman)** — *Fait :* côté frontend (parse, liste d’URLs, limite endpoints) ; voir aussi § reporté pour « fetch URL » optionnel.

---

## 7) Scoring des findings intrusifs

- [x] Pénalités par sévérité et poids par catégorie — *Fait :* `compute_intrusive_score()`, configuration centralisée.
- [x] Bornes score 0–100 et comportement sur corpus vide / findings inconnus — *Fait :* couvert par tests.

---

## 8) Configuration intrusive

- [x] **DoS / rate limit** — *Fait :* paramètres dédiés (burst, limites) dans la config intrusive ; pas d’abus hors budget.
- [x] **Timeouts globaux** — *Fait :* `scan_global` + timeout job worker alignés.
- [x] **Alertes scan planifié (user-service)** — *Fait :* emails régression / finding critique ; **seuil et options par scan** (BDD + API + UI) en complément du toggle principal.

---

## Reporté en 1.2.0 ou hors périmètre 1.1.0

| Sujet | Statut |
|--------|--------|
| **Vérification d’autorisation DNS (Scanner 2)** | Reporté — spécification dans [VERIFICATION-AUTORISATION.md](../../VERIFICATION-AUTORISATION.md), non bloquant pour l’implémentation intrusive en dev. |
| **Détection out-of-band (OOB)** | Reporté — callback serveur dédié, hors MVP 1.1.0. |
| **Tests d’intégration CI** (compose, serveurs démo, `pytest -m integration`) | À renforcer — voir ancienne §1 roadmap générique. |
| **Scan paramétrable par gravité** (critical only, etc.) | Non livré en 1.1.0 — piste produit. |
| **Fetch spec OpenAPI par URL** | Optionnel / reporté. |
| **Credentials sur scan planifié** | Non persistés par design ; pas d’injection creds automatique sur run schedulé. |

---

## Limitations connues (MVP 1.1.0)

- **DNS / preuve de propriété** : non appliqué dans cette version ; à activer en prod via roadmap 1.2.0.
- **OOB** : pas de corrélations blindées (burp collaborator équivalent) sans infrastructure dédiée.
- **Scans planifiés intrusifs** : le scheduler peut passer le `scan_mode`, pas les secrets cible — scans authentifiés réservés au lancement manuel (ou évolution future).
- **Faux positifs / bruit** : certains checks restent heuristiques ; affinage continu hors scope « roadmap close ».

---

## Synthèse MVP 1.1.0

| Domaine | État |
|--------|------|
| **Pipeline intrusif** | 34 checks réels, Phases A/B/C, `scan_type`, credentials éphémères |
| **Lib mutualisée** | HTTP, params, payloads, détection, split domaine/page |
| **Scoring** | Dédié intrusif, configurable |
| **PDF & exports** | Macro-catégories, FR/EN docs utilisateur |
| **Frontend** | Hub, doc contextuelle, résultats macro-catégories, formulaire complet |
| **Qualité** | Suite unitaire intrusive étendue |
| **Alertes planifiées** | Email + options utilisateur (seuil régression, types d’alerte) |
| **Hors scope** | DNS proof, OOB, destructif actif, filtre gravité scan |
