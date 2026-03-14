# Vérifications actives — HTTP request smuggling / desync

Ce document décrit les vérifications actives de desynchronisation HTTP entre proxy et backend.

---

## Contexte et méthodologie

### Objectif

Identifier des divergences d'interpretation de requetes (`Content-Length` vs `Transfer-Encoding`) pouvant mener a des attaques de smuggling.

### Principe

- Tests controles CL.TE / TE.CL selon architecture.
- Observation de reponses anormales, delais, desync.
- Execution reservee aux environnements autorises (risque `L3`).

---

## 1. CL/TE mismatch

### Exemple

- **OK** : requete rejetee proprement.
- **Finding** : comportement desynchronise mesurable.

### Vulnérabilité et impact

- **Vraisemblance** : Faible a moyenne.
- **Impact** : Majeure.

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

- Normaliser le parsing HTTP sur toute la chaine.
- Rejeter ambiguite CL/TE.
- Mettre a jour proxy/gateway et activer mitigations vendor.

### Références

- [PortSwigger – Request Smuggling](https://portswigger.net/web-security/request-smuggling)
- [CWE-444 – Inconsistent Interpretation of HTTP Requests](https://cwe.mitre.org/data/definitions/444.html)
