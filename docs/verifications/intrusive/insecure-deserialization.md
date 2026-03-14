# Vérifications actives — Insecure deserialization

Ce document décrit les vérifications actives de deserialisation non securisee.

---

## Contexte et méthodologie

### Objectif

Detecter des endpoints qui deserialisent des objets non fiables sans validation d'integrite/type.

### Principe

- Identifier formats suspects (Java, .NET, Python, PHP, YAML, etc.).
- Envoyer payloads de test inoffensifs et verifier erreurs/signatures.
- Aucune exploitation RCE en mode standard.

---

## 1. Detection de deserialisation non controlee

### Exemple

- **OK** : format invalide rejete proprement.
- **Finding** : deserialisation acceptee avec comportement inattendu/signatures connues.

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

- Eviter deserialisation d'objets non fiables.
- Signer/chiffrer les objets serialises.
- Utiliser allowlist stricte de types.

### Références

- [OWASP – Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [CWE-502 – Deserialization of Untrusted Data](https://cwe.mitre.org/data/definitions/502.html)
