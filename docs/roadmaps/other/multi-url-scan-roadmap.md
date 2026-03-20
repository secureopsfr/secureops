# Roadmap : Scanner multi-URL sur un même domaine

> **Auteur :** Analyse architecturale — SecureOps
> **Date :** Mars 2026
> **Scope :** `backend/scan-service`, `backend/crawl-service`, `frontend/src`
> **Objectif :** Inspecter N pages d'un même domaine avec le minimum d'appels HTTP,
> en mutualisant tous les checks partagés et en maintenant un code évolutif et lisible.

---

## Table des matières

1. [Contexte et état de l'art](#1-contexte-et-état-de-lart)
2. [Taxonomie des checks : domaine vs page](#2-taxonomie-des-checks--domaine-vs-page)
3. [Architecture cible](#3-architecture-cible)
4. [Stratégie de mutualisation par catégorie](#4-stratégie-de-mutualisation-par-catégorie)
5. [Modèle de données](#5-modèle-de-données)
6. [Contrat API : schémas d'entrée/sortie](#6-contrat-api--schémas-dentréesortie)
7. [Changements backend — scan-service](#7-changements-backend--scan-service)
8. [Changements frontend](#8-changements-frontend)
9. [Modélisation des gains de performance](#9-modélisation-des-gains-de-performance)
10. [Phases d'implémentation](#10-phases-dimplémentation)
11. [Stratégie de tests](#11-stratégie-de-tests)
12. [Points de vigilance et risques](#12-points-de-vigilance-et-risques)

---

## 1. Contexte et état de l'art

### 1.1 Architecture actuelle

Le scan-service repose aujourd'hui sur le triplet `_scan_core.py` / `scan_runner.py` / `scan_stream.py`. L'unité de travail est **une URL** : on normalise, on SSRF-check, on ouvre un client httpx, on GET la page racine, et on enchaîne 12 étapes séquentielles sur ce `ScanContext`.

```
POST /scan/api/scan/async  { url: "https://example.com" }
         │
         ▼
   create_job(url=…)
         │
         ▼  (worker)
   validate_and_normalize_url()
   check_ssrf()
   GET https://example.com/   → https_response (réponse mémorisée)
         │
         ▼
   SCAN_STEPS[0..11]  (séquentiels)
         │
         ▼
   build_result_payload()  →  { url, score, findings, category_summaries }
```

**Problème :** pour scanner N pages du même domaine, aujourd'hui il faut déclencher N jobs indépendants. Chaque job refait TLS, robots.txt, sitemap, exposed_files, directory_listing, CORS — des checks qui produisent **exactement le même résultat** pour toutes les pages du même domaine.

### 1.2 Coût réel d'un scan (mesure des appels HTTP)

| Catégorie | Appels HTTP | Niveau |
|-----------|-------------|--------|
| TLS | 1 GET HTTP + 3–5 sockets TLS bruts | Domaine |
| headers | 0 (analyse de `https_response`) | Page |
| cache | 0 (page) + 1 HEAD/GET par asset JS/CSS/img | Page |
| cookies | 0 (analyse de `https_response`) | Page |
| exposed_files | ~20 GET parallèles | Domaine |
| directory_listing | ~15 GET parallèles | Domaine |
| robots_txt | 1 GET `/robots.txt` | Domaine |
| sitemap | 1–3 GET XML | Domaine |
| tech_fingerprinting | 0 (analyse headers + body) | Page |
| information_disclosure | 0 (analyse headers + body) | Page |
| integrity | 0 (analyse HTML) | Page |
| cors_cross_origin | 2 × (1 + N_sensitive_paths) GET/OPTIONS | Domaine + paths |

Pour un domaine quelconque : **~50–70 appels HTTP par scan**. Avec 10 URLs à scanner : **500–700 appels** contre **50–70 + 10 × ~5 = ~100–120** avec mutualisation. **Gain ×4 à ×6.**

---

## 2. Taxonomie des checks : domaine vs page

C'est le cœur de l'architecture multi-URL. Chaque check est classé selon deux axes :

- **Scope** : `domain` (résultat identique pour toutes les pages) ou `page` (spécifique à chaque URL)
- **Données source** : `cached_response` (réutilise `https_response`), `passive` (parsing seulement), `active` (nouveaux appels HTTP)

```
┌─────────────────────────┬──────────┬──────────────────┬────────────────────────────┐
│ Catégorie               │ Scope    │ Données source   │ Peut être partagé ?        │
├─────────────────────────┼──────────┼──────────────────┼────────────────────────────┤
│ tls                     │ domain   │ active (sockets) │ ✅ 100% — run 1×           │
│ exposed_files           │ domain   │ active (GET×20)  │ ✅ 100% — run 1×           │
│ directory_listing       │ domain   │ active (GET×15)  │ ✅ 100% — run 1×           │
│ robots_txt              │ domain   │ active (GET×1)   │ ✅ 100% — run 1×           │
│ sitemap                 │ domain   │ active (GET×1-3) │ ✅ 100% — run 1×           │
│ cors_cross_origin       │ domain   │ active (GET×N)   │ ✅ base domain — run 1×    │
│                         │          │                  │ ⚠️ per-path checks → page  │
├─────────────────────────┼──────────┼──────────────────┼────────────────────────────┤
│ headers                 │ page     │ cached_response  │ ❌ dépend de la page       │
│ cookies                 │ page     │ cached_response  │ ❌ Set-Cookie par réponse  │
│ tech_fingerprinting     │ page     │ passive          │ ⚠️ Server/X-Powered-By     │
│                         │          │                  │    souvent stable → cache  │
│ information_disclosure  │ page     │ passive          │ ❌ body spécifique à la page│
│ integrity               │ page     │ passive          │ ❌ HTML spécifique         │
│ cache                   │ page     │ active (HEAD×N)  │ ⚠️ assets partagés → cache │
└─────────────────────────┴──────────┴──────────────────┴────────────────────────────┘
```

### 2.1 Optimisation spéciale : `tech_fingerprinting`

`Server` et `X-Powered-By` sont des headers de **réponse serveur** : ils ne changent pas selon la page servie (pour un même backend). On peut donc exécuter ce check une seule fois et propager le résultat dans les N rapports de page — avec un flag `inherited_from_domain: true` pour la transparence.

### 2.2 Optimisation spéciale : assets CSS/JS (`cache`)

Sur un site réel, la majorité des assets CSS/JS sont communs à toutes les pages. Si une URL d'asset a déjà été vérifiée (HEAD `Cache-Control`), ne pas la re-sonder. Un simple `dict[str, CacheAssetResult]` keyed par asset URL suffit.

---

## 3. Architecture cible

### 3.1 Vue d'ensemble

```
POST /scan/api/scan/multi-async
  {
    base_url: "https://example.com",
    urls: ["https://example.com/", "https://example.com/blog", …],
    scan_type: "frontend"
  }
            │
            ▼
     create_multi_job(urls=[…])
            │
            ▼  (worker)
  ┌─────────────────────────────────────────────────────────┐
  │                  MultiScanOrchestrator                   │
  │                                                         │
  │  Phase 1 – Domain checks (once)                        │
  │  ┌───────────────────────────────────────────────────┐  │
  │  │  DomainScanContext                                │  │
  │  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
  │  │  │   TLS    │ │ robots   │ │  exposed_files   │  │  │
  │  │  │  (async) │ │ sitemap  │ │  dir_listing     │  │  │
  │  │  │          │ │ (async)  │ │  cors_base       │  │  │
  │  │  └──────────┘ └──────────┘ └──────────────────┘  │  │
  │  └────────────────────── run CONCURRENTLY ───────────┘  │
  │                                                         │
  │  Phase 2 – Page checks (once per URL, concurrent)      │
  │  ┌───────────────────────────────────────────────────┐  │
  │  │  PageScanContext(url_1)  PageScanContext(url_2)   │  │
  │  │  GET url_1              GET url_2                 │  │
  │  │  headers, cookies,      headers, cookies,         │  │
  │  │  integrity, info_disc,  integrity, info_disc,     │  │
  │  │  cache(assets_cache)    cache(assets_cache)       │  │
  │  └────────────── asyncio.gather(*page_tasks) ────────┘  │
  │                                                         │
  │  Phase 3 – Merge & Score                               │
  │  domain_results + page_results[url] → MultiScanResult  │
  └─────────────────────────────────────────────────────────┘
            │
            ▼
  {
    base_url, score_global, page_results: [
      { url, score, findings, category_summaries }, …
    ],
    domain_results: { tls, robots_txt, exposed_files, … }
  }
```

### 3.2 Modèle de concurrence

```
Phase 1 (domaine) : asyncio.gather(
    run_tls(domain),
    run_robots_txt(domain),          # séquentiel → passe résultat à sitemap
    run_exposed_files(domain),
    run_directory_listing(domain),
    run_cors_base(domain),
)

Phase 2 (pages) : asyncio.gather(
    scan_page(url_1, domain_ctx, assets_cache),
    scan_page(url_2, domain_ctx, assets_cache),
    scan_page(url_3, domain_ctx, assets_cache),
    …
)
# concurrency limitée par semaphore (ex. max 5 pages simultanées)
```

> **Note :** `robots_txt` doit finir avant `sitemap`. On peut les chaîner dans une coroutine wrapper, ou garder le pattern actuel `ctx.results["robots_txt"]` pour robots→sitemap uniquement, tout en concurrençant avec les autres.

### 3.3 Gestion du parallélisme et comptage HTTP exact

Le scan multi-URL exécute plusieurs coroutines en concurrence (`asyncio.gather` + `Semaphore`).
Un comptage naïf "avant/après une étape" (`delta = global_after - global_before`) produit des surcomptages :

- l'étape A mesure aussi des requêtes émises pendant le même intervalle par B/C,
- l'étape B mesure ensuite aussi des requêtes de A/C, etc.

Résultat : la somme "par catégorie" peut dépasser le total réel.

#### Solution implémentée

Le comptage est fait **à la requête** (et non au delta d'étape) :

- un hook `httpx` incrémente un compteur global à chaque requête sortante ;
- un `ContextVar` stocke la catégorie courante (`tls`, `cache`, `cors_cross_origin`, etc.) ;
- chaque bloc réseau est tagué via un context manager `http_request_category("...")` ;
- le hook lit la catégorie depuis le `ContextVar` de la coroutine qui émet la requête.

Ainsi, même en concurrence, chaque appel HTTP est attribué à la bonne catégorie.

```python
with http_request_category("cache"):
    await client.head(asset_url)
```

```python
asyncio.gather(
    scan_page(url_1),  # tag courant: "cache"
    scan_page(url_2),  # tag courant: "cors_cross_origin"
)
# Le hook voit le ContextVar de la task active -> attribution correcte
```

#### Garanties et limites

- `http_requests_count` = total exact des requêtes émises par le client de scan.
- `http_requests_by_category` = répartition exacte par catégorie (incluant mode concurrent).
- La somme des catégories doit être égale au total, sauf éventuelle catégorie technique
  `"unattributed"` si un appel HTTP est fait hors zone taguée.

#### Logs de fin de scan

- single URL (async):
  `scan-stream: http_requests_count=... http_requests_by_category={...} url=...`
- single URL (interne/scheduler):
  `scan-runner: http_requests_count=... http_requests_by_category={...} url=...`
- multi URL:
  `multi-scan: http_requests_count=... http_requests_by_category={...} base_url=... urls=...`

---

## 4. Stratégie de mutualisation par catégorie

### 4.1 `DomainScanContext` — checks exécutés une seule fois

Ces checks n'accèdent pas au contenu HTML d'une page spécifique. Ils opèrent sur le domaine.

#### `tls`
```python
# Aucun changement dans checks.py — juste le déplacer dans domain_checks
domain_ctx.results["tls"] = await run_tls_checks(https_url=domain_https_url, client=client)
# Injecté dans chaque PageScanResult tel quel
```

#### `robots_txt` → `sitemap`
```python
robots = await run_robots_txt_checks(base_url=domain_https_url, client=client)
sitemap = await run_sitemap_checks(
    base_url=domain_https_url,
    client=client,
    robots_txt_result=robots,   # même interface qu'aujourd'hui
)
domain_ctx.results["robots_txt"] = robots
domain_ctx.results["sitemap"] = sitemap
```

#### `exposed_files` et `directory_listing`
```python
# path_checks/core.py → run_path_checks() → inchangé
# Juste appelé une fois et stocké dans domain_ctx
domain_ctx.results["exposed_files"] = await run_exposed_file_checks(
    base_url=domain_https_url, client=client
)
domain_ctx.results["directory_listing"] = await run_directory_listing_checks(
    base_url=domain_https_url, client=client
)
```

#### `cors_cross_origin` — séparation base / per-path
Actuellement, CORS sonde aussi les `sensitive_paths` configurés (login, API, etc.). Ces paths **peuvent** correspondre à des URLs dans la liste de scan.

**Stratégie :**
- `run_cors_domain_checks(domain)` → `ACAO: *`, `ACAC` incoherence, `CORP` sur la racine : **exécuté une fois**.
- `run_cors_page_check(url, domain_cors_result)` → per-path CORS/OPTIONS : **exécuté par page scannée**, enrichit le résultat de la page.

```python
# domain phase
domain_ctx.results["cors_base"] = await run_cors_domain_checks(
    https_url=domain_https_url, client=client
)
# page phase — pour chaque URL scannée
page_cors = await run_cors_page_checks(
    url=page_url,
    client=client,
    domain_cors_result=domain_ctx.results["cors_base"],
)
page_ctx.results["cors_cross_origin"] = merge_cors_results(
    domain_ctx.results["cors_base"], page_cors
)
```

---

### 4.2 `PageScanContext` — checks par URL

Ces checks sont liés à la réponse HTTP de la page elle-même.

#### `headers`
```python
page_response = await client.get(page_url)
page_ctx.results["headers"] = run_security_headers_checks(page_response)
```
Chaque page peut avoir des headers différents (ex. CSP granulaire par route). Exécution obligatoire par page.

#### `cookies`
Même logique : les `Set-Cookie` sont émis par chaque endpoint. Exécution par page.

#### `information_disclosure` et `integrity`
Analyse passive du body HTML. Chaque page a son propre contenu.

#### `tech_fingerprinting` — optimisation possible
`Server` et `X-Powered-By` sont identiques sur toutes les pages. Deux stratégies possibles :

**Option A (simple) :** exécuter une fois sur la page racine, injecter dans tous les rapports de page avec `inherited: true`.

**Option B (rigoureuse) :** exécuter sur chaque page, déduplication au moment du merge (si résultats identiques → `shared_domain_finding`). Évite de rater un serveur différent (CDN/microservice) sur une route spécifique.

→ **Recommandation : Option B** pour les scans personnalisés sur des domaines multi-service, Option A par défaut.

#### `cache` — partage du cache d'assets
```python
# Partagé entre toutes les PageScanContext du même scan multi-URL
assets_cache: dict[str, CacheAssetCheckResult] = {}

async def run_cache_checks_with_cache(
    response: httpx.Response,
    page_url: str,
    client: httpx.AsyncClient,
    assets_cache: dict[str, CacheAssetCheckResult],  # ← partagé par référence
) -> CacheCheckResult:
    subresources = extract_subresources(response)
    results = []
    for asset_url in subresources:
        if asset_url in assets_cache:
            results.append(assets_cache[asset_url])   # ← hit
        else:
            result = await check_asset_cache(asset_url, client)
            assets_cache[asset_url] = result          # ← store
            results.append(result)
    return build_cache_result(response, results)
```

> **Thread-safety :** `asyncio` est mono-thread par event loop, pas besoin de lock ici. Si on passe à un modèle multi-process (Celery workers distincts), il faudra un cache Redis pour les assets.

---

## 5. Modèle de données

### 5.1 Nouveaux types Python

```python
# app/models/multi_scan.py

from dataclasses import dataclass, field

@dataclass
class DomainScanContext:
    """Résultats des checks valables pour tout le domaine."""
    base_url: str                       # ex. "https://example.com"
    client: httpx.AsyncClient           # connexion réutilisée
    results: dict[str, Any] = field(default_factory=dict)
    # Clés : "tls", "robots_txt", "sitemap",
    #        "exposed_files", "directory_listing", "cors_base"


@dataclass
class PageScanContext:
    """Résultats des checks spécifiques à une URL."""
    url: str                            # ex. "https://example.com/blog"
    response: httpx.Response            # GET de la page
    domain_ctx: DomainScanContext       # référence partagée (immutable après phase 1)
    results: dict[str, Any] = field(default_factory=dict)
    # Clés : "headers", "cookies", "cache", "tech_fingerprinting",
    #        "information_disclosure", "integrity", "cors_cross_origin"


@dataclass
class MultiScanResult:
    """Résultat agrégé d'un scan multi-URL."""
    base_url: str
    urls: list[str]
    domain_findings: list[dict]         # findings de scope domain
    page_results: list[PageScanResult]  # un résultat par URL
    score_global: int                   # moyenne pondérée des scores de pages
    timestamp: str
    duration: float


@dataclass
class PageScanResult:
    url: str
    score: int
    findings: list[dict]                # domain_findings + page_findings
    category_summaries: list[dict]
    error: str | None = None            # si la page était inaccessible
```

### 5.2 Schéma BDD — `ScanAsyncJob`

Ajouter les colonnes suivantes sur la table existante :

```sql
ALTER TABLE scan_async_jobs ADD COLUMN urls_json    JSONB    DEFAULT NULL;
-- Liste des URLs cibles (NULL = scan single-URL, rétrocompatible)

ALTER TABLE scan_async_jobs ADD COLUMN base_url     TEXT     DEFAULT NULL;
-- Domaine racine déduit des URLs

ALTER TABLE scan_async_jobs ADD COLUMN result_mode  TEXT     DEFAULT 'single';
-- 'single' | 'multi' — permet de distinguer le format de result_json
```

Migration Alembic :

```python
# alembic/versions/0002_multi_url_scan.py
def upgrade():
    op.add_column("scan_async_jobs", sa.Column("urls_json", postgresql.JSONB))
    op.add_column("scan_async_jobs", sa.Column("base_url", sa.Text))
    op.add_column("scan_async_jobs", sa.Column("result_mode", sa.Text, server_default="single"))
```

---

## 6. Contrat API : schémas d'entrée/sortie

### 6.1 Endpoint de création — `POST /api/scan/async`

On étend le schéma existant `ScanAsyncCreateRequest` de façon **rétrocompatible** :

```python
# app/schemas/async_job.py

class ScanAsyncCreateRequest(BaseModel):
    url: str = Field(..., min_length=1)          # ← conservé (single URL)
    urls: list[str] | None = Field(None)         # ← NOUVEAU : multi-URL
    scan_type: ScanType = "frontend"
    input: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_urls(self) -> "ScanAsyncCreateRequest":
        if self.urls is not None:
            if len(self.urls) < 2:
                raise ValueError("urls doit contenir au moins 2 URLs")
            if len(self.urls) > 50:
                raise ValueError("urls est limité à 50 URLs par scan")
            domains = {extract_domain(u) for u in self.urls}
            if len(domains) > 1:
                raise ValueError(
                    f"Toutes les URLs doivent appartenir au même domaine. "
                    f"Domaines détectés : {domains}"
                )
        return self
```

> **Rétrocompatibilité :** si `urls` est absent, le comportement actuel (single URL) est préservé.

### 6.2 Résultat — format `multi`

```json
{
  "result_mode": "multi",
  "base_url": "https://example.com",
  "urls": ["https://example.com/", "https://example.com/blog"],
  "score_global": 72,
  "timestamp": "2026-03-11T10:00:00Z",
  "duration": 8.4,
  "domain_findings": [
    {
      "id": "tls-cert-expires-soon",
      "category": "tls",
      "scope": "domain",
      ...
    }
  ],
  "page_results": [
    {
      "url": "https://example.com/",
      "score": 75,
      "findings": [...],
      "category_summaries": [...],
      "error": null
    },
    {
      "url": "https://example.com/blog",
      "score": 68,
      "findings": [...],
      "category_summaries": [...],
      "error": null
    }
  ]
}
```

### 6.3 Finding avec scope

Chaque finding gagne un champ `scope` :

```python
class ScanFinding(BaseModel):
    id: str
    category: str
    title: str
    severity: str
    evidence: str
    recommendation: str
    references: list[str]
    scope: Literal["domain", "page"] = "page"     # ← NOUVEAU
    affected_urls: list[str] | None = None         # ← NOUVEAU (domain findings)
```

Les findings `domain` apparaissent dans `domain_findings` **et** sont injectés (avec `scope="domain"`) dans `findings` de chaque `page_result` pour que le rapport individuel de page soit complet.

---

## 7. Changements backend — scan-service

### 7.1 Structure de fichiers cible

```
app/
├── services/
│   ├── _scan_core.py              # ← MODIFIÉ : sépare domain_steps / page_steps
│   ├── multi_scan_orchestrator.py # ← NOUVEAU : orchestration multi-URL
│   ├── domain_checks/             # ← NOUVEAU répertoire
│   │   ├── __init__.py
│   │   └── runner.py              # run_domain_checks() → DomainScanResult
│   ├── page_checks/               # ← NOUVEAU répertoire
│   │   ├── __init__.py
│   │   └── runner.py              # run_page_checks() → PageScanResult
│   ├── scan_runner.py             # ← MODIFIÉ : support multi si urls présent
│   ├── scan_stream.py             # ← MODIFIÉ : progress multi-URL
│   ├── async_scan_executor.py     # ← MODIFIÉ : délègue à orchestrator
│   ├── tls/ …
│   ├── security_headers/ …
│   ├── cache/ …                   # ← MODIFIÉ : partage assets_cache
│   ├── cors_cross_origin/ …       # ← MODIFIÉ : séparation domain/page
│   └── …
├── schemas/
│   └── async_job.py               # ← MODIFIÉ : urls field
├── models/
│   └── multi_scan.py              # ← NOUVEAU
```

### 7.2 `_scan_core.py` — refactoring des SCAN_STEPS

Aujourd'hui, `SCAN_STEPS` est une liste plate de 12 lambdas qui s'exécutent tous sur le même `ScanContext`. Le refactoring consiste à les séparer en deux listes :

```python
# app/services/_scan_core.py

DOMAIN_SCAN_STEPS: list[tuple[str, Callable]] = [
    ("tls",               lambda ctx: run_tls_checks(ctx)),
    ("robots_txt",        lambda ctx: run_robots_txt_checks(ctx)),
    ("sitemap",           lambda ctx: run_sitemap_checks(ctx)),
    ("exposed_files",     lambda ctx: run_exposed_file_checks(ctx)),
    ("directory_listing", lambda ctx: run_directory_listing_checks(ctx)),
    ("cors_base",         lambda ctx: run_cors_domain_checks(ctx)),
]

PAGE_SCAN_STEPS: list[tuple[str, Callable]] = [
    ("headers",              lambda ctx: run_security_headers_checks(ctx)),
    ("cookies",              lambda ctx: run_cookies_checks(ctx)),
    ("tech_fingerprinting",  lambda ctx: run_tech_fingerprinting_checks(ctx)),
    ("information_disclosure", lambda ctx: run_information_disclosure_checks(ctx)),
    ("integrity",            lambda ctx: run_integrity_checks(ctx)),
    ("cache",                lambda ctx: run_cache_checks(ctx)),
    ("cors_cross_origin",    lambda ctx: run_cors_page_checks(ctx)),
]
```

> **Rétrocompatibilité :** `SCAN_STEPS` (ancienne liste plate) est conservée comme alias `DOMAIN_SCAN_STEPS + PAGE_SCAN_STEPS` pour le mode single-URL. Les tests existants continuent de passer.

### 7.3 `multi_scan_orchestrator.py` — nouveau fichier central

```python
# app/services/multi_scan_orchestrator.py

import asyncio
from app.models.multi_scan import DomainScanContext, PageScanContext, MultiScanResult
from app.services._scan_core import DOMAIN_SCAN_STEPS, PAGE_SCAN_STEPS
from app.utils.url_helpers import extract_base_url

MAX_CONCURRENT_PAGES = 5   # semaphore — évite de saturer la cible


async def run_multi_scan(
    urls: list[str],
    on_progress: Callable[[str, str], None] | None = None,
) -> MultiScanResult:
    """
    Orchestrateur principal.

    1. Exécute les domain checks en parallèle (une seule fois).
    2. Exécute les page checks pour chaque URL, avec concurrence limitée.
    3. Merge les résultats et calcule le score global.
    """
    base_url = extract_base_url(urls[0])

    async with scan_client() as client:
        # ── Phase 1 : domain checks ──────────────────────────────────────────
        domain_ctx = DomainScanContext(base_url=base_url, client=client)
        await _run_domain_phase(domain_ctx, on_progress)

        # ── Phase 2 : page checks ────────────────────────────────────────────
        assets_cache: dict[str, Any] = {}
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)

        page_tasks = [
            _run_page_with_semaphore(url, domain_ctx, assets_cache, semaphore, on_progress)
            for url in urls
        ]
        page_results = await asyncio.gather(*page_tasks, return_exceptions=True)

        # ── Phase 3 : merge ──────────────────────────────────────────────────
        return _build_multi_result(base_url, urls, domain_ctx, page_results)


async def _run_domain_phase(
    domain_ctx: DomainScanContext,
    on_progress: Callable | None,
) -> None:
    """
    Lance les domain checks concurrentiellement.
    robots_txt → sitemap sont chaînés (sitemap a besoin de robots).
    Les autres sont indépendants.
    """
    async def robots_then_sitemap():
        await _run_step("robots_txt", domain_ctx, on_progress)
        await _run_step("sitemap", domain_ctx, on_progress)   # lit ctx.results["robots_txt"]

    await asyncio.gather(
        _run_step("tls", domain_ctx, on_progress),
        robots_then_sitemap(),
        _run_step("exposed_files", domain_ctx, on_progress),
        _run_step("directory_listing", domain_ctx, on_progress),
        _run_step("cors_base", domain_ctx, on_progress),
    )


async def _run_page_with_semaphore(
    url: str,
    domain_ctx: DomainScanContext,
    assets_cache: dict,
    semaphore: asyncio.Semaphore,
    on_progress: Callable | None,
) -> PageScanResult:
    async with semaphore:
        return await _run_page_phase(url, domain_ctx, assets_cache, on_progress)
```

### 7.4 Gestion des erreurs par page

Une page inaccessible (timeout, 404, 500) ne doit **pas** faire échouer tout le scan :

```python
async def _run_page_phase(url, domain_ctx, assets_cache, on_progress) -> PageScanResult:
    try:
        response = await domain_ctx.client.get(url, follow_redirects=True)
        page_ctx = PageScanContext(
            url=url, response=response,
            domain_ctx=domain_ctx, assets_cache=assets_cache
        )
        for step_name, step_fn in PAGE_SCAN_STEPS:
            await _run_step(step_name, page_ctx, on_progress)
        return _build_page_result(page_ctx, domain_ctx)
    except Exception as exc:
        # Page inaccessible → résultat partiel avec erreur
        return PageScanResult(
            url=url,
            score=0,
            findings=list(domain_ctx.domain_findings),  # findings domain quand même
            category_summaries=[],
            error=str(exc),
        )
```

### 7.5 Progress reporting — format multi-URL

Le système de progress existant envoie des strings simples. Pour multi-URL, on enrichit :

```python
# Format des progress_log entries pour mode multi
{
    "step": "page_scan_started",
    "message": "Analyse de https://example.com/blog (2/5)",
    "phase": "pages",         # "domain" | "pages" | "merge"
    "page_url": "https://example.com/blog",
    "page_index": 2,
    "total_pages": 5,
    "at": "2026-03-11T10:00:01Z",
    "anomaly_count": null
}
```

### 7.6 Score global

```python
def compute_global_score(page_results: list[PageScanResult]) -> int:
    """
    Moyenne pondérée des scores de pages.
    Les pages avec error contribuent avec score 0 et poids 0.5
    (signal dégradé mais pas ignoré).
    """
    weights = [0.5 if r.error else 1.0 for r in page_results]
    scores = [0 if r.error else r.score for r in page_results]
    return int(sum(s * w for s, w in zip(scores, weights)) / sum(weights))
```

---

## 8. Changements frontend

### 8.1 Nouveau composant : `MultiScanLauncher`

Le composant actuel `ScanLaunchBubble` accepte une seule URL. On crée un composant frère qui :

1. Présente un textarea pour saisir N URLs (une par ligne) ou s'intègre avec les résultats du `CrawlValidationStep` (qui produit déjà une liste d'URLs).
2. Valide que toutes les URLs appartiennent au même domaine.
3. Affiche un compte (`5 pages sélectionnées sur example.com`).

```tsx
// frontend/src/components/scan/MultiScanLauncher.tsx

interface MultiScanLauncherProps {
  initialUrls?: string[];     // pré-rempli depuis le crawl
  onScanStart: (urls: string[]) => void;
}
```

### 8.2 `ScanLoader.tsx` — adaptation pour le progress multi-URL

Le composant de progress existant gère déjà un mode `crawlMode="both"` avec 3 colonnes. On ajoute un mode `multi` :

```
Mode "multi" :
┌─────────────────┬──────────────────────────────────┐
│  Domain checks  │  Page checks                     │
│  (colonne fixe) │  (une ligne par page, expandable) │
│                 │                                  │
│  ✅ TLS          │  [page 1/5] ● headers ● cookies │
│  ✅ robots.txt   │  [page 2/5] ● headers ✅ cookies │
│  ✅ exposed      │  [page 3/5] ⏳ headers           │
│  ⏳ CORS         │  [page 4/5] ⌛ pending           │
│                 │  [page 5/5] ⌛ pending           │
└─────────────────┴──────────────────────────────────┘
```

### 8.3 `ScanResults.tsx` — affichage multi-page

Le composant de résultats actuel affiche un seul rapport. Pour le multi-URL :

- **Vue globale** : score global + findings `scope=domain` (une seule fois, clairement labellisés « s'applique à tout le domaine »).
- **Navigation par page** : tabs ou sidebar avec l'URL de chaque page scannée + son score individuel + badge anomalies.
- **Vue comparée** : tableau montrant les catégories en lignes, les pages en colonnes, avec des scores par cellule (heatmap). Utile pour identifier une page qui déroge au pattern global.

### 8.4 `scanService.ts` — `runMultiScan()`

```typescript
export async function runMultiScan(
  urls: string[],
  onEvent: (ev: MultiScanEventHandler) => void,
  getToken?: () => Promise<string | null>,
): Promise<void> {
  return runAsyncScan(
    urls[0],                // url = base_url pour rétrocompat
    onEvent as any,
    {
      scanType: "frontend",
      input: { urls },      // ← passe les URLs dans input
      logPrefix: "[multi-scan-polling]",
    },
    getToken,
  );
}
```

> **Alternative propre :** passer par le nouvel endpoint `POST /scan/api/scan/multi-async` avec un payload `{ urls: [...] }`. Recommandé pour la version finale.

### 8.5 Intégration avec le Crawl

Le flux naturel pour l'utilisateur devient :

```
[Saisir une URL de départ]
        │
        ▼
  CrawlValidationStep   →  Liste d'URLs crawlées
        │                  avec checkboxes de sélection
        │   sélection
        ▼
  MultiScanLauncher     →  Lance le scan multi-URL
        │
        ▼
  ScanLoader (mode multi)
        │
        ▼
  ScanResults (mode multi)
```

Cette intégration évite à l'utilisateur de copier-coller des URLs. Le crawl alimente le scanner.

---

## 9. Modélisation des gains de performance

### 9.1 Estimation pour 10 URLs, même domaine

```
┌─────────────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ Check                               │ Appels/scan  │ Mode actuel  │ Mode multi   │
│                                     │ unitaire     │ ×10 URLs     │              │
├─────────────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ TLS (sockets bruts)                 │ 5            │ 50           │ 5      (-90%)│
│ robots_txt                          │ 1            │ 10           │ 1      (-90%)│
│ sitemap                             │ 2            │ 20           │ 2      (-90%)│
│ exposed_files                       │ 20           │ 200          │ 20     (-90%)│
│ directory_listing                   │ 15           │ 150          │ 15     (-90%)│
│ cors_base                           │ 8            │ 80           │ 8      (-90%)│
│ headers (par page)                  │ 0            │ 0            │ 0            │
│ cookies (par page)                  │ 0            │ 0            │ 0            │
│ integrity (par page)                │ 0            │ 0            │ 0            │
│ info_disclosure (par page)          │ 0            │ 0            │ 0            │
│ tech_fingerprinting (par page)      │ 0            │ 0            │ 0            │
│ cache/assets (partagés, ~30 assets) │ 30           │ 300→30*      │ 30     (-90%)│
│ GET des pages elles-mêmes           │ 1            │ 10           │ 10           │
├─────────────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ TOTAL                               │ ~82          │ ~820         │ ~91  (-89%)  │
└─────────────────────────────────────┴──────────────┴──────────────┴──────────────┘
* cache assets : avec déduplication, les 30 assets partagés ne sont sondés qu'une fois
```

### 9.2 Estimation du temps d'exécution

| Scénario | Mode actuel (séquentiel) | Mode multi (concurrent) |
|----------|--------------------------|-------------------------|
| 1 URL (baseline) | ~5s | ~5s |
| 5 URLs, même domaine | ~25s | ~6–8s |
| 10 URLs, même domaine | ~50s | ~9–12s |
| 20 URLs, même domaine | ~100s | ~15–20s |

**Hypothèses :** domain phase ~4s (TLS + probes parallèles), page scan ~1–2s par page avec concurrence ×5.

### 9.3 Formule de calcul des requêtes HTTP

Pour estimer le nombre total de requêtes HTTP en scan multi-URL :

\[
R(N)=D + N \cdot P + A(N)
\]

Avec :

- \(N\) : nombre d'URLs scannées
- \(D\) : coût domaine (exécuté une seule fois : `tls`, `robots_txt`, `sitemap`, `exposed_files`, `directory_listing`, CORS domaine)
- \(P\) : coût fixe par page (au minimum `initial_fetch`)
- \(A(N)\) : coût variable réseau des checks page (principalement `cache` + CORS page), après mutualisation

Bornes pratiques :

- cas favorable (assets très mutualisés) :
  \[
  R_{min}(N)=D + N\cdot P + a
  \]
- cas défavorable (assets peu mutualisés) :
  \[
  R_{max}(N)=D + N\cdot(P+a)
  \]

où \(a\) est le nombre moyen d'assets testés par page.

Exemple réel (log scan-worker, 15 URLs) :

- `http_requests_count=131`
- `http_requests_by_category={'tls': 2, 'robots_txt': 1, 'cors_cross_origin': 48, 'exposed_files': 20, 'directory_listing': 8, 'sitemap': 1, 'initial_fetch': 15, 'cache': 36}`

Vérification :

\[
2 + 1 + 48 + 20 + 8 + 1 + 15 + 36 = 131
\]

---

## 10. Phases d'implémentation

### Phase 0 — Préparation et fondations (1–2 jours)

> Prérequis : aucune régression sur l'existant.

- [ ] **Classifier** tous les checks dans `_scan_core.py` : ajouter un attribut `scope: Literal["domain", "page"]` à chaque `SCAN_STEP`.
- [ ] **Ajouter** `scope: Literal["domain", "page"] = "page"` et `affected_urls: list[str] | None = None` au modèle `ScanFinding` (Python + TypeScript).
- [ ] **Écrire** `extract_base_url(url: str) -> str` dans `app/utils/url_helpers.py` (factorisation propre).
- [ ] **Créer** `app/models/multi_scan.py` avec `DomainScanContext`, `PageScanContext`, `MultiScanResult`, `PageScanResult`.
- [ ] **Migration Alembic** : colonnes `urls_json`, `base_url`, `result_mode` sur `scan_async_jobs`.

---

### Phase 1 — Refactoring des checks (3–5 jours)

> Objectif : préparer les checks pour être appelés dans les deux contextes.

#### 1.1 `cors_cross_origin/checks.py` — séparation domain/page

```python
# Extraire :
async def run_cors_domain_checks(base_url: str, client: httpx.AsyncClient) -> CorsDomainResult:
    """ACAO:*, ACAC, CORP sur la racine uniquement."""
    ...

async def run_cors_page_checks(
    url: str,
    client: httpx.AsyncClient,
    domain_result: CorsDomainResult,
) -> CorsPageResult:
    """CORS/OPTIONS sur cette URL spécifique + sensitive paths de cette page."""
    ...

def merge_cors_results(domain: CorsDomainResult, page: CorsPageResult) -> CorsCheckResult:
    """Produit le CorsCheckResult final pour une page (compatibilité avec normalizers.py)."""
    ...
```

#### 1.2 `cache/checks.py` — injection d'un assets_cache externe

```python
async def run_cache_checks(
    response: httpx.Response,
    page_url: str,
    client: httpx.AsyncClient,
    config: CacheSettings,
    assets_cache: dict[str, CacheAssetCheckResult] | None = None,  # ← NOUVEAU
) -> CacheCheckResult:
    ...
    # Si assets_cache est None → comportement actuel (aucune régression)
    # Si assets_cache est fourni → lookup avant requête HTTP
```

#### 1.3 Vérifier les interfaces de chaque check

Pour chaque module dans `app/services/`, s'assurer que la fonction principale accepte en argument `client: httpx.AsyncClient` explicitement (et non pas via ctx) afin qu'elle soit appellable indépendamment d'un `ScanContext`.

---

### Phase 2 — Orchestrateur multi-URL (3–4 jours)

> Objectif : le cœur de la feature.

- [ ] **Créer** `app/services/multi_scan_orchestrator.py` (cf. §7.3).
- [ ] **Créer** `app/services/domain_checks/runner.py` avec `run_domain_checks(domain_ctx) -> None`.
- [ ] **Créer** `app/services/page_checks/runner.py` avec `run_page_checks(page_ctx) -> None`.
- [ ] **Modifier** `scan_runner.py` : si `urls` présent dans le job, déléguer à `run_multi_scan()`.
- [ ] **Modifier** `async_scan_executor.py` : passer le `on_progress` enrichi (phase + page_index).
- [ ] **Tests unitaires** :
  - `test_domain_checks_run_once.py` : mock le client httpx, vérifier que les sockets TLS / GETs sont appelés exactement 1× quel que soit le nombre d'URLs.
  - `test_assets_cache_dedup.py` : vérifier que 2 pages partageant le même asset ne génèrent qu'1 requête HEAD.
  - `test_page_error_resilience.py` : une page en 500 ne fait pas échouer le scan global.

---

### Phase 3 — Schémas API et endpoints (1–2 jours)

- [ ] **Modifier** `ScanAsyncCreateRequest` : ajouter `urls`, valider same-domain (cf. §6.1).
- [ ] **Modifier** `create_scan_async_job` : persister `urls_json` et `base_url` dans la DB.
- [ ] **Modifier** `get_scan_async_job_result` : retourner le bon format selon `result_mode`.
- [ ] **(Optionnel)** Créer endpoint dédié `POST /api/scan/multi-async` pour séparer clairement single/multi.
- [ ] **Tests d'intégration** : appel complet single-URL → même résultat qu'avant.

---

### Phase 4 — Frontend (4–6 jours)

- [ ] Mettre à jour les types TypeScript `ScanFinding` (champ `scope`, `affected_urls`).
- [ ] Créer `MultiScanLauncher.tsx`.
- [ ] Modifier `scanService.ts` : `runMultiScan()`.
- [ ] Adapter `ScanLoader.tsx` : mode `multi` avec deux colonnes domain/pages.
- [ ] Adapter `ScanResults.tsx` : navigation tabs par page + vue comparée en tableau.
- [ ] Intégration avec `CrawlValidationStep` : bouton « Scanner ces X pages ».
- [ ] Internationalisation (clés i18n fr/en).

---

### Phase 5 — Observabilité et limites (1–2 jours)

- [ ] **Rate limiting** par domaine cible : si un scan multi-URL démarre et qu'un autre scan du même domaine est en cours, retarder ou rejeter (éviter de DDoS la cible).
- [ ] **Métriques** : logger `multi_scan_urls_count`, `domain_phase_duration_s`, `page_phase_duration_s`, `assets_cache_hit_ratio`.
- [ ] **Timeout** par phase (domain: 30s, par page: 20s) avec `asyncio.wait_for()`.
- [ ] **Limites utilisateur** : par plan (`free`: max 3 URLs, `pro`: max 20 URLs, `enterprise`: max 50 URLs).

---

### Récapitulatif de la roadmap

```
Semaine 1   │ Phase 0 + Phase 1 (fondations + refactoring checks)
Semaine 2   │ Phase 2 (orchestrateur) + Phase 3 (API)
Semaine 3   │ Phase 4 (frontend)
Semaine 4   │ Phase 5 (observabilité) + QA + staging
```

---

## 11. Stratégie de tests

### 11.1 Tests unitaires — scan-service

```
tests/
├── test_multi_scan_orchestrator.py
│   ├── test_domain_checks_called_once_for_n_urls
│   ├── test_page_checks_called_for_each_url
│   ├── test_concurrent_page_scans_respect_semaphore
│   └── test_page_error_does_not_abort_scan
│
├── test_assets_cache.py
│   ├── test_shared_asset_not_double_fetched
│   └── test_cache_miss_triggers_fetch
│
├── test_cors_split.py
│   ├── test_cors_domain_result_reused_across_pages
│   └── test_cors_page_check_merges_correctly
│
└── test_multi_scan_schema.py
    ├── test_urls_same_domain_valid
    ├── test_urls_different_domains_rejected
    └── test_urls_too_many_rejected
```

### 11.2 Tests d'intégration

- Scénario **rétrocompat** : `POST /scan/async { url: "…" }` → résultat identique à avant.
- Scénario **multi** : `POST /scan/async { url: "…", urls: ["…", "…"] }` → `result_mode: "multi"`, 2 `page_results`.
- Scénario **page inaccessible** : 1 page sur 3 répond 500 → 2 résultats complets + 1 avec `error`.

### 11.3 Tests de performance (benchmark)

```python
# tests/bench/test_multi_scan_perf.py
import pytest, time

@pytest.mark.slow
async def test_10_urls_under_15_seconds(mock_http_client, target_domain):
    urls = [f"https://{target_domain}/page-{i}" for i in range(10)]
    t0 = time.monotonic()
    result = await run_multi_scan(urls)
    elapsed = time.monotonic() - t0
    assert elapsed < 15.0
    assert len(result.page_results) == 10
```

---

## 12. Points de vigilance et risques

### 12.1 Courtoisie envers la cible

Avec N pages scannées en parallèle, on génère potentiellement **N × page_checks + domain_probes** requêtes concurrentes vers le même serveur. Risques :

- Déclencher un WAF/rate-limiter de la cible.
- Être perçu comme une attaque et se faire blacklister.

**Mitigations :**
- `asyncio.Semaphore(MAX_CONCURRENT_PAGES)` : max 5 pages en parallèle (configurable).
- Respecter `Crawl-delay` issu de `robots_txt` pour les pages checks.
- Ajouter un délai configurable entre page scans (`scan_page_delay_ms`, défaut 200ms).
- Header `User-Agent` clair : `SecureOps-Scanner/1.0 (+https://secureops.fr/bot)`.

### 12.2 Mémoire

Avec N `httpx.Response` en mémoire simultanément (bodies HTML), surveiller la consommation. Les checks passifs tronquent déjà à `max_body_bytes` — s'assurer que c'est appliqué **avant** de stocker dans `PageScanContext`, pas après.

### 12.3 `tech_fingerprinting` — pages sur CDN différent

Dans un contexte multi-service (ex. `/api/` sur un serveur Node.js, `/` sur Nginx), les headers `Server` peuvent différer par page. L'option B (§4.2) est donc préférable à terme.

### 12.4 Rétrocompatibilité du progress_log

Le format actuel de `progress_log` dans la DB est `list[{step, message, at, anomaly_count?}]`. Le mode multi ajoute `phase`, `page_url`, `page_index`, `total_pages`. Étant du JSONB, c'est rétrocompat pour la lecture. Mais l'UI frontend doit gérer les deux formats (anciens scans single sans `phase`).

### 12.5 Histogramme et alertes

Le système d'alertes existant (`scan_alert_service.py`) est basé sur 1 scan = 1 URL. Pour les scans multi-URL, définir si :
- L'alerte se déclenche sur le **score global** (recommandé par défaut).
- L'alerte peut cibler **une page spécifique** (score individuel < seuil).
- Les findings `scope=domain` génèrent une seule alerte (pas N par page).

---

## Annexe — Checklist de décision rapide

| Question | Réponse |
|----------|---------|
| Le check dépend-il du body HTML d'une URL spécifique ? | → `page` scope |
| Le check sonde-t-il des paths fixes à la racine du domaine ? | → `domain` scope |
| Le check dépend-il des headers de réponse d'une URL ? | → `page` scope |
| Le check fait-il des sockets TLS bruts ? | → `domain` scope |
| L'asset HTTP vérifié pourrait-il apparaître sur plusieurs pages ? | → `assets_cache` |
| Le header (`Server`, `X-Powered-By`) est-il identique sur toutes les pages ? | → candidat `domain`, mais vérifier page par page si multi-service |
