# Vérifications actives — CORS (réflexion d'origine)

Ce document décrit les vérifications actives CORS : objectif, méthodologie, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Détecter les configurations CORS dangereuses, en particulier :

- réflexion non validée d'origine ;
- usage des credentials avec origines trop permissives ;
- incohérences preflight.

### Principe (actif léger, MVP 1.0.0)

Le scanner envoie des requêtes avec `Origin` contrôlée (ex. `https://evil.test`) et observe :

- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Credentials`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Vary: Origin`

Le scanner exécute aussi un preflight `OPTIONS` minimal sur une cible limitée.

---

## 1. Réflexion d'origine non validée + credentials

### Résumé

Si le serveur reflète l'origine fournie par le client et autorise les credentials, un domaine tiers peut lire des réponses authentifiées.

### Explication détaillée

Pattern critique :

1. requête avec `Origin: https://evil.test`,
2. réponse `Access-Control-Allow-Origin: https://evil.test`,
3. réponse `Access-Control-Allow-Credentials: true`.

Ce pattern indique souvent une allowlist absente ou contournable.

### Exemple

- **OK** : origine non autorisée -> aucun `Access-Control-Allow-Origin`
- **Finding** : origine malveillante reflétée + credentials autorisés

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Majeure (exfiltration cross-origin de données utilisateur).

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : élevé à critique.**

### Conseils

- Définir une allowlist stricte d'origines de confiance.
- Ne jamais autoriser `credentials` avec origine non validée.
- Ajouter `Vary: Origin` si la réponse dépend de l'origine.
- Journaliser et auditer les origines refusées.

### Références

- [OWASP – CORS Security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing)
- [MDN – CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [CWE-942 – Permissive Cross-domain Policy](https://cwe.mitre.org/data/definitions/942.html)
