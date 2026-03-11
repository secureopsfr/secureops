# API publique SecureOps — Gestion des clés API

Documentation exhaustive de la gestion de l'API publique et des clés API dans SecureOps (roadmap MVP 0.3.0, section 1).

---

## 1. Vue d'ensemble

L'API publique permet d'authentifier les requêtes avec une **clé API** à la place d'un JWT. Elle cible principalement les intégrations CI/CD, scripts et outils automatisés. Les clés sont créées depuis l'interface utilisateur, stockées sous forme de hash, et peuvent être révoquées à tout moment.

**État actuel :** Modèle, authentification, CRUD des clés, frontend et documentation sont implémentés. **Quotas et rate limiting** ne sont pas encore en place (voir [A-PENSER-PLUS-TARD.md](./A-PENSER-PLUS-TARD.md)).

---

## 2. Modèle de données

### 2.1 Table `api_keys`

| Colonne      | Type         | Description                                      |
|-------------|--------------|--------------------------------------------------|
| `id`        | UUID         | Clé primaire                                     |
| `user_id`   | UUID FK      | Référence vers `users.id` (CASCADE on delete)    |
| `key_hash`  | VARCHAR(64)   | Hash SHA-256 hex de la clé (jamais stockée en clair) |
| `name`      | VARCHAR(100) | Nom de la clé (unique par utilisateur)           |
| `prefix`     | VARCHAR(16)  | Préfixe affiché (ex. `sk_xxxx`)                  |
| `created_at`| TIMESTAMPTZ  | Date de création                                 |
| `last_used_at` | TIMESTAMPTZ | Dernière utilisation (nullable)                  |
| `expires_at` | TIMESTAMPTZ | Date d'expiration (nullable = jamais)            |
| `tags` | JSONB | Tags optionnels (ex. ["production", "CI"])      |
| `description` | VARCHAR(500) | Description optionnelle de la clé              |

**Contraintes :**
- `UNIQUE (user_id, name)` — un nom de clé unique par utilisateur
- `UNIQUE (key_hash)` — unicité des clés

**Fichiers :**
- Modèle : `backend/user-service/app/models/api_key.py`
- Migration : `backend/user-service/alembic/versions/0011_add_api_keys_table.py`, `0012_add_expires_at_to_api_keys.py`

### 2.2 Génération des clés

- **Préfixe :** `sk_`
- **Partie aléatoire :** `secrets.token_urlsafe(24)` → ~32 caractères (base64url)
- **Format complet :** `sk_<32 caractères>` (ex. `sk_Abc12Xyz...`)
- **Hash :** SHA-256 en hex (64 caractères), stocké dans `key_hash`
- **Préfixe affiché :** `sk_` + 4 premiers caractères du random (ex. `sk_Abc1`) pour la liste sans exposer la clé

**Fichier :** `backend/user-service/app/services/api_key_repository.py`

---

## 3. Authentification

### 3.1 Headers acceptés

Deux méthodes pour envoyer la clé API :

1. **`X-API-Key: <clé>`**
2. **`Authorization: Bearer <clé>`** — uniquement si le token ne ressemble pas à un JWT

**Détection JWT :** un token est considéré comme JWT s'il contient exactement 2 points (3 parties base64). Si `Authorization: Bearer sk_xxx` est utilisé, le `sk_xxx` n'a pas 2 points, donc il est traité comme clé API.

### 3.2 Flux d'authentification (gateway)

1. Le middleware du gateway (`backend/gateway/app/middleware.py`) intercepte chaque requête.
2. `extract_api_key_from_request()` lit `X-API-Key` ou `Authorization: Bearer` (si non-JWT).
3. Si une clé est présente, le gateway appelle le user-service :
   - **URL :** `POST {user-service}/api/internal/keys/verify`
   - **Body :** `{ "key": "<clé en clair>" }`
   - **Header :** `X-Internal-Api-Key: <USER_SERVICE_INTERNAL_API_KEY>` (si défini)
4. Le user-service vérifie le hash, met à jour `last_used_at` et retourne `{ user_id, email, sub }`.
5. Le gateway stocke dans `request.state.user` avec `auth_type: "api_key"`.
6. Pour les appels proxy vers les backends (ex. sauvegarde historique), le gateway ajoute `Authorization: Bearer <clé>` dans les headers transmis.

**Fichiers :**
- Gateway : `backend/gateway/app/utils/api_key_auth.py`, `backend/gateway/app/middleware.py`
- User-service (vérification) : `backend/user-service/app/routers/internal_api_keys.py`
- User-service (auth JWT + clé directe) : `backend/user-service/app/utils/auth.py`

### 3.3 Endpoint interne de vérification

| Méthode | Chemin | Protection |
|---------|--------|------------|
| POST | `/api/internal/keys/verify` | `X-Internal-Api-Key` (si `USER_SERVICE_INTERNAL_API_KEY` définie) |

**Body :**
```json
{ "key": "sk_..." }
```

**Réponse 200 :**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "sub": "cognito_sub"
}
```

**Erreurs :**
- 401 : clé invalide ou révoquée
- 401 : clé interne manquante ou incorrecte (si `USER_SERVICE_INTERNAL_API_KEY` définie)

### 3.4 Restrictions

- Les clés API **ne donnent pas accès aux routes admin** (`/admin/*`). Réponse 403 si une clé API est utilisée sur une route admin.

---

## 4. API CRUD des clés

Toutes les routes passent par le gateway. L'utilisateur doit être authentifié par **JWT** (connexion via l'UI). Les clés API ne permettent pas de gérer les clés (créer/lister/révoquer) ; c'est une opération réservée à l'interface web avec JWT.

### 4.1 Créer une clé

| Méthode | Chemin | Auth |
|---------|--------|------|
| POST | `/user/api/keys` | JWT (Bearer) |

**Body :**
```json
{
  "name": "Intégration CI/CD",
  "ttl_days": 30,
  "tags": ["production", "CI"],
  "description": "Clé pour l'intégration CI/CD"
}
```

- `ttl_days` (optionnel) : durée de validité en jours. Valeurs autorisées : 30 (1 mois, défaut), 90, 180, 365, 0 (jamais d'expiration).
- `tags` (optionnel) : liste de tags (max 10, 50 caractères chacun). Ex. `["production", "CI"]`.
- `description` (optionnel) : description de la clé (max 500 caractères).

**Réponse 201 :**
```json
{
  "id": "uuid",
  "key": "sk_Abc12Xyz...",
  "name": "Intégration CI/CD",
  "created_at": "2026-03-09T12:00:00Z",
  "expires_at": "2026-04-08T12:00:00Z"
}
```

- `expires_at` : date d'expiration (null si `ttl_days` était 0).

**Important :** La clé complète (`key`) n'est retournée qu'une seule fois. Elle doit être copiée et stockée de façon sécurisée.

**Erreurs :**
- 403 : limite de clés atteinte (`api_keys.max_per_user` dans `config/settings.yml`, défaut 5)
- 409 : une clé avec ce nom existe déjà

### 4.2 Lister les clés

| Méthode | Chemin | Auth |
|---------|--------|------|
| GET | `/user/api/keys` | JWT (Bearer) |

**Réponse 200 :**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Intégration CI/CD",
      "prefix": "sk_Abc1",
      "created_at": "2026-03-09T12:00:00Z",
      "last_used_at": "2026-03-09T14:30:00Z",
      "expires_at": "2026-04-08T12:00:00Z",
      "tags": ["production", "CI"],
      "description": "Clé pour l'intégration CI/CD"
    }
  ]
}
```

- `expires_at` : date d'expiration (null si la clé n'expire jamais).

Les clés ne sont jamais retournées en clair ; seul le `prefix` est affiché.

### 4.3 Modifier une clé

| Méthode | Chemin | Auth |
|---------|--------|------|
| PATCH | `/user/api/keys/{id}` | JWT (Bearer) |

**Body (tous les champs sont optionnels, seuls les champs fournis sont modifiés) :**
```json
{
  "name": "Nouveau nom",
  "ttl_days": 90,
  "expires_at": "2026-06-15",
  "tags": ["production", "staging"],
  "description": "Nouvelle description"
}
```

- `name` : nouveau nom (unique par utilisateur).
- `ttl_days` / `expires_at` : si fournis, modifier la validité. Même logique que la création (`expires_at` prioritaire).
- `tags` : liste de tags. Liste vide = supprimer tous les tags.
- `description` : description de la clé. Chaîne vide ou null = supprimer la description.

**Réponse 200 :** même format qu'un élément de la liste (4.2).

**Erreurs :**
- 400 : aucune modification fournie, ou format de date invalide
- 404 : clé non trouvée
- 409 : une clé avec ce nom existe déjà

### 4.4 Révoquer une clé

| Méthode | Chemin | Auth |
|---------|--------|------|
| DELETE | `/user/api/keys/{id}` | JWT (Bearer) |

**Réponse :** 204 No Content

**Erreurs :**
- 404 : clé non trouvée ou n'appartient pas à l'utilisateur

---

## 5. Endpoints protégés par clé API

### 5.1 Scan asynchrone (queue)

Endpoint recommandé pour les intégrations API (CI/CD, scripts).

| Méthode | Chemin | Auth |
|---------|--------|------|
| POST | `/scan/api/scan/async` | Optionnel pour `scan_type=frontend` ; requis sinon |

**Body :**
```json
{
  "url": "https://example.com",
  "scan_type": "backend",
  "input": {}
}
```

**Réponse :** `202` avec `job_id` (et `job_token` pour anonyme). Le client doit ensuite poller :
- `GET /scan/api/scan/async/{job_id}`
- `GET /scan/api/scan/async/{job_id}/result`

**Exemple curl :**
```bash
curl -X POST "https://api.secureops.io/scan/api/scan/async" \
  -H "X-API-Key: sk_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","scan_type":"backend","input":{}}'
```

### 5.2 Routes publiques (sans auth)

Les routes asynchrones suivantes sont publiques pour `scan_type=frontend` :
- `POST /scan/api/scan/async`
- `POST /crawl/api/crawl/async`

Les routes de statut/résultat nécessitent ownership (JWT propriétaire ou `X-Job-Token` anonyme).

---

## 6. Configuration

### 6.1 User-service

**Fichier :** `backend/user-service/config/settings.yml`

```yaml
api_keys:
  max_per_user: 5  # Nombre maximum de clés par utilisateur
  default_ttl_days: 30  # Durée par défaut (1 mois), 0 = jamais
  allowed_ttl_days: [0, 30, 90, 180, 365]  # Options (0 = sans expiration)
```

**Variables d'environnement (`.env.example`) :**
```
# Clé pour protéger l'endpoint /api/internal/keys/verify (appelé par le gateway)
# Définir la même valeur que USER_SERVICE_INTERNAL_API_KEY sur le gateway.
USER_SERVICE_INTERNAL_API_KEY=exemple-secret-partagé
```

### 6.2 Gateway

**Variable d'environnement :**
```
USER_SERVICE_INTERNAL_API_KEY=exemple-secret-partagé
```

Si définie, le gateway envoie `X-Internal-Api-Key` lors de l'appel à `/api/internal/keys/verify`. Le user-service vérifie cette clé avant de traiter la requête.

---

## 7. Frontend

### 7.1 Pages

| Route | Description |
|-------|-------------|
| `/scanner/cles-api` | Gestion des clés API (liste, création, révocation) |
| `/scanner/docs/api` | Documentation de l'API publique (auth, exemple curl) |

### 7.2 Composants

- **`ApiKeysContent`** (`frontend/src/components/scan/ApiKeysContent.tsx`) : liste des clés, modals création/affichage clé/révocation
- **`apiKeysService`** (`frontend/src/services/apiKeysService.ts`) : `listApiKeys`, `createApiKey`, `revokeApiKey`, erreurs typées `ApiKeyError` avec codes (`LIMIT_EXCEEDED`, `NAME_EXISTS`, `NOT_FOUND`)

### 7.3 Flux UX

1. **Création :** modal avec champ nom + durée de validité (1 mois, 3 mois, 6 mois, 1 an, Jamais) → création → modal affichant la clé avec bouton Copier et avertissement « Ne sera plus visible »
2. **Liste :** affichage de `prefix`, `created_at`, `expires_at`, `last_used_at` ; bouton Révoquer par clé
3. **Révocation :** modal de confirmation avec le nom de la clé

### 7.4 Traductions

Clés i18n : `scanner.clesApi.*` (intro, createBtn, createTitle, keyWarning, copy, revoke, erreurs spécifiques, etc.) et `scanner.docsApi.*` pour la documentation.

---

## 8. Erreurs et codes HTTP

| Code | Contexte | Message type |
|------|----------|--------------|
| 401 | Clé invalide ou révoquée | « Clé API invalide ou révoquée » |
| 401 | Clé expirée | « Clé API expirée » |
| 401 | IP non autorisée | « Clé API : IP non autorisée » |
| 403 | Limite de clés atteinte | « Limite de clés atteinte (N maximum)... » |
| 403 | Clé API sur route admin | « Accès refusé. Les clés API ne permettent pas l'accès admin. » |
| 404 | Clé non trouvée (DELETE) | « Clé non trouvée » |
| 409 | Nom déjà utilisé | « Une clé avec le nom « X » existe déjà. » |

Le frontend mappe ces situations aux clés i18n via `ApiKeyError` et ses codes.

---

## 9. Non implémenté (roadmap 1.3)

- **Quotas par compte (web)** : nombre max de scans/jour par utilisateur connecté
- **Quotas par clé API** : nombre max de scans/jour par clé
- **Rate limiting** : ex. requêtes/minute par clé ou par IP
- **Réponse 429** (Too Many Requests) avec `Retry-After`
- Documentation des seuils retenus

---

## 10. Fichiers de référence

| Rôle | Fichier |
|------|---------|
| Modèle | `backend/user-service/app/models/api_key.py` |
| Repository | `backend/user-service/app/services/api_key_repository.py` |
| Schémas | `backend/user-service/app/schemas/api_key.py` |
| CRUD router | `backend/user-service/app/routers/api_keys.py` |
| Verify interne | `backend/user-service/app/routers/internal_api_keys.py` |
| Auth user-service | `backend/user-service/app/utils/auth.py` |
| Auth gateway | `backend/gateway/app/utils/api_key_auth.py` |
| Middleware gateway | `backend/gateway/app/middleware.py` |
| Proxy (forward clé) | `backend/gateway/app/services/proxy/proxy.py` |
| Scan async | `backend/scan-service/app/routers/scan.py` |
| Migration | `backend/user-service/alembic/versions/0011_add_api_keys_table.py` |
| Config | `backend/user-service/config/settings.yml` |
| Service frontend | `frontend/src/services/apiKeysService.ts` |
| Composant | `frontend/src/components/scan/ApiKeysContent.tsx` |
| Page clés | `frontend/src/app/[locale]/scanner/cles-api/page.tsx` |
| Doc API | `frontend/src/app/[locale]/scanner/docs/api/page.tsx` |

---

## Voir aussi

- [Intégration CI/CD — GitHub Action SecureOps](./INTEGRATION-GITHUB-ACTION.md) : workflow GitHub Actions, action dédiée, exemples de pipelines
