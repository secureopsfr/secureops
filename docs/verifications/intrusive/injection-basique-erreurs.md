# Vérifications actives — Injection basique (erreurs révélatrices)

Ce document décrit les vérifications actives légères de détection d'injection par observation d'erreurs : objectif, méthode, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Détecter des signes d'injection potentielle (principalement SQL) sans exploitation. Le scanner déclenche des erreurs contrôlées et observe la robustesse de la gestion d'erreur.

### Principe (actif léger, MVP 1.0.0)

Le scanner teste des paramètres fréquents (`id`, `search`, `q`, etc.) avec des caractères simples :

- `'`
- `"`

Il recherche ensuite des signatures d'erreur connues :

- `SQL syntax`
- `mysql_fetch`
- `PostgreSQL`
- `ORA-`
- `SQLite`
- traces de driver/ORM dans la réponse.

### Limite volontaire

Le scanner ne réalise pas de preuve d'exploitation (pas d'union select, pas de time-based, pas d'exfiltration).

---

## 1. Détection d'erreurs SQL révélatrices

### Résumé

La présence d'erreurs SQL dans la réponse indique une entrée mal maîtrisée et/ou une gestion d'erreur inadaptée, compatible avec un risque d'injection.

### Explication détaillée

Le scanner classe les résultats :

- **Info** : erreur applicative générique ;
- **Medium** : message moteur SQL explicite ;
- **High potentiel** : stack trace DB détaillée avec requête partielle.

La sévérité réelle dépend du contexte de l'endpoint et de la protection applicative.

### Exemple

- **OK** : réponse stable, pas de message technique.
- **Finding** : `You have an error in your SQL syntax` après `id='`.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Importante à majeure (selon exploitabilité réelle).

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

- Utiliser des requêtes paramétrées partout.
- Masquer les erreurs techniques côté client.
- Journaliser les détails en interne.
- Valider strictement les types et formats d'entrée.

### Références

- [OWASP – SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [CWE-89 – SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
