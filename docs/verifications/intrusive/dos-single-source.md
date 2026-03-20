# Vérifications actives — DoS single-source (léger)

Ce document décrit les vérifications actives limitées de résilience DoS depuis une source unique : objectif, méthode, risques, exemples et recommandations.

**Priorité :** P0 (indispensable). Ce test est **non destructif** et sert d’indicateur de posture.

---

## Distinction DoS P0 vs DoS P4

| Aspect | **Ce document (P0)** | **DoS P4** (mode expert) |
|--------|----------------------|---------------------------|
| Périmètre | Rate limiting absence, slowloris minimal | Burst agressif, amplification, volume élevé |
| Seuils | 5–10 req/s max, fenêtre 2 s, 1–2 connexions | Configurable, plus agressif |
| Objectif | Indicateur de posture faible | Évaluation résilience avancée |
| Activation | Par défaut (P0) | Mode expert, opt-in explicite |
| Risque cible | Très faible | Modéré, potentiellement perturbant |

Le test P4 est documenté dans le [catalogue complet](catalogue-complet-tests-intrusifs.md) — section P4. **Ce fichier ne couvre que le test P0 léger.**

---

## Contexte et méthodologie

### Objectif

Identifier des signaux de fragilité (absence de rate limiting, timeouts trop permissifs) sans réaliser d'attaque de saturation.

### Périmètre

- tests strictement bornés (requêtes, durée, connexions) ;
- une seule source scanner ;
- aucun comportement DDoS.

### Principe (MVP 1.0.0)

1. burst court (ex. 5-10 req/s, fenêtre brève) ;
2. observation des codes (`429`, `503`), latence et erreurs ;
3. test slowloris-like minimal (1-2 connexions).

---

## 1. Absence apparente de rate limiting

### Résumé

Un endpoint sensible qui accepte un burst court sans signe de régulation remonte un indicateur de risque DoS.

### Explication détaillée

Ce test n'établit pas une vulnérabilité DoS exploitable à grande échelle. Il indique une posture potentiellement faible.

### Exemple

- **OK** : apparition de `429` ou ralentissement contrôlé.
- **Info/Finding** : aucune limitation observable sur endpoint critique.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Significative à importante (selon architecture réelle).

---

## 2. Connexions lentes et timeouts serveurs

### Résumé

Le scanner vérifie si des connexions lentes restent ouvertes anormalement longtemps, ce qui peut augmenter le risque de consommation de ressources.

### Explication détaillée

Le test envoie lentement des fragments d'en-têtes sur 1-2 connexions uniquement. Le comportement attendu est une fermeture via timeout serveur.

### Exemple

- **OK** : connexion fermée rapidement selon la politique timeout.
- **Info/Finding** : connexions maintenues longtemps sans mécanisme de coupure.

### Vulnérabilité et impact

- **Vraisemblance** : Faible à moyenne.
- **Impact** : Significative.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead>
<tr>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Gravité \ Vraisemblance</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Forte</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très forte</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Mineure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : faible à modéré (indicateur de posture).**

### Conseils

- Mettre en place rate limiting par IP, route et méthode.
- Configurer des timeouts stricts (header/read/body/idle).
- Protéger via reverse proxy/WAF (burst + sustained).
- Suivre les métriques de saturation (connexions, p95/p99, erreurs 5xx).

### Références

- [OWASP – Denial of Service](https://owasp.org/www-community/attacks/Denial_of_Service)
- [CWE-400 – Uncontrolled Resource Consumption](https://cwe.mitre.org/data/definitions/400.html)
