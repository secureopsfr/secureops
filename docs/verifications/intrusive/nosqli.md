# Vérifications actives — NoSQL injection

Ce document décrit les vérifications actives basiques de NoSQL injection (Mongo-like et variantes JSON).

---

## Contexte et méthodologie

### Objectif

Detecter les endpoints acceptant des structures/operateurs NoSQL non attendus (`$ne`, `$gt`, `$regex`, etc.).

### Principe

- Envoyer structures JSON controlees sur champs de filtre/login.
- Observer bypass d'authentification, resultats anormaux, erreurs moteur.

---

## 1. Injection d'operateurs

### Résumé

Si des operateurs NoSQL sont interpretes comme logique de requete au lieu de donnees, l'application peut etre bypass.

### Exemple

- **OK** : operateurs rejetes/neutralises.
- **Finding** : filtre `{"username":{"$ne":null}}` change le comportement.

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

- Valider schema et types strictement.
- Interdire operateurs non autorises en entree.
- Utiliser bindings/ORM securises.

### Références

- [OWASP – NoSQL Security](https://cheatsheetseries.owasp.org/)
- [PortSwigger – NoSQL Injection](https://portswigger.net/web-security/nosql-injection)
