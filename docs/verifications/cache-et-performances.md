# Vérifications Cache et performances

Ce document décrit les vérifications relatives aux **headers de cache** et à la **mise en cache des ressources** : objectif, risques (données sensibles cachées, incohérences), exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Les headers de cache (`Cache-Control`, `ETag`, `Last-Modified`, `Vary`) contrôlent comment les navigateurs et les proxies mettent en cache les réponses. Une mauvaise configuration peut :
com
- **Exposer des données sensibles** : une page de login ou d’admin cachée publiquement peut être lue depuis le cache d’un poste partagé.
- **Réduire les performances** : des assets statiques sans cache long sont re-téléchargés inutilement.
- **Créer des incohérences** : `Pragma: no-cache` sans `Cache-Control` cohérent peut donner des comportements imprévisibles.

Le scan analyse les headers de cache sur la **page principale fournie** (uniquement l’URL scannée) et, si possible, sur un **sous-ensemble limité de sous-requêtes** (scripts, CSS, images) déclarées dans le HTML :

- aucune autre page du site n’est appelée (pas de crawling) ;
- seules les balises `<script src>`, `<link rel="stylesheet" href>` et `<img src>` sont prises en compte ;
- un **plafond configurable** limite le nombre de sous-ressources analysées (ex. `cache.max_sub_resources` dans `settings.yml`) ;
- le scan privilégie les scripts et feuilles de style, puis les images, afin de couvrir en priorité les ressources les plus critiques pour la performance.

---

## 1. Headers de cache (page principale)

### 1.1 Cache-Control : présence et directives

#### Résumé

Vérifier la présence et le contenu de l’en-tête **`Cache-Control`**. Pour les pages dynamiques ou sensibles (login, admin, API), les directives doivent empêcher la mise en cache (`no-store`, `no-cache`, `private`). Pour les assets statiques, un cache long (`max-age`, `immutable`) est recommandé.

#### Explication détaillée

Directives principales :

| Directive | Effet |
|-----------|-------|
| `no-store` | Ne pas stocker la réponse (le plus restrictif) |
| `no-cache` | Revalider avant utilisation (peut stocker avec revalidation) |
| `private` | Cache autorisé uniquement côté client (pas dans les proxies partagés) |
| `public` | Cache autorisé partout (proxies, CDN) |
| `max-age=N` | Durée de validité en secondes |
| `immutable` | La ressource ne change pas ; pas de revalidation |

Pour une page de login ou d’administration : `Cache-Control: no-store` ou `private, no-cache` est attendu.

#### Exemple

- **OK** : Page login avec `Cache-Control: no-store` ou `private, no-cache`.
- **Finding** : Page login avec `Cache-Control: public, max-age=3600` → risque que des données de session soient cachées et accessibles depuis un poste partagé.

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les configurations par défaut des serveurs et frameworks mettent souvent en cache les réponses.
- **Impact** : Importante. Fuite de données sensibles depuis le cache (poste partagé, navigateur public), atteinte à la confidentialité.

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

- Pages sensibles : `Cache-Control: no-store` ou `private, no-cache`.
- Assets immuables (JS/CSS avec hash) : `Cache-Control: public, max-age=31536000, immutable`.

#### Références

- [OWASP – Caching](https://cheatsheetseries.owasp.org/cheatsheets/Web_Service_Security_Cheat_Sheet.html#caching)
- [MDN – Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

---

### 1.2 Pragma: no-cache (legacy)

#### Résumé

L’en-tête **`Pragma: no-cache`** est un legacy HTTP/1.0, encore utilisé pour la compatibilité. Il doit être **cohérent** avec `Cache-Control`. Si `Cache-Control` dit `max-age=3600` mais `Pragma: no-cache` est présent, le comportement peut être ambigu.

#### Explication détaillée

`Pragma: no-cache` est équivalent à `Cache-Control: no-cache` pour les requêtes. En réponse, il est moins standard. Le scan peut signaler une incohérence entre les deux headers.

#### Conseils

- S’assurer que `Pragma` et `Cache-Control` sont cohérents ; privilégier `Cache-Control` pour les configurations modernes.

#### Références

- [MDN – Pragma](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Pragma)

---

### 1.3 ETag et Last-Modified

#### Résumé

Les en-têtes **`ETag`** et **`Last-Modified`** permettent la **validation conditionnelle** : le client peut envoyer `If-None-Match` ou `If-Modified-Since` pour éviter de retélécharger une ressource inchangée. Leur présence est une bonne pratique pour les ressources qui peuvent changer.

#### Explication détaillée

- **ETag** : identifiant unique de la version de la ressource.
- **Last-Modified** : date de dernière modification.

Pour les pages dynamiques sensibles, éviter de les exposer si la ressource ne doit pas être mise en cache du tout. Pour les assets, ETag et Last-Modified permettent des requêtes conditionnelles efficaces.

#### Conseils

- Utiliser ETag ou Last-Modified pour les ressources qui peuvent changer ; éviter sur les pages sensibles si le cache doit être interdit.

#### Références

- [MDN – ETag](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag)
- [MDN – Last-Modified](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Last-Modified)

---

### 1.4 Vary

#### Résumé

L’en-tête **`Vary`** indique quels en-têtes de requête influencent la sélection de la réponse (content negotiation). Par exemple, `Vary: Accept-Encoding` signifie que les réponses peuvent différer selon l’encodage demandé (gzip, etc.). Son absence sur des réponses négociées peut provoquer des caches incorrects.

#### Explication détaillée

Si une ressource est servie en différentes versions (langue, encodage), `Vary` doit lister les en-têtes concernés pour que le cache stocke des entrées séparées. Sinon, un client peut recevoir une version incorrecte depuis le cache.

#### Conseils

- Ajouter `Vary: Accept-Encoding` pour les réponses compressées ; `Vary: Accept-Language` si le contenu varie selon la langue.

#### Références

- [MDN – Vary](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Vary)

---

### 1.5 Alerte : page sensible cacheable publiquement

#### Résumé

Générer une **alerte** si une page identifiée comme **sensible** (login, admin, API avec données utilisateur) est servie avec des directives de cache permissives (`public`, `max-age` élevé sans `private`/`no-store`).

#### Explication détaillée

Le scan identifie les pages sensibles **uniquement à partir de l’URL scannée** (ex. `/login`, `/admin`, `/api/`). Il ne crawle pas d’autres pages. Si `Cache-Control` autorise un cache public ou partagé (`public` ou `max-age` strictement supérieur à la valeur autorisée pour les pages sensibles), c’est un finding de niveau Medium à High.

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les pages sensibles sont parfois mal configurées.
- **Impact** : Importante. Données de session, tokens, ou contenu privé accessibles depuis le cache d’un poste partagé ou d’un proxy.

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

**Risque global : élevé sur pages sensibles.**

#### Conseils

- Identifier les pages sensibles (login, admin, API) et appliquer `Cache-Control: no-store` ou `private, no-cache`.

#### Références

- [OWASP – Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

---

## 2. Cache des ressources statiques (sous-requêtes)

### 2.1 Analyse des sous-requêtes (scripts, CSS, images)

#### Résumé

Analyser les **headers Cache-Control** des ressources chargées par la page : scripts, feuilles de style, images. Les assets **immuables** (fichiers avec hash dans le nom, ex. `main.abc123.js`) devraient avoir un cache long. Les assets sans hash ou souvent modifiés peuvent avoir un cache court ou une revalidation.

#### Explication détaillée

Le scan peut :

1. Parser le HTML de la **page scannée** pour extraire les URLs des `<script src>`, `<link rel="stylesheet" href>`, `<img src>`.
2. Normaliser ces URLs par rapport à l’URL de base (sans découvrir de nouvelles pages HTML).
3. Sélectionner au plus **N sous-requêtes** (paramètre `cache.max_sub_resources` dans `config/settings.yml`), en priorisant les scripts et feuilles de style, puis les images.
4. Effectuer des requêtes `HEAD` vers ces URLs, puis `GET` en fallback si le serveur ne supporte pas `HEAD`, afin de récupérer les headers `Cache-Control`, `ETag`, `Last-Modified`.

Recommandation : `max-age=31536000, immutable` pour les assets avec hash ; `max-age=3600` ou revalidation pour les autres.

#### Exemple

- **OK** : `main.abc123.js` avec `Cache-Control: public, max-age=31536000, immutable`.
- **Finding** : `bundle.js` sans cache ou avec `no-cache` alors qu’il est immuable → opportunité d’optimisation ; pas une vulnérabilité directe, mais une recommandation (info).

#### Conseils

- Configurer le serveur pour envoyer des directives de cache adaptées selon le type de ressource (immuable vs dynamique).

#### Références

- [Web.dev – Cache static assets](https://web.dev/uses-long-cache-ttl/)

---

### 2.2 Recommandation : cache long pour assets immuables

#### Résumé

Pour les ressources dont l’URL contient un **hash** (ex. `app.1a2b3c4d.js`), un cache long est recommandé. Le hash garantit que toute modification change l’URL ; le cache peut être conservé indéfiniment sans risque de servir une ancienne version.

#### Conseils

- Utiliser des noms de fichiers avec hash (Webpack, Vite, etc.).
- Configurer le serveur pour envoyer `Cache-Control: public, max-age=31536000, immutable` sur ces chemins.

#### Références

- [MDN – HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)

---

## Matrice de sévérité (synthèse)

| Vérification | Sévérité typique |
|--------------|------------------|
| Page sensible (login, admin) cacheable publiquement | High |
| Absence de Cache-Control sur page sensible | Medium |
| Incohérence Pragma / Cache-Control | Low |
| Assets immuables sans cache long | Info |

---

## Tests locaux (serveur de démo)

Pour tester les vérifications cache en local, un serveur de démo est fourni à la racine du projet : `bad_cache_server.py` (écoute sur `http://127.0.0.1:8001`).

En environnement **production** (`IS_PROD=true` ou variable absente), le scan-service refuse les URLs en localhost et les ports autres que 80, 443, 1010, 1011 (comportement conservateur).

En **développement local**, le script `launch_dev.sh` démarre le scan-service avec `IS_PROD=false`, ce qui :

- autorise les adresses localhost / 127.0.0.1 / ::1 ;
- autorise les ports libres (ex. 8001).

Exemple : lancer `python bad_cache_server.py`, puis scanner `http://127.0.0.1:8001/login` avec la stack démarrée via `./launch_dev.sh`. En production, ne pas exposer de service interne sur localhost/ports non standard.

---

## Références générales

- [OWASP – Caching](https://cheatsheetseries.owasp.org/cheatsheets/Web_Service_Security_Cheat_Sheet.html#caching)
- [CWE-524 – Use of Cache Containing Sensitive Information](https://cwe.mitre.org/data/definitions/524.html)
