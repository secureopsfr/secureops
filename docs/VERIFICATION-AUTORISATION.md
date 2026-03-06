# Vérification d’autorisation — Spécification

Ce document décrit la **vérification que l’utilisateur a l’autorisation de scanner un site**. Cette fonctionnalité est **activée uniquement en production**.

---

## Contexte

SecureOps propose **deux scanners** :

| Scanner | Vérification requise |
|---------|----------------------|
| **Scanner 1 (passif)** | Aucune. Fonctionne sur toute URL. |
| **Scanner 2 (actif)** | **Obligatoire.** Ne fonctionne que pour les URLs dont le domaine a été vérifié. |

La vérification DNS prouve que l'utilisateur contrôle le domaine. Elle est **requise uniquement pour le Scanner 2** (tests actifs). Le Scanner 1 (tests passifs uniquement) peut scanner n'importe quelle URL sans vérification.

---

## Méthode : vérification DNS (TXT)

### Principe

L’utilisateur ajoute un enregistrement **TXT** dans la zone DNS du domaine à scanner. Seul le propriétaire ou l’administrateur du domaine peut effectuer cette action. Si l’enregistrement est présent et correct, le scan est autorisé.

Références : Let's Encrypt (HTTP-01, DNS-01), Google Search Console, services de vérification de domaine.

### Enregistrement attendu

| Champ | Valeur |
|-------|--------|
| **Type** | TXT |
| **Nom / Host** | `_secureops-verify` (sous-domaine du domaine à scanner) |
| **Valeur** | Token unique généré par SecureOps (ex. `secureops-verify-abc123xyz`) |

Exemple pour `example.com` :
```
_secureops-verify.example.com.  TXT  "secureops-verify-abc123xyz"
```

---

## Flux technique

### 1. Demande de vérification (Scanner 2)

- L'utilisateur choisit le Scanner 2 (actif) et saisit l'URL à scanner (ex. `https://example.com`)
- Le backend extrait le domaine (`example.com`) et génère un token unique
- Le token est stocké temporairement (ex. Redis, DB) avec `domain`, `user_id`, `created_at`
- Le frontend affiche l’enregistrement DNS à ajouter

### 2. Vérification

- L’utilisateur ajoute l’enregistrement dans son gestionnaire DNS
- Clic sur « Vérifier » → le backend effectue une résolution DNS :
  - Requête TXT sur `_secureops-verify.example.com`
  - Si la valeur retournée correspond au token → succès
- En cas de succès : enregistrement en base (domaine vérifié pour user_id, date d’expiration)

### 3. Scan autorisé (Scanner 2)

- Si le domaine est déjà vérifié (et non expiré), le scan peut démarrer directement
- Sinon, afficher le flux de vérification
- Le Scanner 2 peut inclure les tests passifs en premier (option utilisateur, défaut : oui), puis les tests actifs

---

## Cache et expiration

- **Durée de validité :** 90 jours (configurable)
- **Stockage :** Table `domain_verifications` (user_id, domain, verified_at, expires_at)
- **Ré-vérification :** Après expiration, l’utilisateur doit re-ajouter l’enregistrement DNS (ou le garder en place pour une vérification immédiate)

---

## Environnement

| Environnement | Vérification activée |
|---------------|----------------------|
| **Production** | Oui (si `AUTHORIZATION_CHECK_ENABLED=true`) |
| **Staging** | Optionnel (configurable) |
| **Développement / Local** | Non (pour faciliter les tests) |

Variable d’environnement : `AUTHORIZATION_CHECK_ENABLED` (default: `false` en dev, `true` en prod).

---

## Cas particuliers

### DNS privé / résolution impossible

Si la résolution DNS échoue (timeout, domaine derrière DNS privé, propagation en cours) :

- **Option A :** Fallback sur case à cocher + avertissement renforcé
- **Option B :** Refuser le scan et demander de réessayer plus tard
- À configurer selon la politique de sécurité

### Sous-domaines

- `blog.example.com` → vérifier `_secureops-verify.blog.example.com` OU `_secureops-verify.example.com` (selon politique : le domaine parent peut autoriser tous les sous-domaines)

### API publique

- Les appels avec clé API : le domaine peut être pré-vérifié dans le compte de l’utilisateur
- Ou : acceptation préalable via CGU/documentation (l’utilisateur certifie avoir les droits sur les domaines qu’il scanne)

---

## Modèle de données (proposition)

```sql
CREATE TABLE domain_verifications (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    verified_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, domain)
);
```

---

## Références

- [RFC 1035 – DNS](https://tools.ietf.org/html/rfc1035)
- [Let's Encrypt – DNS-01 challenge](https://letsencrypt.org/docs/challenge-types/#dns-01-challenge)
- [Google Search Console – Vérification de propriété](https://support.google.com/webmasters/answer/9008080)
