# Vérifications APIs et formats

Ce document décrit les vérifications relatives aux **APIs exposées** (GraphQL, Swagger, REST) et aux **formats de réponse** (Content-Type, headers, compression) : objectif, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Les **APIs** (REST, GraphQL, etc.) et leur **documentation** (Swagger, OpenAPI) peuvent être exposées sans authentification, révélant la structure complète des endpoints, les schémas et les paramètres. Les **formats de réponse** incorrects (Content-Type, X-Content-Type-Options, compression) peuvent créer des problèmes de sécurité ou de compatibilité.

Le scan teste des chemins courants d’APIs et de documentation, et analyse les headers de réponse.

---

## 1. APIs exposées

### 1.1 Détection GraphQL : introspection activée

**Périmètre :** Backend uniquement (endpoints GraphQL).

#### Résumé

**GraphQL** permet une requête **introspection** qui permet de découvrir l’intégralité du schéma (types, champs, mutations). Si l’introspection est activée sur un endpoint public, un attaquant peut mapper toute l’API sans documentation. Le scan envoie une requête introspection vers `/graphql` (ou chemins similaires) et vérifie si le schéma est retourné.

#### Explication détaillée

Requête introspection typique :

```graphql
query { __schema { types { name } } }
```

Si la réponse contient le schéma complet, l’introspection est activée. En production, elle devrait être désactivée pour les endpoints publics, ou protégée par authentification.

#### Exemple

- **OK** : Requête introspection → erreur ou réponse vide (introspection désactivée).
- **Finding** : Requête introspection → 200 avec schéma JSON complet → API exposée.

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. L’introspection est activée par défaut sur de nombreux serveurs GraphQL.
- **Impact** : Significative à importante. Découverte complète de l’API, des types sensibles, des mutations ; facilitation des attaques ciblées.

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

**Risque global : modéré à élevé.**

#### Conseils

- Désactiver l’introspection en production sur les endpoints publics.
- Protéger l’endpoint GraphQL par authentification et autorisation.
- Limiter la profondeur de requête et le rate limiting.

#### Références

- [OWASP – GraphQL](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [GraphQL – Introspection](https://graphql.org/learn/introspection/)

---

### 1.2 Swagger / OpenAPI exposé sans auth

**Périmètre :** Backend uniquement (chemins de documentation API).

#### Résumé

Les chemins **`/swagger`**, **`/api-docs`**, **`/openapi.json`** exposent souvent la documentation complète de l’API. Si cette documentation est accessible sans authentification, un attaquant peut découvrir tous les endpoints, paramètres, schémas. Le scan teste ces chemins et vérifie si une documentation est retournée.

#### Explication détaillée

Swagger UI et OpenAPI sont des standards pour documenter les APIs. En production, la documentation ne devrait être accessible qu’aux développeurs autorisés (authentification, réseau interne). Une exposition publique facilite la reconnaissance.

#### Exemple

- **OK** : `GET /swagger` → 404 ou 401.
- **Finding** : `GET /swagger` → 200 avec interface Swagger UI ou JSON OpenAPI → documentation exposée.

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les projets incluent souvent Swagger par défaut et oublient de le protéger.
- **Impact** : Significative. Cartographie complète de l’API, découverte d’endpoints sensibles, tests d’exploitation facilités.

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

**Risque global : modéré à élevé.**

#### Conseils

- Protéger la documentation par authentification ou la désactiver en production.
- Limiter l’accès par IP (réseau interne, VPN).
- Ne pas exposer de détails sensibles (exemples de tokens, secrets) dans la doc.

#### Références

- [OWASP – API Security](https://cheatsheetseries.owasp.org/cheatsheets/API_Security_Cheat_Sheet.html)
- [Swagger – Security](https://swagger.io/docs/specification/authentication/)

---

### 1.3 Endpoints REST : listes non paginées

**Périmètre :** Backend uniquement (endpoints REST retournant des listes).

#### Résumé

Les endpoints REST qui retournent des **listes** (ex. `/api/users`, `/api/orders`) sans **pagination** peuvent exposer des volumes de données importants ou permettre des dénis de service (requête massive). Le scan peut détecter des réponses JSON avec des tableaux non paginés (info ou low).

#### Explication détaillée

Une API qui retourne `{"users": [...], "total": 10000}` sans pagination peut :
- Surcharger le client et le serveur.
- Exposer des données en masse.

Le scan peut signaler une réponse avec un tableau de grande taille ou sans paramètres `page`/`limit` comme une recommandation.

#### Conseils

- Implémenter la pagination (page, limit) sur tous les endpoints retournant des listes.

#### Références

- [OWASP – API Security](https://cheatsheetseries.owasp.org/cheatsheets/API_Security_Cheat_Sheet.html)

---

## 2. Formats de réponse

### 2.1 Content-Type incorrect

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Vérifier que le **`Content-Type`** correspond au contenu réel. Par exemple, du JSON servi avec `Content-Type: text/html` peut provoquer des comportements inattendus (MIME sniffing, exécution). Une API JSON doit renvoyer `Content-Type: application/json`.

#### Explication détaillée

Le scan peut :
- Envoyer une requête vers une API (ex. `GET /api/`).
- Vérifier que `Content-Type` est cohérent (JSON → `application/json`, HTML → `text/html`).

Un Content-Type incorrect peut favoriser le MIME sniffing ou des attaques XSS si le contenu est interprété comme un script.

#### Exemple

- **OK** : API JSON avec `Content-Type: application/json`.
- **Finding** : API JSON avec `Content-Type: text/html` → Content-Type incorrect.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les serveurs mal configurés peuvent envoyer un mauvais Content-Type.
- **Impact** : Significative. MIME sniffing, exécution non prévue, XSS.

#### Conseils

- S’assurer que chaque type de réponse a le Content-Type approprié (application/json pour JSON, text/html pour HTML, etc.).

#### Références

- [OWASP – MIME Sniffing](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- [CWE-434 – Unrestricted Upload of File with Dangerous Type](https://cwe.mitre.org/data/definitions/434.html)

---

### 2.2 X-Content-Type-Options: nosniff sur tous les types

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

L’en-tête **`X-Content-Type-Options: nosniff`** doit être présent sur **toutes** les réponses (HTML, JSON, API, etc.) pour empêcher le MIME sniffing. Le scan vérifie sa présence sur la page principale et, si possible, sur les réponses API.

#### Explication détaillée

Voir [security-headers.md](security-headers.md). Sans `nosniff`, un navigateur peut interpréter un fichier JSON comme du HTML ou du JavaScript. Pour les APIs, c’est souvent moins critique (car consommées par programmation), mais la cohérence est recommandée.

#### Conseils

- Ajouter `X-Content-Type-Options: nosniff` sur toutes les réponses, y compris les APIs.

#### Références

- [MDN – X-Content-Type-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options)

---

### 2.3 Compression (gzip/brotli)

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Vérifier si la réponse est **compressée** (gzip, brotli) via l’en-tête `Content-Encoding`. La compression réduit la taille des réponses et la surface d’attaque (moins de données en transit). Son absence n’est pas une vulnérabilité, mais une recommandation d’optimisation (info).

#### Explication détaillée

Le scan envoie une requête avec `Accept-Encoding: gzip, deflate, br` et vérifie si la réponse contient `Content-Encoding: gzip` (ou `br`). Pour les sites à fort trafic, la compression est une bonne pratique.

#### Exemple

- **OK** : Réponse avec `Content-Encoding: gzip` ou `br`.
- **Info** : Réponse sans compression pour une page HTML volumineuse → opportunité d’optimisation.

#### Conseils

- Activer la compression gzip ou brotli sur le serveur pour les réponses textuelles (HTML, JSON, CSS, JS).

#### Références

- [MDN – Content-Encoding](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding)

---

## Matrice de sévérité (synthèse)

| Vérification | Périmètre | Sévérité typique |
|--------------|-----------|------------------|
| GraphQL introspection activée | Backend | Medium à High |
| Swagger/OpenAPI exposé sans auth | Backend | Medium à High |
| Listes non paginées | Backend | Info à Low |
| Content-Type incorrect | Les deux | Medium |
| X-Content-Type-Options manquant | Les deux | Low à Medium |
| Absence de compression | Les deux | Info |

---

## Références générales

- [OWASP – API Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/API_Security_Cheat_Sheet.html)
- [OWASP – GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
- [CWE-200 – Exposure of Sensitive Information](https://cwe.mitre.org/data/definitions/200.html)
