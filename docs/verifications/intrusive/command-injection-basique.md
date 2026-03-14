# Vérifications actives — Command injection (basique)

Ce document décrit les vérifications actives non destructives de command injection.

---

## Contexte et méthodologie

### Objectif

Identifier des endpoints qui passent des entrees utilisateur a un shell/system call sans neutralisation suffisante.

### Principe (safe mode)

- Payloads limites et non destructifs.
- Recherche d'erreurs systeme, differences de reponse, indices de concatenation shell.
- Aucun payload de prise de controle.

---

## 1. Detection d'indices de command injection

### Résumé

Le scanner signale les symptomes d'execution shell potentielle (erreurs, comportement inattendu), sans exploitation complete.

### Exemple

- **OK** : entree invalide rejetee proprement.
- **Finding** : message d'erreur shell ou resultat anormal coherent avec interpretation de metacaracteres.

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

- Eviter `shell=True` / concatenation de commande.
- Utiliser APIs natives avec arguments listes.
- Appliquer allowlist stricte des caracteres/valeurs.

### Références

- [OWASP – OS Command Injection Defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)
- [CWE-78 – OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
