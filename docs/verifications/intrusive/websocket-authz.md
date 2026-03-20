# Vérifications actives — WebSocket authorization

Ce document décrit les vérifications actives d'autorisation sur canaux WebSocket.

---

## Contexte et méthodologie

### Objectif

Verifier qu'un client authentifie ne peut pas executer des actions ou lire des flux hors de son scope apres handshake.

### Tests

- Tentatives d'abonnement a des topics non autorises.
- Emission d'actions reservees a d'autres roles.
- Reconnexion avec token expire/revoque.

---

## 1. Authz post-handshake

### Exemple

- **OK** : actions non autorisees refusees.
- **Finding** : lecture/ecriture cross-tenant possible.

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

- Revalider authz a chaque message sensible.
- Segmenter topics/canaux par tenant/utilisateur.
- Expirer/revoquer sessions WS proprement.

### Références

- [OWASP – WebSocket Security](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)
