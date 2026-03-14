# Architecture et mutualisation — Tests intrusifs

Ce document décrit les composants techniques mutualisables pour réduire la redondance et assurer la cohérence entre les tests actifs du Scanner 2.

---

## Vue d'ensemble

Certaines familles de tests partagent des besoins techniques communs. Concevoir des composants réutilisables dès le départ réduit la dette technique et accélère l'implémentation des nouveaux tests.

---

## 1. Moteur d'extraction de paramètres

### Portée

Tests concernés : **paramètres réfléchis**, **injection SQL**, **NoSQLi**, **path traversal**, **LFI/RFI**, **command injection**, **mass assignment**.

### Fonctionnalités

| Capacité | Description | Consommateurs |
|----------|-------------|---------------|
| Extraction query | Récupérer `?param=value` depuis l'URL | Tous les tests paramètres |
| Extraction body | Query string, JSON, form-urlencoded, multipart | NoSQLi, mass assignment, upload |
| Extraction headers | Cookies, headers personnalisés | CORS, Host, auth |
| Liste paramètres courants | `q`, `search`, `query`, `id`, `page`, `file`, `path`, `document`, `template`, `include`, `redirect`, `url`, `next` | Par catégorie de test |
| Contexte de sortie | HTML, attribut, script inline, JSON | Paramètres réfléchis, XSS |

### Interface proposée

```
extract_parameters(response, scope: "query"|"body"|"headers") -> List[Param]
get_common_params(category: "injection"|"file"|"redirect") -> List[str]
```

---

## 2. Client HTTP enrichi

### Portée

Tests concernés : **méthodes HTTP**, **CORS**, **Host header injection**, **open redirect**, **request smuggling**.

### Fonctionnalités

| Capacité | Description | Consommateurs |
|----------|-------------|---------------|
| Envoi requêtes | Méthodes GET, POST, OPTIONS, TRACE, HEAD, etc. | Méthodes HTTP |
| Headers personnalisables | Origin, Host, X-Forwarded-Host, etc. | CORS, Host injection |
| Suivi redirections | Limité, configurable, détection domaine final | Open redirect |
| Lecture headers réponse | Access-Control-*, Location, Allow | CORS, redirect, OPTIONS |
| Gestion session | Cookies, tokens, isolation par test | Auth, CSRF, IDOR |

### Interface proposée

```
request(method, url, headers?, body?, follow_redirects?, max_redirects?)
get_response_headers(response) -> Map
is_external_redirect(location, original_host) -> bool
```

---

## 3. Module redirections unifié

### Portée

Tests concernés : **open redirect** (redirections-actives), **OAuth/OIDC** (`redirect_uri` dans oauth-oidc-misuse).

### Fonctionnalités

| Capacité | Description | Consommateurs |
|----------|-------------|---------------|
| Paramètres cibles | `redirect`, `url`, `next`, `return`, `redirect_uri`, `returnUrl`, `continue`, `destination` | Open redirect générique |
| Payloads | `https://evil.test`, `//evil.test`, encodages URL | Open redirect |
| Contexte OAuth | Flow spécifique, validation `redirect_uri` vs allowlist | OAuth/OIDC |
| Détection | Location externe, domaine final après suivi | Les deux |

### Architecture

- **Module générique** : injection payload redirection dans paramètres courants, détection domaine externe.
- **Module OAuth** : utilise le module générique pour `redirect_uri` dans le flux d'autorisation ; ajoute vérifications `state`, PKCE, relay state.

```
redirect_module.inject_and_check(url, params) -> Finding?
oauth_module.check_redirect_uri(auth_url, callback) -> Finding?
```

---

## 4. Moteur de payloads et mutations

### Portée

Tests concernés : **SQLi**, **NoSQLi**, **SSTI**, **XXE**, **command injection**, **path traversal**.

### Fonctionnalités

| Capacité | Description | Consommateurs |
|----------|-------------|---------------|
| Payloads par catégorie | SQL, NoSQL, template, XML, shell, path | Chaque famille |
| Mutations | Case, encodages (URL, double URL, Unicode), wrappers | Tous |
| Payload ID unique | Traçabilité de la réflexion | Paramètres réfléchis, injections |
| Budget par paramètre | Limite requêtes (ex. 1–2 pour path traversal) | Tous |

### Interface proposée

```
get_payloads(category, encoding?) -> List[Payload]
mutate(payload, strategy) -> Payload
trace_reflection(param, payload_id, response) -> bool
```

---

## 5. Détection par signatures

### Portée

Tests concernés : **injection SQL**, **NoSQLi**, **SSTI**, **XXE**, **command injection**, **path traversal**, **LFI/RFI**.

### Fonctionnalités

| Capacité | Description | Consommateurs |
|----------|-------------|---------------|
| Signatures regex | Erreurs SQL, stack traces, messages parser | SQLi, command injection |
| Signatures NoSQL | Structure JSON, opérateurs MongoDB | NoSQLi |
| Signatures template | Erreurs Jinja, Twig, etc. | SSTI |
| Signatures XXE | DOCTYPE, entity | XXE |
| Détection temporelle | Délai (time-based SQLi) avec seuil et bruit | SQLi time-based |
| Diff baseline/probe | Comparaison réponse normale vs payload | Injections |

---

## 6. Matrice de priorisation d'implémentation

| Composant | Priorité | Tests débloqués |
|-----------|----------|-----------------|
| Client HTTP enrichi | Haute | Méthodes HTTP, CORS, redirect, Host |
| Moteur paramètres | Haute | Réflexion, SQLi, path traversal, NoSQLi |
| Module redirections | Moyenne | Open redirect, OAuth |
| Moteur payloads | Moyenne | Toutes les injections |
| Détection signatures | Moyenne | SQLi, NoSQLi, SSTI, XXE |

---

## Références

- [Catalogue complet](catalogue-complet-tests-intrusifs.md)
- [Roadmap MVP 0.4.0](../../roadmaps/versions/ROADMAP-MVP-0.4.0.md) — sections 3.17, 3.18
