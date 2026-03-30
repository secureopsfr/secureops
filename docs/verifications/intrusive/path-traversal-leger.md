# Vérifications actives — Path Traversal (léger)

Ce document décrit les vérifications actives légères de path traversal : objectif, méthode, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Détecter les endpoints manipulant des chemins/fichiers (`file`, `path`, `document`, `template`, `include`) sans contrôles suffisants.

### Principe (actif léger, MVP 1.0.0)

Le scanner teste un jeu réduit de payloads :

- `../../../etc/passwd`
- `..%2f..%2f..%2fetc/passwd`
- `..\\..\\..\\windows\\win.ini` (si contexte Windows)

La détection s'appuie sur :

- variations de statut anormales (`500`, `200` inattendu) ;
- messages d'erreur de chemin (`No such file`, `Permission denied`, chemins absolus) ;
- signatures de contenu sensible.

### Limites

- 1 à 2 requêtes par paramètre ;
- pas de fuzzing exhaustif ;
- arrêt immédiat sur signal fort.

---

## 1. Indices de traversal sur paramètres de fichiers

### Résumé

Le scanner recherche des symptômes d'accès hors répertoire autorisé. L'objectif est la détection précoce, pas l'extraction massive.

### Explication détaillée

Niveaux de confiance possibles :

- **Info** : comportement anormal non concluant ;
- **Low/Medium** : erreur explicite liée au système de fichiers ;
- **High** : contenu sensible confirmé.

### Exemple

- **OK** : `400`/`404` propre, sans fuite de chemin.
- **Finding** : réponse contenant `root:x:0:0:` ou `C:\Windows\win.ini`.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Importante à majeure (lecture de secrets, pivot vers compromission).

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

- Canoniser les chemins avant accès disque.
- Appliquer une allowlist stricte de répertoires autorisés.
- Bloquer `..`, variantes encodées, séparateurs mixtes.
- Exécuter les processus avec privilèges minimaux.

### Références

- [OWASP – Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [CWE-22 – Path Traversal](https://cwe.mitre.org/data/definitions/22.html)
