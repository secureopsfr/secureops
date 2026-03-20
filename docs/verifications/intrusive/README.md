# Vérifications intrusives (tests actifs)

Ce dossier regroupe la documentation des vérifications **actives/intrusives** du Scanner 2 (MVP 1.0.0).

## Cadre

- Usage autorisé uniquement (tests sur cibles maîtrisées).
- Domaine vérifié requis (ownership DNS en production).
- Tests actifs légers au MVP (pas de bruteforce, pas de fuzzing massif).
- Requêtes et charge strictement limitées.

## Référentiels

| Document | Description |
|----------|-------------|
| [catalogue-complet-tests-intrusifs.md](catalogue-complet-tests-intrusifs.md) | Référentiel exhaustif : P0→P4, garde-fous, exigences techniques, checklist, clarification DoS |
| [architecture-mutualisation.md](architecture-mutualisation.md) | Composants mutualisables (moteur paramètres, client HTTP, module redirections) |

## Documents par type de test

### P0 — Indispensable

- `auth-bruteforce-lockout-enumeration.md`
- `session-fixation-invalidation-token-lifecycle.md`
- `autorisation-idor-bola-bfla.md`
- `csrf-enforcement.md`
- `redirections-actives.md`
- `methodes-http-actives.md`
- `cors-actif.md`
- `parametres-reflechis.md`
- `injection-basique-erreurs.md`
- `nosqli.md`
- `command-injection-basique.md`
- `path-traversal-leger.md`
- `dos-single-source.md`

### P1 — Tres recommande

- `upload-abuse.md`
- `mass-assignment.md`
- `graphql-abuse.md`
- `api-schema-validation-abuse.md`
- `ssrf-applicative.md`
- `xxe.md`
- `ssti.md`
- `insecure-deserialization.md`
- `file-inclusion-lfi-rfi.md`

### P2 — Avance

- `host-header-injection.md`
- `cache-poisoning-web-cache-deception.md`
- `request-smuggling-desync.md`
- `race-conditions.md`
- `business-logic-abuse.md`

### P3 — Specialises

- `websocket-authz.md`
- `graphql-subscriptions-abuse.md`
- `grpc-abuse.md`
- `object-storage-exposure-actif.md`
- `service-mesh-internal-api-exposure.md`
- `oauth-oidc-misuse.md`
