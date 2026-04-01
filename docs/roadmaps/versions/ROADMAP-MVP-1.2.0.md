# SecureOps — Roadmap MVP 1.2.0 (Vérification DNS domaine)

**Périmètre :** preuve de propriété DNS (TXT) pour les **modes de scan non passifs**, alignée sur [VERIFICATION-AUTORISATION.md](../../VERIFICATION-AUTORISATION.md).

**Prérequis :** migrations Alembic `0023` appliquées sur la base user-service.

---

## Livré dans cette version

| Domaine | État |
|--------|------|
| Normalisation eTLD+1 | `common.url_helpers.registered_domain_from_url` / `registered_domain_from_host` (tldextract) |
| Persistance | Tables `domain_verifications`, `domain_verification_challenges` (unicité globale sur `domain`) |
| user-service | `POST/GET/DELETE /api/user/domain-verifications/*`, résolution TXT (`dnspython`), `POST /api/internal/domain-verifications/assert` |
| scan-service | Garde-fou si `AUTHORIZATION_CHECK_ENABLED=true` sur création job async et endpoints internes (`cognito_sub`) |
| Scheduler | Skip scan planifié non passif si domaine non vérifié (même flag) |
| Frontend | Bloc « Vérification du domaine » sur le hub scanner (modes non passifs) |
| Ops | Variables documentées dans [VARIABLES-ENVIRONNEMENT.md](../../VARIABLES-ENVIRONNEMENT.md), `docker-compose` |

---

## Critères de done (production)

- `AUTHORIZATION_CHECK_ENABLED=true`, `USER_SERVICE_URL` et `USER_SERVICE_INTERNAL_API_KEY` alignés sur le user-service.
- Test manuel : challenge → TXT → verify → scan intrusif accepté ; sans TXT → 403 avec détail structuré côté API async.

---

## Hors périmètre / suite

- Rate limiting dédié aux endpoints challenge/verify (renforcer si abus).
- Re-vérification périodique en tâche de fond (TXT retiré avant expiration).
