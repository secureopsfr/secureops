# Vérifications actives — SSTI

Ce document décrit les vérifications actives Server-Side Template Injection (SSTI).

---

## Contexte et méthodologie

### Objectif

Detecter des templates serveur evaluant directement des entrees utilisateur.

### Principe

- Envoyer des marqueurs de test non destructifs selon moteurs probables.
- Observer evaluation inattendue, erreurs template, differences de rendu.

---

## 1. Detection de rendu evalue

### Exemple

- **OK** : la valeur est rendue comme texte brut.
- **Finding** : sortie evalutee ou erreur moteur template.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Importante a majeure.

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

**Risque global : élevé.**

### Conseils

- Eviter evaluation dynamique de templates depuis entree utilisateur.
- Encoder/echapper strictement les variables.
- Restreindre les fonctions accessibles au moteur template.

### Références

- [PortSwigger – SSTI](https://portswigger.net/web-security/server-side-template-injection)
- [CWE-94 – Code Injection](https://cwe.mitre.org/data/definitions/94.html)
