# Vérifications actives — Session fixation / invalidation / token lifecycle

Ce document décrit les vérifications actives de gestion de session : rotation d'identifiant, invalidation et cycle de vie des tokens.

---

## Contexte et méthodologie

### Objectif

Verifier que la session est correctement regeneree apres login, correctement invalidee au logout, et que les tokens expirent/rotent correctement.

### Tests

- Session fixation : comparer session avant/apres login.
- Invalidation : reutiliser token/cookie apres logout.
- Lifecycle : verifier `exp`, refresh token, revocation.

---

## 1. Session fixation

### Résumé

Si l'identifiant de session ne change pas apres authentification, un attaquant peut forcer une session connue.

### Exemple

- **OK** : nouveau cookie/session id apres login.
- **Finding** : meme identifiant avant/apres login.

### Conseils

- Regenerer la session apres authentification et elevation de privilege.

---

## 2. Invalidation de session

### Résumé

Un logout doit rendre token/cookie inutilisable immediatement.

### Exemple

- **OK** : token refuse apres logout (`401/403`).
- **Finding** : token encore accepte.

### Conseils

- Implementer revocation blacklist/version de session.

---

## 3. Token lifecycle

### Résumé

Verifier expiration, rotation refresh token, et validation stricte des claims.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Importante.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead><tr>
<th style="border:2px solid #1f2937; padding:8px">Gravité \ Vraisemblance</th>
<th style="border:2px solid #1f2937; padding:8px">Très faible</th>
<th style="border:2px solid #1f2937; padding:8px">Faible</th>
<th style="border:2px solid #1f2937; padding:8px">Forte</th>
<th style="border:2px solid #1f2937; padding:8px">Très forte</th>
</tr></thead>
<tbody>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Mineure</strong></td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Significative</strong></td><td style="border:2px solid #1f2937; background-color:#22c55e"> </td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Importante</strong></td><td style="border:2px solid #1f2937; background-color:#facc15"> </td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td></tr>
<tr><td style="border:2px solid #1f2937; padding:8px"><strong>Majeure</strong></td><td style="border:2px solid #1f2937; background-color:#f97316"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td><td style="border:2px solid #1f2937; background-color:#ef4444"> </td></tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : modéré à élevé.**

### Références

- [OWASP – Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [RFC 7519 (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
