# Vérifications Exposition fichiers / endpoints sensibles

Ce document décrit la vérification des fichiers et chemins sensibles exposés par erreur sur un serveur web : objectif, liste MVP, signatures de détection et gravité par endpoint.

---

## Contexte et méthodologie

### Objectif

De nombreux déploiements exposent accidentellement des fichiers ou répertoires qui ne devraient jamais être accessibles publiquement : fichiers de configuration contenant des secrets, dépôts Git, sauvegardes, interfaces d’administration, etc. Un attaquant peut les découvrir par énumération ou par des chemins connus. Le scan teste une **liste fixe** d’URLs sensibles et signale toute exposition confirmée.

### Méthode de détection

Pour chaque URL de la liste MVP, le scan effectue une requête **GET** et analyse la réponse :

1. **Statut HTTP 200** : la ressource est accessible (pas de 403, 404, 301 vers login, etc.).
2. **Contenu suspect** : le corps de la réponse correspond à des signatures connues pour ce type de fichier (format, motifs, taille).

Si les deux conditions sont remplies → **finding**.

### Heuristiques « contenu suspect »

| Type | Signatures typiques |
|------|---------------------|
| `.env` | Lignes `KEY=value`, présence de `DATABASE_URL`, `SECRET_KEY`, `API_KEY`, `PASSWORD` |
| `.git/config` | Section `[core]`, `[remote]`, `repositoryformatversion` |
| `backup.zip` | En-tête binaire ZIP (`PK`), taille > 0 |
| `phpinfo.php` | Chaîne `phpinfo`, `PHP Version`, `Configuration` |
| `admin/` | Page de login, formulaire, ou interface d’administration (pas une 404 générique) |
| `.DS_Store` | En-tête binaire Apple (structure `Bud1`, `DSDB`) ou contenu structuré caractéristique |

Un 200 avec un corps vide ou une page d’erreur générique (ex. « 404 Not Found » en HTML) ne doit pas être considéré comme une exposition. Le scan doit filtrer les faux positifs (pages personnalisées 404, messages d’erreur).

### Liste fixe MVP

| # | Chemin | Gravité typique |
|---|--------|-----------------|
| 1 | `/.env` | Critique |
| 2 | `/.git/config` | Critique |
| 3 | `/backup.zip` | Élevée |
| 4 | `/phpinfo.php` | Élevée |
| 5 | `/admin/` | Moyenne à élevée |
| 6 | `/.DS_Store` | Faible |

---

## 1. /.env

### Résumé

Le fichier **`.env`** contient généralement les variables d’environnement de l’application : clés API, mots de passe de base de données, secrets. S’il est accessible via le web, un attaquant peut récupérer l’ensemble des credentials et prendre le contrôle du système (base de données, services externes, back-office).

### Explication détaillée

Les frameworks (Laravel, Django, Node.js, etc.) utilisent souvent un fichier `.env` à la racine du projet pour stocker la configuration sensible. En production, ce fichier ne doit **jamais** être servi par le serveur web. Une mauvaise configuration (document root pointant sur le projet, absence de règle de refus) peut le rendre accessible. Le scan envoie `GET /.env` ; un 200 avec du contenu contenant des motifs `KEY=value`, `DATABASE_`, `SECRET_`, `PASSWORD`, etc. indique une exposition.

### Exemple

- **OK** : `GET /.env` → 403, 404, ou 200 avec page d’erreur générique → pas d’exposition.
- **Finding** : `GET /.env` → 200 avec corps contenant `DATABASE_URL=postgres://user:pass@host/db` → exposition critique.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les projets copiés sans configuration serveur adaptée exposent souvent `.env` ; les chemins sont connus et testés par les attaquants.
- **Impact** : Majeure. Accès complet à la base de données, aux APIs tierces, possibilité d’usurpation et de compromission totale.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : critique.**

### Conseils

- Exclure `.env` du document root ou placer l’application hors de la racine web.
- Configurer le serveur (Nginx, Apache) pour refuser l’accès aux fichiers commençant par `.`.
- Utiliser des variables d’environnement système ou un secret manager (AWS Secrets Manager, Vault) plutôt qu’un fichier `.env` en production.

### Références

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [OWASP – Configuration and Deployment](https://cheatsheetseries.owasp.org/cheatsheets/Configuration_Cheat_Sheet.html)

---

## 2. /.git/config

### Résumé

Le fichier **`.git/config`** fait partie du dépôt Git. S’il est accessible, un attaquant peut découvrir la structure du projet, les URLs des remotes (éventuellement avec credentials), et potentiellement exploiter d’autres fichiers du dépôt (`.git/HEAD`, `.git/objects`) pour reconstituer le code source.

### Explication détaillée

Un dépôt Git déployé en production avec le dossier `.git` présent peut exposer la configuration et, via `git-dumper` ou outils similaires, l’intégralité du code source. Le fichier `.git/config` contient les sections `[core]`, `[remote "origin"]` avec l’URL du dépôt, parfois des tokens. Sa présence en 200 avec un contenu structuré (lignes `[section]`, `key = value`) confirme l’exposition. Le scan envoie `GET /.git/config` et vérifie les signatures.

### Exemple

- **OK** : `GET /.git/config` → 403, 404 → pas d’exposition.
- **Finding** : `GET /.git/config` → 200 avec `[core]`, `[remote "origin"]`, `url = https://...` → dépôt Git exposé.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les déploiements par copie directe du projet (sans `.git` exclu) sont fréquents.
- **Impact** : Majeure. Fuite du code source, secrets potentiels dans l’historique, découverte de vulnérabilités, reverse engineering.

### Matrice gravité / vraisemblance

Identique à `/.env`. **Risque global : critique.**

### Conseils

- Ne jamais déployer le dossier `.git` en production.
- Utiliser des artefacts de build (tar, Docker image) sans métadonnées Git.
- Configurer le serveur pour bloquer l’accès à `/.git/`.

### Références

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [Git Dumper](https://github.com/arthaud/git-dumper)

---

## 3. /backup.zip

### Résumé

Un fichier **`backup.zip`** (ou équivalent) à la racine du site peut contenir une sauvegarde complète de l’application, de la base de données ou des fichiers utilisateurs. Son exposition permet à un attaquant de télécharger et d’extraire des données sensibles, du code source ou des credentials.

### Explication détaillée

Les sauvegardes sont parfois créées manuellement ou par des scripts et laissées dans des emplacements accessibles. Un `backup.zip`, `dump.sql`, `backup.tar.gz` à la racine web est un vecteur d’attaque classique. Le scan envoie `GET /backup.zip` ; un 200 avec un corps binaire dont les premiers octets correspondent à l’en-tête ZIP (`PK`) indique une archive exposée.

### Exemple

- **OK** : `GET /backup.zip` → 404, 403 → pas d’exposition.
- **Finding** : `GET /backup.zip` → 200, `Content-Type: application/zip`, corps commence par `PK` → archive exposée.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les sauvegardes mal placées existent mais sont moins systématiques que `.env` ou `.git`.
- **Impact** : Importante à majeure. Fuite de code, données, configuration, possibilité de compromission complète selon le contenu.

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

**Risque global : élevé.**

### Conseils

- Ne jamais placer de sauvegardes dans le document root.
- Stocker les backups sur un espace dédié (stockage objet, volume monté) non accessible via HTTP.
- Automatiser les sauvegardes avec des outils qui écrivent hors de la racine web.

### Références

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)

---

## 4. /phpinfo.php

### Résumé

La page **`phpinfo.php`** affiche la configuration complète de PHP (versions, modules, chemins, variables d’environnement). Elle est utile au débogage mais ne doit jamais être accessible en production. Son exposition révèle des informations sensibles (chemins, extensions, potentiellement des secrets dans `$_ENV`) et facilite le ciblage d’attaques.

### Explication détaillée

`phpinfo()` est une fonction PHP de diagnostic. Un fichier `phpinfo.php` laissé sur un serveur de production est une mauvaise pratique courante. La page générée contient des détails sur le serveur, les modules chargés, et parfois des variables d’environnement. Le scan envoie `GET /phpinfo.php` ; un 200 avec du contenu contenant `phpinfo`, `PHP Version`, `Configuration` indique une exposition. Note : applicable uniquement aux sites PHP.

### Exemple

- **OK** : `GET /phpinfo.php` → 404, ou site non-PHP → pas d’exposition.
- **Finding** : `GET /phpinfo.php` → 200 avec page HTML contenant « PHP Version », « Configuration » → exposition.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les développeurs oublient souvent de supprimer ou de protéger `phpinfo.php` après le déploiement.
- **Impact** : Significative à importante. Fuite d’informations (version PHP, chemins, modules), aide au fingerprinting et au choix d’exploits.

### Matrice gravité / vraisemblance

**Risque global : modéré à élevé.**

### Conseils

- Supprimer ou désactiver `phpinfo.php` en production.
- Si un diagnostic est nécessaire, le limiter à un environnement de staging non exposé.
- Ne jamais exposer de pages de diagnostic sur l’internet public.

### Références

- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)
- [PHP – phpinfo](https://www.php.net/manual/fr/function.phpinfo.php)

---

## 5. /admin/

### Résumé

Le répertoire **`/admin/`** (ou chemin similaire) héberge souvent l’interface d’administration du site. S’il est accessible sans authentification ou avec une protection faible, un attaquant peut tenter des accès directs, des attaques par force brute ou exploiter des vulnérabilités connues des CMS.

### Explication détaillée

Les interfaces d’administration (WordPress `/wp-admin/`, Django `/admin/`, back-offices custom) sont des cibles privilégiées. Le scan teste `GET /admin/` ; un 200 avec une page de login, un formulaire ou une interface d’administration (et non une 404 générique) indique que l’endpoint est exposé. La gravité dépend du niveau de protection (authentification, rate limiting, 2FA). Pour le MVP, on signale l’exposition ; une analyse plus poussée pourrait vérifier si l’accès est protégé.

### Exemple

- **OK** : `GET /admin/` → 404, ou redirection vers une page publique non sensible.
- **Finding** : `GET /admin/` → 200 avec formulaire de connexion, champs « username » / « password » → interface admin exposée (à protéger).

### Vulnérabilité et impact

- **Vraisemblance** : Très forte. Les chemins `/admin/`, `/wp-admin/`, `/administrator/` sont standards et connus.
- **Impact** : Variable. Si l’authentification est robuste, le risque est limité ; sinon, prise de contrôle du back-office, modification du contenu, injection de code.

### Matrice gravité / vraisemblance

**Risque global : modéré** (exposition seule) ; **élevé** si l’authentification est faible ou absente.

### Conseils

- Protéger l’interface d’administration par authentification forte (mot de passe complexe, 2FA).
- Limiter l’accès par IP (VPN, whitelist) si possible.
- Renommer le chemin `/admin/` pour éviter l’énumération triviale (security through obscurity, à combiner avec d’autres mesures).
- Activer le rate limiting et le verrouillage après tentatives échouées.

### Références

- [OWASP – Broken Access Control](https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control)
- [OWASP – Admin Interfaces](https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html)

---

## 6. /.DS_Store

### Résumé

Le fichier **`.DS_Store`** est un fichier caché créé par macOS pour stocker les métadonnées d’un dossier (ordre des icônes, vue, etc.). S’il est exposé, il peut révéler la structure des répertoires et des noms de fichiers, ce qui facilite l’énumération et le ciblage d’autres ressources sensibles.

### Explication détaillée

Les développeurs sur Mac copient parfois des projets complets vers un serveur sans exclure les fichiers système. `.DS_Store` est binaire mais peut être parsé pour extraire des noms de fichiers et de dossiers. Le scan envoie `GET /.DS_Store` ; un 200 avec un corps binaire présentant la structure Apple (signatures `Bud1`, `DSDB`) ou une taille/format cohérent indique une exposition. L’impact est limité par rapport à `.env` ou `.git`, mais l’exposition reste une mauvaise pratique.

### Exemple

- **OK** : `GET /.DS_Store` → 403, 404 → pas d’exposition.
- **Finding** : `GET /.DS_Store` → 200, corps binaire avec structure `.DS_Store` → exposition (fuite d’information sur la structure).

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les `.DS_Store` sont souvent présents dans les projets versionnés ou déployés depuis un Mac.
- **Impact** : Faible à significative. Fuite d’informations sur l’arborescence, aide à l’énumération ; pas d’exposition directe de credentials.

### Matrice gravité / vraisemblance

**Risque global : faible à modéré.**

### Conseils

- Ajouter `.DS_Store` au `.gitignore` pour éviter de le versionner.
- Configurer le serveur pour refuser l’accès aux fichiers commençant par `.`.
- Nettoyer les projets avant déploiement (script, `.dockerignore`).

### Références

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [DS_Store structure](https://en.wikipedia.org/wiki/.DS_Store)
