# Crawler HTTP — Découverte des URLs

Ce document décrit le **crawler HTTP** de SecureOps : objectif, fonctionnement détaillé, choix techniques, limites et contrat API. Le crawler est un agent indépendant des scans : il découvre les URLs d'un site pour permettre à l'utilisateur de valider et éditer la liste avant de lancer un scan.

---

## Contexte et objectif

### Rôle du crawler

Le crawler HTTP est un **agent de découverte** qui :

1. **Télécharge** la page HTML de l'URL de départ (ou la rend via Playwright en mode SPA).
2. **Parse** le DOM pour extraire les liens (balises `<a>`, `<form>`, `<script>`, `<link>`, `<iframe>`).
3. **Suit** les liens du même domaine en profondeur (BFS) jusqu'à des limites configurées.
4. **Produit** une liste d'URLs avec métadonnées (type, profondeur) pour le frontend.
5. **Ne lance pas** de scan : l'utilisateur valide ou édite la liste, puis lance le scan manuellement.

### Objectif métier

Permettre à l'utilisateur de **découvrir les pages d'un site** avant de scanner, afin de :

- Visualiser la surface d'attaque potentielle.
- Retirer des URLs non pertinentes (ex. pages de login, ressources statiques).
- Ajouter manuellement des URLs non découvertes (ex. endpoints API connus).
- Préparer une évolution future : scan sur l'ensemble des URLs validées (actuellement, le scan ne s'exécute que sur l'URL de départ).

### Indépendance du scan

Le crawler est **découplé** du scan de posture sécurité. Il ne déclenche aucune vérification (TLS, headers, etc.). Il alimente uniquement une étape de validation frontend. Le scan s'exécute ensuite sur la base de la liste validée (pour l'instant, uniquement sur l'URL de départ).

---

## 1. Fonctionnement détaillé

### Récapitulatif : ce que fait le crawler

1. **Validation** : l'URL de départ est validée (format, schéma, pas de credentials) et vérifiée SSRF (pas de localhost/IP privée en production).
2. **Robots.txt** : récupération de `/robots.txt`, extraction des chemins Disallow/Allow et des URLs Sitemap.
3. **Sitemap** (mode HTML) : récupération du sitemap dès le début (directive Sitemap: ou fallback /sitemap.xml). Toutes les URLs extraites sont ajoutées à la frontier.
4. **Crawl BFS** : selon le mode (HTML ou SPA), visite des pages en BFS sur la frontier (seed + URLs sitemap). Extraction des liens HTML, ajout à la queue, déduplication, jusqu'aux limites (profondeur 2, max URLs, timeout 60 s).
5. **Alignement** : toutes les URLs sont réécrites pour utiliser le même host que l'URL de départ (www ou apex).
6. **Résultat** : liste triée (depth, url) avec type (page, form, script, api_endpoint, sitemap) envoyée au frontend.

### 1.0 Modes de crawl : HTML, Playwright, Both

Le crawler propose **trois modes** selon le type de site :

| Mode | Déclenchement | Méthode | Cas d'usage |
|------|---------------|---------|-------------|
| **html** (défaut) | `mode: "html"` | Requêtes HTTP (httpx) + parsing HTML statique | Sites classiques, HTML pré-rendu côté serveur |
| **playwright** | `mode: "playwright"` | Playwright (Chromium headless) + exécution JavaScript | Next.js, React, Vue, etc. — liens injectés par JS |
| **both** | `mode: "both"` | Les deux en parallèle, fusion et déduplication des résultats | Découverte maximale, comparaison HTML vs SPA |

**Mode HTML** : rapide, léger. Télécharge le HTML brut et extrait les liens des balises. Ne voit pas les liens générés dynamiquement par JavaScript.

**Mode Playwright** : plus lent, plus consommateur (navigateur headless). Charge chaque page, attend le rendu JavaScript, extrait les liens du DOM. Découvre les articles, pages de blog, etc. sur les sites Next.js/React.

**Mode Both** : exécute HTML et Playwright en parallèle, fusionne les URLs (déduplication par URL, préférence au type `page`).

### 1.1 Flux global

```
Utilisateur saisit URL
        │
        ▼
┌─────────────────────────────────────┐
│ « Scanner uniquement cette page » ?  │
└─────────────────────────────────────┘
        │                    │
       Oui                  Non
        │                    │
        ▼                    ▼
  Scan direct          ┌─────────────────┐
  sur l'URL            │ « Site SPA » ?   │
                       └─────────────────┘
                        │              │
                       Non            Oui
                        │              │
                        ▼              ▼
                 mode: "html"     mode: "playwright"
                        │              │
                        ▼              ▼
                 Crawl HTML        Crawl Playwright
                 (httpx + parse)   (Chromium + JS)
                        │              │
                        ▼              ▼
                 robots.txt + sitemap (URLs ajoutées à la frontier)
                        │              │
                        ▼              ▼
                 BFS sur frontier (seed + sitemap)
                        │              │
                        └──────┬───────┘
                               ▼
              POST /api/crawl/stream → Liste d'URLs → Frontend
                               │
                               ▼
                    Étape validation : affichage du nombre,
                    ajout/suppression d'URLs
                               │
                               ▼
                    Bouton « Lancer le scan »
                               │
                               ▼
                    Scan sur URL de départ
```

### 1.2 Téléchargement

- **Client HTTP** : réutilisation du client `scan_client()` (httpx, SSL permissif, timeouts configurés).
- **User-Agent** : `SecureOps-Crawler/1.0` pour transparence côté serveur cible.
- **Redirections** : suivies automatiquement.
- **Content-Type** : seules les réponses `text/html` sont parsées pour extraire des liens. Les autres types (JSON, PDF, etc.) ne sont pas crawlés.

### 1.3 Parsing HTML

- **Parser** : `html.parser` natif Python (pas de dépendance BeautifulSoup ou lxml).
- **Balises extraites** :
  - `<a href="...">` → type `page`
  - `<form action="...">` → type `form` (action vide = URL de la page courante)
  - `<script src="...">` → type `script`
  - `<link rel="stylesheet" href="...">` → type `stylesheet`
  - `<iframe src="...">` → type `page`

### 1.4 Normalisation et filtrage des URLs

- **Schémas** : `http` et `https` uniquement. `mailto:`, `tel:`, `javascript:`, `data:`, ancres pures (`#`) sont ignorés.
- **Fragment** : retiré (`#section` → supprimé).
- **Host** : normalisé en minuscules.
- **Dédupliquage** : une URL n'est traitée qu'une seule fois.

### 1.5 Politique de suivi

- **Même domaine strict** : seuls les liens dont le host est identique ou sous-domaine du host de l'URL de départ sont suivis. **www et apex** : `www.example.com` et `example.com` sont traités comme le même site (ex. crawl sur `www.immosphere.co` → liens vers `immosphere.co` acceptés).
- **Exclusion des binaires** : URLs dont l'extension ou le chemin suggère une ressource binaire (images, PDF, ZIP, etc.) ne sont pas mises en file. Liste configurable dans `settings.yml` (`.jpg`, `.png`, `.pdf`, `.zip`, etc.).

### 1.6 Détection des endpoints API

Les URLs dont le chemin contient un pattern type API sont marquées `api_endpoint` :

- `/api`, `/graphql`, `/v1`, `/rest`, `/swagger`, `/api-docs`

Cela permet une évolution future : scanner différemment les endpoints API (CORS, headers, Content-Type).

### 1.7 Algorithme de crawl (stratégie hybride)

Le crawler suit une **stratégie hybride** (seed + robots.txt + sitemap + BFS) :

1. **Seed principale** : l'URL de départ est ajoutée à la frontier (file d'attente).
2. **Robots.txt** : récupération de `/robots.txt`, extraction des règles `Disallow`/`Allow` et des URLs `Sitemap`.
3. **Sitemap** (mode HTML) : téléchargement du sitemap, parse XML, extraction de toutes les URLs dans les balises `<loc>`. **Toutes ces URLs sont ajoutées à la frontier** (depth=1).
4. **BFS global** : le crawler explore en parcours en largeur :
   - prendre une URL dans la queue
   - télécharger la page
   - extraire les liens HTML
   - ajouter les nouvelles URLs à la queue
5. **Déduplication** : set d'URLs déjà visitées pour éviter boucles et doublons.
6. **Canonicalisation** : normalisation des URLs avant ajout (fragment retiré, host en minuscules, etc.).
7. **Limites** : profondeur max, nombre max d'URLs, exclusions (extensions, chemins).
8. **Arrêt sur 403** : si 5 requêtes 403 consécutives (protection anti-bot, WAF), le crawl s'arrête. Les URLs déjà trouvées sont retournées, ainsi que les URLs sitemap en attente dans la file (jusqu'à `max_urls`). Le champ `requests_blocked` est mis à `true`.

**Frontier initiale** : `[homepage] + [toutes les URLs du sitemap]`. Le BFS traite cette frontier et découvre d'autres liens au fil du crawl.

**Profondeur** : depth 0 = page initiale, depth 1 = URLs sitemap ou liens directs, depth 2 = liens des liens. Au-delà de `max_depth` (2 par défaut), l'URL est ajoutée au résultat mais on ne la fetch pas.

### 1.8 Sitemap et frontier (mode HTML uniquement)

En mode HTML, le sitemap est récupéré **dès le début** et toutes ses URLs sont ajoutées à la frontier :

- **Source** : directive `Sitemap:` dans robots.txt, puis fallback `/sitemap.xml`, `/sitemap_index.xml`, `/sitemap-index.xml`.
- **Traitement** : parse du sitemap XML (urlset et sitemap index), extraction des URLs du même domaine, application des filtres (robots.txt, extensions exclues, préfixes exclus). Pour un sitemap index, **tous** les sous-sitemaps sont récupérés (jusqu'à 50).
- **Frontier** : toutes les URLs du sitemap sont ajoutées à la queue au démarrage du BFS. Le crawler les visite et en extrait d'autres liens.
- **Type** : les URLs issues du sitemap sont marquées `type: "sitemap"`.

Exemple : crawl sur `https://www.seloger.com/` → robots.txt + sitemap → frontier = [homepage, url1, url2, …] → BFS explore en largeur.

### 1.9 Mode SPA (Playwright)

Quand l'utilisateur coche « Site SPA », le crawl utilise **Playwright** (Chromium headless). La même stratégie hybride que le mode HTML : robots.txt, sitemap (URLs ajoutées à la frontier), puis BFS avec Chromium pour le rendu JavaScript.

1. **Lancement** : Chromium en mode headless (`--no-sandbox`, `--disable-setuid-sandbox`).
2. **Pour chaque URL** de la file (BFS) :
   - Navigation vers l'URL (`page.goto`).
   - Attente `domcontentloaded` puis `networkidle` (5 s max) pour que le JavaScript s'exécute.
   - Extraction des liens via `page.evaluate` : `document.querySelectorAll('a[href]')`, `form[action]`, formulaires sans action (URL courante).
   - Les liens sont déjà absolus (`a.href`), filtrés par même domaine, exclusions, robots.txt.
   - Nouvelles URLs ajoutées à la file avec `depth + 1`.
3. **Même logique** : profondeur max 2, max URLs (paramètre utilisateur), timeout 60 s, respect robots.txt, exclusions binaires et chemins build.

**Avantage** : découvre les articles, pages de blog, liens de navigation rendus par React/Next.js. Ex. `https://www.immosphere.co/actualites` → liens vers `/articles/loi-de-finances-2025-...`.

**Inconvénient** : plus lent (navigateur par page), plus consommateur en CPU/RAM. Nécessite Playwright et Chromium installés (`playwright install chromium`).

### 1.10 Alignement des URLs (www vs apex)

Pour une **cohérence d'affichage**, toutes les URLs retournées utilisent le **même format de host** que l'URL de départ saisie par l'utilisateur :

- Si l'utilisateur saisit `https://www.immosphere.co/`, les URLs du sitemap (`https://immosphere.co/articles`, etc.) sont réécrites en `https://www.immosphere.co/articles`.
- Si l'utilisateur saisit `https://immosphere.co/`, les URLs restent en `immosphere.co`.

Les domaines `www.example.com` et `example.com` sont traités comme le **même site** pour le suivi des liens (politique « même domaine »).

### 1.11 Options utilisateur (frontend)

| Option | Défaut | Description |
|--------|--------|-------------|
| **Scanner uniquement cette page** | décoché | Si coché : pas de crawl, scan direct sur l'URL. |
| **Mode** | `html` | `html` (HTTP), `playwright` (SPA), `both` (parallèle + fusion). |
| **Limite d'URLs** | 50 | Nombre max d'URLs à découvrir (5–200). |

---

## 2. Respect de robots.txt

### 2.1 Récupération

Le crawler réutilise la logique existante de `run_robots_txt_checks` pour récupérer `/robots.txt` sur le domaine de l'URL de départ. Les chemins `Disallow` et `Allow` sont extraits.

### 2.2 Vérification avant crawl

Avant d'ajouter une URL à la file d'attente ou de la fetcher, le crawler vérifie si son **chemin** est interdit par robots.txt :

- **Disallow** : correspondance par préfixe. Ex. `Disallow: /admin/` → `/admin/`, `/admin/foo` interdits.
- **Allow** : peut surcharger un Disallow. Ex. `Disallow: /api/` puis `Allow: /api/public/` → `/api/public/` autorisé.
- **Règle** : le plus long match gagne. Si Allow et Disallow matchent, Allow est prioritaire si plus spécifique.

### 2.3 Crawl-delay

La directive **Crawl-delay** (non standard) n'est pas implémentée pour l'instant. Une évolution future pourrait ajouter une attente entre les requêtes si elle est présente dans robots.txt.

---

## 3. Choix techniques

### 3.1 API synchrone (Option A)

**Choix** : endpoint `POST /api/crawl` synchrone. Le frontend envoie l'URL, attend la réponse (jusqu'à ~60 s), puis reçoit la liste d'URLs.

**Raisons** :
- Simplicité : pas de stockage de jobs, pas de polling.
- Limites actuelles (60 s, 50 URLs) restent dans des timeouts HTTP raisonnables.
- Évolution possible vers une version asynchrone (job_id + polling) si les crawls deviennent plus longs.

### 3.2 HTMLParser natif

**Choix** : `html.parser` de la bibliothèque standard Python au lieu de BeautifulSoup ou lxml.

**Raisons** :
- Aucune dépendance externe.
- Suffisant pour extraire des attributs simples (`href`, `src`, `action`).
- Cohérent avec le module `integrity` qui utilise déjà un HTMLParser personnalisé.

### 3.3 Service dédié (crawl-service)

**Choix** : le crawler est intégré dans un **service dédié** `crawl-service` (port 8014), exposé via le gateway sous le préfixe `/crawl`.

**Raisons** :
- Isolation : le crawl peut être long (60 s+) sans bloquer les autres services.
- Réutilisation du client HTTP, de la config SSRF, de la validation d'URL, de la logique robots.txt (module commun).
- Config centralisée dans `backend/crawl-service/config/settings.yml`.

### 3.4 Streaming SSE

Le crawl peut être lancé en streaming via `POST /api/crawl/stream`. Le client envoie `Accept: text/event-stream`. Les étapes émises sont :

1. `validation_url_check` / `validation_url_done` : validation de l'URL.
2. `ssrf_check` / `ssrf_done` : vérification SSRF (résolution DNS, blocage localhost).
3. `robots_check` / `robots_done` : lecture de robots.txt (si activé, mode HTML et SPA).
4. `sitemap_check` / `sitemap_done` : récupération du sitemap (modes HTML et SPA).
5. `crawl_progress` : progression (ex. « Exploration des pages (10 URLs) »).
6. `result` : liste finale d'URLs avec `timeout_reached`, `anti_bot_suspected`, `requests_blocked`.

Le gateway applique un timeout de 90 s pour le crawl stream (vs 20 s pour les requêtes standard).

### 3.5 SSRF et URL de départ

**Choix** : l'URL de départ est validée avec `validate_and_normalize_url` puis `check_ssrf` (résolution DNS, blocage localhost, IP privées). Les URLs découvertes ne font qu'une vérification `is_hostname_blocked` (localhost, etc.) sans résolution DNS.

**Raisons** :
- L'URL de départ est contrôlée par l'utilisateur → validation stricte obligatoire.
- Les URLs découvertes sont toutes du même domaine (filtrées par `_is_same_domain`) → si le domaine de départ a passé le SSRF, les sous-chemins sont considérés sûrs. Une résolution DNS par URL serait trop coûteuse en latence.

### 3.6 Arrêt sur 403 (requests_blocked)

Lorsque 5 requêtes HTTP 403 consécutives sont rencontrées (protection anti-bot, WAF, restriction d'accès), le crawl s'arrête. Les URLs déjà découvertes sont retournées, ainsi que les URLs du sitemap encore en attente dans la file (jusqu'à `max_urls`). Le frontend affiche un message d'avertissement et l'utilisateur peut valider ou éditer la liste partielle.

### 3.7 Architecture des modules (crawl-service)

Le package `app/services/crawler` est organisé en modules métier :

| Module | Rôle |
|--------|------|
| `core` | BFS, fetch HTTP, parsing HTML, sitemap, `CrawlContext`, `CrawlUrlEntry`. |
| `executor` | Orchestration des modes (html, playwright, both), `make_run_crawler`, `execute_crawl_by_mode`. |
| `results` | Fusion et conversion des résultats (`merge_entries`, `entries_to_payload`). |
| `stream_queue` | Gestion de la queue SSE et des erreurs. |
| `playwright_page` | Navigation Playwright, extraction des liens DOM, fetch page. |
| `playwright_crawl` | Point d'entrée du crawl Playwright (`run_crawl_playwright`). |
| `crawl_stream` | Pipeline SSE (`crawl_stream_generator`). |
| `anti_bot` | Détection des protections anti-bot dans le HTML. |
| `constants` | Constantes (ex. script JS d'extraction des liens). |
| `types` | `CrawlMode`, `CrawlResultPayload`. |

---

## 4. Contrat API

### 4.1 Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/crawl/stream` | Crawl en streaming SSE : émet des étapes (validation, SSRF, robots, sitemap, crawl) puis `result` ou `error`. |

Exposé via le gateway : `POST /crawl/api/crawl/stream` (route publique, pas d'authentification requise pour le MVP). Timeout étendu (90 s) côté gateway pour les crawls longs.

### 4.2 Requête

```json
{
  "url": "https://example.com",
  "max_urls": 50,
  "mode": "html"
}
```

- **url** (string, requis) : URL de départ à crawler. Doit être valide (schéma http/https, pas de credentials, host résolvable, pas de localhost/IP privée en production).
- **max_urls** (int, optionnel) : Nombre max d'URLs à découvrir. Valeur entre 5 et 200, défaut 50. L'utilisateur peut le définir dans l'interface.
- **mode** (string, optionnel) : `"html"` (défaut), `"playwright"` ou `"both"`. `"playwright"` utilise Chromium pour les SPA ; `"both"` exécute les deux en parallèle et fusionne les résultats.

### 4.3 Réponse succès (200)

```json
{
  "urls": [
    { "url": "https://example.com/", "type": "page", "depth": 0 },
    { "url": "https://example.com/about", "type": "page", "depth": 1 },
    { "url": "https://example.com/api/users", "type": "api_endpoint", "depth": 1 }
  ],
  "timeout_reached": false,
  "anti_bot_suspected": false,
  "requests_blocked": false,
  "disallow_paths": []
}
```

- **urls** (array) : liste d'objets `{ url, type, depth }` avec URL normalisée, type (`page`, `form`, `script`, `stylesheet`, `api_endpoint`, `sitemap`) et profondeur.
- **timeout_reached** (bool) : `true` si le crawl a été interrompu par le timeout (résultats partiels).
- **anti_bot_suspected** (bool) : `true` si une protection anti-bot a été détectée (mode Playwright).
- **requests_blocked** (bool) : `true` si trop de requêtes 403 consécutives (protection anti-bot, WAF) ; le crawl s'arrête et retourne les URLs trouvées + celles en attente dans la file sitemap.
- **disallow_paths** (array) : chemins Disallow extraits de robots.txt (retournés pour référence).

### 4.4 Réponse erreur

| Code | Cas |
|------|-----|
| 400 | URL invalide (validation, schéma, format, credentials, etc.) ou refusée par SSRF (localhost, IP privée). |
| 500 | Erreur interne (timeout, exception, etc.). |
| 503 | Mode playwright ou both demandé mais Playwright non installé ou indisponible. |
| 504 | Timeout du stream SSE dépassé. |

Le corps d'erreur suit le format FastAPI : `{ "detail": "message" }`. En SSE, l'événement `error` contient `message` et `status_code`.

---

## 5. Configuration

Section `crawler` dans `backend/crawl-service/config/settings.yml` :

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `max_depth` | 2 | Profondeur max du crawl (0 = page initiale uniquement). |
| `max_urls` | 50 | Nombre max d'URLs à crawler. |
| `timeout_seconds` | 60 | Timeout global du crawl en secondes. |
| `stream_timeout_seconds` | 120 | Timeout du stream SSE (annulation si dépassé). |
| `respect_robots_txt` | true | Activer ou désactiver le respect de Disallow/Allow. |
| `user_agent` | `SecureOps-Crawler/1.0` | User-Agent envoyé sur les requêtes. |
| `playwright_page_timeout_ms` | 15000 | Timeout navigation Playwright (ms). |
| `playwright_network_idle_timeout_ms` | 5000 | Timeout networkidle Playwright (ms). |
| `consecutive_403_threshold` | 5 | Nombre de 403 consécutifs avant arrêt. |
| `api_patterns` | liste | Patterns pour marquer les URLs en `api_endpoint`. |
| `anti_bot_indicators` | liste | Chaînes détectées dans le HTML (Cloudflare, captcha, etc.). |
| `excluded_extensions` | liste | Extensions de fichiers à exclure du crawl. |
| `excluded_path_prefixes` | liste | Préfixes de chemin exclus (ex. `/_next/`). |

**Extensions exclues par défaut** : `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`, `.ico`, `.pdf`, `.zip`, `.tar`, `.gz`, `.mp4`, `.mp3`, `.woff`, `.woff2`, `.ttf`, `.eot`, `.js`, `.css`.

**Préfixes de chemin exclus** (build artifacts) : `/_next/`, `/__next/`, `/static/` — évite de lister les chunks Next.js, webpack, etc.

### 5.1 Installation Playwright (modes playwright et both)

Pour les **modes playwright et both**, Playwright et Chromium doivent être installés :

```bash
# Dans backend/crawl-service
pip install -r requirements.txt
playwright install chromium
```

En **Docker**, le Dockerfile exécute déjà `playwright install --with-deps chromium`. La variable `PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright` est définie.

---

## 6. Limites

### 6.1 Limites techniques

| Limite | Valeur par défaut | Impact |
|--------|-------------------|--------|
| Profondeur | 2 | Sites très profonds (> 2 niveaux) : URLs non découvertes. |
| Nombre d'URLs | 50 | Sites volumineux : liste tronquée. |
| Timeout | 60 s | Crawl long : arrêt prématuré. |
| Taille HTML | 1 Mo | Pages très volumineuses : HTML tronqué, liens potentiellement manquants. |

### 6.2 Limites fonctionnelles

- **Pas de JavaScript** (mode par défaut) : le crawler ne rend pas le JavaScript. Les liens générés dynamiquement (SPA, etc.) ne sont pas découverts dans le HTML. **Sitemap** : récupéré dès le début, toutes les URLs sont ajoutées à la frontier au démarrage du BFS (voir §1.8).
- **Mode SPA** : si l'utilisateur coche « Site SPA », le crawl utilise Playwright (Chromium headless) pour exécuter le JavaScript et extraire les liens du DOM après rendu. Plus lent et consommateur en ressources, mais découvre les liens des sites Next.js, React, etc.
- **Pas de Crawl-delay** : la directive `Crawl-delay` de robots.txt n'est pas respectée.
- **Sous-domaines** : les sous-domaines du même domaine sont suivis (ex. `www.example.com` → `api.example.com` si même domaine). La politique exacte dépend de `_is_same_domain`) : `host` identique ou `host` se termine par `.base_host`.
- **Scan uniquement sur l'URL de départ** : pour l'instant, le scan s'exécute sur l'URL de départ uniquement. La liste validée est conservée pour une évolution future (scan multi-URLs).

### 6.3 Non implémenté (prévu)

- **Quotas** : pas de limite de crawls/jour par utilisateur ou par domaine.
- **Liste noire** : pas de config pour bloquer des domaines ou patterns d'URL.
- **Crawl-delay** : pas d'attente entre requêtes si robots.txt le demande.
- **Version asynchrone** : pas de job_id + polling pour les crawls longs.

---

## 7. Sécurité et prévention des abus

### 7.1 SSRF

- **URL de départ** : validation complète (validation d'URL + `check_ssrf`). Résolution DNS, blocage localhost, IP privées (RFC 1918), IP de bouclage.
- **URLs découvertes** : vérification `is_hostname_blocked` (localhost, etc.) sans résolution DNS.

### 7.2 Même domaine

Le crawler ne suit que les liens du même domaine. Aucune fuite vers des domaines externes (évite crawl sauvage et SSRF indirect).

### 7.3 Évolutions prévues

- Quotas de crawls par utilisateur/domaine.
- Liste noire configurable (domaines ou patterns interdits).
- Logging des tentatives pour audit/modération.

---

## 8. Références

- [Robots Exclusion Protocol](https://www.robotstxt.org/)
- [Google – robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)
- [OWASP – SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- Roadmap : [ROADMAP-MVP-0.3.0.md](../roadmaps/ROADMAP-MVP-0.3.0.md) §7

---

## 9. Améliorations prévues

- **Tests unitaires** : parsing HTML → liste d'URLs attendue ; respect Disallow ; limites (profondeur, max URLs).
- **Test d'intégration** : crawl d'une page de test (serveur ou fixture HTML) → vérifier la sortie et l'absence de fuite hors domaine.
- **Version asynchrone** : job_id + polling si les crawls dépassent les timeouts HTTP.
- **Scan multi-URLs** : exécuter le scan sur l'ensemble des URLs validées par l'utilisateur.
- **Crawl-delay** : respecter la directive Crawl-delay de robots.txt (attente entre requêtes).
