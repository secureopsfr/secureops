# Vérifications Intégrité et sous-ressources

Ce document décrit les vérifications relatives à l’**intégrité des ressources** (SRI – Subresource Integrity), à l’**analyse du HTML** (formulaires, liens, meta) et aux bonnes pratiques : objectif, risques, exemples et recommandations.

---

## Contexte et méthodologie

### Objectif

Les ressources chargées depuis des CDN ou des domaines tiers (scripts, CSS) peuvent être **modifiées** (compromission du CDN, MITM). L’attribut **`integrity`** (SRI) permet de vérifier que le contenu n’a pas été altéré. Par ailleurs, l’analyse du HTML peut révéler des configurations à risque : formulaires sans `autocomplete="off"` sur les champs sensibles, formulaires POST sans champ CSRF, liens `target="_blank"` sans `rel="noopener noreferrer"`, meta robots absente sur pages sensibles, etc.

Le scan parse le HTML de la page et analyse les balises `<script>`, `<link>`, `<form>`, `<a>`, `<meta>`.

**Métadonnées meta :** deux modules couvrent les balises meta :
- **Meta robots** : ce module (intégrité) vérifie la présence de `<meta name="robots">` et de la directive `noindex` sur les pages sensibles (login, admin, API).
- **Meta generator** : le module [information-disclosure](information-disclosure.md) signale `<meta name="generator">` comme fuite d’information (CMS/version exposés) ; le module [tech-fingerprinting](tech-fingerprinting.md) l’utilise pour le fingerprinting et la détection de versions vulnérables.

---

## 1. Subresource Integrity (SRI)

### 1.1 Scripts/CSS externes sans attribut integrity

#### Résumé

Les **scripts** et **feuilles de style** chargés depuis des **domaines externes** (CDN, tiers) devraient avoir l’attribut **`integrity`** (SRI). Sans SRI, une compromission du CDN ou une attaque MITM peut injecter du code malveillant. Le scan détecte les balises `<script src="https://...">` et `<link href="https://...">` sans attribut `integrity`.

#### Explication détaillée

L’attribut `integrity` contient un hash (ex. `sha384-xxx`) du contenu attendu. Le navigateur vérifie que le contenu téléchargé correspond au hash avant de l’exécuter. Pour les ressources tierces, c’est une protection essentielle.

Exemple correct :

```html
<script src="https://cdn.example.com/script.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
        crossorigin="anonymous"></script>
```

#### Exemple

- **OK** : Script externe avec `integrity="sha384-..."` et `crossorigin="anonymous"`.
- **Finding** : Script externe avec `src="https://cdn.example.com/lib.js"` sans `integrity` → risque d’exécution de code modifié.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les CDN sont rarement compromis, mais le risque existe (supply chain, MITM sur réseau non sécurisé).
- **Impact** : Importante. Exécution de JavaScript malveillant, vol de session, XSS.

#### Matrice gravité / vraisemblance

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré à élevé.**

#### Conseils

- Utiliser SRI pour toutes les ressources externes (scripts, CSS).
- Générer les hashes avec `openssl dgst -sha384 -binary script.js | openssl base64 -A`.
- Mettre à jour le hash lors de chaque mise à jour de la ressource.

#### Références

- [MDN – Subresource Integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity)
- [OWASP – SRI](https://cheatsheetseries.owasp.org/cheatsheets/Subresource_Integrity_Cheat_Sheet.html)
- [CWE-353 – Missing Support for Integrity Check](https://cwe.mitre.org/data/definitions/353.html)

---

### 1.2 Recommandation : utiliser SRI pour ressources tierces

#### Résumé

Même si le scan ne détecte pas de ressource externe sans SRI, la **recommandation** peut être ajoutée au rapport : « Pour les ressources chargées depuis des CDN ou des tiers, utiliser l’attribut `integrity` pour garantir l’intégrité. »

#### Références

- [OWASP – Subresource Integrity Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Subresource_Integrity_Cheat_Sheet.html)

---

## 2. Analyse du HTML

### 2.1 Balises script sans nonce ou integrity (contexte CSP)

#### Résumé

Dans le contexte d’une **CSP stricte**, les scripts inline doivent utiliser un **nonce** ou un **hash** pour être autorisés. Les balises `<script>` sans `nonce` ni `integrity` (pour le inline) peuvent indiquer une CSP qui autorise `unsafe-inline`, ce qui affaiblit la protection. Le scan analyse cette cohérence **uniquement lorsque l’en-tête CSP est présent** : si aucune **Content-Security-Policy** n’est définie, les tests avancés sur les scripts inline (nonces/hashes) **ne sont pas appliqués** et cela est indiqué explicitement dans les résultats.

#### Explication détaillée

Une CSP avec `script-src 'nonce-xxx'` exige que chaque script inline ait `nonce="xxx"`. Si des scripts inline n’ont pas de nonce, soit la CSP n’est pas appliquée, soit elle utilise `unsafe-inline`. Le scan peut signaler cette incohérence.

#### Conseils

- Utiliser des nonces ou des hashes pour les scripts inline ; éviter `unsafe-inline` dans la CSP.

#### Références

- [MDN – CSP nonce](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src#nonce)

---

### 2.2 Formulaires sans autocomplete="off" sur champs sensibles

#### Résumé

Les champs **password** et autres champs sensibles (numéro de carte, code secret) devraient avoir **`autocomplete="off"`** ou **`autocomplete="new-password"`** (pour les champs de nouveau mot de passe) pour éviter que le navigateur ne propose des valeurs stockées ou ne les enregistre incorrectement.

#### Explication détaillée

Sans `autocomplete="off"` sur un champ password, le navigateur peut :
- Proposer des mots de passe sauvegardés (risque sur poste partagé).
- Enregistrer le mot de passe (peut être indésirable pour certains types de champs).

Pour les formulaires de login et de changement de mot de passe, `autocomplete` doit être configuré correctement.

#### Exemple

- **OK** : `<input type="password" name="password" autocomplete="current-password">` (login) ou `autocomplete="new-password"` (création).
- **Finding** : `<input type="password">` sans `autocomplete` sur un formulaire de paiement → risque de stockage non désiré.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les navigateurs gèrent de plus en plus `autocomplete` ; l’impact dépend du contexte.
- **Impact** : Faible à significative. Fuite de credentials sur poste partagé, stockage mal configuré.

#### Conseils

- Utiliser `autocomplete="current-password"` pour les champs de login, `autocomplete="new-password"` pour la création de mot de passe.

#### Références

- [OWASP – Autocomplete](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [MDN – autocomplete](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete)

---

### 2.3 target="_blank" sans rel="noopener noreferrer"

#### Résumé

Les liens avec **`target="_blank"`** ouvrent une nouvelle fenêtre. Sans **`rel="noopener noreferrer"`**, la page ouverte peut accéder à `window.opener` et potentiellement rediriger la page d’origine (tabnabbing). `noopener` supprime l’accès à `opener` ; `noreferrer` supprime aussi l’en-tête Referer.

#### Explication détaillée

Une attaque « tabnabbing » : l’utilisateur clique sur un lien qui ouvre un site malveillant dans un nouvel onglet ; ce site peut rediriger l’onglet d’origine vers une page de phishing. Avec `rel="noopener noreferrer"`, la nouvelle page n’a pas accès à l’opener.

#### Exemple

- **OK** : `<a href="https://external.com" target="_blank" rel="noopener noreferrer">Lien</a>`.
- **Finding** : `<a href="https://external.com" target="_blank">Lien</a>` sans `rel` → risque de tabnabbing.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. L’exploitation nécessite d’ouvrir un lien vers un site malveillant.
- **Impact** : Significative. Tabnabbing, phishing, redirection de l’onglet d’origine.

#### Matrice gravité / vraisemblance

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#f97316; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
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

**Risque global : modéré.**

#### Conseils

- Toujours ajouter `rel="noopener noreferrer"` aux liens `target="_blank"`.
- Ou utiliser `rel="noopener"` seul (noreferrer est optionnel pour la sécurité, mais utile pour la confidentialité).

#### Références

- [OWASP – Tabnabbing](https://owasp.org/www-community/attacks/Reverse_Tabnabbing)
- [MDN – rel](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel)

---

### 2.4 Formulaires POST sans champ CSRF

#### Résumé

Les formulaires **POST** qui modifient des données côté serveur devraient inclure un champ de token CSRF (ex. `csrf_token`, `_token`, `authenticity_token`) pour se protéger contre les attaques Cross-Site Request Forgery. Le scan détecte les formulaires `<form method="post">` qui ne contiennent aucun champ hidden dont le nom figure dans la liste configurée (`integrity.csrf_field_names` dans `settings.yml`).

#### Explication détaillée

Sans token CSRF, un site tiers peut créer une page qui soumet un formulaire à l'insu de l'utilisateur (requête forgée). Le scan parse le HTML et vérifie que chaque formulaire POST contient au moins un champ hidden avec un nom reconnu comme token CSRF. La liste des noms est configurable.

#### Exemple

- **OK** : `<form method="post">` avec `<input type="hidden" name="csrf_token" value="...">`.
- **Finding** : formulaire POST sans champ csrf_token, _token ou équivalent → risque CSRF.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les formulaires sans CSRF sont encore fréquents sur des applications legacy.
- **Impact** : Significative. Actions non autorisées (changement d'email, de mot de passe, etc.) déclenchées depuis un site tiers.

#### Conseils

- Ajouter un champ hidden avec token CSRF dans chaque formulaire POST.
- Valider le token côté serveur à chaque soumission.
- Configurer la liste des noms de champs CSRF dans `integrity.csrf_field_names` si le framework utilise un nom personnalisé.

#### Références

- [OWASP – CSRF](https://owasp.org/www-community/attacks/csrf)
- [OWASP – Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

---

### 2.5 Meta robots (noindex sur pages sensibles)

#### Résumé

Les pages **sensibles** (login, admin, erreurs) ne devraient pas être indexées par les moteurs de recherche. La balise **`<meta name="robots" content="noindex, nofollow">`** empêche l’indexation. Le scan peut vérifier sa présence sur les pages identifiées comme sensibles.

#### Explication détaillée

Sans `noindex`, une page de login ou d’erreur peut être indexée et apparaître dans les résultats de recherche, exposant des informations ou des chemins. Pour les pages sensibles, `noindex, nofollow` est recommandé.

#### Exemple

- **OK** : Page login avec `<meta name="robots" content="noindex, nofollow">`.
- **Finding** : Page login sans meta robots → risque d’indexation.

#### Vulnérabilité et impact

- **Vraisemblance** : Forte. Les pages sensibles sans noindex sont souvent indexées par défaut.
- **Impact** : Faible à moyenne. Fuite d’information via l’indexation, révélation de chemins sensibles.

#### Conseils

- Ajouter `<meta name="robots" content="noindex, nofollow">` sur les pages de login, admin et d’erreur.

#### Références

- [MDN – meta robots](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta/name)
- [Google – robots meta tag](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)

---

## Matrice de sévérité (synthèse)

| Vérification | Sévérité typique |
|--------------|------------------|
| Scripts/CSS externes sans SRI | Medium à High |
| Formulaires sans autocomplete sur champs sensibles | Low à Medium |
| target="_blank" sans noopener noreferrer | Medium |
| Formulaires POST sans champ CSRF | Low |
| Pages sensibles sans noindex | Low à Info |

---

## Références générales

- [OWASP – Subresource Integrity Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Subresource_Integrity_Cheat_Sheet.html)
- [OWASP – HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
