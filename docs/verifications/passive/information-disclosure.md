# Vérifications Information disclosure (fuites d’information)

Ce document décrit les vérifications relatives aux **fuites d’information** dans les réponses HTTP et les en-têtes de débogage : objectif, risques, exemples et recommandations. Ces tests sont **passifs** (lecture et analyse uniquement).

**Implémentation :** module `app/services/information_disclosure/checks.py`, étape `information_disclosure` dans la pipeline de scan (stream + runner). Le corps de la réponse est tronqué à une taille maximale configurable dans `config/settings.yml` (`information_disclosure.max_body_bytes`, défaut 1 Mo). Findings normalisés avec slugs `info-disclosure-*` et catalogue de recommandations (FR/EN) dans `app/catalogue/recommendations.json`.

---

## Contexte et méthodologie

### Objectif

Les applications en production peuvent exposer accidentellement des informations sensibles : stack traces, messages d’erreur détaillés, tokens, versions de logiciels. Ces fuites facilitent la reconnaissance par un attaquant et peuvent révéler des vulnérabilités exploitables. Le scan analyse le **corps des réponses** et les **en-têtes HTTP** pour détecter ces patterns.

### Principe (passif)

Aucune injection, aucun fuzzing. Le scan se contente de lire les réponses normales et d’analyser leur contenu. Les patterns recherchés sont des indicateurs de mode debug ou de mauvaise configuration.

---

## 1. Fuites dans les réponses (body)

### 1.1 Détection de stack traces

#### Résumé

Détecter les **stack traces** (traces d’exécution) dans le corps des réponses HTTP. Les frameworks (PHP, Python, Java, .NET, Node.js) affichent parfois des traces complètes en cas d’erreur, révélant la structure du code, les chemins de fichiers, les versions et parfois des données sensibles.

#### Explication détaillée

Une stack trace typique contient : noms de fichiers, numéros de lignes, noms de fonctions, parfois des variables. En production, ces informations ne doivent jamais être exposées. Le scan recherche des motifs caractéristiques :

| Langage / Framework | Motifs typiques |
|---------------------|-----------------|
| PHP | `Fatal error`, `Stack trace:`, `#0`, `in /var/www/` |
| Python | `Traceback (most recent call last):`, `File "`, `line ` |
| Java | `java.lang.`, `at com.`, `Exception in thread` |
| .NET | `at System.`, `StackTrace:`, `in :line` |
| Node.js | `Error:`, `at Object.`, `at Module.` |

#### Exemple

- **OK** : Réponse 200 avec page HTML normale, pas de motif de stack trace.
- **Finding** : Réponse 500 avec corps contenant `Traceback (most recent call last):` et chemins de fichiers → fuite d’information.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les environnements de production mal configurés ou les erreurs non gérées peuvent exposer des traces.
- **Impact** : Significative à importante. Révélation de la structure du code, des chemins, des versions ; aide au ciblage d’exploits.

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

#### Conseils

- Désactiver le mode debug en production ; configurer les frameworks pour ne pas afficher les stack traces.
- Utiliser des pages d’erreur génériques pour les utilisateurs ; logger les traces côté serveur uniquement.
- Vérifier les variables d’environnement (DEBUG, NODE_ENV, etc.) avant déploiement.

#### Références

- [OWASP – Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)
- [CWE-209 – Generation of Error Message Containing Sensitive Information](https://cwe.mitre.org/data/definitions/209.html)

---

### 1.2 Détection de messages d’erreur debug (mode dev)

#### Résumé

Détecter les **messages d’erreur en mode développement** : formulations comme « Debug mode », « Development server », « Django DEBUG = True », ou messages explicites invitant à désactiver le mode debug en production.

#### Explication détaillée

Les frameworks ont souvent un mode « debug » ou « development » qui affiche des erreurs détaillées. En production, ce mode doit être désactivé. Le scan recherche des chaînes indicatives dans le body ou les headers.

#### Exemple

- **Finding** : Corps contenant `Django DEBUG = True` ou `FLASK_DEBUG=1` ou `Development server` → mode debug activé en production.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les oublis de configuration en production sont fréquents.
- **Impact** : Significative à importante. Exposition d’informations détaillées, chemins, variables ; facilitation des attaques.

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

#### Conseils

- Désactiver explicitement le mode debug en production (DEBUG=False, NODE_ENV=production, etc.).
- Ne jamais exposer de pages de diagnostic ou de profiler sur l’internet public.

#### Références

- [OWASP – Error Handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)

---

### 1.3 Patterns sensibles : mots de passe, tokens, clés API

#### Résumé

Rechercher des **patterns sensibles** dans le HTML ou JSON : mots de passe, tokens, clés API, secrets. Les expressions régulières peuvent cibler des formats connus (ex. `api_key=`, `password=`, `Bearer `, patterns de tokens JWT, clés AWS).

#### Explication détaillée

Des secrets peuvent fuiter dans le HTML (commentaires, attributs `data-*`, JavaScript inline) ou dans des réponses JSON. Le scan doit être prudent pour éviter les faux positifs (ex. placeholders, exemples). Les patterns doivent être spécifiques et éviter de matcher du contenu public (ex. « password » dans un formulaire de login).

#### Exemple

- **Finding** : Corps contenant `"api_key":"sk_live_xxxx"` ou `DATABASE_PASSWORD=secret123` → fuite de secret.

#### Vulnérabilité et impact

- **Vraisemblance** : Faible à moyenne. Les fuites de secrets sont souvent dues à des oublis ou des configurations par défaut.
- **Impact** : Critique. Fuite de credentials permettant une prise de contrôle ou un accès non autorisé.

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
<td style="border: 2px solid #1f2937; height: 56px; min-height: 56px; background-color:#ef4444; min-width:60px; padding:12px; text-align:center; vertical-align:middle; color:#000"><strong>✗</strong></td>
</tr>
</tbody>
</table>

**Légende :** Vert = faible | Jaune = modéré | Orange = élevé | Rouge = critique

**Risque global : critique.**

#### Conseils

- Ne jamais hardcoder de secrets dans le code ou les templates.
- Utiliser des variables d’environnement ou un secret manager ; exclure les fichiers de config sensibles du déploiement.
- Auditer régulièrement le code et les réponses pour détecter les fuites.

#### Références

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [CWE-798 – Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)

---

### 1.4 Headers révélant des infos (X-AspNet-Version, X-Powered-By avec version)

#### Résumé

Les en-têtes **`X-AspNet-Version`**, **`X-Powered-By`** (avec version complète), **`X-Runtime`** peuvent révéler des informations sur la stack. Une version précise permet de rechercher des CVE.

#### Explication détaillée

Voir aussi [tech-fingerprinting.md](tech-fingerprinting.md). Ces headers sont souvent présents par défaut et exposent des versions exactes. Le scan les signale comme fuite d’information (info ou low selon le contexte).

#### Vulnérabilité et impact

- **Vraisemblance** : Très forte. Ces en-têtes sont présents par défaut sur de nombreux déploiements.
- **Impact** : Faible à significative. Révélation de versions facilite le ciblage d’exploits connus (CVE).

#### Conseils

- Masquer ou supprimer les en-têtes révélateurs (X-Powered-By, X-AspNet-Version, etc.).
- Ne pas exposer de versions précises dans les réponses.

#### Références

- [OWASP – Information Exposure](https://owasp.org/www-community/attacks/Information_exposure_through_query_strings_in_url)

---

## 2. Headers de débogage

### 2.1 X-Debug, X-Debug-Token, X-Runtime

#### Résumé

Détecter les en-têtes de **débogage** : `X-Debug`, `X-Debug-Token`, `X-Runtime`. Ils indiquent que des outils de debug (ex. Symfony Profiler, Laravel Telescope) sont actifs ou que le serveur expose des métriques d’exécution.

#### Explication détaillée

- **X-Debug** : souvent lié à PHP Xdebug.
- **X-Debug-Token** : token pour accéder au profiler (Symfony).
- **X-Runtime** : temps d’exécution de la requête (Rails, etc.) — peut révéler des informations sur les performances et la stack.

Ces headers ne devraient pas être présents en production sur un site public.

#### Exemple

- **OK** : Aucun de ces headers dans la réponse.
- **Finding** : `X-Debug-Token: abc123` présent → profiler potentiellement accessible.

#### Vulnérabilité et impact

- **Vraisemblance** : Moyenne. Les environnements mal configurés ou les oublis de désactivation sont fréquents.
- **Impact** : Significative. Accès possible au profiler, révélation de la structure des requêtes, chemins, requêtes SQL.

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

- Désactiver les outils de debug (Symfony Profiler, Xdebug, etc.) en production.
- Ne pas exposer les en-têtes X-Debug, X-Debug-Token, X-Runtime sur les sites publics.

#### Références

- [Symfony – Profiler](https://symfony.com/doc/current/profiler.html)
- [CWE-489 – Active Debug Code](https://cwe.mitre.org/data/definitions/489.html)

---

### 2.2 Server avec version complète

#### Résumé

L’en-tête **`Server`** avec une **version complète** (ex. `Apache/2.4.41`) facilite le ciblage d’exploits. Recommandation : masquer ou simplifier (ex. `Apache` sans version).

#### Explication détaillée

Voir [tech-fingerprinting.md](tech-fingerprinting.md). Le scan peut extraire la version et la signaler ; une alerte plus forte si une CVE connue est associée.

#### Conseils

- Masquer ou simplifier l’en-tête Server (server_tokens off pour Nginx, ServerTokens Prod pour Apache).

#### Références

- [OWASP – Security Misconfiguration](https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration)

---

### 2.3 Headers custom révélant la stack

#### Résumé

D’autres headers custom peuvent révéler la stack : **`X-Generator`**, **`X-Powered-By`**, **`X-Version`**, etc. Le scan les recense et les signale.

#### Conseils

- Désactiver ou masquer les en-têtes révélateurs dans la configuration du framework ou du serveur.

#### Références

- [OWASP – Fingerprinting](https://owasp.org/www-community/controls/Fingerprinting)

---

### 2.4 Balise meta generator (HTML)

#### Résumé

La balise **`<meta name="generator" content="WordPress 6.4.2">`** (ou équivalent Drupal, Joomla, etc.) expose le CMS et sa version. Les frameworks l'ajoutent souvent par défaut. Le scan la détecte dans le corps HTML et signale une fuite d'information (sévérité info).

#### Explication détaillée

Voir [tech-fingerprinting.md](tech-fingerprinting.md) pour l'usage du meta generator dans le fingerprinting. Le module *information disclosure* signale sa présence comme divulgation d'information, indépendamment du check de version vulnérable.

#### Exemple

- **Finding** : Corps HTML contenant `<meta name="generator" content="WordPress 6.4.2">` → révélation de la stack et de la version.

#### Vulnérabilité et impact

- **Vraisemblance** : Très forte. Beaucoup de CMS ajoutent cette balise par défaut.
- **Impact** : Faible. Facilité de reconnaissance et de ciblage d'exploits connus.

#### Conseils

- Retirer ou généraliser la balise meta generator en production (plugin, configuration, ou templating).
- Ne pas exposer de versions précises dans les réponses HTML.

#### Références

- [OWASP – Fingerprinting](https://owasp.org/www-community/controls/Fingerprinting)
- [MDN – meta name](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta/name)

---

## Matrice de sévérité (synthèse)

| Type de fuite | Sévérité typique |
|---------------|------------------|
| Stack trace complète | High |
| Mode debug activé | Medium à High |
| Secret / token / clé API | Critical |
| Headers de débogage (X-Debug-Token, etc.) | Medium |
| Version précise dans headers | Low à Medium |
| Meta generator (HTML) | Info |

---

## Références générales

- [OWASP – Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [CWE-200 – Exposure of Sensitive Information](https://cwe.mitre.org/data/definitions/200.html)
