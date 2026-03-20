# Vérifications CORS et cross-origin

Ce document décrit les vérifications relatives à la configuration **CORS** (Cross-Origin Resource Sharing) et aux risques **cross-origin** : objectif, configurations dangereuses, mixed content, et recommandations.

---

## Contexte et méthodologie

### Objectif

CORS permet à un site d’autoriser des requêtes cross-origin depuis d’autres domaines. Une mauvaise configuration peut :

- **Exposer des données** : `Access-Control-Allow-Origin: *` sur des endpoints sensibles permet à n’importe quel site de lire les réponses.
- **Créer des incohérences dangereuses** : `Access-Control-Allow-Credentials: true` avec `Origin: *` est invalide mais peut être mal interprété.
- **Révéler des headers sensibles** : `Access-Control-Expose-Headers` peut exposer des en-têtes normalement cachés.

Le scan envoie des requêtes avec l’en-tête `Origin` (ou analyse les réponses à des requêtes cross-origin) et vérifie les headers CORS retournés.

---

## 1. CORS

### 1.1 Access-Control-Allow-Origin: * sur endpoints sensibles

#### Résumé

Si un **endpoint sensible** (API avec données utilisateur, authentification, etc.) renvoie **`Access-Control-Allow-Origin: *`**, n’importe quel site web peut effectuer des requêtes et **lire la réponse**. Les cookies ne sont pas envoyés avec `*`, mais les données en clair (JSON, etc.) le sont.

#### Explication détaillée

`Access-Control-Allow-Origin: *` signifie que toutes les origines sont autorisées à lire la réponse. Pour une API publique (ex. catalogue de produits), cela peut être acceptable. Pour une API d’authentification, de profil utilisateur ou de données sensibles, c’est un **finding**.

Le scan doit identifier les endpoints sensibles (par l’URL, le contenu, ou une liste prédéfinie) et vérifier la valeur de `Access-Control-Allow-Origin`.

#### Exemple

- **OK** : API publique avec `Access-Control-Allow-Origin: *` (si aucune donnée sensible).
- **Finding** : `GET /api/user/profile` retourne `Access-Control-Allow-Origin: *` → toute origine peut lire le profil utilisateur si l’API est appelée avec des credentials (ou si l’auth est par token dans un header).

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les développeurs activent souvent CORS de manière permissive pour faciliter le développement.
- **Impact** : Importante à majeure. Fuite de données cross-site, exfiltration par un site malveillant.

#### Matrice gravité / vraisemblance

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

**Risque global : élevé sur endpoints sensibles.**

#### Conseils

- Restreindre `Access-Control-Allow-Origin` aux origines de confiance (liste explicite).
- Ne jamais utiliser `*` pour des endpoints avec données utilisateur ou authentification.

#### Références

- [OWASP – CORS](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing)
- [MDN – CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

---

### 1.2 Access-Control-Allow-Credentials: true + Origin: *

#### Résumé

La combinaison **`Access-Control-Allow-Credentials: true`** avec **`Access-Control-Allow-Origin: *`** est **invalide** selon la spec CORS : le navigateur doit rejeter la réponse. Cependant, une configuration incorrecte (ex. origine reflétée au lieu de `*`) peut créer une vulnérabilité. Le scan signale toute incohérence.

#### Explication détaillée

Avec `Credentials: true`, le serveur ne peut pas renvoyer `Origin: *` ; il doit refléter l’origine exacte. Si le scan détecte `Credentials: true` et une origine trop permissive, c’est un finding. De plus, une **réflexion d’origine non validée** (le serveur reflète toute origine dans `Access-Control-Allow-Origin`) est une vulnérabilité classique.

#### Exemple

- **Finding** : Requête avec `Origin: https://evil.com` → réponse `Access-Control-Allow-Origin: https://evil.com` et `Access-Control-Allow-Credentials: true` → attaquant peut lire des réponses authentifiées depuis evil.com.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. La réflexion d’origine non validée est une erreur courante.
- **Impact** : Critique. Exfiltration de données authentifiées par un site tiers.

#### Matrice gravité / vraisemblance

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

**Risque global : critique.**

#### Conseils

- Valider strictement l’origine : n’accepter que les domaines de confiance dans une liste blanche.
- Ne jamais refléter l’origine sans validation ; utiliser une liste explicite de domaines autorisés.

#### Références

- [PortSwigger – CORS misconfiguration](https://portswigger.net/web-security/cors)

---

### 1.3 Access-Control-Allow-Methods

#### Résumé

Vérifier **`Access-Control-Allow-Methods`** : les méthodes autorisées en cross-origin. Si des méthodes dangereuses (**PUT**, **DELETE**, **PATCH**) sont exposées sans nécessité, un attaquant peut déclencher des actions depuis un autre site. Recommandation : n’autoriser que les méthodes réellement utilisées.

#### Explication détaillée

Pour une API REST, `GET` et `POST` sont souvent suffisants pour les cas d’usage publics. `PUT`, `DELETE`, `PATCH` modifient des données ; les exposer en CORS sans authentification robuste ou sans nécessité augmente la surface d’attaque.

#### Exemple

- **Info** : API read-only (catalogue) avec `Allow-Methods: GET, POST, PUT, DELETE` → PUT/DELETE peut être inutile.

#### Conseils

- N’autoriser que les méthodes réellement utilisées par l’API.
- Réviser régulièrement la liste des méthodes autorisées.

#### Références

- [MDN – Access-Control-Allow-Methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Methods)

---

### 1.4 Access-Control-Expose-Headers

#### Résumé

**`Access-Control-Expose-Headers`** définit quels en-têtes de réponse sont exposés au JavaScript côté client. Si des en-têtes **sensibles** (tokens, clés, informations internes) sont exposés, ils peuvent être lus par du code JavaScript d’une origine tierce autorisée par CORS.

#### Explication détaillée

Par défaut, seuls quelques en-têtes sont exposés (`Cache-Control`, `Content-Language`, `Content-Type`, etc.). Si le serveur ajoute `X-Auth-Token`, `X-Request-ID` ou d’autres headers sensibles à `Expose-Headers`, ils deviennent lisibles par le client. Le scan peut signaler une exposition d’en-têtes potentiellement sensibles.

#### Conseils

- Ne pas exposer d’en-têtes contenant des tokens ou des informations sensibles.

#### Références

- [MDN – Access-Control-Expose-Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers)

---

## 2. Cross-origin

### 2.1 Mixed content (HTTP sur page HTTPS)

#### Résumé

Détecter les **ressources chargées en HTTP** sur une page servie en **HTTPS**. Les navigateurs bloquent les scripts et styles en HTTP (mixed active content), mais peuvent autoriser les images. Le scan analyse les URLs des ressources (scripts, CSS, images, iframes) et signale celles en `http://`.

#### Explication détaillée

Le mixed content affaiblit la sécurité : une ressource HTTP peut être modifiée en transit (MITM) et, pour les scripts, exécuter du code malveillant. Même pour les images, c’est une mauvaise pratique.

#### Exemple

- **Finding** : Page `https://example.com` charge `<script src="http://cdn.example.com/lib.js">` → mixed content.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les migrations partielles vers HTTPS ou les CDN mal configurés peuvent laisser des URLs en HTTP.
- **Impact** : Importante. Risque de MITM, d’injection de code, dégradation de la confiance utilisateur (avertissements navigateur).

#### Matrice gravité / vraisemblance

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

#### Conseils

- Utiliser des URLs relatives ou des URLs HTTPS pour toutes les ressources.
- Configurer les redirections HTTP → HTTPS côté CDN et serveurs.

#### Références

- [MDN – Mixed content](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)
- [OWASP – Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

### 2.2 Cross-Origin-Resource-Policy manquant sur APIs

#### Résumé

L’en-tête **`Cross-Origin-Resource-Policy`** (CORP) indique si une ressource peut être chargée par des origines cross-origin. Valeurs : `same-origin`, `same-site`, `cross-origin`. Pour les APIs qui ne doivent pas être chargées comme des ressources (fetch, XHR), ou pour limiter l’accès, CORP peut renforcer l’isolation.

#### Explication détaillée

CORP est utile pour empêcher des sites tiers d’inclure des ressources (images, scripts, fetch) depuis votre API. Pour une API REST consommée par des applications tierces, `cross-origin` peut être approprié. Pour une API interne ou sensible, `same-origin` ou `same-site` limite l’accès. L’absence de CORP laisse le comportement par défaut (souvent permissif). Info ou Low selon le contexte.

#### Conseils

- Utiliser `same-origin` ou `same-site` pour les APIs sensibles ; `cross-origin` uniquement si nécessaire.

#### Références

- [MDN – Cross-Origin-Resource-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cross-Origin-Resource-Policy)

---

### 2.3 Referrer-Policy trop permissif

#### Résumé

Vérifier que **`Referrer-Policy`** n’est pas trop permissif : `unsafe-url` ou **absence** de l’en-tête envoie l’URL complète dans le Referer, y compris vers des sites tiers. Cela peut fuiter des tokens, chemins sensibles, etc.

#### Explication détaillée

Voir [security-headers.md](security-headers.md) section Referrer-Policy. Une politique `no-referrer` ou `strict-origin-when-cross-origin` limite les fuites. `unsafe-url` envoie l’URL complète dans tous les cas → finding si utilisé sur des pages sensibles.

#### Conseils

- Utiliser `strict-origin-when-cross-origin` ou `no-referrer` pour les pages sensibles.
- Éviter `unsafe-url` ; ne pas placer de tokens dans l’URL.

#### Références

- [MDN – Referrer-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy)

---

## Matrice de sévérité (synthèse)

| Vérification | Sévérité typique |
|--------------|------------------|
| Access-Control-Allow-Origin: * sur API sensible | High |
| Credentials: true + réflexion d’origine non validée | Critical |
| Méthodes PUT/DELETE exposées sans nécessité | Low à Info |
| Exposition d’headers sensibles | Medium |
| Mixed content (HTTP sur HTTPS) | High |
| CORP manquant sur API sensible | Info à Low |
| Referrer-Policy unsafe-url | Medium |

---

## Références générales

- [OWASP – HTML5 Security Cheat Sheet (CORS)](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#cross-origin-resource-sharing)
- [CWE-346 – Origin Validation Error](https://cwe.mitre.org/data/definitions/346.html)
