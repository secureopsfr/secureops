# Vérifications Sitemap

Ce document décrit la vérification du **sitemap** : présence de la directive `Sitemap:` dans robots.txt, recherche à l'emplacement classique si absent, et analyse du contenu pour détecter des URLs sensibles exposées.

---

## Contexte et méthodologie

### Qu'est-ce qu'un sitemap ?

Un **sitemap** (fichier XML) liste les URLs d'un site que le propriétaire souhaite voir indexées par les moteurs de recherche. Il complète robots.txt en indiquant explicitement quelles pages crawler. Le sitemap peut être :

- **Déclaré** dans robots.txt via la directive `Sitemap: https://example.com/sitemap.xml`
- **Conventionnel** : placé à la racine (`/sitemap.xml`, `/sitemap_index.xml`) même sans déclaration

### Objectif du scan

1. Vérifier la présence de `Sitemap:` dans robots.txt (bonne pratique SEO).
2. Si absent, chercher un sitemap à l'emplacement classique en fallback.
3. Analyser le contenu du sitemap pour détecter des **URLs sensibles** (admin, api, config, etc.) — si présentes, le site les propose explicitement aux crawlers, ce qui est un risque de posture sécurité.

### Méthode de détection

1. **Parsing robots.txt** : extraire les lignes `Sitemap: <URL>`.
2. **Fallback** : si aucune directive Sitemap, requête GET vers `/sitemap.xml`, `/sitemap_index.xml`, `/sitemap-index.xml`.
3. **Analyse du contenu** : parser le XML, extraire les `<loc>`, vérifier si des chemins correspondent à des motifs sensibles.

---

## 1. Vérifier présence de Sitemap: dans robots.txt

### Résumé

Le scan parse le contenu de robots.txt et recherche la directive **`Sitemap:`** suivie d'une URL. Sa présence est une bonne pratique SEO et facilite une indexation maîtrisée.

### Explication détaillée

La directive `Sitemap:` (définie par [sitemaps.org](https://www.sitemaps.org/)) indique aux moteurs où trouver le fichier sitemap. Un site peut en déclarer plusieurs :

```
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-blog.xml
```

- **Présent** : finding Info positif ou absence de finding (bonne pratique respectée).
- **Absent** : finding Info (recommandation) — le scan tentera le fallback à l'emplacement classique.

### Exemple

- **OK** : robots.txt contient `Sitemap: https://example.com/sitemap.xml` → sitemap déclaré.
- **Info** : robots.txt ne contient pas `Sitemap:` → recommandation d'ajouter la directive ; le scan vérifie `/sitemap.xml` en fallback.

---

## 2. Fallback : chercher le sitemap à l'emplacement classique

### Résumé

Si robots.txt ne déclare pas de `Sitemap:`, le scan effectue des requêtes GET vers les emplacements conventionnels pour détecter un sitemap présent mais non déclaré.

### Explication détaillée

De nombreux sites placent leur sitemap à la racine sans le déclarer dans robots.txt. Emplacements testés (dans l'ordre) :

| Chemin | Fréquence |
|--------|-----------|
| `/sitemap.xml` | Très courant |
| `/sitemap_index.xml` | Courant |
| `/sitemap-index.xml` | Courant |
| `/sitemap1.xml`, `/sitemap_1.xml` | Variantes |

- **Trouvé** : le sitemap existe ; si non déclaré dans robots.txt → finding Info (recommandation de déclarer).
- **Non trouvé** : pas de sitemap détecté ; pas de finding critique (certains sites n'en ont pas).

### Exemple

- **OK** : `/sitemap.xml` → 200, contenu XML valide → sitemap présent.
- **Info** : sitemap trouvé à `/sitemap.xml` mais absent de robots.txt → recommandation de déclarer.
- **—** : 404 sur tous les chemins → pas de sitemap ; pas de finding (optionnel : info « aucun sitemap détecté »).

---

## 3. Analyser le contenu du sitemap : URLs sensibles

### Résumé

Le scan parse le sitemap XML, extrait toutes les URLs (`<loc>`), et vérifie si des chemins correspondent à des **motifs sensibles**. Si oui, un finding est généré : le site propose explicitement ces URLs aux crawlers.

### Explication détaillée

Un sitemap liste les URLs que le propriétaire **veut** voir indexées. Si `/admin/`, `/api/`, `/config/` apparaissent dans le sitemap, c'est une **exposition intentionnelle** à l'indexation — contrairement à robots.txt où `Disallow` les cache. C'est un signal de posture sécurité : ces chemins ne devraient pas être dans un sitemap public.

Motifs sensibles (alignés avec robots.txt et exposition fichiers) :

| Motif | Exemples | Gravité suggérée |
|-------|----------|------------------|
| `admin`, `administrator`, `backend` | `/admin/`, `/wp-admin/` | Medium |
| `api` (hors `/api/public/`) | `/api/`, `/api/docs` | Medium |
| `config`, `configs` | `/config/` | Medium |
| `backup`, `backups` | `/backup/` | Medium |
| `login`, `auth`, `signin` | `/login/`, `/auth/` | Low |
| `graphql`, `swagger`, `api-docs` | `/graphql`, `/swagger` | Medium |

### Exemple

- **OK** : sitemap ne contient que des URLs publiques (/, /blog/, /contact/) → pas de finding.
- **Finding (Medium)** : sitemap contient `https://example.com/admin/dashboard` → URL sensible exposée aux crawlers.
- **Finding (Medium)** : sitemap contient `https://example.com/api/docs` → documentation API exposée.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Le sitemap est public ; tout le monde peut le lire.
- **Impact** : Variable. Les URLs sensibles dans le sitemap sont explicitement proposées à l'indexation. Si ces chemins sont protégés par authentification, le risque est limité ; sinon, ils sont découverts et potentiellement indexés.

### Matrice gravité / vraisemblance

| Contexte | Niveau suggéré |
|----------|----------------|
| URL admin/api/config dans sitemap | Medium |
| URL login/auth dans sitemap | Low |
| Aucune URL sensible | — |

### Conseils

- **Exclure** les chemins sensibles du sitemap : admin, api, config, backup, etc.
- **Déclarer** le sitemap dans robots.txt via `Sitemap:`.
- **Protéger** les chemins sensibles par authentification ; le sitemap ne doit pas les lister.

### Références

- [Sitemaps.org](https://www.sitemaps.org/)
- [Google – Sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)
