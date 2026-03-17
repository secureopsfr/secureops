# SecureOps — Idées à envisager plus tard

Ce document regroupe des fonctionnalités envisagées mais non planifiées pour les MVP actuels.

---

## Quotas et rate limiting (web + API)

> **Contexte :** Contenu retiré du scope roadmap 0.3.0 (section 1.3). Politique unifiée : mêmes principes pour les scans lancés depuis l'UI (compte utilisateur) et pour les appels API (clé). Les seuils peuvent être distincts (ex. quota par compte vs par clé) mais la mécanique (comptage, 429) est centralisée.

### Objectif

Limiter les abus et gérer la charge : quotas par compte/clé, rate limiting, réponse 429.

### Tâches

- [ ] **Quotas par compte (web)** : ex. nombre max de scans/jour par utilisateur connecté (à définir).
- [ ] **Quotas par clé API** : ex. 100 scans/jour par clé (ou aligné sur le quota compte).
- [ ] **Rate limiting** : ex. 10 req/min par clé ; par IP ou par compte pour l'UI (à définir).
- [ ] **Réponse 429** (Too Many Requests) en cas de dépassement, avec en-tête `Retry-After` si pertinent.
- [ ] Documenter les seuils retenus (section limites ou doc dédiée) et les faire évoluer selon l'usage.
- [ ] **Limites crawler** : nombre max de crawls/jour par utilisateur (ou par clé API), aligné ou dérivé des quotas (ex. 1 crawl = 1 unité quota ou quota dédié crawl).
- [ ] **Option crawler** : limite par domaine cible (ex. pas plus de X crawls/jour vers le même host) pour éviter le harcèlement.
- [ ] Documenter dans la doc crawler et dans la doc limites/quotas : comportement en cas de dépassement (429), message utilisateur en cas d'URL refusée (liste noire ou interdite).

### Référence

- API publique : [docs/API-PUBLIQUE.md](API-PUBLIQUE.md) — section « Quotas et rate limiting » non implémentés.
- Roadmap ex-0.3.0 : section 1.3, 5, 7.6.

---

## Scanner aussi le backend (domaine distinct)

> **Contexte :** Aujourd’hui, un scan cible une seule URL (ex. `https://www.example.com/`). Les vérifications dérivent des URLs à partir de cette base (ex. `/api/`, `/user/`). Si le backend est sur un **autre domaine** (ex. `https://api.example.com`), il n’est pas testé.

### Objectif

Permettre de tester explicitement le backend (et éventuellement d’autres cibles) pour CORS, headers, fuites, etc., lorsque frontend et backend sont sur des domaines différents.

### Workaround actuel

En attendant : l’utilisateur peut lancer **deux scans** — un sur l’URL du frontend (ex. `https://www.example.com`) et un sur l’URL du backend (ex. `https://api.example.com`) — pour couvrir CORS, méthodes HTTP, redirections, headers, etc. sur chaque cible. Les résultats sont consultés séparément.

### Pistes

- [ ] **Option 1 — URL secondaire :** L’utilisateur saisit une URL « backend » (ou « API ») en plus de l’URL principale. Le scan exécute les vérifications applicables sur les deux cibles (ex. CORS, security headers, information disclosure sur l’API).
- [ ] **Option 2 — Découverte :** Tenter de découvrir l’URL de l’API à partir de la page (scripts, config JS, liens) puis la scanner automatiquement. Plus complexe et fragile.
- [ ] **Option 3 — Scan multi-URL :** Généraliser le scan à une liste d’URLs (saisie manuelle ou import), avec agrégation des résultats par cible.

### Vérifications concernées

- **CORS / cross-origin** : aujourd’hui, si l’API est sur `api.example.com`, un scan de `www.example.com` ne probe pas l’API. Il faudrait pouvoir scanner `api.example.com` pour les findings CORS (ACAO *, réflexion, CORP, etc.).
- **Security headers, information disclosure, cache, etc. :** idem — toute vérification basée sur la réponse HTTP gagnerait à pouvoir cibler l’URL du backend lorsque celle-ci est distincte.

### Référence

Discussion : frontend et backend sur des IP/domaines différents ; besoin de « tester aussi le backend » pour CORS et autres points.

---

## Méthodes HTTP et redirections (ex-roadmap 5.5)

> **Contexte :** Section retirée du scope MVP 0.2.0 (roadmap §5.5). À implémenter comme **nouvelle étape** du scanner (module dédié, catégorie dans les résultats). Référence fonctionnelle : [docs/verifications/methodes-http-et-redirections.md](verifications/methodes-http-et-redirections.md).

### Objectif

Nouvelle étape de scan : vérifier les **méthodes HTTP** exposées (OPTIONS, TRACE, PUT/DELETE/PATCH, HEAD) et les **redirections** (open redirect, chaînes excessives, 301/302 vs 307/308). Les checks portent sur le **serveur cible** (backend de l’URL scannée).

### 5.5.1 Méthodes HTTP

- [ ] Requête `OPTIONS` : lister les méthodes autorisées (en-tête `Allow` ou réponse preflight CORS) — *Info (informatif)*
- [ ] `TRACE` activé → finding (XST, risque fuite cookies/headers) — *Medium à High*
- [ ] `PUT`, `DELETE`, `PATCH` exposés sans nécessité → info — *Info à Low*
- [ ] `HEAD` supporté (bonne pratique) — *Info (recommandation)*

### 5.5.2 Redirections

- [ ] Détection open redirect (paramètre `url`/`redirect`/`next` redirigeant vers domaine externe) — *Medium à High* (intrusif, voir redirections-actives.md)
- [ ] Chaînes de redirection excessives (> 5) — *Info à Low*
- [ ] Redirection HTTP→HTTPS avec code 301/302 (pas 307/308 pour préserver méthode) — *Info*

### Référence

Spécification détaillée et **matrice de sévérité** par vérification : [methodes-http-et-redirections.md](verifications/passive/methodes-http-et-redirections.md). Open redirect (intrusif) : [redirections-actives.md](verifications/intrusive/redirections-actives.md).

---

## APIs et formats (ex-roadmap 5.7)

> **Contexte :** Section retirée du scope MVP 0.2.0 (roadmap §5.7). Vérifications orientées **backend/API** (GraphQL, Swagger, REST, en-têtes de réponse). Référence fonctionnelle : [docs/verifications/apis-et-formats.md](verifications/apis-et-formats.md).

### Objectif

Nouvelle étape de scan : détecter les **APIs exposées** (GraphQL introspection, Swagger/OpenAPI sans auth, listes non paginées) et vérifier les **formats de réponse** (Content-Type, X-Content-Type-Options, compression). Les checks portent sur le serveur cible (backend de l’URL scannée).

### 5.7.1 APIs exposées

- [ ] Détection GraphQL : introspection activée sur `/graphql` ou similaire
- [ ] Swagger/OpenAPI exposé sans auth
- [ ] Endpoints REST retournant des listes non paginées (info)

### 5.7.2 Formats de réponse

- [ ] `Content-Type` incorrect (ex. JSON servi en `text/html`)
- [ ] `X-Content-Type-Options: nosniff` vérifié sur tous les types
- [ ] Compression (gzip/brotli) pour réduire surface

### Référence

Spécification détaillée : [apis-et-formats.md](verifications/apis-et-formats.md).

---

## Vérification avancée des hashes SRI

> **Contexte :** Le scanner passif actuel se contente de détecter les scripts/CSS externes sans attribut `integrity` et de recommander l'usage de SRI. Il ne recalcule pas les hashes ni ne vérifie qu'ils correspondent réellement au contenu servi par le CDN ou le tiers.

### Objectif

Permettre, dans un mode avancé (optionnel), de **vérifier réellement les hashes SRI** pour un sous-ensemble de ressources tierces, en téléchargeant la ressource et en recalculant le hash côté scanner.

### Pistes

- [ ] Ajouter un mode explicite (ex. option avancée dans l'UI) pour activer la vérification des hashes SRI.
- [ ] Parser l'attribut `integrity` (algo + hash(s) en base64) et supporter `sha256`/`sha384`/`sha512`.
- [ ] Télécharger la ressource JS/CSS correspondante (en respectant des limites strictes de taille et de temps).
- [ ] Recalculer le hash avec l'algorithme indiqué et comparer au(x) hash déclarés.
- [ ] En cas de mismatch, générer un finding dédié (SRI mismatch) avec une sévérité élevée, en expliquant clairement le risque (compromission CDN, MITM, corruption).
- [ ] Limiter le nombre de ressources vérifiées par page (ex. 3–5) pour contrôler la charge côté scanner et la latence.

### Références

- [MDN – Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity)
- [OWASP – Subresource Integrity Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Subresource_Integrity_Cheat_Sheet.html)


# Comment fonctionnent les scanners de sécurité existants

Les scanners professionnels ne “devinent” pas le backend interne.
Ils analysent uniquement **la surface d’attaque exposée publiquement**.

---

## 1️⃣ Phase 1 — Discovery (Découverte automatique)

### 🔹 DNS & Sous-domaines

Le scanner commence par :

- Résolution DNS
- Récupération des enregistrements (A, AAAA, CNAME, MX, TXT)
- Détection ASN
- Enumération de sous-domaines
- Analyse historique DNS

Objectif : identifier toutes les surfaces accessibles publiquement.

---

### 🔹 Crawling HTTP

Le scanner :

1. Télécharge la page HTML
2. Parse le DOM
3. Extrait :
   - liens `<a>`
   - `<form>`
   - `<script>`
   - endpoints `/api`
4. Suit les routes internes

Objectif : découvrir les endpoints exposés.

---

### 🔹 Extraction automatique d’API

Recherche de patterns comme :

```
/api
/graphql
/v1
/rest
```

Les endpoints détectés deviennent des cibles de scan.

---

## 2️⃣ Phase 2 — Classification

Le scanner identifie :

- CDN présent ?
- WAF détecté ?
- Backend même domaine ?
- API sur sous-domaine ?
- Serveur web utilisé ?
- Framework détecté ?

Exemples typiques détectés :

- Cloudflare
- Nginx
- Next.js
- AWS

---

## 3️⃣ Phase 3 — Scan de la surface exposée

Important :
Les scanners testent uniquement ce qui est publiquement accessible.

---

### Cas 1 — API même domaine

```
https://example.com/api/...
```

→ Les endpoints sont testés directement.

---

### Cas 2 — API sur sous-domaine

```
https://api.example.com
```

→ Scan séparé.

---

### Cas 3 — Backend privé (non exposé)

→ Non accessible publiquement
→ Non scanné

C’est normal et recommandé en sécurité.

---

## 4️⃣ CDN et Backend caché

Les scanners :

- analysent la couche edge (CDN)
- vérifient si l’origin est exposé
- détectent les mauvaises configurations

Mais ne cherchent pas à contourner un CDN correctement configuré.

---

## 5️⃣ Scan authentifié (optionnel)

Certains outils permettent :

- login automatique
- scan après authentification

Toujours via des URLs publiques.

---

## 6️⃣ Mode interne (Agent)

Pour scanner l’infrastructure interne :

- installation d’un agent
- scan ports internes
- scan services privés
- scan OS et dépendances

Ce n’est plus un scan externe.

---

## 7️⃣ Résumé

Les scanners professionnels :

1. Découvrent automatiquement les endpoints
2. Classifient l’architecture
3. Scannent la surface exposée
4. N’essaient pas d’accéder aux ressources privées
5. Proposent un agent pour le scan interne

---

## Principe clé

Un scanner externe évalue :

> Ce qu’un attaquant Internet peut voir.

Pas l’infrastructure interne protégée.
