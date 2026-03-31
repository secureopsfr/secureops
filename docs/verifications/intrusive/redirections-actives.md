# Vérifications actives — Redirections

Ce document décrit les vérifications actives liées aux redirections : objectif, risques, méthodologie, exemples et recommandations.

---

## Périmètre selon scan_type

| scan_type | Comportement |
|-----------|--------------|
| `frontend` | ✓ Paramètres de redirection découverts via liens HTML (`<a href>`), formulaires et query string |
| `backend` | ✓ Paramètres découverts via query string et body JSON uniquement — pas de parsing HTML |

La logique de test (payloads, détection domaine externe) est **identique** dans les deux cas. Seule la phase de découverte des paramètres diffère.

---

## Contexte et méthodologie

### Objectif

Détecter les cas d'**open redirect** sur les paramètres de navigation (`redirect`, `next`, `url`, etc.) permettant de renvoyer l'utilisateur vers un domaine tiers non autorisé.

### Principe (actif léger, MVP 1.0.0)

Le scanner envoie des requêtes ciblées avec des valeurs de redirection externes puis vérifie :

1. le statut de réponse (`3xx`, `200`, `4xx`) ;
2. l'en-tête `Location` ;
3. le domaine final après suivi limité des redirections ;
4. les variantes d'encodage (`https://evil.test`, `//evil.test`, URL-encoding).

Le test reste borné : faible volume, pas de fuzzing massif, pas de charge agressive.

### Paramètres ciblés (priorité MVP)

- `redirect`
- `url`
- `next`
- `return`
- `redirect_uri`
- `returnUrl`
- `continue`
- `destination`

### Critères de confirmation d'un finding

- `Location` pointe vers un domaine externe non approuvé ;
- ou la navigation aboutit à un domaine externe non approuvé ;
- ou un schéma ambigu (`//evil.test`) est accepté et résolu hors scope.

Ne sont pas des findings :

- redirection interne (même domaine / même scope) ;
- redirection externe explicitement allowlistée et validée.

---

## 1. Open redirect (paramètres explicites)

### Résumé

Le scan injecte une URL externe dans les paramètres de redirection. Si l'application redirige sans validation stricte de la destination, elle est vulnérable à l'open redirect.

### Explication détaillée

Payloads typiques :

- `?redirect=https://evil.test`
- `?next=//evil.test`
- `?url=https%3A%2F%2Fevil.test%2Fcb`

L'open redirect est souvent utilisé pour :

- phishing avec URL d'apparence légitime ;
- contournement de filtres de confiance ;
- abus OAuth/OIDC (`redirect_uri` mal validé).

### Exemple

- **OK** : `GET /login?next=https://evil.test` -> `302 Location: /dashboard`
- **Finding** : `GET /redirect?url=https://evil.test` -> `302 Location: https://evil.test`

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne à forte. Les flux login/logout/callback sont fréquemment mal contraints.
- **Impact** : Significative à importante. Phishing, vol de confiance, facilitation de chaînes d'attaque.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead>
<tr>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Gravité \ Vraisemblance</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Forte</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très forte</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Mineure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : modéré à élevé.**

### Conseils

- Autoriser uniquement les redirections internes ou une allowlist stricte.
- Refuser les destinations absolues externes (`http://`, `https://`, `//`).
- Signer/chiffrer les destinations de retour quand nécessaire.
- Sur OAuth/OIDC, imposer une comparaison exacte de `redirect_uri`.

### Références

- [OWASP – Unvalidated Redirects and Forwards](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)
- [WSTG – Testing for Open Redirect](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE-601 – Open Redirect](https://cwe.mitre.org/data/definitions/601.html)
