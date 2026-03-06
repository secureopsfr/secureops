# Vérifications Directory listing

Ce document décrit la vérification du **directory listing** (affichage du contenu des répertoires) : objectif, répertoires testés, signatures de détection Apache/Nginx et gravité.

---

## Contexte et méthodologie

### Qu’est-ce que le directory listing ?

Le **directory listing** (ou « index de répertoire ») est une fonctionnalité des serveurs web (Apache, Nginx, etc.) qui affiche la liste des fichiers et sous-dossiers d’un répertoire lorsqu’aucun fichier d’index (ex. `index.html`) n’est trouvé. Au lieu de renvoyer une erreur 403 ou une page personnalisée, le serveur génère une page HTML listant le contenu du répertoire avec des liens cliquables.

Cette fonctionnalité est utile en développement ou pour des répertoires publics (ex. miroirs de paquets), mais elle ne doit **pas** être activée sur des chemins contenant des données sensibles ou révélant la structure interne de l’application.

### Objectif du scan

Le scan teste une liste de répertoires usuels et détecte si le serveur renvoie une page de listing (signatures Apache/Nginx). Si oui, un attaquant peut énumérer les fichiers, découvrir des ressources non prévues pour l’accès public, et potentiellement accéder à des fichiers sensibles (uploads, backups, configs).

### Méthode de détection

Pour chaque répertoire de la liste MVP, le scan effectue une requête **GET** et analyse la réponse :

1. **Statut HTTP 200** : le répertoire est accessible.
2. **Signature de listing** : le corps de la réponse contient des motifs caractéristiques des pages d’index générées par Apache ou Nginx (voir section suivante).

Si les deux conditions sont remplies → **finding**.

### Signatures Apache / Nginx

Les serveurs web génèrent des pages HTML structurées pour l’affichage du listing. Le scan recherche les motifs suivants :

| Serveur | Signatures typiques |
|---------|---------------------|
| **Apache** | `Index of`, `Parent Directory`, `[DIR]`, `<title>Index of`, `mod_autoindex` |
| **Nginx** | `Index of`, `nginx`, `<a href="`, liens vers fichiers avec noms visibles |

Exemples de contenu caractéristique :

```
Apache : <title>Index of /uploads/</title>
         <h1>Index of /uploads/</h1>
         <a href="?C=N;O=D">Name</a>

Nginx  : <title>Index of /static/</title>
         <hr><pre><a href="file.txt">file.txt</a>
```

Une page 200 avec une application (SPA, page d’accueil) ou une 404 personnalisée ne contient généralement pas ces motifs. Le scan doit exclure les faux positifs (pages qui contiennent accidentellement « Index of » dans du texte).

### Liste des répertoires MVP

| # | Chemin | Sensibilité | Gravité typique |
|---|--------|-------------|-----------------|
| 1 | `/uploads/` | Élevée (fichiers utilisateurs) | Élevée |
| 2 | `/assets/` | Moyenne (structure, noms) | Modérée |
| 3 | `/static/` | Moyenne (structure, noms) | Modérée |

---

## 1. /uploads/

### Résumé

Le répertoire **`/uploads/`** contient souvent les fichiers uploadés par les utilisateurs (images, documents, pièces jointes). Si le directory listing est activé, un attaquant peut voir la liste complète des fichiers, leurs noms et tailles, et accéder directement à des documents qui auraient dû rester privés ou protégés par des contrôles d’accès.

### Explication détaillée

Les applications (CMS, forums, applications métier) stockent fréquemment les uploads dans un répertoire dédié (`/uploads/`, `/media/`, `/files/`). Sans listing, l’accès nécessite de connaître l’URL exacte du fichier. Avec le listing, l’énumération devient triviale. Les noms de fichiers peuvent révéler des informations (ex. `contrat_dupont_2024.pdf`), et des fichiers mal configurés (exécutables, scripts) peuvent être exposés. Le scan envoie `GET /uploads/` et vérifie la présence des signatures de listing.

### Exemple

- **OK** : `GET /uploads/` → 403, 404, ou 200 avec page d’application (pas de listing) → pas d’exposition.
- **Finding** : `GET /uploads/` → 200 avec `<title>Index of /uploads/</title>`, liste de fichiers → listing activé.

### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les répertoires d’upload sont courants et souvent mal sécurisés.
- **Impact** : Importante à majeure. Fuite de documents utilisateurs, énumération de ressources, accès à des fichiers sensibles (contrats, pièces d’identité, etc.).

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead>
<tr>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Gravité \ Vraisemblance</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Forte</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très forte</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Mineure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : modéré à élevé.**

### Conseils

- Désactiver le directory listing pour `/uploads/` et tout répertoire contenant des données utilisateurs.
- Implémenter un contrôle d’accès : les fichiers ne doivent être accessibles que via une URL signée ou après authentification.
- Stocker les uploads hors du document root ou dans un stockage objet (S3) avec des URLs pré-signées.
- Utiliser des noms de fichiers aléatoires (UUID) pour éviter l’énumération par prédiction.

### Références

- [OWASP – Unrestricted File Upload](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [OWASP – Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)

---

## 2. /assets/

### Résumé

Le répertoire **`/assets/`** contient généralement les ressources statiques de l’application (CSS, JavaScript, images, polices). Le directory listing y est moins critique que pour `/uploads/`, mais il révèle la structure du projet, les noms des bundles, et peut faciliter l’analyse de l’application par un attaquant (fingerprinting, recherche de fichiers obsolètes ou vulnérables).

### Explication détaillée

Les frameworks front-end et les outils de build (Webpack, Vite, etc.) produisent souvent des fichiers dans `/assets/` ou `/dist/`. Un listing expose les noms de fichiers (ex. `main.abc123.js`, `vendor.x.js`), ce qui aide à identifier les versions, les dépendances et les chemins internes. Le risque est plus faible que pour les uploads, mais la bonne pratique reste de désactiver le listing. Le scan envoie `GET /assets/` et vérifie les signatures.

### Exemple

- **OK** : `GET /assets/` → 403, 404, ou 200 sans signature de listing → pas d’exposition.
- **Finding** : `GET /assets/` → 200 avec `Index of /assets/`, liste de fichiers `.js`, `.css` → listing activé.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les répertoires d’assets sont courants ; le listing est parfois laissé activé par défaut.
- **Impact** : Significative. Fuite d’informations sur la structure, les versions, les chemins ; facilitation du fingerprinting et de l’analyse de l’application.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead>
<tr>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Gravité \ Vraisemblance</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Forte</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très forte</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Mineure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : faible à modéré.**

### Conseils

- Désactiver le directory listing pour `/assets/` et les répertoires de ressources statiques.
- Les assets publics (CSS, JS, images) sont accessibles par URL directe de toute façon ; le listing n’apporte rien aux utilisateurs légitimes.
- Configurer le serveur pour refuser l’autoindex sur ces chemins.

### Références

- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)
- [Apache – mod_autoindex](https://httpd.apache.org/docs/2.4/mod/mod_autoindex.html)

---

## 3. /static/

### Résumé

Le répertoire **`/static/`** est similaire à `/assets/` : il héberge des fichiers statiques (CSS, JS, images). Le directory listing y pose les mêmes problèmes : révélation de la structure, des noms de fichiers et des versions. Il doit être désactivé en production.

### Explication détaillée

De nombreux frameworks (Django, Flask, Rails, etc.) utilisent un répertoire `/static/` pour les ressources statiques. Comme pour `/assets/`, un listing facilite l’énumération et le fingerprinting. Le scan envoie `GET /static/` et vérifie les signatures Apache/Nginx. La gravité est comparable à `/assets/`.

### Exemple

- **OK** : `GET /static/` → 403, 404, ou 200 sans signature de listing → pas d’exposition.
- **Finding** : `GET /static/` → 200 avec `Index of /static/`, liste de fichiers → listing activé.

### Vulnérabilité et impact

- **Vraisemblance** : Moyenne.
- **Impact** : Significative. Même nature que `/assets/` : fuite d’informations sur la structure et les versions.

### Matrice gravité / vraisemblance

<table style="border-collapse: collapse">
<thead>
<tr>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Gravité \ Vraisemblance</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Faible</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Forte</th>
<th style="border: 2px solid #1f2937; padding: 8px; height: 48px; min-height: 48px">Très forte</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Mineure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Significative</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#22c55e; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Importante</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#facc15; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
<tr>
<td style="border: 2px solid #1f2937; padding: 12px; height: 56px; min-height: 56px"><strong>Majeure</strong></td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px"> </td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : faible à modéré.**

### Conseils

- Désactiver le directory listing pour `/static/`.
- S’assurer que seuls les fichiers nécessaires sont servis ; éviter d’exposer des répertoires de développement ou de build.

### Références

- [Nginx – autoindex](https://nginx.org/en/docs/http/ngx_http_autoindex_module.html)
- [OWASP – Security Misconfiguration](https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration)

---

## Améliorations prévues (v0.2.0)

Les vérifications suivantes seront ajoutées ou étendues dans la version 0.2.0 du scanner :

### Chemins supplémentaires

| Chemin | Sensibilité | Gravité typique |
|--------|-------------|-----------------|
| `/tmp/` | Élevée | Élevée |
| `/logs/` | Élevée | Élevée |
| `/config/` | Élevée | Élevée |
| `/backup/` | Élevée | Élevée |
| `/data/` | Moyenne à élevée | Modérée à élevée |

Ces répertoires contiennent souvent des données sensibles (logs avec IP, configs, sauvegardes). Un listing activé facilite l’énumération et l’accès à des fichiers non prévus pour le public.

### Détection de listing partiel

Certains serveurs ou applications génèrent des pages HTML avec des **liens vers des fichiers** sans utiliser le format standard Apache/Nginx. Le scan peut détecter des réponses HTML contenant des motifs `<a href="...">` pointant vers des fichiers ou sous-dossiers, indiquant une forme de listing (même partiel). Adapter les signatures pour couvrir ces cas.

### Alerte répertoire sensible en 403

Si un répertoire **sensible** (ex. `/admin/`, `/config/`, `/backup/`) retourne **403 Forbidden** au lieu de 404, cela révèle son **existence** : le serveur connaît le chemin et refuse l’accès. Un attaquant peut en déduire la présence de ressources protégées et tenter des contournements (path traversal, bypass). Gravité : Info à Low.
