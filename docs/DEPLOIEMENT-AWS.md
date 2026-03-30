# Déploiement SecureOps sur AWS — guide pas à pas

Ce document décrit un déploiement **production** de la plateforme SecureOps sur AWS, avec :

- **Frontend** : `https://secureops.fr` → **AWS Amplify Hosting** (Next.js)
- **API + backend + base de données** : **`https://api.secureops.fr` → une seule EC2** — **Docker Compose** (gateway, microservices, workers **et** **PostgreSQL / PostGIS** dans des conteneurs sur la même machine)
- **Authentification** : **Amazon Cognito**
- **DNS** : achat du domaine, enregistrements, option **Cloudflare**

> **Coût / simplicité** : pas d’**RDS** dans ce guide — tout est sur l’EC2 (comme un `docker compose` de prod). Pour des sauvegardes managées, HA ou scaling DB séparé, voir [§14](#14-évolutions-possibles) (migration vers RDS).

Références projet : [ARCHITECTURE.md](ARCHITECTURE.md), [DEPLOIEMENT.md](DEPLOIEMENT.md), [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md).

---

## Table des matières

1. [Avant de déployer — checklist et décisions](#1-avant-de-déployer--checklist-et-décisions)
2. [Acheter et configurer le nom de domaine](#2-acheter-et-configurer-le-nom-de-domaine)
3. [DNS détaillé : apex + sous-domaine API](#3-dns-détaillé--apex--sous-domaine-api)
4. [Amazon Cognito](#4-amazon-cognito)
5. [AWS Amplify — frontend Next.js](#5-aws-amplify--frontend-nextjs)
6. [PostgreSQL sur l’EC2 (Docker + PostGIS)](#6-postgresql-sur-lec2-docker--postgis)
7. [EC2 — stack complète (gateway + services + Postgres)](#7-ec2--stack-complète-gateway--services--postgres)
8. [TLS / certificats pour l’API](#8-tls--certificats-pour-lapi)
9. [CORS et configuration gateway](#9-cors-et-configuration-gateway)
10. [Emails : expéditeur et intégration](#10-emails--expéditeur-et-intégration)
11. [Cloudflare (optionnel mais recommandé)](#11-cloudflare-optionnel-mais-recommandé)
12. [Secrets, sauvegardes, monitoring](#12-secrets-sauvegardes-monitoring)
13. [Ordre d’exécution recommandé](#13-ordre-dexécution-recommandé)
14. [Évolutions possibles](#14-évolutions-possibles)

---

## 1. Avant de déployer — checklist et décisions

### 1.1 Ce que vous déployez (rappel stack)

| Composant | Rôle |
|-----------|------|
| **gateway** | Point d’entrée unique, JWT Cognito + clés API, proxy vers les services |
| **admin-service** | Admin, contacts, newsletter, analytics, docs scanner, images |
| **user-service** | Profils, clés API, préférences, alertes scan |
| **scan-service** | Scanner + jobs async + workers |
| **crawl-service** | Crawler + jobs async (Playwright possible → besoin RAM/CPU) |
| **pdf-service** | PDF (WeasyPrint) |
| **PostgreSQL (conteneur)** | Même instance logique `template_db` que en local ; **non exposée sur Internet** (réseau Docker uniquement) |

Le **navigateur** appelle uniquement :

- `https://secureops.fr` (Amplify)
- `https://api.secureops.fr` (via le gateway sur EC2)

Les services internes ne doivent **pas** être exposés publiquement sans reverse proxy + TLS.

### 1.2 Choix à trancher avant la commande AWS

| Sujet | Recommandation |
|-------|----------------|
| **Région AWS** | `eu-west-3` (Paris) — alignée avec la doc du projet (Cognito, EC2). |
| **Taille EC2** | **DB + app sur la même machine** : viser **t3.xlarge** ou **m6i.xlarge** si crawl SPA/Playwright actif ; **t3.large** seulement pour très faible charge (surveiller RAM et I/O disque). |
| **Disque (EBS)** | Volume racine **gp3** typiquement **50 à 100 Go** au démarrage : OS, images Docker, **données PostgreSQL** (volume nommé ou bind mount). Augmenter si logs / données / couches Docker grossissent ; surveiller l’espace libre. |
| **IP fixe API** | **Elastic IP** sur l’EC2 (recommandé pour `api.secureops.fr`). |
| **Secrets** | **AWS Secrets Manager** ou **SSM Parameter Store** (SecureString) — pas de `.env` en git. |
| **Emails transactionnels** | Aujourd’hui le code **admin-service** utilise **Microsoft Graph** (`TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`, `SENDER_EMAIL`). Voir [§10](#10-emails--expéditeur-et-intégration). |

### 1.3 Conformité et exploitation

- **RGPD** : hébergement UE, politique de confidentialité, DPA avec AWS, durées de rétention (voir docs légales du site).
- **Cognito** : politique de mot de passe, MFA optionnelle, limitation des tentatives.
- **Sauvegardes données** : **snapshots EBS** planifiés et/ou **`pg_dump` vers S3** — pas de backup RDS automatique ; tester une restauration au moins une fois ([§12.2](#122-sauvegardes)).
- **Scan / crawl** : en prod, `IS_PROD` doit refléter la prod pour les garde-fous SSRF du scan-service ([VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md)).

### 1.4 Prérequis techniques

- Compte AWS avec droits IAM suffisants (EC2, EBS, Cognito, Amplify, Route 53 ou DNS externe ; S3 optionnel pour dumps).
- AWS CLI configuré localement (optionnel mais utile).
- Repo SecureOps cloné ; accès au build Docker (`docker compose`).

---

## 2. Acheter et configurer le nom de domaine

### 2.1 Obtenir `secureops.fr`

- Les noms **`.fr`** sont enregistrés chez des **registrars** agréés par l’**AFNIC** (OVH, Gandi, Ionos, etc.).
- Étapes typiques :
  1. Vérifier la disponibilité sur le site du registrar.
  2. Créer un compte et payer l’enregistrement (souvent annuel).
  3. Activer la **validation email** / contacts WHOIS requis pour le `.fr`.
  4. Noter où gérer les **serveurs DNS** du domaine (chez le registrar ou chez Cloudflare / Route 53).

### 2.2 Où héberger la zone DNS ?

Trois modèles courants :

| Modèle | Avantages |
|--------|-----------|
| **DNS du registrar uniquement** | Simple ; vous créez les enregistrements A/AAAA/CNAME à la main. |
| **Amazon Route 53** | Intégration AWS ; health checks ; coût modique par zone. |
| **Cloudflare** (voir [§11](#11-cloudflare-optionnel-mais-recommandé)) | CDN + WAF + Turnstile déjà utilisé côté front ; proxy orange sur le apex peut simplifier TLS côté origin. |

**Important** : pour **Amplify**, vous ajouterez des enregistrements **CNAME** ou **ALIAS** fournis par la console Amplify lors du branchement du domaine personnalisé.

---

## 3. DNS détaillé : apex + sous-domaine API

### 3.1 Cible finale

| Hôte | Cible technique | Rôle |
|------|-----------------|------|
| `secureops.fr` | Amplify (ou CNAME vers Cloudflare → Amplify selon archi) | Site Next.js |
| `www.secureops.fr` | Redirection 301 vers `https://secureops.fr` (Amplify ou Cloudflare) | SEO |
| `api.secureops.fr` | IP Elastic de l’EC2 **ou** nom d’hôte d’un **ALB** | Gateway HTTPS |

### 3.2 Enregistrements typiques (sans Cloudflare proxy sur l’API)

Si l’API est servie directement sur l’EC2 avec **Certbot** (Let’s Encrypt) :

1. Créer une **Elastic IP** dans EC2 et l’associer à l’instance.
2. Chez le DNS :
   - **A** `api` → `<Elastic-IP>` (TTL 300 s au début).
3. Pour le frontend Amplify :
   - Suivre l’assistant Amplify « Domain management » : il demandera souvent un **CNAME** pour validation ACM et un **CNAME** ou alias pour le domaine racine (selon registrar, un **ALIAS** apex peut nécessiter Route 53 ou Cloudflare).

### 3.3 Certificats SSL

- **Amplify** : gère les certificats **ACM** pour le domaine branché à Amplify.
- **api.secureops.fr** : soit **ACM sur un ALB** (recommandé en montée en charge), soit **Let’s Encrypt** sur Nginx sur l’EC2 (simple pour un MVP).

### 3.4 Vérifications

```bash
dig +short secureops.fr
dig +short api.secureops.fr
curl -sI https://secureops.fr | head -5
curl -sI https://api.secureops.fr/health | head -5
```

---

## 4. Amazon Cognito

### 4.1 Créer un User Pool

1. Console AWS → **Cognito** → **Create user pool**.
2. **Sign-in options** : Email (cohérent avec `loginMechanisms: ["email"]` dans le frontend).
3. **Password policy** : selon votre politique de sécurité.
4. **MFA** : optionnel au démarrage ; activable ensuite.
5. **User pool name** : ex. `secureops-prod`.

### 4.2 Créer un « App client » pour SPA

1. Dans le pool → **App integration** → **App clients** → **Add app client**.
2. Type **Public client** (pas de secret côté navigateur — PKCE, comme dans Amplify v6).
3. **Allowed callback URLs** (exemples) :
   - `https://secureops.fr/`
   - `https://secureops.fr/fr/` (si vos locales sont dans le path — **à aligner avec les routes Next.js réelles**)
4. **Sign-out URLs** (recommandé si Cognito les exige pour l’app client) :
   - `https://secureops.fr/connexion`

### 4.3 Groupe `admin`

Le gateway vérifie le groupe Cognito **`admin`** pour les routes `/admin/*`.
Dans Cognito → **Groups** → créer le groupe `admin` et y ajouter les comptes administrateurs.

### 4.4 IAM pour le user-service (gestion utilisateurs Cognito)

Le **user-service** peut utiliser l’API Cognito (création / désactivation) avec des credentials IAM (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` dans `.env.example`).
Créer un **utilisateur IAM** avec politique minimale (ex. `cognito-idp:Admin*` limitée au pool prod) et stocker les clés dans **Secrets Manager**.

### 4.5 Variables à recopier

| Variable | Où l’utiliser |
|----------|----------------|
| Région (ex. `eu-west-3`) | Front `NEXT_PUBLIC_AWS_REGION`, backend `COGNITO_REGION` |
| User Pool ID | `NEXT_PUBLIC_AWS_USER_POOL_ID`, `COGNITO_USER_POOL_ID` |
| App client ID | `NEXT_PUBLIC_AWS_CLIENT_ID`, `COGNITO_CLIENT_ID` |

Backend (gateway, user-service, etc.) : voir [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md).

---

## 5. AWS Amplify — frontend Next.js

### 5.1 Pourquoi Amplify

- Build managé Next.js, CDN, certificats pour `secureops.fr`.
- Variables d’environnement par branche (prod).

### 5.2 Connecter le dépôt

1. **Amplify Hosting** → **New app** → **Host web app** → choisir GitHub/GitLab/Bitbucket.
2. Sélectionner le repo **SecureOps**, branche `main` (ou `production`).
3. **Build settings** : Amplify détecte souvent Next.js ; sinon fournir un `amplify.yml` à la racine ou dans `frontend/`.

### 5.3 Exemple `amplify.yml` (monorepo, app dans `frontend/`)

À adapter selon la structure exacte du repo et la version Node :

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: .next
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

> **Note** : Amplify Gen 2 / Next.js SSR peut exiger une config spécifique (compute SSR). Vérifiez la doc AWS « Next.js on Amplify » pour la version Next du projet. Si le build échoue, essayez le mode **SSR** recommandé par Amplify pour votre version.

### 5.4 Variables d’environnement Amplify (build **et** runtime)

Les `NEXT_PUBLIC_*` sont **inlinées au build** — les modifier impose un **redéploiement**.

| Variable | Valeur production (exemple) |
|----------|-----------------------------|
| `NEXT_PUBLIC_APP_URL` | `https://secureops.fr` |
| `NEXT_PUBLIC_GATEWAY_URL` | `https://api.secureops.fr` |
| `NEXT_PUBLIC_AWS_REGION` | `eu-west-3` |
| `NEXT_PUBLIC_AWS_USER_POOL_ID` | `eu-west-3_xxxx` |
| `NEXT_PUBLIC_AWS_CLIENT_ID` | `xxxxxxxx` |
| `NEXT_PUBLIC_IS_PROD` | `true` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Clé site Cloudflare Turnstile (si formulaire contact) |

Optionnel : `NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL_URL`, réseaux sociaux, etc.

### 5.5 Domaine personnalisé sur Amplify

1. Amplify → **Domain management** → **Add domain** → `secureops.fr`.
2. Suivre les enregistrements DNS (validation ACM + routage).
3. Configurer **redirect** `www` → apex si souhaité.

### 5.6 Après déploiement

- Tester connexion / inscription Cognito depuis `https://secureops.fr`.
- Vérifier dans les outils développeur que les appels API partent vers `https://api.secureops.fr` et ne sont pas bloqués par CORS ([§9](#9-cors-et-configuration-gateway)).

---

## 6. PostgreSQL sur l’EC2 (Docker + PostGIS)

Dans ce modèle, **PostgreSQL n’est pas RDS** : c’est le service **`postgres`** du `docker-compose.yml` du repo (image **PostGIS**), sur le **réseau Docker interne** uniquement.

### 6.1 Persistance des données (critique)

Sans volume dédié, les données sont **perdues** si le conteneur est recréé.

1. Utiliser un **volume Docker nommé** (le `docker-compose.yml` du repo déclare déjà **`pgdata`** → données sous `/var/lib/docker/volumes/...` sur l’EC2, donc sur l’**EBS** si Docker utilise le disque système) **ou** un **bind mount** explicite (ex. `/var/lib/secureops/pgdata` sur EBS) pour localiser et sauvegarder les fichiers plus facilement.
2. Vérifier après un `docker compose down` / redémarrage que la base est toujours là.
3. Dimensionner le **volume EBS** de l’EC2 (souvent **50–100 Go gp3** au départ) pour logs + Docker + **fichiers PostgreSQL** ; étendre le volume en production si besoin.

### 6.2 PostGIS

Comme en développement : l’image du projet inclut PostGIS ; au besoin exécuter une fois `CREATE EXTENSION IF NOT EXISTS postgis;` sur `template_db` (selon image et migrations).

### 6.3 Connexion depuis les services (réseau Docker)

Les services du repo utilisent déjà l’hôte **`postgres`** et le port **5432** sur le réseau Compose, par exemple :

- **admin-service** : `postgresql+asyncpg://USER:PASSWORD@postgres:5432/template_db`
- **user-service / scan-service / crawl-service** : `postgresql://USER:PASSWORD@postgres:5432/template_db`

Définir **`POSTGRES_USER`**, **`POSTGRES_PASSWORD`**, **`POSTGRES_DB`** (ex. `template_db`) via variables d’environnement ou fichier `.env` **sur l’EC2** (secrets hors git).

### 6.4 Ne pas exposer PostgreSQL sur Internet

- Le `docker-compose.yml` du repo publie **`5433:5432`** pour le dev local — en prod, **retirez la section `ports:`** du service `postgres` (override Compose) pour que PostgreSQL ne soit **pas** accessible depuis l’hôte, seulement depuis le réseau Docker.
- **Ne pas** mapper `5432` (ou `5433`) vers l’extérieur.
- Le **Security Group** de l’EC2 ne doit **pas** ouvrir le port 5432 depuis Internet ; seuls **80/443** (et éventuellement **22** depuis votre IP pour SSH) sont nécessaires côté public.

### 6.5 Migrations

Au premier déploiement, exécuter les migrations Alembic pour **admin**, **user**, **scan**, **crawl** (voir [DEPLOIEMENT.md](DEPLOIEMENT.md)) — en général **au démarrage** des conteneurs si votre image le fait déjà, sinon depuis l’EC2 :

```bash
docker compose exec user-service alembic upgrade head
# idem admin-service, scan-service, crawl-service selon procédure du projet
```

---

## 7. EC2 — stack complète (gateway + services + Postgres)

### 7.1 Vue d’ensemble

1. Lancer une **EC2** (Amazon Linux 2023 ou Ubuntu LTS) dans un **VPC** avec subnet public (pour Elastic IP + accès sortant).
2. Attacher un volume **EBS gp3** (**50–100 Go** en général au lancement) ; monter la persistance Postgres dessus si vous utilisez un bind mount.
3. Installer **Docker** et **Docker Compose plugin**.
4. Cloner le repo (ou déployer via artefact CI) sur l’instance.
5. **Production** : repartir du `docker-compose.yml` en adaptant :
   - **`IS_DOCKER=true`** pour tous les services backend ;
   - **`POSTGRES_*`** et secrets forts ;
   - **Ne pas** déployer le service **`frontend`** sur cette EC2 si le site public est sur **Amplify** (voir [§7.7](#77-frontend-amplify-seulement--pas-de-conteneur-front-sur-lec2)) ;
   - **Retirer** (ou ne pas publier) les **ports** des services internes (8010, 8011, etc.) vers l’extérieur — seul le **gateway** doit être joignable depuis l’hôte sur un port mappé vers **8000** pour Nginx.

### 7.2 Architecture réseau recommandée

```
Internet → Nginx (443) → 127.0.0.1:8000 → gateway (conteneur)
                └── réseau Docker interne uniquement :
                    postgres:5432, admin, user, scan, crawl, pdf, workers
```

- **Nginx** sur l’hôte OS (recommandé) ou conteneur avec `network_mode: host` — le plus simple pour Let’s Encrypt est souvent Nginx **sur l’OS**.
- Exposer **uniquement** **80** / **443** (et **22** restreint) dans le **Security Group**.

### 7.3 Variables d’environnement (résumé)

Sur l’hôte ou via `env_file` (secrets hors git) :

- **Postgres** : `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB=template_db` — le compose construit les `DATABASE_URL` comme en local.
- **Cognito** : `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`.
- **User-service** : `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` si gestion Cognito côté API.
- **Clés internes** : `USER_SERVICE_INTERNAL_API_KEY`, `PDF_SERVICE_INTERNAL_API_KEY`, `ADMIN_SERVICE_INTERNAL_API_KEY` si utilisé ([VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md)).
- **Scan-service** : `IS_PROD=true` pour les garde-fous production ; `PDF_SERVICE_URL=http://pdf-service:8013`.
- **Admin-service** : Microsoft Graph — [§10](#10-emails--expéditeur-et-intégration).
- **FRONTEND_URL** : `https://secureops.fr`.

### 7.4 Workers async

Les services **scan** et **crawl** lancent des workers pour les jobs async : conserver les services / commandes `worker` du `docker-compose.yml` du projet.

### 7.5 Ressources (app + DB sur la même machine)

- **PostgreSQL** partage **CPU, RAM et I/O disque** avec les scans, le crawl Playwright et le PDF — surveiller **CloudWatch** (CPU, mémoire, **disk used**).
- **Playwright / crawl SPA** : gourmand en RAM ; **WeasyPrint** : charge CPU ponctuelle.
- Si la machine swap ou OOM : augmenter le type d’instance ou passer la DB sur **RDS** ([§14](#14-évolutions-possibles)).

### 7.6 Pare-feu

- **Security Group** : entrée **443** (et **80**) depuis `0.0.0.0/0` ; **pas** de **5432** public.
- **Sortie** : HTTPS (Cognito, Graph, mises à jour) + trafic HTTP/HTTPS vers les **cibles scannées** (scan-service / crawl-service).

### 7.7 Frontend Amplify seulement — pas de conteneur front sur l’EC2

En suivant ce guide, **`secureops.fr`** est servi par **Amplify**. Sur l’EC2, vous pouvez utiliser un **fichier override** Compose (ex. `docker-compose.prod.yml`) qui **désactive** ou **retire** le service `frontend` pour économiser des ressources et éviter la confusion (un seul point d’entrée web : Amplify).

---

## 8. TLS / certificats pour l’API

### Option A — Nginx + Certbot (Let’s Encrypt) sur l’EC2

1. Installer **Certbot** avec plugin nginx.
2. Obtenir un certificat pour `api.secureops.fr` (DNS doit déjà pointer vers l’EC2).
3. Configurer Nginx :

```nginx
server {
    listen 443 ssl http2;
    server_name api.secureops.fr;

    ssl_certificate     /etc/letsencrypt/live/api.secureops.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.secureops.fr/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Timeouts longs pour scan/crawl async si nécessaire
        proxy_read_timeout 300s;
    }
}
```

4. Renouvellement automatique : timer **certbot renew**.

### Option B — Application Load Balancer + ACM

1. Créer un **ALB** dans des subnets publics.
2. Certificat **ACM** pour `api.secureops.fr` (validation DNS).
3. Target group : instance EC2 port 8000 (ou Nginx 443 interne).
4. DNS : **CNAME** `api` → nom DNS de l’ALB.

---

## 9. CORS et configuration gateway

Le fichier `backend/gateway/config/settings.yml` liste des origines **localhost** par défaut. En production, **ajouter explicitement** :

```yaml
cors:
  allow_origins:
    - "https://secureops.fr"
    - "https://www.secureops.fr"
```

Redéployer le gateway après modification.
Avec `allow_credentials: true`, le navigateur **refuse** `*` — les origines doivent être exactes (schéma + host + pas de slash final selon implémentation Starlette).

---

## 10. Emails : expéditeur et intégration

### 10.1 Comportement actuel du code (admin-service)

L’envoi (newsletter, alertes, contacts selon les flux) passe par **Microsoft Graph** avec :

- `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`
- `SENDER_EMAIL` : adresse Microsoft 365 / Azure AD autorisée à envoyer via Graph
- `ADMIN_ALERT_EMAIL` : destinataire des alertes monitoring (optionnel)
- `FRONTEND_URL` : liens dans les emails (`https://secureops.fr`)

**Pour changer l’email d’envoi** :

1. Utiliser une boîte ou alias **du même tenant** Microsoft configuré pour Graph (`SENDER_EMAIL`).
2. Dans Azure Portal → **App registrations** → votre app → permissions **Application** : *Mail.Send* (selon modèle exact utilisé par votre code).
3. Accorder **admin consent**.
4. Mettre à jour les variables sur l’EC2 / Secrets Manager et redémarrer **admin-service**.

### 10.2 Alternative AWS : Amazon SES

Si vous voulez tout sur AWS sans Microsoft 365 :

1. Vérifier un domaine ou une adresse dans **SES** (sandbox levée pour prod).
2. **Adapter le code** `admin-service` : remplacer l’appel Graph par boto3 `ses.send_email` ou SMTP SES — **ce n’est pas implémenté dans le repo tel quel** ; prévoir un chantier dev ou un bridge (ex. Lambda + SES déclenchée par webhook).

### 10.3 Cognito : emails de vérification / mot de passe oublié

Dans **Cognito** → **Messaging** :

- Par défaut Cognito envoie depuis une adresse AWS (limites).
- Pour un expéditeur **no-reply@secureops.fr** : configurer **SES** dans la même région et lier SES au pool Cognito (console Cognito → options d’email).

---

## 11. Cloudflare (optionnel mais recommandé)

### 11.1 Cas d’usage

| Fonction | Intérêt |
|----------|---------|
| **DNS** | Gestion centralisée des enregistrements ; API. |
| **Proxy orange** | Masque l’IP origin ; DDoS basique ; règles WAF. |
| **Turnstile** | Déjà utilisé côté frontend (`NEXT_PUBLIC_TURNSTILE_SITE_KEY`) — créer un site Turnstile pour `secureops.fr`. |
| **SSL** | « Full (strict) » entre Cloudflare et origin (Amplify / EC2 avec cert valide). |

### 11.2 Configuration typique

1. Créer un compte Cloudflare → **Add site** → `secureops.fr`.
2. Copier les **nameservers** fournis par Cloudflare chez votre **registrar** (remplace les NS du domaine).
3. Enregistrements :
   - **Apex** : selon mode Amplify (souvent CNAME flattening ou instructions Amplify pour CNAME vers `amplifyapp.com`).
   - **api** : A ou CNAME vers l’EC2/ALB ; **proxy** désactivé si vous utilisez Let’s Encrypt HTTP-01 sur l’IP directe, ou activé avec **Full strict** si certificat valide sur l’origin.

### 11.3 Pièges courants

- **Boucles de redirect** : vérifier « Always HTTPS » vs redirections Next.js / Amplify.
- **WebSockets / SSE** : le scan utilise un flux SSE — tester les parcours scanner derrière Cloudflare (timeouts, buffering).
- **IP réelle** : Nginx doit lire `X-Forwarded-For` si derrière Cloudflare (module `real_ip` ou trust des plages Cloudflare).

---

## 12. Secrets, sauvegardes, monitoring

### 12.1 Secrets

- Stocker `POSTGRES_PASSWORD`, clés API internes, `CLIENT_SECRET` Graph, clés IAM dans **Secrets Manager**.
- Référencer les secrets au runtime (script de démarrage qui exporte les variables ou Docker `secrets`).

### 12.2 Sauvegardes

- **EBS** : **snapshots automatiques** du volume racine (et du volume dédié Postgres si séparé) — définir une rétention (ex. 7–35 jours) et **tester** une restauration sur une instance de test au moins une fois par trimestre.
- **PostgreSQL** : en complément, **dump logique** périodique vers **S3** (cron sur l’EC2 : `pg_dump` via `docker compose exec postgres ...`) — utile pour restaurer une base précise sans restaurer toute la VM.
- **Images / fichiers admin** (`admin-service`, galerie) : si stockés sur le disque local, ils sont inclus dans le snapshot EBS ; pour plus de résilience, envisager **S3** (évolution).

### 12.3 Logs et métriques

- **CloudWatch agent** sur EC2 pour logs Docker.
- **Alarmes** : CPU, mémoire, espace disque, healthcheck `https://api.secureops.fr/health`.

### 12.4 Rate limiting

Le gateway implémente du rate limiting ([RATE-LIMITING.md](RATE-LIMITING.md)) ; en multi-instances EC2, il faudra **Redis** partagé — pour une **seule** EC2, le stockage mémoire local peut suffire au début.

---

## 13. Ordre d’exécution recommandé

1. Acheter **secureops.fr** et préparer la zone DNS (Route 53 ou Cloudflare).
2. Créer **Cognito** (pool, client, domaine, groupe `admin`).
3. Lancer **EC2** (EBS **50–100 Go** gp3 en pratique, **Elastic IP**), Security Group **443/80** (pas 5432), installer Docker + Compose.
4. Cloner le repo, configurer **volume persistant** pour Postgres et `.env` / secrets (`POSTGRES_*`, Cognito, Graph, clés internes, `FRONTEND_URL`).
5. Construire et démarrer la stack (**postgres** puis services, gateway) — variante **sans** conteneur `frontend` si tout le web passe par Amplify ([§7.7](#77-frontend-amplify-seulement--pas-de-conteneur-front-sur-lec2)).
6. Lancer les **migrations** Alembic si besoin, vérifier les `/health` (gateway et services).
7. Installer **Nginx + Certbot**, TLS pour **`api.secureops.fr`**, proxy vers le port **8000** du gateway.
8. Mettre à jour **CORS** sur le gateway avec `https://secureops.fr` ([§9](#9-cors-et-configuration-gateway)).
9. Activer les **snapshots EBS** (et optionnellement cron `pg_dump` → S3).
10. Brancher **Amplify** + variables `NEXT_PUBLIC_*` + domaine `secureops.fr`.
11. Finaliser les enregistrements **DNS** (apex → Amplify, `api` → Elastic IP).
12. Tests bout en bout : auth, scan async, crawl, PDF, contact, admin.

---

## 14. Évolutions possibles

| Évolution | Description |
|-----------|-------------|
| **Amazon RDS (PostgreSQL + PostGIS)** | Décharger la base de l’EC2 : backups managés, snapshots PITR, scaling disque/IOPS. Mettre à jour `DATABASE_URL` / `ADMIN_DATABASE_URL` vers l’endpoint RDS et restreindre le SG RDS à l’EC2 uniquement. |
| **ECS Fargate** | Remplace EC2 bare metal pour les conteneurs applicatifs ; la DB peut rester RDS. |
| **ALB + plusieurs EC2** | Haute disponibilité API ; nécessite alors **Redis** (ou autre store partagé) pour le rate limiting ([RATE-LIMITING.md](RATE-LIMITING.md)). |
| **ElastiCache Redis** | Rate limiting et quotas cohérents multi-instances. |
| **WAF AWS** | Règles managées sur l’ALB. |
| **S3 + CloudFront** | Assets statiques si vous sortez du modèle Amplify pur. |

---

## Documents liés

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DEPLOIEMENT.md](DEPLOIEMENT.md)
- [VARIABLES-ENVIRONNEMENT.md](VARIABLES-ENVIRONNEMENT.md)
- [API-PUBLIQUE.md](API-PUBLIQUE.md)
- [RATE-LIMITING.md](RATE-LIMITING.md)

---

*Document pour le déploiement cible `secureops.fr` (Amplify) / `api.secureops.fr` (EC2 unique : gateway + services + PostgreSQL Docker). À adapter à chaque évolution d’infrastructure ou de version Next.js / Amplify.*
