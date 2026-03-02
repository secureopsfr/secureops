# SecureOps — Idées à envisager plus tard

Ce document regroupe des fonctionnalités envisagées mais non planifiées pour le MVP 0.2.0.

---

## Mode asynchrone + queue

> **Contexte :** Retiré du scope MVP 0.2.0. À réintégrer si les scans deviennent trop longs ou si les timeouts HTTP posent problème.

### Objectif

Permettre des scans longs sans timeout : l’utilisateur lance un scan, reçoit immédiatement un `job_id`, puis consulte le statut et les résultats plus tard.

### 2.1 Choix technologique

- [ ] Choisir stack : SQS + worker Python **ou** Celery + Redis
- [ ] Documenter décision (pros/cons, coût, complexité)

### 2.2 Infrastructure queue

- [ ] Créer file SQS (ou Redis pour Celery)
- [ ] Configurer dead-letter queue (DLQ) pour échecs
- [ ] Timeout et retry policy (ex. 3 tentatives, backoff exponentiel)

### 2.3 Worker scan

- [ ] Worker dédié : consomme jobs de la queue, exécute le scan
- [ ] Réutiliser la logique existante (`scan_stream`, checks, normalisation)
- [ ] Stocker résultat en base (ex. PostgreSQL) avec `job_id`, `status`, `result`

### 2.4 API endpoints

- [ ] `POST /api/scan/async` : enqueue un job, retourne `job_id`
- [ ] `GET /api/scan/async/{job_id}` : statut du job (pending, running, completed, failed)
- [ ] `GET /api/scan/async/{job_id}/result` : résultat du scan (si completed)

### 2.5 Frontend

- [ ] Option : lancer scan en mode async si durée estimée > seuil
- [ ] Polling ou WebSocket pour afficher le statut
- [ ] Page résultats accessible via URL partageable (`/scan/{job_id}`)

### Référence

Voir le guide détaillé (Redis + Celery) dans l’historique des discussions ou recréer à partir de ce document.
