# Vérifications Méthodes HTTP et redirections

Ce document décrit les vérifications relatives aux **méthodes HTTP** exposées et aux **redirections** : objectif, risques (TRACE/XST, chaînes excessives), exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Les serveurs web peuvent accepter des **méthodes HTTP** variées (GET, POST, PUT, DELETE, TRACE, OPTIONS, etc.). Certaines méthodes sont dangereuses (TRACE → XST) ou inutilement exposées (PUT, DELETE sans nécessité). Les **redirections** mal configurées peuvent révéler des chaînes de redirection excessives.

Le scan effectue des requêtes **OPTIONS** pour lister les méthodes, des requêtes **TRACE** pour détecter XST, et suit les redirections pour compter les chaînes excessives.

> **Note :** La détection d'**open redirect** (paramètres url/redirect/next vers domaine externe) est une vérification **intrusive** prévue dans la roadmap ; voir [redirections-actives.md](../intrusive/redirections-actives.md).

---

## 1. Méthodes HTTP

### 1.1 Requête OPTIONS : méthodes autorisées

**Niveau :** Info (informatif — pas un finding de sécurité, aide à l'analyse de surface d'attaque).

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Envoyer une requête **OPTIONS** pour récupérer les **méthodes autorisées** via l’en-tête `Allow` ou via la réponse à une requête CORS preflight. Cela permet de connaître la surface d’attaque : quelles méthodes sont exposées ?

#### Explication détaillée

Une requête `OPTIONS` vers une URL peut renvoyer `Allow: GET, POST, OPTIONS` ou une liste plus longue. Le scan enregistre ces méthodes et les compare aux bonnes pratiques. Les méthodes dangereuses (TRACE, CONNECT) ou non nécessaires (PUT, DELETE sans usage documenté) peuvent être signalées.

#### Relation avec la vérification CORS

La catégorie **CORS et cross-origin** lisait auparavant `Access-Control-Allow-Methods` (ACAM) pour signaler PUT/DELETE/PATCH. Ce finding est **déplacé intégralement** dans la présente catégorie pour centraliser l'analyse des méthodes HTTP. CORS ne signale plus les méthodes dangereuses.

| Aspect | CORS (reste ACAO, ACAC, CORP…) | Méthodes HTTP |
|--------|--------------------------------|---------------|
| **Findings méthodes** | Aucun | Allow, ACAM, PUT/DELETE/PATCH, TRACE, HEAD |
**Allow vs ACAM :** Allow = surface globale ; ACAM = exposition cross-origin. Les deux sont extraits de la même réponse OPTIONS, sans requête supplémentaire.

#### Exemple

- **OK** : `Allow: GET, POST, OPTIONS` pour une API REST standard.
- **Info** : `Allow: GET, POST, PUT, DELETE, TRACE, OPTIONS` → TRACE et méthodes potentiellement inutiles sont exposées.

#### Conseils

- Réviser régulièrement la liste des méthodes autorisées ; n’exposer que celles qui sont nécessaires.

#### Références

- [MDN – HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)

---

### 1.2 TRACE activé

**Niveau :** Medium à High (risque XST, fuite cookies/headers).

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Si la méthode **TRACE** est activée, un attaquant peut l’utiliser pour une attaque **XST** (Cross-Site Tracing). TRACE renvoie au client le corps de la requête reçue ; si un cookie est envoyé, il peut être récupéré par du JavaScript malveillant via une requête TRACE cross-site (historiquement, avec des techniques d’anciens navigateurs).

#### Explication détaillée

TRACE est une méthode de diagnostic qui renvoie l’écho de la requête. Elle est rarement utilisée en production et peut révéler des headers sensibles (cookies, tokens). Les navigateurs modernes ont des protections, mais la désactivation de TRACE reste une bonne pratique.

#### Exemple

- **OK** : Requête TRACE → 405 Method Not Allowed ou 501.
- **Finding** : Requête TRACE → 200 avec corps contenant l’écho de la requête → TRACE activé, risque XST.

#### Vulnérabilité et impact

- **Vraisemblance** : Faible à moyenne. TRACE est souvent désactivé par défaut sur les serveurs modernes.
- **Impact** : Significative. Risque de fuite de cookies ou headers sensibles via XST (selon le navigateur et les configurations).

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

- Désactiver TRACE sur le serveur web (Nginx, Apache, IIS).
- Vérifier la configuration : `TraceEnable Off` (Apache), pas de support TRACE (Nginx).

#### Références

- [OWASP – Cross-Site Tracing](https://owasp.org/www-community/attacks/Cross_Site_Tracing)
- [CWE-693 – Protection Mechanism Failure](https://cwe.mitre.org/data/definitions/693.html)

---

### 1.3 PUT, DELETE, PATCH exposés sans nécessité

**Niveau :** Info à Low (surface d'attaque élargie ; gravité selon le contexte).

**Périmètre :** Les deux avec distinction — Frontend (site vitrine) : méthodes modifiantes inattendues → Low. Backend (API REST) : souvent légitimes → Info.

#### Résumé

Si les méthodes **PUT**, **DELETE**, **PATCH** sont exposées sans être nécessaires pour l’application, c’est une **augmentation de la surface d’attaque**. Un attaquant peut tenter des actions de modification ou suppression. Niveau info ou low : à vérifier si ces méthodes sont protégées et utilisées.

#### Explication détaillée

Pour une API REST, PUT/DELETE/PATCH sont souvent légitimes. Pour un site vitrine (pages statiques), elles ne devraient pas être présentes. Le scan signale leur présence comme information ; la gravité dépend du contexte (authentification, autorisation, rate limiting).

#### Conseils

- N’exposer que les méthodes nécessaires ; protéger PUT/DELETE/PATCH par authentification et autorisation.

#### Références

- [OWASP – HTTP Verb Tampering](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/03-Testing_for_HTTP_Verb_Tampering)

---

### 1.4 HEAD supporté

**Niveau :** Info (recommandation d'optimisation — pas un finding de sécurité).

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Vérifier que la méthode **HEAD** est supportée. HEAD est une bonne pratique : elle permet de récupérer les en-têtes sans télécharger le corps, utile pour la validation de cache (ETag, Last-Modified). Absence de HEAD = info, pas un finding de sécurité.

#### Explication détaillée

HEAD doit renvoyer les mêmes headers que GET mais sans corps. Certains serveurs ne l’implémentent pas correctement. Le scan peut le vérifier pour une recommandation d’optimisation.

#### Conseils

- S’assurer que le serveur supporte HEAD pour permettre la validation de cache (ETag, Last-Modified).

#### Références

- [MDN – HEAD](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD)

---

## 2. Redirections

### 2.1 Chaînes de redirection excessives (> 5)

**Niveau :** Info à Low.

**Périmètre :** Les deux (frontend et backend), sans distinction.

#### Résumé

Détecter les **chaînes de redirection** longues (plus de 5 redirections). Une chaîne excessive peut indiquer une mauvaise configuration (boucles, redirects inutiles) ou être utilisée pour contourner des contrôles. Elle dégrade aussi les performances et l'expérience utilisateur.

#### Explication détaillée

Le scan suit les redirections (avec une limite, ex. 10) et compte le nombre de sauts. Si plus de 5 redirections sont nécessaires pour atteindre la page finale, c’est un finding (info ou low).

#### Exemple

- **OK** : `http://example.com` → 301 → `https://example.com` → 200 (1 redirection).
- **Finding** : 6 redirections successives avant d’atteindre la page finale → chaîne excessive.

#### Conseils

- Simplifier les chaînes de redirection ; éviter les boucles ou les redirects inutiles.

#### Références

- [OWASP – Unvalidated Redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)

---

### 2.2 Redirection HTTP→HTTPS : code 301/302 vs 307/308

**Niveau :** Info (recommandation pour formulaires sensibles).

**Périmètre :** Les deux avec distinction — Frontend prioritaire (formulaires, login) : 301/302 sur POST peut perdre les données. Backend : pertinent si l'API redirige des requêtes POST.

#### Résumé

Pour une redirection **HTTP → HTTPS**, le code recommandé dépend du cas :

- **301** (Moved Permanently) ou **302** (Found) : la méthode peut être changée en GET par certains clients (comportement legacy).
- **307** (Temporary Redirect) ou **308** (Permanent Redirect) : la méthode est **préservée** (POST reste POST).

Pour une redirection de login ou de formulaire, **307/308** est préférable pour éviter qu’un POST ne soit converti en GET (perte de données). Le scan peut signaler 301/302 pour des redirections de formulaires sensibles comme une recommandation (info).

#### Explication détaillée

RFC 7231 : 301 et 302 peuvent changer en GET ; 307 et 308 préservent la méthode. Pour les formulaires, une redirection 302 peut faire perdre les données POST.

#### Conseils

- Utiliser 307 ou 308 pour les redirections de formulaires afin de préserver la méthode HTTP (POST reste POST).

#### Références

- [MDN – Redirections](https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections)
- [RFC 7231 – Status Codes](https://tools.ietf.org/html/rfc7231#section-6.4)

---

## Matrice de sévérité (synthèse)

| Vérification | Sévérité typique | Périmètre |
|--------------|------------------|-----------|
| OPTIONS (méthodes autorisées) | Info | Les deux |
| TRACE activé (XST) | Medium à High | Les deux |
| PUT/DELETE/PATCH exposés sans nécessité | Info à Low | Les deux (distinction frontend/backend) |
| HEAD supporté | Info | Les deux |
| Chaîne de redirection > 5 | Info à Low | Les deux |
| 301/302 sur formulaire POST | Info | Les deux (frontend prioritaire) |

---

## Décisions d'implémentation

### 1.3 PUT/DELETE/PATCH

Le finding est **déplacé entièrement** de la catégorie CORS vers `methodes_http_et_redirections`. CORS ne signale plus les méthodes dangereuses.

### TRACE, HEAD, redirections : périmètre des URLs

| Vérification | Périmètre | Justification |
|--------------|-----------|---------------|
| **TRACE** | Page + chemins sensibles (base + paths configurés) | Oui, ça sert : une API (`/api/`) peut avoir TRACE activé alors que la page d'accueil non. Limite configurable (ex. max 6 URLs). |
| **HEAD** | Uniquement l'URL de la page | Non nécessaire sur plusieurs chemins : le cas d'usage principal (validation cache ETag/Last-Modified) concerne la page principale. |
| **Redirections** (chaîne, 301/302) | Chaîne du fetch initial de chaque page | Déjà disponible : le fetch GET de la page suit les redirections. Pas de fetch supplémentaire sur base ou chemins sensibles. |

### 2.2 Formulaire sensible (301/302 vs 307/308)

**Détection des chemins à formulaire sensible :** liste configurable dans `settings.yml`, par ex. `form_sensitive_paths` avec des fragments de chemin par défaut : `/login`, `/auth`, `/signin`, `/register`, `/signup`. Une URL est considérée « formulaire sensible » si son chemin contient l'un de ces fragments. Pas de heuristique générique (détecter tout chemin pouvant servir un formulaire) — liste explicite uniquement.

### Catégorie et configuration

- **Catégorie dédiée** : `methodes_http_et_redirections` dans le rapport (section distincte).
- **Config** : tout défini dans `settings.yml` (scan-service). Exemple de section :

```yaml
methodes_http_et_redirections:
  redirect_chain_max: 5        # Nombre max de redirections avant finding
  trace_timeout: 3.0           # Timeout (s) pour requête TRACE
  trace_max_urls: 6            # Limite URLs testées (page + chemins sensibles)
  form_sensitive_paths:       # Chemins considérés formulaire sensible (301/302 vs 307/308)
    - "/login"
    - "/auth"
    - "/signin"
    - "/register"
    - "/signup"
  checks:
    trace: true
    head: true
    redirect_chain: true
    redirect_301_302: true
```

---

## Références générales

- [OWASP – Unvalidated Redirects and Forwards](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)
- [CWE-601 – URL Redirection to Untrusted Site](https://cwe.mitre.org/data/definitions/601.html)
