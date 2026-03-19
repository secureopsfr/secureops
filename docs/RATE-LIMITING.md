# Rate Limiting et Protection Anti-Abus (SecureOps)

Ce document explique pourquoi mettre du rate limiting, comment le concevoir proprement, et comment l'implementer dans SecureOps sans casser l'experience utilisateur.
Le perimetre d'application immediat est volontairement limite a `scan` et `crawl`.

## 1) Pourquoi c'est important

Sans rate limiting, une API est vulnerable a plusieurs problemes :

- abus automatise (spam, credential stuffing, scraping agressif) ;
- deni de service applicatif (saturation CPU/DB/appels externes) ;
- couts cloud plus eleves (requetes inutiles, jobs asynchrones lances en masse) ;
- degradation pour les vrais utilisateurs (latence, erreurs, timeouts).

Le rate limiting est une mesure defensive standard qui complete l'authentification, la validation et le captcha.

## 2) Objectifs concrets pour SecureOps

Dans ce projet, l'objectif n'est pas seulement "bloquer", mais surtout :

- proteger les endpoints publics sensibles ;
- lisser la charge (burst court + debit soutenu) ;
- appliquer des limites adaptees selon le contexte (IP, utilisateur, cle API) ;
- fusionner le quota journalier pour un meme proprietaire (usage UI + API) ;
- renvoyer une reponse claire et standard (`429 Too Many Requests`) ;
- permettre l'observabilite (logs + metriques) pour ajuster les seuils.

## 3) Ce qu'il faut limiter en priorite

### Perimetre actuel (maintenant)

- `POST /scan/api/scan/async`
- `POST /crawl/api/crawl/async`

### Hors perimetre pour l'instant (phase ulterieure)

- `POST /admin/api/analytics/ingest`
- `POST /api/contact`
- endpoints d'authentification (login/reset)

## 4) Strategie recommandee (defense en couches)

Ne pas tout faire dans un seul endroit. La strategie la plus robuste est :

1. **Couche edge/reverse proxy (obligatoire)**
   Limitation rapide pres du reseau pour absorber les pics.
2. **Couche applicative (recommandee)**
   Regles metier plus fines (par utilisateur, par cle API, par route).
3. **Quotas journaliers/hebdo fusionnes (complement)**
   Limites de volume sur une periode longue, partagees entre UI et API pour un meme utilisateur proprietaire.

La combinaison des trois est plus fiable qu'une seule couche.

### Politique recommandee SecureOps (decision produit)

- **Quota global fusionne par user** pour la conso journaliere (UI + API cumules).
- **Sous-limites separees court terme** pour la protection anti-abus :
  - bucket JWT (`user_id + route + method`)
  - bucket API key (`api_key_id + route + method`)
  - bucket anonyme (`ip + route + method`)
- Cette approche garde une facturation/consommation simple, tout en permettant de contenir une cle API compromise sans bloquer tout le compte.

## 5) Choisir la bonne "cle de limitation"

Une mauvaise cle cree des faux positifs ou laisse passer l'abus.

Definition importante pour ce document :

- **Anonyme** = aucune identite d'authentification fournie (`Authorization` absent et `X-API-Key` absent).
- Le `job_token` des endpoints async n'est pas un token d'auth globale : il sert uniquement a acceder au statut/resultat d'un job anonyme.

- **Par IP** : utile pour endpoints anonymes/publics.
- **Par utilisateur (`user_id`)** : pour sessions JWT.
- **Par cle API** : pour API publique.
- **Par route + methode** : evite qu'un endpoint critique soit noye par des routes peu sensibles.

Regle pratique :

- anonyme => `ip + route + method`
- authentifie JWT => `user_id + route + method`
- API key => `api_key_id + route + method`

## 6) Algorithmes de rate limiting

Les 3 approches courantes :

- **Fixed window** : simple, mais effet de bord aux frontieres de fenetre.
- **Sliding window** : plus juste, un peu plus couteux.
- **Token bucket / leaky bucket** : tres adapte aux APIs (autorise un petit burst puis stabilise).

Pour SecureOps, **token bucket** ou **sliding window** sont de bons choix.

## 7) Reponse HTTP attendue

Quand la limite est depassee :

- status code : `429 Too Many Requests`
- payload JSON clair (machine-readable + humain)
- header `Retry-After` (secondes ou date HTTP) quand possible

Exemple de payload :

```json
{
  "detail": "Rate limit exceeded",
  "limit_key": "scan_async_per_user",
  "retry_after_seconds": 30
}
```

## 8) Seuils de depart proposes (a ajuster avec metriques)

Ces valeurs sont des **seuils initiaux** raisonnables pour lancer la protection :

- `POST /scan/api/scan/async`
  - anonyme: 3 req/min par IP, burst 2
  - authentifie: 10 req/min par utilisateur
- `POST /crawl/api/crawl/async`
  - anonyme: 2 req/min par IP
  - authentifie: 6 req/min par utilisateur

Ajouter en plus un quota long terme, ex:

- scans async: 100/jour par utilisateur proprietaire (UI + API cumules)
- crawls: 20/jour par utilisateur proprietaire (UI + API cumules)

Exemple de fonctionnement :

- un utilisateur lance 60 scans via UI et 40 via API key => quota journalier scan atteint (100/100) ;
- les buckets court terme restent distincts (user/API key/IP) pour absorber les abus sans melanger les canaux.

## 9) Architecture technique conseillee

### Stockage du compteur

Utiliser **Redis** pour les compteurs (TTL natif, performant, partage multi-instances).

Pourquoi pas uniquement en memoire locale :

- casse en multi-replicas ;
- reset au redemarrage ;
- comportement incoherent selon le pod/instance.

### Source d'identite

Dans la gateway, reutiliser ce qui existe deja :

- JWT decode => `request.state.user["sub"]` (ou equivalent stable)
- API key auth => identifiant cle ou utilisateur associe
- fallback anonyme => IP client (`X-Forwarded-For` parsee proprement)

## 10) Option d'implementation A: au niveau gateway (prioritaire)

Le plus simple operationnellement : faire la limite dans la gateway FastAPI avant proxy.

Etapes :

1. Ajouter un middleware/dependance de rate limiting (Redis-backed).
2. Definir un mapping de regles par route/methode.
3. Calculer la cle de limitation (user/api key/ip).
4. Incrémenter + verifier la limite.
5. Retourner `429` + `Retry-After` si depassement.

Pseudo-code simplifie :

```python
key = build_limit_key(request)  # user_id|api_key_id|ip + method + path
allowed, retry_after = await limiter.check(key=key, limit="10/min", burst=2)
if not allowed:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded", "retry_after_seconds": retry_after},
        headers={"Retry-After": str(retry_after)},
    )
```

## 11) Option d'implementation B: reverse proxy (Nginx/Traefik)

Si un reverse proxy externe est present, faire aussi des limites "edge" :

- limite globale par IP ;
- limite plus stricte sur endpoints critiques ;
- anti-burst court.

Cette couche est tres utile contre les pics brutaux avant meme d'atteindre la logique Python.

## 12) Observabilite (indispensable)

Sans metriques, impossible de savoir si les seuils sont bons.

A instrumenter :

- nombre de `429` par route ;
- top cles de limitation (anonymisees/hachees si necessaire) ;
- taux d'erreur apres activation ;
- latence P95/P99 avant/apres ;
- ratio trafic legitime / trafic bloque.

## 13) Bonnes pratiques anti-regressions

- ne jamais limiter agressivement `GET /health` ;
- whitelister les probes internes si necessaire ;
- prevoir un mode "shadow" (observe sans bloquer) avant enforcement strict ;
- documenter les limites pour les clients API ;
- ajouter des tests d'integration (N requetes -> `429` attendu).

## 14) Plan de mise en place progressif (recommande)

### Phase 1 - Foundation (FAIT)

- rate limiting court terme en memoire dans la gateway (`utils/rate_limiter.py`) ;
- quota long terme PostgreSQL dans le user-service (`daily_quotas` table) ;
- middleware gateway etendu : rate limit + quota sur `scan/async` et `crawl/async` ;
- frontend : hook `useQuota` + affichage `X / 50` dans le header.

### Phase 2 - Quotas long terme

- ajouter quotas journaliers fusionnes par utilisateur proprietaire (UI + API) ;
- conserver des sous-limites techniques separees (JWT/API key/anonyme-IP).

### Phase 3 - Hardening

- affiner par plan (free/pro), par route, par methode ;
- activer alertes (pic de `429`, pic de traffic anonyme).
- etendre ensuite aux autres endpoints publics (analytics, contact, auth) si besoin.

## 15) Ce que le rate limiting ne remplace pas

Le rate limiting est necessaire mais ne suffit pas seul. Garder aussi :

- validation stricte des payloads ;
- captcha sur formulaires publics ;
- protections auth (lockout/backoff pour login) ;
- timeouts, circuit breakers et files d'attente pour jobs lourds.

## 16) Checklist "Definition of Done"

- [x] Regles de limitation definies par endpoint critique
- [x] Rate limiting court terme en memoire (gateway `utils/rate_limiter.py`)
- [x] Quota long terme en PostgreSQL (user-service `daily_quotas` table)
- [x] Endpoint interne `POST /api/internal/quota/check-and-increment` (user-service)
- [x] Endpoint public `GET /api/user/quota/daily` (user-service)
- [x] Gateway : `AuthMiddleware` etendu avec check rate limit + quota
- [x] Reponse standard `429` + `Retry-After` + payload JSON
- [x] Frontend : hook `useQuota` + affichage header
- [ ] Migration Alembic executee en production (`0021_add_daily_quotas`)
- [ ] Variable `DAILY_QUOTA_LIMIT` configuree dans les `.env` si besoin de surcharger (defaut: 50)
- [ ] Logs et metriques dashboardees
- [ ] Tests automatises de depassement de seuil

---

## Resume

Pour SecureOps, la voie la plus robuste est :

- **edge limiting** (proxy/gateway) pour proteger vite ;
- **limites metier en app** avec buckets separes (IP / user / API key) ;
- **quotas long terme fusionnes par user** pour une conso simple (UI + API) ;
- **observabilite + ajustements** pour eviter de penaliser les utilisateurs legitimes.

Cette approche permet de reduire le risque d'abus et de DoS tout en gardant une experience stable.
