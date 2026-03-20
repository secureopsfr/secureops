# Vérifications actives — Cache poisoning / web cache deception

Ce document décrit les vérifications actives de cache poisoning et web cache deception.

---

## Contexte et méthodologie

### Objectif

Detecter des mecanismes de cache qui peuvent servir du contenu inapproprie (empoisonnement) ou mettre en cache des donnees privees.

### Tests

- Variations d'en-tetes influents.
- Chemins ambigus/extensions trompeuses.
- Verification de separation contenu public/prive.

---

## 1. Cache poisoning

### Exemple

- **OK** : cache key robuste, en-tetes non fiables ignores.
- **Finding** : contenu altere sert a d'autres utilisateurs.

## 2. Web cache deception

### Exemple

- **OK** : pages privees non cachees ou cache key correcte.
- **Finding** : contenu prive servi via URL pseudo-statique.

### Vulnérabilité et impact

- **Vraisemblance** : Faible a moyenne.
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

- Definir cache keys robustes.
- Eviter mise en cache de contenu authentifie.
- Normaliser en-tetes et chemins avant cache.

### Références

- [OWASP – Web Cache Poisoning](https://owasp.org/www-community/attacks/Cache_Poisoning)
- [PortSwigger – Web cache deception](https://portswigger.net/web-security/web-cache-deception)
