# Vérifications Tech fingerprinting (léger)

Ce document décrit la vérification **légère** du fingerprinting technologique : lecture des en-têtes révélateurs, détection heuristique des frameworks et CMS, et remontée d’informations sur la stack sans sur-promettre.

---

## Contexte et méthodologie

### Qu’est-ce que le tech fingerprinting ?

Le **tech fingerprinting** (ou « reconnaissance technologique ») consiste à identifier les technologies utilisées par un site web : serveur web (Nginx, Apache), langage (PHP, Python, Node.js), framework (Laravel, Django, Express), CMS (WordPress, Drupal), etc. Les attaquants utilisent ces informations pour cibler des exploits connus (CVE, vulnérabilités de version) et adapter leurs outils. Plus un site révèle d’informations, plus la phase de reconnaissance est rapide et efficace.

### Objectif du scan (MVP, léger)

Le scan MVP effectue un **fingerprinting léger** : il lit quelques en-têtes HTTP standards et applique des heuristiques simples pour détecter la stack. L’objectif n’est pas de fournir une analyse exhaustive (outils dédiés comme Wappalyzer, WhatWeb, ou Shodan le font mieux), mais d’**informer l’utilisateur** que son site expose des informations techniques et de remonter une « stack info » basique. Le rapport doit rester factuel et ne pas sur-promettre (ex. « probablement WordPress » plutôt que « WordPress 6.4.2 » sans preuve).

### Méthode de détection

1. **Requête GET** vers l’URL cible (page d’accueil ou chemin racine).
2. **Lecture des en-têtes** : `Server`, `X-Powered-By`, `X-AspNet-Version`, `X-Runtime`, `X-Generator`, etc.
3. **Heuristiques simples** : correspondance de chaînes (ex. `Server` contient `nginx`, `Apache` ; `X-Powered-By` contient `PHP`, `ASP.NET`).
4. **Rapport** : synthèse « stack info » avec les éléments détectés, niveau **Info**, sans garantie d’exhaustivité.

### En-têtes couramment révélateurs

| En-tête | Exemples | Révèle |
|---------|----------|--------|
| `Server` | `nginx/1.24.0`, `Apache/2.4.52` | Serveur web et version |
| `X-Powered-By` | `PHP/8.2`, `ASP.NET`, `Express` | Langage / framework |
| `X-AspNet-Version` | `4.0.30319` | Version .NET |
| `X-Runtime` | `0.123456` | Framework (ex. Rails) |
| `X-Generator` | `Drupal 10`, `WordPress 6.4` | CMS |
| `X-Drupal-Cache` | `HIT` | Drupal |
| `X-Varnish` | `123456` | Varnish (cache) |

---

## 1. Lecture des en-têtes Server et X-Powered-By

### Résumé

Le scan lit les en-têtes **`Server`** et **`X-Powered-By`** dans la réponse HTTP. Ces en-têtes sont les plus courants pour révéler le serveur web et le langage/framework. Leur présence et leur contenu sont remontés dans le rapport « stack info ».

### Explication détaillée

- **Server** : défini par le serveur web (Nginx, Apache, IIS, etc.). Il contient souvent le nom et la version (ex. `nginx/1.24.0`). Certaines configurations le masquent ou le simplifient pour des raisons de sécurité.
- **X-Powered-By** : défini par l’application ou le framework (PHP, ASP.NET, Express, etc.). Il n’est pas standard mais très répandu. Beaucoup de frameworks le désactivent par défaut ou permettent de le supprimer.

Le scan enregistre les valeurs brutes et les inclut dans la synthèse. Aucun finding de type « vulnérabilité » n’est généré pour la simple présence de ces en-têtes ; l’information est remontée à titre informatif.

### Exemple

- **Server** : `nginx/1.24.0` → serveur Nginx détecté.
- **X-Powered-By** : `PHP/8.2.0` → PHP détecté.
- **Absence** : pas d’en-tête `X-Powered-By` → aucune information sur le langage (ou masquage volontaire).

### Vulnérabilité et impact

- **Vraisemblance** : Très forte. Ces en-têtes sont présents par défaut sur de nombreux déploiements.
- **Impact** : Faible à significative. En soi, révéler « Nginx » ou « PHP » n’est pas une faille. Mais combiner avec une version précise permet de chercher des CVE connues et de prioriser les attaques. Plus l’information est détaillée (version exacte), plus le risque augmente.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : faible à modéré.**

### Conseils

- **Masquer ou simplifier** l’en-tête `Server` : Nginx (`server_tokens off`), Apache (`ServerTokens Prod`).
- **Supprimer** `X-Powered-By` : la plupart des frameworks permettent de le désactiver (middleware, configuration).
- **Ne pas exposer** de versions précises si possible ; un attaquant peut les croiser avec des bases de vulnérabilités.

### Références

- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)
- [MDN – Server](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Server)

---

## 2. Détection framework / CMS (heuristiques simples)

### Résumé

Le scan applique des **heuristiques simples** pour identifier le framework ou le CMS : correspondance de chaînes dans les en-têtes, motifs connus (ex. `X-Drupal-Cache` → Drupal, `X-Powered-By: Express` → Node.js/Express). La détection est indicative, pas exhaustive.

### Explication détaillée

Une heuristique simple consiste à vérifier si une chaîne connue apparaît dans un en-tête ou dans le corps de la réponse (optionnel pour le MVP). Exemples :

| Condition | Détection |
|-----------|-----------|
| `Server` contient `nginx` | Nginx |
| `Server` contient `Apache` | Apache |
| `X-Powered-By` contient `PHP` | PHP |
| `X-Powered-By` contient `ASP.NET` | ASP.NET |
| `X-Powered-By` contient `Express` | Node.js / Express |
| `X-Generator` contient `WordPress` | WordPress |
| `X-Generator` contient `Drupal` | Drupal |
| `X-Drupal-Cache` présent | Drupal |
| Corps HTML contient `wp-content`, `wp-includes` | WordPress (si étendu au corps) |

Pour le MVP, on se limite aux **en-têtes** pour rester léger et éviter de parser tout le HTML. Les heuristiques sont des correspondances partielles (ex. `"PHP" in x_powered_by`), pas des expressions régulières complexes.

### Exemple

- **Détecté** : `X-Powered-By: Express` → « Stack probable : Node.js / Express ».
- **Détecté** : `X-Generator: WordPress 6.4` → « CMS probable : WordPress ».
- **Non détecté** : Aucun motif reconnu → « Stack : non identifiée (ou masquée) ».

### Principe « sans sur-promettre »

Le rapport doit formuler les résultats de manière prudente :

- ✅ « Serveur web détecté : Nginx » (factuel, basé sur l’en-tête `Server`).
- ✅ « Framework probable : Express » (indicatif, basé sur `X-Powered-By`).
- ❌ « WordPress 6.4.2 installé » (trop précis sans preuve suffisante).

On évite les affirmations catégoriques lorsque la détection repose sur des heuristiques faibles. Un libellé du type « information détectée » ou « probable » est préférable à « confirmé ».

### Vulnérabilité et impact

- **Vraisemblance** : Variable. Les frameworks et CMS bien configurés masquent parfois ces informations ; d’autres les exposent par défaut.
- **Impact** : Faible à modérée. La détection aide un attaquant à cibler des exploits, mais ne constitue pas une faille en soi. La recommandation est de réduire la surface d’information exposée.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
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

**Risque global : faible à modéré.**

### Conseils

- Désactiver ou masquer les en-têtes révélateurs (`X-Powered-By`, `X-Generator`, etc.).
- Utiliser des configurations « production » des frameworks qui suppriment les informations de debug.
- Ne pas afficher de versions dans les réponses HTML (meta generator, commentaires).

### Références

- [OWASP – Fingerprinting](https://owasp.org/www-community/controls/Fingerprinting)
- [Wappalyzer](https://www.wappalyzer.com/) (référence pour un fingerprinting avancé)

---

## 3. Remontée « stack info » sans sur-promettre

### Résumé

Le scan agrège les informations collectées (en-têtes, détections heuristiques) dans une section **« Stack info »** du rapport. Cette section est factuelle, limitée aux éléments observés, et ne prétend pas à l’exhaustivité. Les formulations évitent les affirmations excessives.

### Explication détaillée

La « stack info » est un bloc informatif qui peut contenir :

- **Serveur web** : valeur de l’en-tête `Server` (si présent).
- **Langage / runtime** : valeur de `X-Powered-By` ou détection déduite (si présent).
- **Framework / CMS** : détection heuristique avec libellé « probable » ou « détecté » (pas « confirmé » sauf preuve forte).

Exemple de rendu :

```
Stack info (indicatif) :
- Serveur : nginx/1.24.0
- Runtime : PHP/8.2.0
- Framework/CMS probable : non identifié
```

Ou :

```
Stack info (indicatif) :
- Serveur : Apache/2.4.52
- Runtime : PHP/8.1
- CMS probable : WordPress
```

### Principes de formulation

| À faire | À éviter |
|---------|----------|
| « Serveur détecté : Nginx » | « Le site utilise exclusivement Nginx » |
| « CMS probable : WordPress » | « WordPress 6.4.2 installé » |
| « Runtime : PHP (X-Powered-By) » | « Langage : PHP (certain) » |
| « Stack : non identifiée » | « Aucune technologie détectée » (peut être masquée) |

### Niveau de gravité

La remontée « stack info » est un finding de type **Info** : elle n’indique pas une vulnérabilité directe, mais informe l’utilisateur des informations techniques exposées. L’utilisateur peut décider de les masquer pour réduire la surface d’attaque.

### Références

- [OWASP – Security Misconfiguration](https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration)
- [CWE – Information Exposure](https://cwe.mitre.org/data/definitions/200.html)
