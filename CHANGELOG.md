# Changelog

Toutes les modifications notables du projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et le projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [0.1.0] - (en cours)

### Ajouté

#### Backend — Sécurité et fondations

- **Validation URL** : autorisation uniquement `http`/`https`, refus des credentials dans l’URL, ports limités (80/443 par défaut, 1010/1011 pour badssl.com), normalisation (schéma/netloc en minuscules, fragment supprimé)
- **Protection SSRF** : blocage de localhost, 127.0.0.1, ::1, résolution DNS avec timeout 5s, blocage des IP privées (IPv4 et IPv6)
- **Timeouts** : connexion (3s), lecture (10s), durée globale du scan (60s), configurables via `settings.yml`

#### Backend — Tests de posture sécurité

- **TLS / HTTPS** : vérification HTTPS activé, redirection HTTP→HTTPS, validité du certificat (valide/expiré/auto-signé), détection TLS 1.0/1.1
- **Security Headers** : Content-Security-Policy, Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy
- **Cookies** : vérification des flags Secure, HttpOnly, SameSite ; détection des cookies sans Secure sur site HTTPS
- **Exposition fichiers** : tests GET sur `/.env`, `/.git/config`, `/backup.zip`, `/phpinfo.php`, `/admin/`, `/.DS_Store` avec signatures par chemin
- **Directory listing** : tests sur `/uploads/`, `/assets/`, `/static/` avec détection des signatures Apache/Nginx
- **robots.txt** : lecture et parsing des directives Disallow, signalement des routes potentiellement sensibles
- **Tech fingerprinting** : analyse des en-têtes Server, X-Powered-By, X-Generator, X-Drupal-Cache ; heuristiques pour Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal

#### Backend — Modèles et scoring

- **Schéma Finding** : id, category, title, severity, evidence, recommendation, references
- **Schéma ScanResult** : url, timestamp, duration, score, findings[]
- **Système de scoring** : score /100, pondération par catégorie (TLS 25, Headers 25, Cookies 20, Exposure 20, Fingerprinting 10), mapping sévérité (critical/high/medium/low/info), upgrade .git/config et .env → critical

#### Backend — API

- **Endpoint** `POST /scan/api/scan` : lance le scan et retourne le résultat via SSE
- **Gestion des erreurs** : URL invalide (400), site inaccessible / timeout / erreur TLS (503/504/502) avec classification (connection_failed, timeout, tls_error)
- **Logging structuré** : request_id (correlation_id), duration_seconds, nb_findings, status à la fin de chaque scan

#### Frontend

- **Landing** : hero, champ URL, CTA « Scan », disclaimer usage autorisé
- **Page résultats** : score global avec badge (🟢/🟡/🔴), résumé par catégorie, liste des findings triés par sévérité, bloc « How to fix » (recommandations)
- **UX** : loader pendant le scan, états idle/loading/success/error, responsive mobile
- **Gate authentification** : invitation à se connecter après scan si non authentifié ; stockage des résultats en sessionStorage, restauration après connexion
- **Favicon** : affichage du favicon du site scanné (Google Favicon API), fallback icône globe SVG

#### Infrastructure

- **Gateway** : route publique `POST /scan/api/scan` pour le scanner MVP
- **Documentation** : docs de vérifications (TLS/HTTPS, exposition fichiers, robots.txt, etc.)

### Limites connues (MVP 0.1.0)

- Pas de rate limiting sur l’endpoint de scan
- Pas de login requis pour lancer un scan (disclaimer côté front)
- Résumé « TLS posture » non implémenté
- Blocage des redirections vers IP privées non appliqué (à venir)
- Pas de tests CI exécutés (lint uniquement)

---

[0.1.0]: https://github.com/pierreglerant/secureops/releases/tag/v0.1.0
