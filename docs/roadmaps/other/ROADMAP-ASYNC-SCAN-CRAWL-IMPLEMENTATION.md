# Roadmap detaillee - Mode asynchrone scan + crawl (dev puis prod)

## 1) Decision validee

Ce document remplace la version "scan only" et definit la V1 pour **scan-service + crawl-service**.

Decisions confirmees:

- Scope immediat: **scan async + crawl async** dans le meme lot.
- Transport queue V1: **DB queue only** (pas SQS en dev).
- SSE: **retire directement** (remplace par polling + progress log).
- Loader frontend: conserver le detail etape par etape via **progress_log** persiste en base.
- Acces anonyme: autorise avec **`X-Job-Token`** (rigoureux), stocke en base sous forme de **hash**.
- Retry/backoff: `15s`, `60s`, `180s`.
- Timeout job: `300s` (scan et crawl).
- `scan_type`:
  - `frontend`: execution reelle
  - `backend`/`custom`: resultat **fake** en `completed` (message fake)
- Tests V1: minimum backend (create/status/result + ownership), pas d'e2e frontend pour l'instant.
- Docker Compose: ajouter `scan-worker` et `crawl-worker`.

---

## 2) Objectif produit

Pour un traitement long:

1. frontend lance un job async et recoit immediatement un `job_id` (+ eventuellement `job_token`).
2. worker execute en arriere-plan.
3. frontend fait polling du statut puis du resultat.
4. frontend affiche un ecran de chargement progressif base sur les etapes persistees.

---

## 3) Contrat API cible (stable)

Le contrat est identique entre scan et crawl.

## 3.1 Scan

- `POST /scan/api/scan/async`
- `GET /scan/api/scan/async/{job_id}`
- `GET /scan/api/scan/async/{job_id}/result`

## 3.2 Crawl

- `POST /crawl/api/crawl/async`
- `GET /crawl/api/crawl/async/{job_id}`
- `GET /crawl/api/crawl/async/{job_id}/result`

## 3.3 Request create (shape commune)

```json
{
  "url": "https://example.com",
  "scan_type": "frontend",
  "input": {}
}
```

## 3.4 Response create

```json
{
  "job_id": "uuid",
  "status": "pending",
  "scan_type": "frontend",
  "job_token": "plain-token-only-for-anonymous"
}
```

`job_token`:

- present uniquement pour les jobs anonymes
- retourne une seule fois au `POST`
- jamais re-expose en clair ensuite

## 3.5 Response status

```json
{
  "job_id": "uuid",
  "scan_type": "frontend",
  "status": "pending|running|completed|failed",
  "attempt_count": 1,
  "created_at": "ISO-8601",
  "started_at": "ISO-8601|null",
  "completed_at": "ISO-8601|null",
  "last_step": "tls_check",
  "last_message": "Verification TLS...",
  "progress_log": [
    {"step": "validation_url_check", "message": "Validation URL...", "at": "ISO-8601"},
    {"step": "validation_url_done", "message": "URL validee.", "at": "ISO-8601"}
  ],
  "error": {
    "message": "string",
    "status_code": 500,
    "error_type": "unexpected_error"
  }
}
```

## 3.6 Response result

- `200` si `completed`
- `409` si job non termine
- `404` si inconnu/non autorise

Resultat:

- pour `frontend`: payload metier reel
- pour `backend/custom` (V1): payload fake standardise (`completed`, `message` fake)

---

## 4) Auth, anonymat et ownership

## 4.1 Jobs authentifies

- si `Authorization` present au `POST`, le job est lie a `user_id`
- lectures status/result autorisees uniquement au meme user

## 4.2 Jobs anonymes

- autorises pour `scan_type=frontend` uniquement
- lectures status/result exigeant `X-Job-Token`
- en DB: stocker `job_token_hash` uniquement (jamais le token en clair)

## 4.3 Rigueur transport token

- header unique: `X-Job-Token`
- pas de query param `job_token`
- hash recommande: SHA-256/HMAC (avec secret serveur)

---

## 5) Schema de donnees (service-owned)

Meme instance Postgres possible, mais chaque table est "owned" par son service.

## 5.1 `scan_async_jobs` (scan-service)

- `id` UUID PK
- `user_id` UUID nullable
- `url` text not null
- `scan_type` varchar(20) not null default `frontend`
- `input_json` JSONB nullable
- `status` text not null (`pending|running|completed|failed`)
- `result_json` JSONB nullable
- `error_json` JSONB nullable
- `progress_log_json` JSONB not null default `[]`
- `last_step` text nullable
- `last_message` text nullable
- `attempt_count` int not null default 0
- `max_attempts` int not null default 3
- `next_retry_at` timestamptz nullable
- `job_token_hash` text nullable
- `created_at`, `started_at`, `completed_at` timestamptz
- `expires_at` timestamptz nullable

Indexes:

- `(status, created_at)`
- `(status, next_retry_at)`
- `(scan_type, status, created_at)`
- `(user_id, created_at desc)`
- `(expires_at)`

## 5.2 `crawl_async_jobs` (crawl-service)

Meme pattern de colonnes que `scan_async_jobs`.

---

## 6) Worker model (processus separes API vs worker)

## 6.1 Exemple concret

Deux processus par service:

- `scan-service-api`: FastAPI
- `scan-service-worker`: boucle worker
- `crawl-service-api`: FastAPI
- `crawl-service-worker`: boucle worker

Meme codebase/image par service, commande differente.

## 6.2 Boucle worker (identique scan/crawl)

1. claim atomique d'un job `pending` (ou retryable)
2. passage `running`
3. push progress dans `progress_log` + maj `last_step/last_message`
4. execution metier
5. `completed + result_json` ou `failed + error_json`
6. retry/backoff (`15s/60s/180s`) jusqu'a `max_attempts=3`
7. timeout force a `failed_timeout` si > `300s`

---

## 7) Plan implementation DEV (DB queue only)

## Phase D1 - Models + migrations

- creer `scan_async_jobs` (scan-service)
- creer `crawl_async_jobs` (crawl-service)
- ajouter enums/status communs dans `common` (sans SQL metier)

## Phase D2 - Endpoints async (scan + crawl)

- create/status/result pour scan et crawl
- auth ownership + regles anonymes
- validation `scan_type`
- `backend/custom` -> fake completed

## Phase D3 - Workers (scan + crawl)

- ajouter worker scan
- ajouter worker crawl
- gestion retries/backoff/timeouts
- ecriture `progress_log`

## Phase D4 - Front polling + loader

- remplacer SSE par polling
- conserver l'ecran de progression via `progress_log`
- lecture result quand status `completed`

## Phase D5 - Tests minimum

- tests API create/status/result
- tests ownership (cross-user bloque)
- tests anonymes via `X-Job-Token`
- test de base worker (pending -> completed)

---

## 8) Plan implementation PROD (apres V1)

## Phase P1 - SQS + DLQ

- queue principale par domaine (scan/crawl)
- DLQ + redrive policy
- IAM minimal API/worker

## Phase P2 - Abstraction queue provider

- provider `db` (dev) et `sqs` (prod)
- switch via config sans changer API/frontend

## Phase P3 - Hardening et ops

- idempotence stricte
- alerting backlog/age messages/DLQ
- runbooks incident + rollback provider

---

## 9) Docker Compose (microservices)

Modifier:

- `backend/docker-compose.backend.betatest.yml`

Ajouts:

- `scan-worker` (meme image que scan-service, commande worker)
- `crawl-worker` (meme image que crawl-service, commande worker)

Variables recommandees:

- `ASYNC_ENABLED=true`
- `ASYNC_QUEUE_PROVIDER=db`
- `ASYNC_WORKER_POLL_INTERVAL_SECONDS=2`
- `ASYNC_JOB_TIMEOUT_SECONDS=300`
- `ASYNC_MAX_ATTEMPTS=3`

---

## 10) Risques et mitigations (valides)

- fuite cross-user -> ownership strict + tests autorisation
- jobs bloques -> watchdog `running` + timeout 300s
- charge polling -> backoff client + cadence max
- duplication -> idempotence sur statuts terminaux
- incompatibilite `scan_type/input` -> validation stricte + erreurs explicites
- cout prod -> dashboards queue + budget alerts

---

## 11) Definition of Done V1

- scan async et crawl async operationnels en DB queue
- SSE retire (plus de dependance frontend au streaming)
- loader frontend conserve les etapes via `progress_log`
- anonymes securises par `X-Job-Token` (hash en base)
- workers separes dans docker-compose
- tests minimum backend verts
