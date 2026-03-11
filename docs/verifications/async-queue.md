# Queue asynchrone scan + crawl

Ce document decrit en detail le fonctionnement du systeme asynchrone de `scan-service` et `crawl-service` (creation de job, worker, retries, ownership, polling frontend).

---

## 1) Objectif

Le but est de remplacer les traitements longs synchrones par un modele:

1. le client cree un job (`POST .../async`)
2. un worker traite le job en arriere-plan
3. le client poll le statut (`GET .../async/{job_id}`)
4. le client recupere le resultat final (`GET .../async/{job_id}/result`)

Benefices:

- pas de timeout HTTP cote client pour les scans/crawls longs
- progression persistante en base (`progress_log_json`)
- retries controls et timeout job centralises
- meme contrat fonctionnel pour scan et crawl

---

## 2) Endpoints

## 2.1 Scan

- `POST /scan/api/scan/async`
- `GET /scan/api/scan/async/{job_id}`
- `GET /scan/api/scan/async/{job_id}/result`

## 2.2 Crawl

- `POST /crawl/api/crawl/async`
- `GET /crawl/api/crawl/async/{job_id}`
- `GET /crawl/api/crawl/async/{job_id}/result`

---

## 3) Contrat de donnees

## 3.1 Creation de job

Request:

```json
{
  "url": "https://example.com",
  "scan_type": "frontend",
  "input": {}
}
```

Response:

```json
{
  "job_id": "uuid",
  "status": "pending",
  "scan_type": "frontend",
  "job_token": "only-for-anonymous"
}
```

Notes:

- `job_token` est renvoye uniquement pour un job anonyme
- `job_token` n'est plus jamais renvoye ensuite

## 3.2 Statut

`GET .../async/{job_id}` retourne:

- `status`: `pending | running | completed | failed`
- `attempt_count`
- timestamps (`created_at`, `started_at`, `completed_at`)
- `progress_log` (liste d'etapes)
- `last_step`, `last_message`
- `error` si echec

## 3.3 Resultat

`GET .../async/{job_id}/result`:

- `200` si `completed`
- `409` si job non termine
- `404` si job absent
- `403` si ownership invalide

---

## 4) Authentification et ownership

## 4.1 Jobs authentifies

- si l'utilisateur est authentifie au `POST`, le job est lie a `user_id`
- seuls ce user peut lire status/result

## 4.2 Jobs anonymes

- autorises pour `scan_type=frontend`
- acces status/result via `X-Job-Token`
- en base, seul `job_token_hash` est stocke (jamais le token en clair)

## 4.3 Verification d'acces

Regles:

1. si `job.user_id` existe -> match strict avec `X-Authenticated-User-Id`
2. sinon -> verifier `X-Job-Token` contre `job_token_hash`

---

## 5) Tables et persistence

Tables dediees:

- `scan_async_jobs` (owner: scan-service)
- `crawl_async_jobs` (owner: crawl-service)

Champs principaux:

- identite: `id`, `user_id`, `scan_type`, `url`, `input_json`
- execution: `status`, `attempt_count`, `max_attempts`, `next_retry_at`
- resultat: `result_json`, `error_json`
- progression: `progress_log_json`, `last_step`, `last_message`
- token anonyme: `job_token_hash`
- timestamps: `created_at`, `started_at`, `completed_at`, `expires_at`

---

## 6) Workers

Chaque service a 2 processus:

- API FastAPI
- worker async dedie

Boucle worker:

1. claim atomique du prochain job (`pending` ou retryable)
2. passage en `running`
3. execution metier via executor
4. flush de progression en base
5. finalisation:
   - `completed` + `result_json`
   - ou `failed` + `error_json`

---

## 7) Retry, timeout, backoff

Configuration appliquee:

- `max_attempts = 3`
- backoff: `15s`, `60s`, `180s`
- timeout job: `300s`

En cas d'echec retryable:

- statut `failed`
- `next_retry_at` calcule selon la tentative

En cas d'echec final (ou timeout):

- statut `failed`
- `completed_at` renseigne
- plus de retry

---

## 8) Progression temps reel (polling)

Le frontend ne recoit plus un stream SSE direct.
Il poll le statut et lit `progress_log`.

Pour eviter les commits DB trop frequents, les workers batchent la progression:

- buffer en memoire
- flush toutes les `progress_batch_window_seconds` (defaut `0.2`)
- flush force en fin de job

Le frontend adapte son intervalle de polling:

- demarrage a `500ms`
- +`250ms` si aucune nouvelle etape
- reset a `500ms` quand une nouvelle etape arrive

---

## 9) Scan types

Regles:

- `scan_type=frontend`: execution reelle
- `scan_type=backend` ou `custom`: resultat fake en `completed`

Ce comportement est implemente dans:

- `scan-service/app/services/async_scan_executor.py`
- `crawl-service/app/services/async_crawl_executor.py`

---

## 10) Infra et execution locale

Services docker ajoutes:

- `scan-worker`
- `crawl-worker`

Les workers utilisent la meme base que leurs APIs respectives, mais des processus distincts.
Les parametres async viennent de `config/settings.yml` de chaque service (`async_jobs`).

---

## 11) Nettoyage legacy effectue

Points retires ou migres:

- endpoints SSE legacy pour scan/crawl
- references docs vers `/scan/fake` et `/crawl/stream`
- services/tests legacy SSE obsoletes

Le flux de reference est maintenant le flux async queue + polling.
