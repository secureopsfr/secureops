# SecureOps — Roadmap MVP 0.1.0 (étape par étape)

Objectif : livrer un **scanner de posture sécurité web** (non-intrusif) destiné aux devs débutants/intermédiaires :
**URL → scan rapide → score + rapport clair**.

---

## 0) Décisions MVP (à figer avant de coder)

- [ ] **Scope MVP** : scans passifs + tests légers (pas de pentest agressif)
- [ ] **Durée cible** : < 10–20s par scan (à ajuster)
- [ ] **Extensions testées** : TLS/HTTPS, headers, cookies, exposition fichiers, directory listing, robots.txt, fingerprinting
- [ ] **Pas de login / pas d’API publique** (MVP)
- [ ] **Disclaimer** : usage autorisé uniquement

---

## 1) Setup Repo + Gestion Projet (GitHub)

### 1.1 Structure repo (monorepo conseillé)
- [ ] Créer dossiers :
  - `backend/`
  - `frontend/`
  - `infra/`
  - `docs/`
  - `.github/workflows/`

### 1.2 Project board
- [ ] Colonnes : `Backlog` → `Ready` → `In Progress` → `Review` → `Done`
- [ ] Milestone : `MVP v0.1`
- [ ] Labels : utiliser ceux déjà créés (`backend`, `frontend`, `infra`, `aws`, `ci`, `security`, `ux`, etc.)

### 1.3 Fichiers repo
- [ ] `README.md` (setup + run local)
- [ ] `SECURITY.md` (disclosure + disclaimer)
- [ ] `.env.example`
- [ ] `.gitignore`

---

## 2) Backend Foundation (sécurité obligatoire dès le début)

### 2.1 Validation stricte URL (anti-abus) ✅
- [x] Autoriser uniquement `http/https` ✅
- [x] Refuser `user:pass@host` ✅
- [x] Refuser ports non autorisés (MVP: 80/443, option: liste blanche) ✅
- [x] Limiter longueur URL ✅
- [x] Normaliser l’URL ✅

> **Fait :** Implémenté dans le scan-service (`app/utils/url_validator.py`). Endpoint `POST /api/scan` valide l’URL et retourne l’URL normalisée (schéma/netloc en minuscules, fragment supprimé). Tests unitaires (validateur + route) + chargement du `.env` pour pytest.

### 2.2 Protection SSRF (critique) ✅
- [x] Bloquer `localhost`, `127.0.0.1`, `::1` ✅
- [x] Résoudre DNS (A/AAAA) et **bloquer IP privées** ✅ :
  - IPv4: `10/8`, `172.16/12`, `192.168/16`, `169.254/16`, `127/8`, etc.
  - IPv6: `fc00::/7`, `fe80::/10`, `::1`
- [ ] Bloquer redirections vers IP privées (redirect safety) — à appliquer lors du suivi des redirections (client HTTP à venir)

> **Fait :** Module `app/utils/ssrf.py` : hostnames interdits (localhost, 127.0.0.1, ::1, 0.0.0.0), résolution DNS avec timeout (5 s), blocage si une IP résolue est en plage privée/loopback/link-local. Intégré dans `POST /api/scan`. Tests unitaires (is_hostname_blocked, is_ip_blocked, check_ssrf) + tests route (refus localhost / 127.0.0.1).

### 2.3 Timeouts ✅
- [x] Timeout connexion (ex: 3s) ✅
- [x] Timeout lecture (ex: 10s) ✅
- [x] Timeout global scan (ex: 60–120s) ✅

> **Fait :** Section `timeouts` dans config/settings.yml (`connection: 3`, `read: 10`, `scan_global: 60`). `ScanTimeoutsSettings` et `get_scan_timeouts()` dans le config_loader. À utiliser par le client HTTP du scan (connexion + lecture) et pour borner la durée totale du scan.

---

## 3) Implémenter les tests cyber MVP (scan “posture”)

> Objectif : tests à forte valeur, faible risque juridique, résultats lisibles.

### 3.1 TLS / HTTPS
- [x] HTTPS activé ? ✅
- [x] Redirection HTTP→HTTPS ? ✅
- [x] Certificat valide / expiré / auto-signé ? ✅
- [x] Version TLS (au minimum détecter 1.0/1.1) ✅
- [ ] Résumé “TLS posture”

Pour les explications détaillées (failles, exemples, matrices de risque, conseils), voir [Vérifications TLS/HTTPS](verifications/tls-https.md).

**Limitations et notes d’implémentation :**

- **Ports autorisés** : par défaut 80 et 443. Les ports 1010 et 1011 sont autorisés pour les tests badssl.com (TLS 1.0 sur `tls-v1-0.badssl.com:1010`, TLS 1.1 sur `tls-v1-1.badssl.com:1011`). Configurable dans `config/settings.yml` (`url_validation.allowed_ports`).
- **Port non standard** : le scan utilise le port explicite de l’URL pour les vérifications TLS (certificat, versions obsolètes). Ex. `https://tls-v1-0.badssl.com:1010` est testé sur le port 1010, pas 443.
- **OpenSSL 3.x** : TLS 1.0 et 1.1 sont désactivés par défaut dans OpenSSL 3.x. Les serveurs qui n’acceptent que TLS 1.0/1.1 (ex. `tls-v1-0.badssl.com:1010`) ne sont pas joignables depuis un environnement avec OpenSSL 3.x. Le scan affiche alors un message explicite : *« Le serveur n'accepte peut-être que TLS 1.0/1.1, désactivés par défaut dans OpenSSL 3.x (limitation de l'environnement de scan) »*. Pour tester la détection TLS 1.0/1.1, utiliser un environnement avec TLS 1.0 activé (ex. conteneur avec ancienne OpenSSL) ou un site qui propose TLS 1.0 en plus de TLS 1.2+ sur le port 443.

### 3.2 Security Headers ✅
- [x] Vérifier présence :
  - `Content-Security-Policy`
  - `Strict-Transport-Security`
  - `X-Frame-Options`
  - `X-Content-Type-Options` (valeur attendue : `nosniff`)
  - `Referrer-Policy`
  - `Permissions-Policy`

> **Fait :** Module `app/services/security_headers/` (checks.py). Intégré dans le flux SSE après TLS (`headers_check` → `headers_done`). Résultat exposé dans l’événement `result.headers`. Tests unitaires dans `tests/test_security_headers_checks.py`.

### 3.3 Cookies ✅
- [x] Vérifier flags :
  - `Secure`
  - `HttpOnly`
  - `SameSite`
- [x] Détecter cookies sans `Secure` si site HTTPS

> **Fait :** Module `app/services/cookies/` (checks.py). Parse les en-têtes Set-Cookie, vérifie Secure/HttpOnly/SameSite. Détecte cookies sans Secure sur site HTTPS. Intégré dans le flux SSE après headers (`cookies_check` → `cookies_done`). Réutilise la réponse HTTPS (pas de requête supplémentaire). Tests dans `tests/test_cookies_checks.py`.

### 3.4 Exposition fichiers / endpoints sensibles (liste fixe MVP) ✅
- [x] Tester GET sur une petite liste :
  - `/.env`
  - `/.git/config`
  - `/backup.zip`
  - `/phpinfo.php`
  - `/admin/`
  - `/.DS_Store`
- [x] Si status 200 + contenu suspect → finding

> **Fait :** Module `app/services/exposed_files/` (checks.py). Requêtes GET en parallèle via `fetch_url`, signatures par chemin (KEY=value pour .env, [core] pour .git/config, PK pour ZIP, etc.). Intégré dans le flux SSE après cookies (`exposed_files_check` → `exposed_files_done`). Résultat dans `result.exposed_files`. Config `exposed_files` dans settings.yml. Tests dans `tests/test_exposed_files_checks.py`.

### 3.5 Directory listing ✅
- [x] Tester quelques répertoires usuels :
  - `/uploads/`
  - `/assets/`
  - `/static/`
- [x] Détecter signatures d'index Apache/Nginx (listing)

> **Fait :** Module `app/services/directory_listing/` (checks.py). Requêtes GET en parallèle via `run_path_checks`, signatures Apache/Nginx (Index of, Parent Directory, [DIR], mod_autoindex, nginx, `<a href=`). Intégré dans le flux SSE après exposed_files (`directory_listing_check` → `directory_listing_done`). Résultat dans `result.directory_listing`. Config `directory_listing` dans settings.yml. Tests dans `tests/test_directory_listing_checks.py`.

### 3.6 robots.txt ✅
- [x] Lire `/robots.txt`
- [x] Extraire `Disallow` et signaler routes potentiellement sensibles

> **Fait :** Module `app/services/robots_txt/` (checks.py). Requête GET /robots.txt via client partagé, parsing des directives Disallow, détection des routes sensibles (admin, api, backup, etc.) via motifs configurables. Intégré dans le flux SSE après directory_listing (`robots_txt_check` → `robots_txt_done`). Résultat dans `result.robots_txt`. Config `robots_txt.patterns` dans settings.yml. Tests dans `tests/test_robots_txt_checks.py`.

### 3.7 Tech fingerprinting (léger) ✅
- [x] Lire `Server`, `X-Powered-By`
- [x] Détecter framework/cms (heuristiques simples)
- [x] Remonter "stack info" sans sur-promettre

> **Fait :** Module `app/services/tech_fingerprinting/` (checks.py). Analyse les en-têtes de la réponse HTTPS (Server, X-Powered-By, X-Generator, X-Drupal-Cache). Heuristiques pour Nginx, Apache, PHP, ASP.NET, Express, WordPress, Drupal. Formulations indicatives (« probable », « détecté »). Intégré dans le flux SSE après robots_txt (`tech_fingerprinting_check` → `tech_fingerprinting_done`). Résultat dans `result.tech_fingerprinting`. Tests dans `tests/test_tech_fingerprinting_checks.py`.

---

## 4) Normalisation des résultats (format interne) ✅

- [x] Définir un schéma `Finding` :
  - `id`, `category`, `title`, `severity`, `evidence`, `recommendation`, `references`
- [x] Définir `ScanResult` :
  - `url`, `timestamp`, `duration`, `score`, `findings[]`

> **Fait :** Modèles `app/models/finding.py` et `app/models/scan_result.py`. Catalogue `app/catalogue/recommendations.py`. Normaliseurs `app/services/normalization/`. Payload SSE remplacé par format normalisé (url, timestamp, duration, score, findings).

---

## 5) Système de scoring (simple mais cohérent) ✅

- [x] Score /100
- [x] Pondération par catégories (exemple) :
  - TLS/HTTPS : 25
  - Headers : 25
  - Cookies : 20
  - Exposure : 20
  - Fingerprinting/robots : 10
- [x] Mapping sévérité :
  - `critical`, `high`, `medium`, `low`, `info` (minuscules)
- [x] Ajouter règles de downgrade/upgrade (ex : `.git/config` exposé = Critical)

> **Fait :** Module `app/services/scoring.py`. Pénalités par sévérité. Upgrade .git/config et .env → critical.

---

## 6) API backend (MVP)

- [x] `POST /scan` : lance scan et retourne résultat ✅ (étape actuelle : validation URL uniquement, pas encore le scan métier)
- [x] Validation entrée ✅ (dans scan-service ; SSRF + timeouts à faire en §2.2 et §2.3)
- [x] Gestion erreurs : URL invalide ✅ (400 + message détaillé via common error_handlers)
- [x] Gestion erreurs : site inaccessible, timeout, TLS error ✅
- [x] Logging structuré : request_id, durée, nb findings, status ✅

> **Fait (logging) :** À la fin de chaque scan (succès ou erreur), log structuré via `logger.info("Scan terminé", extra={...})` avec request_id (correlation_id), duration_seconds, nb_findings, status (success, error_400, error_408, error_503, etc.). Utilise `correlation_id_ctx` du common.

> **Fait (gestion erreurs) :** Module `app/errors/fetch_errors.py` : classification des exceptions (connection_failed, timeout, tls_error). `get_with_client_or_error` dans http_fetch retourne `FetchResult`. Détection précoce dans scan_stream : si fetch HTTPS échoue → événement `error` avec message, status_code (503/504/502), error_type. Pas de result partiel. Tests dans `tests/test_fetch_errors.py` et `tests/test_scan_router.py`.

> MVP : synchrone possible (scan rapide).
> Si scan long → passer asynchrone en V2.

---

## 7) Frontend MVP (simple et pro)

### 7.1 Landing ✅
- [x] Hero + promesse claire
- [x] Champ URL + CTA “Scan”
- [x] Disclaimer usage autorisé

### 7.2 Page résultats ✅
- [x] Score global + badge (🟢/🟡/🔴)
- [x] Résumé par catégorie
- [x] Liste des findings (triés par sévérité)
- [x] Bloc “How to fix” (recommandations pédagogiques)
- [x] Erreurs affichées proprement

### 7.3 UX ✅
- [x] Loader pendant scan
- [x] États : idle / loading / success / error
- [x] Responsive mobile

> **Fait :** Page `/scanner` (fr/en), service SSE `scanService.ts`, composants ScanLoader/ScanResults/ScannerContent. Gateway : `POST /scan/api/scan` rendu public. Lien "Scanner" dans le Header.

### 7.4 Accès aux résultats réservé aux utilisateurs connectés ✅
- [x] Gate « Connectez-vous pour accéder aux résultats » si non authentifié après scan
- [x] Stockage temporaire des résultats en `sessionStorage` (Option C hybride)
- [x] Restauration automatique des résultats après connexion (redirection vers scanner)
- [x] Composant `ScanResultsGate` + utilitaires `scanStorage.ts`

> **Fait :** Une fois le scan terminé, l’utilisateur non connecté voit une carte l’invitant à se connecter. Les résultats sont stockés en `sessionStorage`. Après connexion, si l’utilisateur revient sur la page scanner, les résultats sont restaurés et affichés. Si l’onglet est fermé avant connexion, les résultats sont perdus (fallback : relancer un scan).

### 7.5 Affichage du favicon / logo du site scanné ✅
- [x] Favicon du domaine affiché au-dessus de l'URL dans les résultats
- [x] Service Google Favicon (`/s2/favicons?domain=...&sz=128`) côté frontend
- [x] Fallback : icône globe SVG vectorielle si favicon indisponible (évite la pixellisation)

> **Fait :** Le composant `ScanResults` affiche le favicon du site scanné au-dessus du nom de domaine. Extraction du hostname depuis `result.url`, requête vers le service Google. En cas d'échec (404, CORS), affichage d'une icône globe SVG nette en fallback.

---

# V2 (après MVP) — Roadmap MVP 0.2.0

> Voir [ROADMAP-MVP-0.2.0.md](ROADMAP-MVP-0.2.0.md) pour le détail complet.

- [ ] Mode asynchrone + queue (SQS / Celery)
- [ ] Auth + dashboard + historique scans
- [ ] Export PDF
- [ ] Monitoring continu (scans planifiés)
- [ ] Scan plus avancé (OWASP light)
- [ ] API publique + clés API
- [ ] Intégration CI/CD (GitHub Action)

---

# Notes importantes (MVP)

- Le MVP **n’est pas** un pentest complet.
- Les tests doivent rester **non destructifs**.
- Ajouter un disclaimer clair : “vous certifiez avoir l’autorisation de scanner ce site”.
- La protection SSRF + timeout est **non négociable** dès le début.
