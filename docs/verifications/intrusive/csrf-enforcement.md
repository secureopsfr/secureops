# Vérifications actives — CSRF enforcement

Ce document décrit les vérifications actives CSRF : presence des mecanismes anti-CSRF et enforcement sur actions sensibles.

---

## Périmètre selon scan_type

| scan_type | Comportement |
|-----------|--------------|
| `frontend` | ✓ **Check complet** — détection formulaires POST, replay sans token CSRF, vérification `SameSite` |
| `backend` | **Partiel** — **skip total si auth Bearer/API key détectée** (CSRF ne s'applique pas sans cookies). Si l'API utilise des cookies de session : vérification `SameSite` uniquement |

---

## Contexte et méthodologie

### Objectif

Verifier que les actions d'etat (POST/PUT/PATCH/DELETE) sont protegees contre les requetes cross-site non legitimes.

### Tests

- Presence token CSRF dans formulaires/requetes.
- Rejeu sans token / token invalide.
- Verification des attributs cookies (`SameSite`, `Secure`, `HttpOnly`).

---

## 1. Presence et validation du token

### Résumé

Une action sensible doit refuser les requetes sans token CSRF valide.

### Exemple

- **OK** : sans token -> `403`.
- **Finding** : action executee sans token.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne a forte.
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

### Conseils

- Token synchronizer ou double-submit cookie.
- Validation stricte `Origin/Referer`.
- `SameSite=Lax/Strict` pour cookies session.

### Références

- [OWASP – CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
