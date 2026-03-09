# Vérifications robots.txt

Ce document décrit la vérification du fichier **robots.txt** : lecture, extraction des directives `Disallow`, et signalement des routes potentiellement sensibles.

---

## Contexte et méthodologie

### Qu’est-ce que robots.txt ?

Le fichier **robots.txt** est un standard (défini par le [Robots Exclusion Protocol](https://www.robotstxt.org/)) placé à la racine d’un site (`/robots.txt`). Il indique aux robots d’indexation (Googlebot, Bingbot, etc.) quelles URLs ils peuvent ou non crawler. Il ne protège **pas** l’accès aux ressources : un attaquant ou un bot malveillant peut ignorer complètement ce fichier.

Format typique :

```
User-agent: *
Disallow: /admin/
Disallow: /api/
Allow: /api/public/

User-agent: Googlebot
Disallow: /private/
```

- **User-agent** : identifie le robot concerné (`*` = tous).
- **Disallow** : chemins que le robot ne doit pas indexer.
- **Allow** : exceptions (chemins autorisés malgré un Disallow parent).

### Le paradoxe de sécurité

En listant des chemins dans `Disallow`, le site **révèle publiquement** l’existence de ces routes. Un attaquant qui découvre `Disallow: /admin/` sait qu’une interface d’administration existe et peut tenter d’y accéder. Le fichier robots.txt sert donc de **carte** pour l’énumération : il signale des endpoints potentiellement sensibles sans les protéger.

### Objectif du scan

Le scan lit `/robots.txt`, extrait toutes les directives `Disallow`, et signale celles qui correspondent à des **routes potentiellement sensibles** (admin, API, config, backup, etc.). L’objectif n’est pas de qualifier robots.txt de « vulnérable », mais d’informer l’utilisateur que ces chemins sont exposés dans un fichier public et qu’ils devraient être protégés par d’autres moyens (authentification, contrôle d’accès, restriction IP).

### Méthode de détection

1. **Requête GET** vers `https://<host>/robots.txt` (ou `http://` si le site n’est pas en HTTPS).
2. **Parsing** : extraire les lignes `Disallow: <path>` (ignorer les commentaires, lignes vides, `User-agent`).
3. **Classification** : pour chaque chemin extrait, vérifier s’il correspond à un motif de route potentiellement sensible.
4. **Rapport** : lister les routes sensibles détectées avec un niveau d’information (Info) ou d’avertissement (Low) selon le contexte.

### Motifs de routes potentiellement sensibles

| Motif | Exemples | Sensibilité |
|-------|----------|-------------|
| `admin`, `administrator`, `backend`, `manage` | `/admin/`, `/wp-admin/` | Élevée |
| `api` (hors `/api/public/`) | `/api/`, `/api/v1/` | Moyenne à élevée |
| `config`, `configs`, `configuration` | `/config/` | Élevée |
| `backup`, `backups`, `dump` | `/backup/`, `/backups/` | Élevée |
| `private`, `internal`, `secret` | `/private/` | Élevée |
| `cgi-bin`, `bin` | `/cgi-bin/` | Moyenne |
| `upload`, `uploads`, `media`, `files` | `/uploads/`, `/media/` | Moyenne |
| `tmp`, `temp`, `cache` | `/tmp/`, `/cache/` | Moyenne |
| `db`, `database`, `sql` | `/db/` | Élevée |
| `git`, `env`, `.env` | `/.git/`, `/.env` | Critique |
| `login`, `auth`, `signin` | `/login/`, `/auth/` | Moyenne |

Le scan peut utiliser des correspondances partielles (ex. chemin contient `admin`) ou une liste de motifs prédéfinis. Les chemins génériques (`/`) ou très larges ne sont pas signalés comme sensibles.

---

## 1. Lecture de robots.txt

### Résumé

Le scan effectue une requête **GET** vers `/robots.txt` pour récupérer le contenu du fichier. Si le fichier est absent (404) ou inaccessible, aucune extraction n’est possible. Si présent, le contenu est parsé pour extraire les directives `Disallow`.

### Explication détaillée

Le fichier robots.txt doit être accessible à la racine du domaine. Une requête `GET https://example.com/robots.txt` renvoie le contenu en texte brut. Le scan vérifie le statut HTTP (200 = OK) et le type de contenu (généralement `text/plain`). En cas de 404, le site n’a pas de robots.txt explicite ; les robots appliquent alors le comportement par défaut (tout crawler). Ce n’est pas une vulnérabilité, mais une absence d’information.

### Exemple

- **Présent** : `GET /robots.txt` → 200, corps contenant `User-agent:` et `Disallow:` → fichier lu.
- **Absent** : `GET /robots.txt` → 404 → pas de robots.txt (comportement par défaut des crawlers).

### Note

L’absence de robots.txt n’est pas un finding de sécurité. Sa présence est une bonne pratique pour le référencement ; le scan se concentre sur l’**analyse du contenu** lorsqu’il existe.

---

## 2. Extraction des directives Disallow

### Résumé

Le scan parse le contenu de robots.txt et extrait toutes les valeurs des directives **Disallow**. Chaque chemin est normalisé (suppression des espaces, gestion des chemins relatifs) et stocké pour l’analyse des routes sensibles.

### Explication détaillée

Le format robots.txt est simple mais peut contenir des variantes :

- `Disallow:` (vide) = tout est autorisé pour ce bloc.
- `Disallow: /` = tout est interdit.
- `Disallow: /admin/` = le chemin `/admin/` et ses sous-chemins.
- Les lignes commençant par `#` sont des commentaires.
- Plusieurs blocs `User-agent` peuvent exister ; les `Disallow` s’appliquent au dernier `User-agent` mentionné avant la ligne.

Le scan extrait les chemins et ignore les lignes vides, commentaires et directives non pertinentes (`Allow` peut être utilisé pour affiner, mais le focus MVP est sur `Disallow`).

### Exemple

```
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /config/
Allow: /api/public/
```

→ Chemins extraits : `/admin/`, `/api/`, `/config/`.

---

## 3. Signalement des routes potentiellement sensibles

### Résumé

Pour chaque chemin extrait, le scan vérifie s’il correspond à un **motif de route sensible**. Si oui, un finding de type **Info** ou **Low** est généré, indiquant que ce chemin est mentionné dans robots.txt et qu’il pourrait être une cible pour des attaquants. L’utilisateur est invité à s’assurer que ces routes sont correctement protégées.

### Explication détaillée

Le fait qu’un chemin soit dans `Disallow` ne signifie pas qu’il est vulnérable. Il signifie qu’il est **connu publiquement**. Un attaquant peut :

1. Tenter d’accéder directement à ces URLs (GET, POST).
2. Utiliser cette liste pour prioriser ses tests d’intrusion.
3. Combiner avec d’autres découvertes (ex. robots.txt + directory listing sur `/uploads/`).

Le scan signale les routes pour **sensibilisation** : si `/admin/` ou `/backup/` apparaissent dans robots.txt, l’utilisateur doit vérifier qu’ils sont protégés par authentification, contrôle d’accès ou restriction réseau.

### Exemple

- **OK** : robots.txt ne contient que `Disallow: /search?` (paramètre de recherche) → pas de route sensible signalée.
- **Finding (Info)** : robots.txt contient `Disallow: /admin/` → route potentiellement sensible signalée ; vérifier la protection.
- **Finding (Info)** : robots.txt contient `Disallow: /backup/`, `Disallow: /.git/` → routes sensibles signalées.

### Vulnérabilité et impact

- **Vraisemblance** : Très forte. robots.txt est public par conception ; tout le monde peut le lire.
- **Impact** : Variable. En soi, robots.txt n’est pas une vulnérabilité. L’impact dépend de la protection réelle des routes listées. Si `/admin/` est dans Disallow mais non protégé → risque élevé. Si `/admin/` est protégé par authentification forte → risque limité.

### Matrice gravité / vraisemblance

Le signalement des routes sensibles dans robots.txt est généralement classé en **Info** ou **Low** : c’est une information pour l’utilisateur, pas une faille directe. La gravité réelle dépend de l’exposition effective des routes.

| Contexte | Niveau suggéré |
|----------|----------------|
| Routes sensibles listées + non protégées | Low à Medium |
| Routes sensibles listées + protégées | Info |
| Aucune route sensible | — |

### Conseils

- **Ne pas supprimer** robots.txt : il est utile pour le référencement. En revanche, éviter d’y lister des chemins qui ne devraient pas exister ou qui sont critiques (ex. `/.git/`, `/backup/`).
- **Protéger** toutes les routes sensibles par authentification, contrôle d’accès, ou restriction IP. robots.txt n’est pas une mesure de sécurité.
- **Réduire la surface** : si un chemin n’a pas besoin d’être connu (ex. `/internal/`), envisager de ne pas le mettre dans robots.txt pour ne pas attirer l’attention. Les robots ne le crawleront pas par défaut s’il n’est pas lié depuis des pages publiques.
- **Auditer** régulièrement : vérifier que les chemins listés correspondent bien à la politique souhaitée et que chacun est correctement sécurisé.

### Références

- [Robots Exclusion Protocol](https://www.robotstxt.org/)
- [Google – robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)
- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)

---

## Améliorations prévues (v0.2.0)

Les vérifications suivantes seront ajoutées ou étendues dans la version 0.2.0 du scanner :

### 4. Détecter Crawl-delay

La directive **`Crawl-delay`** (non standard, supportée par certains robots comme Bingbot) demande un délai entre les requêtes. Sa présence peut indiquer une volonté de limiter la charge. Info uniquement : ce n’est pas une mesure de sécurité.

### 5. Analyser Allow en complément de Disallow

Les directives **`Allow`** peuvent affiner les règles (ex. `Disallow: /api/` puis `Allow: /api/public/`). Le scan doit parser `Allow` pour avoir une vue complète des chemins autorisés ou interdits, et éviter les faux positifs sur les exceptions.

---

## Vérification Sitemap (séparée)

La vérification du **sitemap** (présence de `Sitemap:` dans robots.txt, fallback à l'emplacement classique, analyse des URLs sensibles) est documentée dans [sitemap.md](sitemap.md).

## Crawler HTTP (réutilisation)

Le **crawler HTTP** réutilise la logique robots.txt pour respecter les directives `Disallow` et `Allow` avant de crawler une URL. Voir [crawler.md](crawler.md).
