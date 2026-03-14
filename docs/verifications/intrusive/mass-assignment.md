# Vérifications actives — Mass assignment

Ce document décrit les vérifications actives de mass assignment sur API.

---

## Contexte et méthodologie

### Objectif

Detecter l'acceptation de champs sensibles non exposes par le contrat API (ex. `role`, `is_admin`, `status`, `owner_id`).

### Principe

- Partir d'une requete legitime.
- Ajouter des champs sensibles potentiels.
- Observer si la modification est prise en compte.

---

## 1. Champs sensibles non whitelistes

### Résumé

L'API ne doit jamais accepter des champs sensibles non prevus par le contrat d'entree.

### Exemple

- **OK** : champs inconnus ignores/rejetes.
- **Finding** : `is_admin=true` accepte et persiste.

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

### Conseils

- Whitelist stricte des champs modifiables.
- Separation DTO entree/sortie.
- Validation schema stricte server-side.

### Références

- [OWASP API Top 10 – Mass Assignment](https://owasp.org/API-Security/)
