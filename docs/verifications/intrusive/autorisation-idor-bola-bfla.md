# Vérifications actives — Autorisation (IDOR / BOLA / BFLA)

Ce document décrit les vérifications actives d'autorisation horizontale et verticale sur API et routes applicatives : objectif, méthode, impact et recommandations.

---

## Contexte et méthodologie

### Objectif

Detecter l'absence de controle d'acces sur les objets (IDOR/BOLA) et les fonctions (BFLA/escalade verticale).

### Principe

- Rejouer une requete legitime avec identifiant d'objet d'un autre compte.
- Tenter une action admin depuis un role standard.
- Verifier qu'aucune donnee sensible n'est retournee.
- Comparer les reponses (`403/404` attendu) et la variation de donnees.

---

## 1. Escalade horizontale (IDOR/BOLA)

### Résumé

Un utilisateur ne doit pas acceder aux objets d'un autre utilisateur via manipulation d'identifiant.

### Exemple

- **OK** : `403/404` sur objet d'un autre compte.
- **Finding** : acces autorise a la ressource tierce.

### Vulnérabilité et impact

- **Vraisemblance** : Forte.
- **Impact** : Majeure (exposition cross-tenant, fuite de donnees, actions illegitimes).

---

## 2. Escalade verticale (BFLA)

### Résumé

Un role non admin ne doit pas appeler des fonctions admin.

### Exemple

- **OK** : endpoint admin refuse (`403`).
- **Finding** : endpoint admin accessible depuis role standard.

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

**Risque global : élevé à critique.**

### Conseils

- Verifier l'autorisation cote serveur sur chaque ressource/fonction.
- Ne jamais deduire les droits depuis le client.
- Mettre en place tests automatiques par role et par tenant.

### Références

- [OWASP API Top 10 – BOLA](https://owasp.org/API-Security/)
- [OWASP ASVS – Access Control](https://owasp.org/www-project-application-security-verification-standard/)
