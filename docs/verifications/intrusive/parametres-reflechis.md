# Vérifications actives — Paramètres réfléchis (premiers pas)

Ce document décrit les vérifications actives sur les paramètres réfléchis : objectif, méthodologie, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Identifier les paramètres dont la valeur est reflétée dans la réponse HTML. Ce signal n'est pas une preuve d'exploitation XSS, mais un indicateur de surface d'attaque.

### Principe (actif léger, MVP 0.4.0)

Le scanner injecte une chaîne neutre unique (ex. `SecureOpsTest123`) dans des paramètres courants :

- `q`
- `search`
- `query`
- `id`
- `page`

Puis il vérifie la présence de la chaîne dans :

- texte HTML ;
- attribut HTML ;
- bloc JavaScript inline.

### Limite volontaire

Aucun payload d'exploitation XSS n'est envoyé au MVP. Le test se limite à la détection de réflexion.

---

## 1. Détection de réflexion contrôlée

### Résumé

Si la valeur injectée apparaît dans la réponse, l'application reflète une entrée utilisateur. Le niveau de risque dépend du contexte de sortie et de l'encodage appliqué.

### Explication détaillée

Classification utile :

- **Info** : réflexion en texte HTML avec encodage correct ;
- **Low/Medium** : réflexion en attribut ou contexte ambigu ;
- **High potentiel** : réflexion en script inline sans neutralisation visible.

Le scanner conserve les preuves minimales (paramètre, valeur test, extrait de réponse).

### Exemple

- **OK** : `SecureOpsTest123` absent de la réponse.
- **Info** : chaîne reflétée en texte HTML.
- **Finding** : chaîne reflétée dans un attribut sans encodage défensif.

### Vulnérabilité et impact

- **Vraisemblance** : Forte.
- **Impact** : Faible à significative selon contexte de rendu et défenses XSS.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : faible à modéré (signal précurseur).**

### Conseils

- Encoder systématiquement les sorties selon le contexte (HTML, attribut, JS, URL).
- Valider/normaliser les entrées avant rendu.
- Renforcer CSP (`unsafe-inline` interdit si possible).
- Corréler ce signal avec les tests passifs CSP/headers.

### Références

- [OWASP – Cross Site Scripting Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP – Output Encoding](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html)
- [CWE-79 – Cross-site Scripting](https://cwe.mitre.org/data/definitions/79.html)
