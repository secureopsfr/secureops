# Vérifications Cookies

Ce document décrit en détail les vérifications relatives aux cookies HTTP : contexte, flags de sécurité, et détection des configurations à risque.

---

## Contexte : les cookies HTTP

### Qu’est-ce qu’un cookie ?

Un **cookie HTTP** (ou cookie web) est un petit fichier de données que le serveur envoie au navigateur via l’en-tête `Set-Cookie`. Le navigateur le stocke localement et le renvoie automatiquement à chaque requête vers le même domaine. Les cookies permettent au serveur de maintenir un **état** entre les requêtes, alors que le protocole HTTP est par nature sans état (stateless).

Techniquement, un cookie est défini par une paire nom/valeur et des attributs optionnels : `Domain`, `Path`, `Expires` ou `Max-Age`, `Secure`, `HttpOnly`, `SameSite`, `Partitioned`.

### À quoi servent les cookies ?

| Usage | Exemple |
|-------|---------|
| **Session / authentification** | Cookie `session_id` ou `PHPSESSID` pour identifier l’utilisateur connecté |
| **Préférences** | Langue, thème (clair/sombre), devise |
| **Panier d’achat** | Articles sélectionnés avant la finalisation |
| **Analytics** | Suivi de visite (ex. Google Analytics) |
| **Publicité** | Ciblage, remarketing (cookies tiers) |
| **Sécurité** | Token CSRF, consentement RGPD |

### Exemples de cookies

```
Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Strict
Set-Cookie: lang=fr; Path=/; Max-Age=31536000
Set-Cookie: _ga=GA1.2.123456; Domain=.example.com; Path=/; Max-Age=63072000; SameSite=Lax
```

Le premier exemple est un cookie de session typique : `HttpOnly` empêche l’accès en JavaScript (protection XSS), `Secure` impose l’envoi uniquement en HTTPS, `SameSite=Strict` limite l’envoi aux requêtes same-site (protection CSRF).

### Dimensions légales

Les cookies sont encadrés par plusieurs textes, notamment en Europe :

- **RGPD (règlement UE 2016/679)** : les cookies qui permettent d’identifier une personne (session, analytics, publicité) sont des données personnelles. Le traitement doit reposer sur une base légale (consentement, intérêt légitime, etc.) et respecter les principes de minimisation, limitation de la finalité et durée de conservation.

- **Directive ePrivacy (2002/58/CE)** et **Loi Informatique et Libertés (France)** : le stockage ou l’accès à des informations sur le terminal de l’utilisateur (cookies) nécessite le **consentement préalable** de l’utilisateur, sauf pour les cookies strictement nécessaires au fonctionnement du service (ex. session, panier).

- **CNIL (France)** : les cookies publicitaires et de mesure d’audience nécessitent un consentement explicite. Les bandeaux de consentement (cookie banners) doivent permettre un refus aussi simple que l’acceptation.

- **Sanctions** : non-respect du consentement ou du RGPD peut entraîner des amendes (jusqu’à 4 % du chiffre d’affaires mondial ou 20 M€ pour le RGPD).

**En résumé** : la conformité légale concerne surtout le **type** de cookies (nécessaires vs optionnels) et le **consentement**. Les vérifications techniques ci-dessous portent sur la **sécurité** des cookies (flags Secure, HttpOnly, SameSite) pour limiter les risques de vol de session et d’usurpation.

---

## 1. Flag Secure

### Résumé

Vérifier que les cookies sensibles (session, authentification) sont définis avec le flag **Secure**. Ce flag impose au navigateur de n’envoyer le cookie que sur des connexions HTTPS. Sans Secure, un cookie peut être transmis en clair sur HTTP et être intercepté par un attaquant (MITM, SSL stripping).

### Explication détaillée

Le flag `Secure` est un attribut booléen dans `Set-Cookie`. S’il est présent, le navigateur n’envoie le cookie que si la requête est effectuée via HTTPS. Sur un site accessible en HTTPS, tout cookie de session ou d’authentification doit avoir ce flag. Si le site est servi en HTTPS et qu’un cookie sensible n’a pas `Secure`, il peut être exposé lors d’une requête HTTP (redirection, lien mixte, downgrade). Le scan doit détecter les cookies sans `Secure` lorsque le site est accessible en HTTPS.

### Exemple

- **OK** : `Set-Cookie: session_id=xyz; Secure; HttpOnly; SameSite=Strict` sur `https://example.com`.
- **Finding** : `Set-Cookie: session_id=xyz; HttpOnly` sur `https://monsite.com` → cookie sans `Secure` alors que le site est en HTTPS → risque d’interception.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les attaques MITM ou SSL stripping sur Wi‑Fi public ou réseau compromis permettent de capturer les cookies envoyés en HTTP.
- **Impact** : Importante à majeure. Vol de session, usurpation d’identité, accès non autorisé au compte de l’utilisateur.

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

- Toujours définir `Secure` pour les cookies de session et d’authentification sur un site HTTPS.
- S’assurer que tout le site est servi en HTTPS avant d’activer `Secure` (sinon le cookie ne sera jamais envoyé).
- Vérifier la configuration du framework (Django, Flask, Express, etc.) et du serveur (Nginx, Apache) pour les cookies générés automatiquement.

### Références

- [OWASP – Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [MDN – Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)

---

## 2. Flag HttpOnly

### Résumé

Vérifier que les cookies sensibles (session, authentification) sont définis avec le flag **HttpOnly**. Ce flag empêche l’accès au cookie via JavaScript (`document.cookie`). Sans HttpOnly, un attaquant qui exploite une faille XSS peut voler le cookie de session et usurper l’identité de l’utilisateur.

### Explication détaillée

Le flag `HttpOnly` indique au navigateur que le cookie ne doit pas être accessible aux scripts côté client. Il est envoyé automatiquement avec les requêtes HTTP/HTTPS, mais `document.cookie` ne peut pas le lire ni le modifier. Cela réduit considérablement la surface d’attaque XSS : même si du JavaScript malveillant s’exécute, il ne peut pas exfiltrer le cookie de session. Le scan vérifie la présence de `HttpOnly` sur les cookies identifiés comme sensibles (session, auth, CSRF).

### Exemple

- **OK** : `Set-Cookie: PHPSESSID=abc123; HttpOnly; Secure; SameSite=Strict` → cookie protégé.
- **Finding** : `Set-Cookie: session_token=xyz; Secure` sans `HttpOnly` → accessible en JavaScript, vulnérable à XSS.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les vulnérabilités XSS (réfléchi, stocké, DOM-based) sont fréquentes ; sans HttpOnly, le vol de session est trivial.
- **Impact** : Importante à majeure. Vol de session, prise de contrôle du compte, actions effectuées au nom de la victime.

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

- Appliquer `HttpOnly` à tous les cookies de session et d’authentification.
- Les cookies accessibles en JavaScript (ex. préférences côté client) peuvent rester sans HttpOnly, mais ne doivent jamais contenir de données sensibles.
- Vérifier les frameworks et middlewares (ex. `session.cookie_httponly` en Express, `SESSION_COOKIE_HTTPONLY` en Django).

### Références

- [OWASP – Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [MDN – Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)

---

## 3. Flag SameSite

### Résumé

Vérifier que les cookies sensibles sont définis avec l’attribut **SameSite** (`Strict` ou `Lax`). SameSite limite l’envoi des cookies aux requêtes « same-site » (même domaine), ce qui réduit le risque d’attaques CSRF (Cross-Site Request Forgery) où un site tiers déclenche une requête authentifiée à l’insu de l’utilisateur.

### Explication détaillée

`SameSite` peut prendre trois valeurs :

- **Strict** : le cookie n’est envoyé que pour les requêtes same-site (navigation directe, pas de liens externes).
- **Lax** : le cookie est envoyé pour les requêtes same-site et pour les navigations top-level (clic sur un lien, GET). Pas envoyé pour les requêtes cross-site (formulaires POST, iframes, fetch depuis un autre site).
- **None** : le cookie est envoyé pour toutes les requêtes cross-site (nécessite `Secure`). À réserver aux cas où le cross-site est requis (ex. widgets, intégrations).

Sans `SameSite`, le navigateur applique par défaut `Lax` (comportement récent), mais une configuration explicite est recommandée. Le scan vérifie la présence et la valeur de `SameSite` ; `SameSite=None` sans besoin avéré peut être signalé.

### Exemple

- **OK** : `Set-Cookie: session_id=abc; SameSite=Strict; Secure; HttpOnly` → protection CSRF maximale.
- **OK** : `Set-Cookie: session_id=abc; SameSite=Lax; Secure; HttpOnly` → compromis entre sécurité et UX (liens externes fonctionnent).
- **Finding** : `Set-Cookie: session_id=abc; Secure; HttpOnly` sans `SameSite` → dépend du navigateur ; configurer explicitement.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne à forte. Les attaques CSRF sont courantes (formulaires malveillants, images, requêtes forgées) ; sans SameSite strict, un site tiers peut déclencher des actions authentifiées.
- **Impact** : Importante. Modification de données, transferts, changements de mot de passe, actions non autorisées au nom de l’utilisateur.

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

**Risque global : modéré.**

### Conseils

- Utiliser `SameSite=Strict` pour les cookies de session lorsque l’UX le permet (pas de redirection depuis des liens externes vers des pages authentifiées).
- Utiliser `SameSite=Lax` comme compromis si des liens externes pointent vers le site (ex. email de réinitialisation, liens partagés).
- Réserver `SameSite=None` aux cas où le cookie doit être envoyé en cross-site (widgets, intégrations) ; toujours combiner avec `Secure`.

### Références

- [OWASP – Cross-Site Request Forgery](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN – SameSite cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)

---

## 4. Cookies sans Secure sur site HTTPS

### Résumé

Détecter les cookies **sans le flag Secure** lorsque le site est servi en **HTTPS**. Sur un site HTTPS, tout cookie (surtout session, auth) doit être transmis uniquement en HTTPS ; l’absence de `Secure` permet au navigateur de l’envoyer aussi en HTTP, ce qui expose le cookie à l’interception.

### Explication détaillée

Cette vérification est un cas particulier du flag Secure (section 1), mais elle mérite une attention explicite dans le scan. Le flux est le suivant :

1. Le scan détermine que le site cible est accessible en HTTPS (ou qu’il redirige HTTP → HTTPS).
2. Une requête GET est envoyée vers l’URL cible (HTTPS).
3. Les en-têtes `Set-Cookie` de la réponse sont analysés.
4. Pour chaque cookie, on vérifie la présence du flag `Secure`.
5. Si un cookie n’a pas `Secure` et que le site est en HTTPS → finding.

Les cookies « techniques » (ex. préférence de langue sans donnée sensible) peuvent être tolérés sans Secure dans certains contextes, mais les cookies de session, d’authentification ou contenant des tokens doivent impérativement avoir `Secure`.

### Exemple

- **OK** : Site `https://example.com`, tous les cookies ont `Secure` → pas de finding.
- **Finding** : Site `https://monsite.com`, cookie `session_id=abc; HttpOnly; Path=/` sans `Secure` → cookie sensible exposé au risque d’interception sur HTTP.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Une requête HTTP peut survenir (lien mixte, redirection, SSL stripping) ; le cookie sans Secure sera envoyé en clair.
- **Impact** : Importante à majeure. Vol de session, usurpation d’identité, accès non autorisé.

### Matrice gravité / vraisemblance

Identique à la section 1 (Flag Secure). Voir la matrice ci-dessus.

**Risque global : modéré à élevé.**

### Conseils

- Appliquer systématiquement `Secure` à tous les cookies sur un site HTTPS.
- Auditer les réponses de login, d’inscription et des pages nécessitant une authentification.
- Vérifier les cookies définis par des sous-domaines ou des services tiers (API, CDN) si le scan les inclut.

### Références

- [OWASP – Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [MDN – Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)

---

## Améliorations v0.2.0 (implémentées)

### 5. Préfixes __Host- et __Secure- ✅

Détecter l’utilisation des préfixes **`__Host-`** et **`__Secure-`** sur les cookies sensibles. Finding : `cookies-no-host-secure-prefix` (info).

### 6. Cookie Partitioned (CHIPS) ✅

Vérifier l’attribut **`Partitioned`** (CHIPS – Cookies Having Independent Partitioned State) pour les cookies tiers. Ce mécanisme isole les cookies par site de premier niveau, limitant le tracking cross-site. Pertinent pour les cookies tiers (analytics, widgets). Info si cookie tiers sans Partitioned.

### 7. Alerte cookie de session sans HttpOnly + Secure + SameSite=Strict ✅

Alerte high **critique ou high** si un cookie identifié comme **session** (noms courants : `session`, `sessionid`, `PHPSESSID`, `JSESSIONID`, `connect.sid`, etc.) n’a pas les trois flags : `HttpOnly`, `Secure` et `SameSite=Strict` (ou `Lax` selon le cas). Combinaison minimale pour une session sécurisée.

### 8. Détection Expires trop lointain pour session ✅

Pour les cookies de session, si **`Expires`** ou **`Max-Age`** > 24h, finding : `cookies-session-expires-long` (low). Recommandation : sessions courtes ou cookies sans Expires.
