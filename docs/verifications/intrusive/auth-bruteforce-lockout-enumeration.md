# Vérifications actives — Auth brute force / lockout / enumeration

Ce document décrit les vérifications actives autour de l'authentification : protection brute force, lockout, backoff et enumeration utilisateur.

---

## Contexte et méthodologie

### Objectif

Verifier qu'un endpoint de login resiste aux tentatives repetées et ne revele pas d'information exploitable sur l'existence des comptes.

### Principe (actif modere, borne)

- Repetitions controlees sur un petit jeu d'identifiants.
- Observation de `429`, captcha, delais progressifs, lockout temporaire.
- Comparaison des messages d'erreur "user inexistant" vs "mot de passe invalide".

---

## 1. Bruteforce protection et lockout

### Résumé

L'absence de rate limiting/backoff/lockout sur login facilite le credential stuffing et le bruteforce.

### Exemple

- **OK** : apres N tentatives, `429` ou verrouillage temporaire.
- **Finding** : tentatives illimitees, aucune degradation/limitation.

### Vulnérabilité et impact

- **Vraisemblance** : Forte.
- **Impact** : Importante a majeure (prise de compte).

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

### Conseils

- Activer rate limiting et backoff progressif.
- Ajouter lockout temporaire et alerting.
- Combiner avec MFA sur comptes sensibles.

### Références

- [OWASP – Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP – Credential Stuffing](https://owasp.org/www-community/attacks/Credential_stuffing)

---

## 2. Enumeration utilisateur

### Résumé

Des messages d'erreur differencies permettent de confirmer l'existence d'un compte.

### Exemple

- **OK** : message unique generique pour tous les echecs.
- **Finding** : "utilisateur inconnu" vs "mot de passe invalide".
