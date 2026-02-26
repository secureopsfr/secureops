# SecureOps — Roadmap MVP (étape par étape)

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

### 3.6 robots.txt
- [ ] Lire `/robots.txt`
- [ ] Extraire `Disallow` et signaler routes potentiellement sensibles

### 3.7 Tech fingerprinting (léger)
- [ ] Lire `Server`, `X-Powered-By`
- [ ] Détecter framework/cms (heuristiques simples)
- [ ] Remonter “stack info” sans sur-promettre

---

## 4) Normalisation des résultats (format interne)

- [ ] Définir un schéma `Finding` :
  - `id`, `category`, `title`, `severity`, `evidence`, `recommendation`, `references`
- [ ] Définir `ScanResult` :
  - `url`, `timestamp`, `duration`, `score`, `findings[]`

---

## 5) Système de scoring (simple mais cohérent)

- [ ] Score /100
- [ ] Pondération par catégories (exemple) :
  - TLS/HTTPS : 25
  - Headers : 25
  - Cookies : 20
  - Exposure : 20
  - Fingerprinting/robots : 10
- [ ] Mapping sévérité :
  - `Critical`, `High`, `Medium`, `Low`, `Info`
- [ ] Ajouter règles de downgrade/upgrade (ex : `.git/config` exposé = Critical)

---

## 6) API backend (MVP)

- [x] `POST /scan` : lance scan et retourne résultat ✅ (étape actuelle : validation URL uniquement, pas encore le scan métier)
- [x] Validation entrée ✅ (dans scan-service ; SSRF + timeouts à faire en §2.2 et §2.3)
- [x] Gestion erreurs : URL invalide ✅ (400 + message détaillé via common error_handlers)
- [ ] Gestion erreurs : site inaccessible, timeout, TLS error
- [ ] Logging structuré : request_id, durée, nb findings, status

> MVP : synchrone possible (scan rapide).
> Si scan long → passer asynchrone en V2.

---

## 7) Frontend MVP (simple et pro)

### 7.1 Landing
- [ ] Hero + promesse claire
- [ ] Champ URL + CTA “Scan”
- [ ] Disclaimer usage autorisé

### 7.2 Page résultats
- [ ] Score global + badge (🟢/🟡/🔴)
- [ ] Résumé par catégorie
- [ ] Liste des findings (triés par sévérité)
- [ ] Bloc “How to fix” (recommandations pédagogiques)
- [ ] Erreurs affichées proprement

### 7.3 UX
- [ ] Loader pendant scan
- [ ] États : idle / loading / success / error
- [ ] Responsive mobile

---

## 8) Qualité / CI (dès MVP)

### 8.1 Backend CI
- [ ] Lint (ruff/flake8)
- [ ] Tests unitaires (pytest)
- [ ] Coverage minimal

### 8.2 Frontend CI
- [ ] Lint (eslint)
- [ ] Build (npm run build)

### 8.3 Branch protection (main)
- [ ] PR required
- [ ] checks required

---

## 9) Déploiement AWS (MVP)

### 9.1 Infra minimale
- [ ] EC2 (Docker ou runtime direct)
- [ ] Nginx reverse proxy
- [ ] Certificat SSL (ACM via ALB ou Let’s Encrypt)

### 9.2 Sécurité AWS (minimum)
- [ ] Security Group : ouvrir seulement 80/443
- [ ] SSH restreint à ton IP
- [ ] Activer IMDSv2 sur EC2 (recommandé)
- [ ] Logs CloudWatch (au minimum app logs)

---

## 10) Tests finaux (avant annonce)

- [ ] Tester sur sites de test (DVWA/Juice Shop en local)
- [ ] Tester sur un vrai site vitrine simple
- [ ] Tester cas d’erreurs : DNS, timeout, redirect, TLS broken
- [ ] Vérifier que SSRF est impossible (tests IP privées)
- [ ] Vérifier charge (10 scans rapides)

---

## 11) Release MVP v0.1

- [ ] Tag `v0.1.0`
- [ ] Release notes (fonctionnalités + limites)
- [ ] Démo GIF / screenshots
- [ ] Feedback form (Google Form / email)

---

# V2 (après MVP) — évolutions naturelles

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
