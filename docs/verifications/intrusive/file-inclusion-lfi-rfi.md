# Vérifications actives — File Inclusion (LFI/RFI)

Ce document décrit les vérifications actives de file inclusion locale/distante selon la stack cible.

---

## Contexte et méthodologie

### Objectif

Detecter les endpoints qui incluent/chargent des fichiers depuis un parametre non contraint.

### Principe

- Tests sur parametres typiques (`file`, `template`, `view`, `include`).
- Detection d'erreurs d'inclusion et de contenu inattendu.
- Variantes encodees et chemins relatifs.

---

## 1. Local File Inclusion (LFI)

### Exemple

- **OK** : refus propre ou mapping strict.
- **Finding** : inclusion de fichier local hors scope.

## 2. Remote File Inclusion (RFI, selon techno)

### Exemple

- **OK** : URLs distantes refusees.
- **Finding** : tentative d'inclusion distante acceptee.

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

**Risque global : modéré à élevé.**

### Conseils

- Interdire toute inclusion dynamique basee sur entree utilisateur.
- Mapper des identifiants logiques vers templates/fichiers fixes.
- Bloquer chemins absolus, traversal et URLs distantes.

### Références

- [OWASP – File Inclusion](https://owasp.org/www-community/vulnerabilities/PHP_File_Inclusion)
- [CWE-98 – Improper Control of Filename for Include](https://cwe.mitre.org/data/definitions/98.html)
