# Catalogue complet des tests intrusifs — Scanner 2

Référentiel exhaustif des tests actifs du Scanner 2 SecureOps (MVP 1.0.0). Ce document centralise les priorités (P0–P4), les garde-fous, les exigences techniques et la checklist complète.

---

## Niveaux de priorité

| Code | Signification | Périmètre |
|------|--------------|-----------|
| **P0** | Indispensable | Tests courants, forte valeur. Implémentation prioritaire MVP. |
| **P1** | Très recommandé | Haute valeur, dépendance stack ou contexte. |
| **P2** | Avancé | Moins fréquents, impact potentiel élevé. |
| **P3** | Spécialisés | Contexte technique spécifique (WebSocket, gRPC, OAuth, cloud). |
| **P4** | Rare/recherche | Mode expert explicite, opt-in obligatoire. |

---

## Garde-fous obligatoires (toutes phases)

- Autorisation forte : preuve de contrôle du domaine (DNS TXT), audit trail, acceptation explicite.
- Kill switch global : arrêt immédiat d'un scan actif en cours.
- Rate limit strict par hôte, endpoint, catégorie.
- Budget de requêtes par test / endpoint / scan.
- Timeouts courts + retries limités + jitter.
- Méthodes interdites par défaut : `PUT`, `PATCH`, `DELETE`, `POST` non idempotent (sauf opt-in explicite).
- Payload safety : pas d'écriture irréversible, pas d'exfiltration réelle.
- Journalisation complète : requête rédigée, cible, timestamp, statut, preuve.
- Scopes explicites (frontend, backend optionnel, exclusions).
- Protection SSRF non négociable côté scanner.

---

## P0 — Indispensable

### Authentification et session

| Test | Doc | Description |
|------|-----|-------------|
| Bruteforce protection login | `auth-bruteforce-lockout-enumeration.md` | Lockout, backoff, captcha, 429 |
| Énumération utilisateur | idem | Messages différenciés selon l'existence |
| Session fixation | `session-fixation-invalidation-token-lifecycle.md` | Rotation post-login |
| Invalidation session | idem | Logout effectif token/cookie |
| JWT basique | idem | alg, exp, nbf, aud, iss |

### Autorisation (IDOR / BOLA / BFLA)

| Test | Doc | Description |
|------|-----|-------------|
| Escalade horizontale | `autorisation-idor-bola-bfla.md` | `/users/{id}` ou équivalent |
| Escalade verticale | idem | Routes admin accès rôle non admin |
| Contrôle objet/fonction manquant | idem | Sur API |

### Injections fréquentes

| Test | Doc | Description |
|------|-----|-------------|
| SQLi error-based + time-based léger | `injection-basique-erreurs.md` | Erreurs révélatrices, délai minimal |
| NoSQLi basique | `nosqli.md` | Opérateurs, injection structure JSON |
| XSS réfléchi (détection) | `parametres-reflechis.md` | Détection réflexion + contexte |
| Path traversal | `path-traversal-leger.md` | Variantes encodées |
| Command injection basique | `command-injection-basique.md` | Erreurs/comportements anormaux |

### Web/API classiques

| Test | Doc | Description |
|------|-----|-------------|
| Open redirect actif | `redirections-actives.md` | Paramètres url/redirect/next vers domaine externe |
| CORS actif | `cors-actif.md` | Origin reflection + credentials |
| Méthodes HTTP | `methodes-http-actives.md` | OPTIONS, TRACE, HEAD |
| CSRF présence + enforcement | `csrf-enforcement.md` | Token, validation |
| Rate limiting endpoint | `dos-single-source.md` | Burst court contrôlé — **voir clarif. DoS ci-dessous** |

---

## P1 — Très recommandé

### Upload et contenu utilisateur

| Test | Doc | Description |
|------|-----|-------------|
| Upload type non autorisé | `upload-abuse.md` | MIME spoof, double extension, malformé |
| Exécution de fichier upload | idem | Accès direct + exécution serveur |
| Traversal via nom de fichier | idem | `../` dans le nom |

### APIs modernes

| Test | Doc | Description |
|------|-----|-------------|
| GraphQL actif | `graphql-abuse.md` | Introspection, depth, alias, batching abuse |
| GraphQL subscriptions | `graphql-subscriptions-abuse.md` | Sous-catégorie GraphQL |
| Mass assignment | `mass-assignment.md` | Champs sensibles acceptés sans whitelist |
| Validation schéma API | `api-schema-validation-abuse.md` | Type confusion, champs inattendus, arrays excessifs |
| Pagination abuse | idem (sous-catégorie) | `limit` excessif, bornes absentes |

### SSRF applicative

| Test | Doc | Description |
|------|-----|-------------|
| SSRF via paramètres URL | `ssrf-applicative.md` | Parsing, schémas, redirections |
| Metadata cloud probes | idem | Mode safe, sans exfiltration |

### XML/Template/Deserialize

| Test | Doc | Description |
|------|-----|-------------|
| XXE | `xxe.md` | External entity |
| SSTI | `ssti.md` | Server-Side Template Injection |
| Insecure deserialization | `insecure-deserialization.md` | Selon techno |

### File inclusion

| Test | Doc | Description |
|------|-----|-------------|
| LFI/RFI | `file-inclusion-lfi-rfi.md` | Selon techno |

---

## P2 — Avancé

| Test | Doc | Description |
|------|-----|-------------|
| HTTP request smuggling / desync | `request-smuggling-desync.md` | CL/TE |
| Cache poisoning | `cache-poisoning-web-cache-deception.md` | En-têtes non normalisés |
| Web cache deception | idem | |
| Host header injection | `host-header-injection.md` | Reset password poisoning, liens absolus |
| Race conditions | `race-conditions.md` | Double spend, TOCTOU |
| Business logic abuse | `business-logic-abuse.md` | Bypass workflow, coupons, fenêtre métier |

---

## P3 — Spécialisés

| Test | Doc | Description |
|------|-----|-------------|
| WebSocket authz | `websocket-authz.md` | Autorisation sur flux temps réel |
| GraphQL subscriptions abuse | `graphql-subscriptions-abuse.md` | |
| gRPC abuse | `grpc-abuse.md` | |
| Object storage exposure | `object-storage-exposure-actif.md` | |
| Service mesh/internal API exposure | `service-mesh-internal-api-exposure.md` | |
| OAuth/OIDC misconfig | `oauth-oidc-misuse.md` | redirect_uri, state, PKCE, relay state |

---

## P4 — Rare/recherche (mode expert explicite)

| Test | Description |
|------|-------------|
| DoS applicatif contrôlé (agressif) | Burst, slow request/headers, amplification — **distinct du DoS P0** |
| HTTP/2 abuse patterns | |
| Unicode normalization confusion sur authz | |
| DNS rebinding applicatif | |
| Parser differential attacks multi-proxy | |

**Activation :** uniquement en mode expert, opt-in explicite, limites strictes.

---

## Clarification DoS : P0 vs P4

| Aspect | DoS P0 (`dos-single-source.md`) | DoS P4 |
|--------|----------------------------------|--------|
| **Priorité** | Indispensable, inclus MVP | Mode expert uniquement |
| **Périmètre** | Rate limiting absence, slowloris minimal (1–2 connexions) | Burst agressif, amplification, volume élevé |
| **Seuils** | 5–10 req/s, 2 s max, bornes strictes | Configurable, plus agressif |
| **Objectif** | Indicateur de posture faible | Évaluation résilience avancée |
| **Risque cible** | Très faible | Modéré, requiert opt-in |

Le test P0 est **non destructif** et sert d’indicateur. Le test P4 est **potentiellement perturbant** et reste désactivé par défaut.

---

## Checklist exhaustive (familles à couvrir)

- [ ] Auth brute force / lockout / enumeration
- [ ] Session fixation / invalidation / token lifecycle
- [ ] Horizontal + vertical authorization (IDOR/BOLA/BFLA)
- [ ] CSRF enforcement
- [ ] CORS actif (origin reflection, credentials)
- [ ] Open redirect
- [ ] Méthodes HTTP (OPTIONS/TRACE/HEAD)
- [ ] SQLi (error/time)
- [ ] NoSQLi
- [ ] XSS réfléchi (détection)
- [ ] Command injection basique
- [ ] Path traversal
- [ ] File inclusion (LFI/RFI selon techno)
- [ ] XXE
- [ ] SSTI
- [ ] Insecure deserialization
- [ ] Upload abuse (MIME, extension, execution)
- [ ] Mass assignment
- [ ] GraphQL abuse (introspection/depth/alias/batch)
- [ ] GraphQL subscriptions (sous-catégorie GraphQL)
- [ ] API schema validation abuse
- [ ] Pagination abuse (sous-catégorie API schema)
- [ ] SSRF applicative
- [ ] Host header injection
- [ ] Cache poisoning / web cache deception
- [ ] HTTP request smuggling / desync
- [ ] Race conditions
- [ ] Business logic abuse
- [ ] WebSocket authz
- [ ] OAuth/OIDC misuse
- [ ] DoS contrôle (borne) — P0 léger ; P4 mode expert

---

## Exigences techniques minimales (moteur intrusif)

### Moteur de requêtes

- Rejouer méthodes, headers, query, body
- Support encodages URL/double URL/unicode/JSON
- Session stateful (cookies/tokens), isolation entre tests
- Retry intelligent + jitter

### Moteur de payloads

- Payloads paramétrables par catégorie
- Mutations auto (case, encodings, wrappers)
- Payload IDs uniques pour tracer la réflexion

### Détection

- Signatures regex (SQL/template/parser/errors)
- Diff baseline/probe
- Détection temporelle robuste au bruit
- Heuristiques anti faux positifs

### Reporting

- Requête rédigée, endpoint, paramètre, payload_id
- Observation brute + interprétation
- Reproduction minimale
- Recommandation concrète

---

## Ordre de développement recommandé

### Phase A (MVP intrusif)

Open redirect → Méthodes HTTP → CORS actif → Reflection params → SQL error-based basique → Path traversal basique → CSRF enforcement basique → IDOR simple

### Phase B

NoSQLi, SSTI, XXE → Upload abuse → Mass assignment → Rate limiting/auth abuse (lockout, enumeration) → Session tests (fixation/invalidation)

### Phase C

Request smuggling/desync → Cache poisoning/deception → Race conditions → WebSocket/gRPC/OAuth avancés → DoS contrôle (toujours borné)

---

## Désactivé par défaut (mode expert uniquement)

- Tests potentiellement destructifs
- Scénarios impliquant écriture irréversible
- Flood haute fréquence longue durée
- Exploitation complète (RCE, exfiltration)

---

## Architecture et mutualisation

Voir `architecture-mutualisation.md` pour les composants mutualisables (moteur de paramètres, client HTTP, module redirections).
