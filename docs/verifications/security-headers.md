# Vérifications Security Headers

Ce document décrit en détail chaque en-tête de sécurité HTTP à vérifier : objectif, failles associées, explication et exemples.

---

## 1. Content-Security-Policy

### Résumé

Vérifier la présence de l’en-tête **Content-Security-Policy** (CSP). Il définit les sources autorisées pour les scripts, styles, images, polices, etc. Sans CSP, une attaque XSS peut charger et exécuter du code arbitraire injecté depuis n’importe quelle origine.

### Explication détaillée

Le CSP restreint les origines depuis lesquelles le navigateur peut charger des ressources (scripts, styles, images, iframes, formulaires). Une politique stricte limite les vecteurs d’attaque XSS (Cross-Site Scripting) et de data injection. Le scan vérifie la présence de l’en-tête dans la réponse HTTP. Une analyse plus poussée (V2) pourrait évaluer la qualité de la politique (directives `default-src`, `script-src`, `style-src`, etc.).

### Exemple

- **OK** : `Content-Security-Policy: default-src 'self'; script-src 'self'` → en-tête présent.
- **Finding** : Aucun en-tête `Content-Security-Policy` dans la réponse → pas de restriction, risque XSS accru.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les vulnérabilités XSS sont fréquentes ; sans CSP, un attaquant peut injecter du JavaScript malveillant et l’exécuter dans le contexte de la page.
- **Impact** : Importante. Vol de session (cookies), exfiltration de données, redirection vers des sites malveillants, modification du contenu affiché.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré à élevé.**

### Conseils

- Ajouter une politique CSP stricte (principe du moindre privilège : `default-src 'self'` puis assouplir selon les besoins).
- Utiliser `report-uri` ou `report-to` pour détecter les violations en production.
- Tester en mode `Content-Security-Policy-Report-Only` avant de déployer en mode bloquant.
- Éviter `unsafe-inline` et `unsafe-eval` pour les scripts ; privilégier les nonces ou hashes.

### Références

- [OWASP – Content Security Policy](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [MDN – Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)

---

## 2. Strict-Transport-Security

### Résumé

Vérifier la présence de l’en-tête **Strict-Transport-Security** (HSTS). Il indique au navigateur de n’accéder au site qu’en HTTPS pendant une durée donnée. Sans HSTS, une attaque par downgrade ou SSL stripping peut forcer une connexion HTTP non chiffrée.

### Explication détaillée

HSTS envoie une directive (`max-age`, optionnellement `includeSubDomains`, `preload`) qui demande au navigateur de ne jamais utiliser HTTP pour ce domaine pendant la période indiquée. Cela protège contre les attaques MITM qui tentent de faire accepter une version HTTP de la page. Le scan vérifie la présence de l’en-tête dans la réponse HTTPS. Note : HSTS n’a de sens que sur un site déjà servi en HTTPS.

### Exemple

- **OK** : `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` → en-tête présent.
- **Finding** : Aucun en-tête `Strict-Transport-Security` dans la réponse HTTPS → risque de downgrade vers HTTP.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les attaques SSL stripping (downgrade HTTPS → HTTP) sont réalisables sur des réseaux non sécurisés (Wi‑Fi public, ARP spoofing).
- **Impact** : Importante. Interception du trafic, vol de cookies de session, usurpation d’identité si l’utilisateur accepte une page HTTP.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré à élevé.**

### Conseils

- Configurer HSTS avec `max-age` d’au moins 31536000 (1 an).
- Utiliser `includeSubDomains` si tous les sous-domaines sont en HTTPS.
- Envisager `preload` pour figurer dans la liste HSTS préchargée des navigateurs.
- Ne pas activer HSTS tant que le site n’est pas entièrement accessible en HTTPS.

### Références

- [OWASP – HTTP Strict Transport Security](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html#http-strict-transport-security-hsts)
- [MDN – Strict-Transport-Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
- [HSTS Preload](https://hstspreload.org/)

---

## 3. X-Frame-Options

### Résumé

Vérifier la présence de l’en-tête **X-Frame-Options**. Il empêche le site d’être affiché dans une iframe sur un autre domaine. Sans cet en-tête, une attaque par clickjacking peut inciter l’utilisateur à cliquer sur des éléments masqués.

### Explication détaillée

`X-Frame-Options` indique au navigateur s’il peut afficher la page dans une frame (`DENY`, `SAMEORIGIN`, ou `ALLOW-FROM` obsolète). Un site sans protection peut être intégré dans une page malveillante transparente ; l’utilisateur croit cliquer sur un bouton innocent alors qu’il déclenche une action sensible (transfert d’argent, changement de mot de passe). Le scan vérifie la présence de l’en-tête.

### Exemple

- **OK** : `X-Frame-Options: DENY` ou `X-Frame-Options: SAMEORIGIN` → en-tête présent.
- **Finding** : Aucun en-tête `X-Frame-Options` dans la réponse → risque de clickjacking.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Le clickjacking est simple à mettre en place ; une page malveillante peut iframer n’importe quel site non protégé.
- **Impact** : Significative à importante. Actions non autorisées (clics, formulaires), vol de données sensibles, escroquerie selon les fonctionnalités du site.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré.**

### Conseils

- Utiliser `X-Frame-Options: DENY` pour interdire tout framing, ou `SAMEORIGIN` si des iframes internes sont nécessaires.
- Pour une politique plus fine, privilégier la directive `frame-ancestors` de CSP (remplace progressivement X-Frame-Options).
- Appliquer l’en-tête sur toutes les pages, y compris les erreurs (404, 500).

### Références

- [OWASP – Clickjacking Defense](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html)
- [MDN – X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)

---

## 4. X-Content-Type-Options

### Résumé

Vérifier la présence de l’en-tête **X-Content-Type-Options: nosniff**. Il empêche le navigateur de deviner le type MIME d’une ressource (MIME sniffing). Sans cet en-tête, un fichier mal étiqueté peut être interprété comme un script exécutable, favorisant des attaques XSS ou l’exécution de contenu non prévu.

### Explication détaillée

Par défaut, certains navigateurs peuvent ignorer le `Content-Type` et deviner le type d’un fichier à partir de son contenu. Un attaquant peut uploader un fichier (ex. image) contenant du JavaScript ; si le serveur le sert avec un type incorrect ou générique, le navigateur peut l’exécuter. `X-Content-Type-Options: nosniff` force le respect du `Content-Type` déclaré. Le scan vérifie la présence de l’en-tête.

### Exemple

- **OK** : `X-Content-Type-Options: nosniff` → en-tête présent.
- **Finding** : Aucun en-tête `X-Content-Type-Options` dans la réponse → risque de MIME sniffing.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne à forte. L’exploitation nécessite d’uploader ou de servir du contenu mal typé ; les cas sont courants sur les sites avec upload de fichiers ou CDN mal configurés.
- **Impact** : Significative. Exécution de script non prévu, XSS, contournement de protections basées sur le type de contenu.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré.**

### Conseils

- Toujours envoyer `X-Content-Type-Options: nosniff` sur les réponses HTML et les ressources potentiellement exécutables.
- S’assurer que le serveur envoie un `Content-Type` correct pour chaque ressource.
- Appliquer sur les pages d’erreur et les réponses API.

### Références

- [OWASP – MIME Sniffing](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [MDN – X-Content-Type-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options)

---

## 5. Referrer-Policy

### Résumé

Vérifier la présence de l’en-tête **Referrer-Policy**. Il contrôle la quantité d’informations envoyées dans l’en-tête `Referer` lors des navigations (liens, redirections, requêtes cross-origin). Sans politique stricte, des URLs sensibles (tokens, paramètres) peuvent fuiter vers des sites tiers.

### Explication détaillée

Le `Referer` est envoyé automatiquement par le navigateur lors des requêtes ; il peut contenir des chemins complets, des query strings (tokens, IDs de session). Une politique permissive (`no-referrer-when-downgrade`, défaut) envoie l’URL complète vers des sites HTTPS tiers. `Referrer-Policy` permet de restreindre (ex. `strict-origin-when-cross-origin`, `no-referrer`). Le scan vérifie la présence de l’en-tête.

### Exemple

- **OK** : `Referrer-Policy: strict-origin-when-cross-origin` ou `Referrer-Policy: no-referrer` → en-tête présent.
- **Finding** : Aucun en-tête `Referrer-Policy` dans la réponse → comportement par défaut, risque de fuite d’URLs sensibles.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. La fuite dépend des liens externes et des paramètres sensibles dans l’URL ; les cas sont fréquents (liens de partage, analytics, réseaux sociaux).
- **Impact** : Significative. Fuite de tokens dans l’URL, de chemins internes, d’identifiants de session ; atteinte à la confidentialité et à la vie privée.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : faible à modéré.**

### Conseils

- Utiliser `strict-origin-when-cross-origin` comme compromis (origine seule en cross-origin, URL complète en same-origin).
- Pour les pages sensibles (authentification, paiement), envisager `no-referrer` ou `same-origin`.
- Éviter de placer des tokens ou données sensibles dans l’URL ; privilégier les en-têtes ou le corps de requête.

### Références

- [OWASP – Referrer Policy](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#referrer-policy)
- [MDN – Referrer-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy)

---

## 6. Permissions-Policy

### Résumé

Vérifier la présence de l’en-tête **Permissions-Policy** (anciennement Feature-Policy). Il contrôle quelles fonctionnalités du navigateur (géolocalisation, caméra, microphone, etc.) peuvent être utilisées par la page et ses iframes. Sans cet en-tête, des APIs sensibles restent accessibles par défaut, augmentant la surface d’attaque.

### Explication détaillée

Permissions-Policy permet de désactiver ou restreindre des fonctionnalités (ex. `geolocation=()`, `camera=()`, `microphone=()`, `payment=()`) pour la page et ses frames. Une politique stricte limite l’exposition en cas de XSS ou d’injection de contenu tiers. Le scan vérifie la présence de l’en-tête. Une analyse plus poussée pourrait vérifier que les APIs non utilisées sont explicitement désactivées.

### Exemple

- **OK** : `Permissions-Policy: geolocation=(), microphone=(), camera=()` → en-tête présent, APIs sensibles désactivées.
- **Finding** : Aucun en-tête `Permissions-Policy` dans la réponse → APIs accessibles par défaut selon le navigateur.

### Vulnérabilité et impact

- **Vraisemblance** : Faible à moyenne. L’exploitation nécessite une vulnérabilité préexistante (XSS) ou une intégration tierce malveillante ; l’impact dépend des fonctionnalités exposées.
- **Impact** : Variable. Accès non autorisé à la caméra, au micro, à la géolocalisation ; atteinte à la vie privée ; abus de fonctionnalités (ex. paiement) si le site les utilise.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : faible à modéré.**

### Conseils

- Désactiver les APIs non utilisées : `geolocation=(), microphone=(), camera=(), payment=(), usb=()` etc.
- Utiliser la liste vide `()` pour interdire une fonctionnalité à tous les origines.
- Consulter la liste des directives supportées (MDN, spécification) et adapter selon les besoins du site.

### Références

- [MDN – Permissions-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy)
- [W3C – Permissions Policy](https://w3c.github.io/webappsec-permissions-policy/)
