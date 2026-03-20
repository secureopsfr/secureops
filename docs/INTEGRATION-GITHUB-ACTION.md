# Intégration CI/CD — GitHub Action SecureOps

Documentation détaillée pour intégrer les scans SecureOps dans vos pipelines CI/CD (GitHub Actions). Cette intégration permet de **faire échouer un job** si le score de sécurité est trop bas ou si des findings critiques sont détectés.

---

## 1. Vue d'ensemble

### Objectif

L’intégration CI/CD SecureOps permet de :

1. **Lancer un scan** sur une URL (par ex. votre site déployé en staging)
2. **Récupérer** le score (0–100) et la liste des findings (sévérités : critical, high, medium, low, info)
3. **Bloquer le pipeline** si :
   - le score est inférieur à un seuil configuré (`fail_on_score_below`)
   - ou au moins un finding de sévérité **critical** est détecté

### Endpoints API

| Endpoint | Auth | Usage |
|----------|------|-------|
| `POST /scan/api/scan/async` | Optionnel pour `scan_type=frontend` ; clé API recommandée en CI | Crée un job de scan asynchrone |

Pour la CI/CD, utilisez **`POST /scan/api/scan/async`** avec une **clé API** pour :
- sauvegarder le scan dans l’historique
- garantir la compatibilité avec les futurs quotas et rate limiting

### Format de réponse (async + polling)

L’API renvoie un **job async** :

- `POST /scan/api/scan/async` retourne `job_id`
- `GET /scan/api/scan/async/{job_id}` retourne statut + `progress_log`
- `GET /scan/api/scan/async/{job_id}/result` retourne le résultat final

Structure de l’événement `result` :

```json
{
  "url": "https://example.com",
  "timestamp": "2025-03-09T12:00:00.000Z",
  "duration": 45.2,
  "score": 78,
  "findings": [
    {
      "id": "headers-csp-absent",
      "category": "headers",
      "title": "Content-Security-Policy absent",
      "severity": "high",
      "evidence": "Content-Security-Policy absent : risque XSS accru.",
      "recommendation": "...",
      "references": ["https://..."]
    }
  ]
}
```

Sévérités possibles : `critical`, `high`, `medium`, `low`, `info`.

---

## 2. Prérequis

### 2.1 Créer une clé API

1. Connectez-vous à [SecureOps](https://secureops.fr) (ou votre instance)
2. Allez dans **Mon compte** → **Clés API** (ou **Paramètres** → **Sécurité**)
3. Créez une clé avec un tag `CI` ou `github-actions`
4. Copiez la clé **une seule fois** (format `sk_...`) — elle ne sera plus affichée

### 2.2 Configurer le secret GitHub

1. Dans votre dépôt GitHub : **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Nom : `SECUREOPS_API_KEY`
4. Valeur : votre clé API (`sk_...`)

---

## 3. Option A : Action GitHub dédiée (recommandé)

### 3.1 Structure de l’action

Deux emplacements possibles :

- **Repo dédié** : `secureops/secureops-scan` (ou `secureops/actions`) — pour une action publique
- **Monorepo** : `.github/actions/secureops-scan/` — pour une action interne

Structure minimale :

```
secureops-scan/
├── action.yml          # Métadonnées et inputs
├── package.json
├── dist/
│   └── index.js        # Script principal (build)
└── src/
    └── index.js
```

### 3.2 Définition de l’action (`action.yml`)

```yaml
name: 'SecureOps Scan'
description: 'Lance un scan de posture sécurité et fait échouer le job si le score est trop bas ou si un finding critique est détecté.'
author: 'SecureOps'

branding:
  icon: 'shield'
  color: 'blue'

inputs:
  url:
    description: "URL à scanner (ex. https://staging.example.com)"
    required: true
  api_key:
    description: "Clé API SecureOps (stockée dans GitHub Secrets)"
    required: true
  base_url:
    description: "URL de base de l'API SecureOps (par défaut https://api.secureops.fr)"
    required: false
    default: 'https://api.secureops.fr'
  fail_on_score_below:
    description: "Seuil de score minimal (0-100). Le job échoue si score < seuil. Défaut : 80"
    required: false
    default: '80'
  fail_on_critical:
    description: "Si true, le job échoue dès qu'un finding critical est présent. Défaut : true"
    required: false
    default: 'true'

outputs:
  score:
    description: "Score du scan (0-100)"
  passed:
    description: "true si le scan a passé les critères, false sinon"

runs:
  using: 'node20'
  main: 'dist/index.js'
```

### 3.3 Script principal (`src/index.js`)

```javascript
const https = require('https');
const http = require('http');

async function main() {
  const url = process.env.INPUT_URL;
  const apiKey = process.env.INPUT_API_KEY;
  const baseUrl = (process.env.INPUT_BASE_URL || 'https://api.secureops.fr').replace(/\/$/, '');
  const failOnScoreBelow = parseInt(process.env.INPUT_FAIL_ON_SCORE_BELOW || '80', 10);
  const failOnCritical = process.env.INPUT_FAIL_ON_CRITICAL !== 'false';

  const scanUrl = `${baseUrl}/scan/api/scan/async`;
  const body = JSON.stringify({ url });

  const parsed = new URL(scanUrl);
  const client = parsed.protocol === 'https:' ? https : http;

  const req = client.request(scanUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      'Content-Length': Buffer.byteLength(body),
    },
  });

  return new Promise((resolve, reject) => {
    req.on('response', (res) => {
      if (res.statusCode >= 400) {
        reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
        return;
      }

      let body = '';
      res.on('data', (chunk) => { body += chunk.toString(); });
      res.on('end', async () => {
        try {
          const created = JSON.parse(body);
          const jobId = created.job_id;
          if (!jobId) throw new Error('job_id manquant');
          const statusUrl = `${baseUrl}/scan/api/scan/async/${jobId}`;
          const resultUrl = `${statusUrl}/result`;

          let done = false;
          while (!done) {
            await new Promise(r => setTimeout(r, 1000));
            const statusRaw = await fetch(statusUrl, { headers: { 'X-API-Key': apiKey } });
            if (!statusRaw.ok) throw new Error(`Status HTTP ${statusRaw.status}`);
            const status = await statusRaw.json();
            if (status.status === 'failed') {
              throw new Error(status.error?.message || 'Scan failed');
            }
            if (status.status === 'completed') {
              const resultRaw = await fetch(resultUrl, { headers: { 'X-API-Key': apiKey } });
              if (!resultRaw.ok) throw new Error(`Result HTTP ${resultRaw.status}`);
              const result = await resultRaw.json();
              const score = result.score ?? 0;
              const findings = result.findings || [];
              const hasCritical = findings.some(f => (f.severity || '').toLowerCase() === 'critical');

              if (process.env.GITHUB_OUTPUT) {
                const fs = require('fs');
                fs.appendFileSync(process.env.GITHUB_OUTPUT, `score=${score}\n`);
                fs.appendFileSync(process.env.GITHUB_OUTPUT, `passed=${!(hasCritical || score < failOnScoreBelow)}\n`);
              }

              if (hasCritical && failOnCritical) {
                const criticalList = findings.filter(f => (f.severity || '').toLowerCase() === 'critical');
                throw new Error(
                  `Scan échoué : ${criticalList.length} finding(s) critical détecté(s). ` +
                  `Score : ${score}/100. ` +
                  `Findings: ${criticalList.map(f => f.title || f.evidence).join('; ')}`
                );
              }
              if (score < failOnScoreBelow) {
                throw new Error(
                  `Scan échoué : score ${score}/100 < seuil ${failOnScoreBelow}. ` +
                  `Findings: ${findings.length}`
                );
              }

              console.log(`✅ SecureOps Scan : score ${score}/100 (${findings.length} finding(s))`);
              done = true;
              resolve();
            }
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

main().catch((err) => {
  console.error('❌', err.message);
  process.exit(1);
});
```

### 3.4 Exemple d’utilisation dans un workflow

```yaml
name: Security Scan

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    outputs:
      deploy_url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4

      # Déploiement vers staging (exemple)
      - name: Deploy to staging
        id: deploy
        run: |
          # ... votre déploiement (ex. Vercel, Netlify) ...
          echo "url=https://staging.example.com" >> $GITHUB_OUTPUT

  secureops-scan:
    runs-on: ubuntu-latest
    needs: deploy
    steps:
      - name: SecureOps Security Scan
        id: scan
        uses: secureops/secureops-scan@v1
        with:
          url: ${{ needs.deploy.outputs.deploy_url }}
          api_key: ${{ secrets.SECUREOPS_API_KEY }}
          fail_on_score_below: 80
          fail_on_critical: true

      - name: Log score
        if: success()
        run: echo "Score SecureOps : ${{ steps.scan.outputs.score }}/100"
```

---

## 4. Option B : Workflow manuel (sans action dédiée)

Si l’action n’est pas encore publiée, vous pouvez intégrer le scan directement dans un workflow avec un script inline ou une action `run`.

### 4.1 Workflow avec script Node.js inline

```yaml
name: Security Scan (Manual)

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  secureops-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: SecureOps Scan
        env:
          SCAN_URL: "https://votre-site-staging.example.com"
          API_KEY: ${{ secrets.SECUREOPS_API_KEY }}
          BASE_URL: "https://api.secureops.fr"
          FAIL_ON_SCORE_BELOW: "80"
          FAIL_ON_CRITICAL: "true"
        run: |
          node << 'SCRIPT'
          const https = require('https');
          const body = JSON.stringify({ url: process.env.SCAN_URL });
          const req = https.request(
            `${process.env.BASE_URL}/scan/api/scan/async`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-API-Key': process.env.API_KEY,
                'Content-Length': Buffer.byteLength(body),
              },
            },
            (res) => {
              if (res.statusCode >= 400) {
                console.error('HTTP', res.statusCode);
                process.exit(1);
              }
              let buf = '';
              res.on('data', (c) => { buf += c.toString(); });
              res.on('end', () => {
                const blocks = buf.split('\n\n');
                for (const b of blocks) {
                  const m = b.match(/event:\s*result\s*\ndata:\s*(.+)/s);
                  if (m) {
                    const r = JSON.parse(m[1]);
                    const score = r.score || 0;
                    const findings = r.findings || [];
                    const critical = findings.filter(f => (f.severity || '').toLowerCase() === 'critical');
                    const threshold = parseInt(process.env.FAIL_ON_SCORE_BELOW || '80', 10);
                    if (critical.length > 0 && process.env.FAIL_ON_CRITICAL !== 'false') {
                      console.error('Échec :', critical.length, 'finding(s) critical');
                      process.exit(1);
                    }
                    if (score < threshold) {
                      console.error('Échec : score', score, '<', threshold);
                      process.exit(1);
                    }
                    console.log('Score:', score, '/ 100');
                    return;
                  }
                }
                console.error('Pas d\'événement result trouvé');
                process.exit(1);
              });
            }
          );
          req.on('error', (e) => { console.error(e); process.exit(1); });
          req.write(body);
          req.end();
          SCRIPT
```

### 4.2 Workflow avec curl + jq (alternative)

```yaml
name: Security Scan (curl + jq)

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  secureops-scan:
    runs-on: ubuntu-latest
    steps:
      - name: SecureOps Scan
        env:
          SCAN_URL: "https://votre-site-staging.example.com"
          API_KEY: ${{ secrets.SECUREOPS_API_KEY }}
          BASE_URL: "https://api.secureops.fr"
          FAIL_ON_SCORE_BELOW: "80"
        run: |
          set -e
          # --max-time 300 : scan long possible (30-90 s typiquement)
          JOB=$(curl -s --max-time 60 -X POST "${BASE_URL}/scan/api/scan/async" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${API_KEY}" \
            -d "{\"url\": \"${SCAN_URL}\", \"scan_type\": \"frontend\", \"input\": {}}")
          JOB_ID=$(echo "$JOB" | jq -r '.job_id // empty')
          [ -n "$JOB_ID" ] || { echo "Erreur: job_id manquant"; exit 1; }

          while true; do
            STATUS_JSON=$(curl -s --max-time 30 -H "X-API-Key: ${API_KEY}" "${BASE_URL}/scan/api/scan/async/${JOB_ID}")
            STATUS=$(echo "$STATUS_JSON" | jq -r '.status // empty')
            if [ "$STATUS" = "failed" ]; then
              echo "Erreur: scan échoué"
              echo "$STATUS_JSON"
              exit 1
            fi
            if [ "$STATUS" = "completed" ]; then
              RESULT=$(curl -s --max-time 30 -H "X-API-Key: ${API_KEY}" "${BASE_URL}/scan/api/scan/async/${JOB_ID}/result")
              break
            fi
            sleep 1
          done

          SCORE=$(echo "$RESULT" | jq -r '.score // 0')
          CRITICAL=$(echo "$RESULT" | jq -r '[.findings[]? | select((.severity | ascii_downcase) == "critical")] | length')
          echo "Score SecureOps : $SCORE / 100"
          echo "Findings critiques : $CRITICAL"

          if [ "$CRITICAL" -gt 0 ]; then
            echo "Échec : $CRITICAL finding(s) critical détecté(s)"
            exit 1
          fi

          if [ "$SCORE" -lt "${FAIL_ON_SCORE_BELOW}" ]; then
            echo "Échec : score $SCORE < ${FAIL_ON_SCORE_BELOW}"
            exit 1
          fi
```

> **Note** : avec `curl -sN`, tout le flux est lu d’un coup. Pour des scans longs, le timeout par défaut de curl peut être dépassé. Utilisez `--max-time 300` si besoin.

---

## 5. Exemples complets de workflows

### 5.1 Scan après déploiement Vercel / Netlify

```yaml
name: Deploy + SecureOps Scan

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        id: deploy

  secureops:
    runs-on: ubuntu-latest
    needs: deploy
    steps:
      - name: SecureOps Scan
        uses: secureops/secureops-scan@v1
        with:
          url: ${{ steps.deploy.outputs.preview-url }}
          api_key: ${{ secrets.SECUREOPS_API_KEY }}
          fail_on_score_below: 80
```

### 5.2 Scan sur pull request (commentaire)

```yaml
name: PR Security Scan

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: SecureOps Scan
        id: scan
        uses: secureops/secureops-scan@v1
        with:
          url: ${{ vars.STAGING_URL }}
          api_key: ${{ secrets.SECUREOPS_API_KEY }}
          fail_on_score_below: 70

      - name: Comment score on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## SecureOps Scan\nScore : ${{ steps.scan.outputs.score }}/100`
            });
```

### 5.3 Scan async minimal (test de l’intégration)

Pour tester rapidement que l’API et la clé fonctionnent :

```yaml
- name: Test SecureOps API (async backend scan)
  run: |
    curl -s -X POST "https://api.secureops.fr/scan/api/scan/async" \
      -H "X-API-Key: ${{ secrets.SECUREOPS_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{"url":"https://example.com","scan_type":"backend","input":{}}' | jq .
```

La réponse doit contenir un `job_id`, puis le statut/résultat doivent être lisibles via les endpoints async.

---

## 6. Bonnes pratiques

| Bonne pratique | Description |
|----------------|-------------|
| **Secret dédié** | Créez un secret `SECUREOPS_API_KEY` séparé, ne partagez jamais la clé dans le workflow |
| **Clé CI** | Utilisez une clé API dédiée avec le tag `CI` pour la révoquer facilement |
| **URL dynamique** | Passez l’URL de déploiement (staging) via `needs.*.outputs` ou variables d’environnement |
| **Seuil réaliste** | Commencez avec `fail_on_score_below: 70` puis augmentez progressivement |
| **Timeout** | Les scans peuvent prendre 30–90 s ; augmentez le `timeout-minutes` du job si nécessaire |

---

## 7. Badge « Scan SecureOps » (optionnel)

Vous pouvez ajouter un badge dans le README de votre projet pour indiquer qu’un scan SecureOps est exécuté en CI.

### 7.1 Badge statique

```markdown
![SecureOps Scan](https://img.shields.io/badge/SecureOps-Scan%20actif-blue)
```

### 7.2 Badge dynamique (via l’API Shields)

Si SecureOps expose plus tard un endpoint de statut par projet, vous pourriez utiliser :

```markdown
![SecureOps Score](https://img.shields.io/endpoint?url=https://api.secureops.fr/badge/score/YOUR_PROJECT_ID)
```

### 7.3 Badge GitHub Actions (statut du workflow)

```markdown
![SecureOps Scan](https://github.com/VOTRE_ORG/VOTRE_REPO/actions/workflows/secureops-scan.yml/badge.svg)
```

Exemple complet dans le README :

```markdown
# Mon projet

[![SecureOps Scan](https://github.com/mon-org/mon-repo/actions/workflows/secureops-scan.yml/badge.svg)](https://github.com/mon-org/mon-repo/actions/workflows/secureops-scan.yml)

Ce projet est scanné par [SecureOps](https://secureops.fr) à chaque push sur `main`.
```

---

## 8. Dépannage

| Erreur | Cause probable | Solution |
|--------|----------------|----------|
| `HTTP 401` | Clé API invalide ou expirée | Vérifier le secret `SECUREOPS_API_KEY`, régénérer une clé |
| `HTTP 404` | URL de l’API incorrecte | Vérifier `base_url` (ex. `https://api.secureops.fr`) |
| `Pas d'événement result` | Site cible inaccessible ou timeout | Vérifier que l’URL est joignable depuis GitHub (réseau public) |
| `Result HTTP ...` | Job non terminé ou erreur API | Poller le statut jusqu’à `completed`, puis appeler `/result` |

---

## 9. Références

- [API publique SecureOps](./API-PUBLIQUE.md) — authentification et clés API
- [Roadmap MVP 0.3.0](./roadmaps/ROADMAP-MVP-0.3.0.md) — section 3 (Intégration CI/CD)

---

## 10. Roadmap d'intégration (côté SecureOps)

Roadmap détaillée pour développer, publier et maintenir l'action GitHub SecureOps dans le projet.

### Phase 1 : Créer l'action

| Étape | Tâche | Détails |
|-------|-------|---------|
| 1.1 | Choisir l'emplacement | **Option A** : repo dédié `secureops/secureops-scan` (recommandé pour action publique). **Option B** : monorepo `.github/actions/secureops-scan/` (action interne). |
| 1.2 | Créer la structure | Créer les dossiers et fichiers : `action.yml`, `package.json`, `src/index.js` (voir sections 3.1–3.3). |
| 1.3 | Écrire le script | Copier/adapter le script Node.js (§3.3) : create job async, polling status, fetch result, outputs `score`/`passed`, exit 1 si échec. |
| 1.4 | Tester en local | `npm install` puis `node src/index.js` avec variables `INPUT_URL`, `INPUT_API_KEY`, etc. Valider contre l'API async réelle. |

**Exemple structure initiale :**

```
.github/actions/secureops-scan/
├── action.yml
├── package.json          # { "type": "commonjs", "scripts": { "build": "cp src/index.js dist/index.js" } }
├── dist/
│   └── index.js
└── src/
    └── index.js
```

---

### Phase 2 : GitHub — Repo et configuration

| Étape | Tâche | Détails |
|-------|-------|---------|
| 2.1 | Créer le dépôt GitHub | **Si repo dédié** : `github.com/secureops/secureops-scan` — repo public, description « GitHub Action pour scanner la posture sécurité avec SecureOps ». |
| 2.2 | Push du code | Initialiser git, ajouter les fichiers, push sur `main`. |
| 2.3 | README du repo | Rédiger un README avec : description, usage (`uses: secureops/secureops-scan@v1`), inputs, exemples, lien vers la doc complète. |
| 2.4 | `.gitignore` | Ignorer `node_modules/`, `.env`, `*.log`. Optionnel : builder `dist/` en CI plutôt que le committer. |

---

### Phase 3 : Workflow de release (tags/versions)

| Étape | Tâche | Détails |
|-------|-------|---------|
| 3.1 | Workflow de build | Créer `.github/workflows/build.yml` : sur push/PR, lancer `npm install` et `npm run build`, vérifier que `dist/index.js` est généré. |
| 3.2 | Workflow de release | Créer `.github/workflows/release.yml` : sur création d'un tag `v*`, builder, créer une GitHub Release, attacher les artefacts si besoin. |
| 3.3 | Tag v1 | Créer le tag `v1` (ou `v1.0.0`) : `git tag v1 && git push origin v1`. Les utilisateurs pourront utiliser `secureops/secureops-scan@v1`. |
| 3.4 | Versionnement sémantique | Pour les mises à jour : `v1.1.0` (patch), `v2.0.0` (breaking). Documenter dans le README les changements par version. |

**Exemple workflow de build :**

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - name: Verify dist
        run: test -f dist/index.js
```

---

### Phase 4 : Tests automatisés

| Étape | Tâche | Détails |
|-------|-------|---------|
| 4.1 | Test du script (async) | Job dans la CI : appeler l'API `/scan/api/scan/async` avec une clé de test (secret `SECUREOPS_API_KEY` dans le repo SecureOps). Vérifier create/poll/result et sortie attendue. |
| 4.2 | Test d'intégration | Optionnel : workflow qui utilise `uses: ./.github/actions/secureops-scan` (action locale) sur une URL de staging connue. |
| 4.3 | Tests unitaires | Optionnel : extraire la logique de polling async dans un module testable ; ajouter Jest ou Node native test. |

---

### Phase 5 : Documentation et communication

| Étape | Tâche | Détails |
|-------|-------|---------|
| 5.1 | README du repo action | Titre, badges (build, release), installation, inputs, outputs, exemples minimaux, lien vers `docs/INTEGRATION-GITHUB-ACTION.md`. |
| 5.2 | Marketplace GitHub (optionnel) | Soumettre l'action au [GitHub Marketplace](https://github.com/marketplace?type=actions) : formulaire, catégories, icône, description. |
| 5.3 | Page doc SecureOps | S'assurer que la page docs/INTEGRATION-GITHUB-ACTION.md est accessible (ex. `/scanner/docs/ci-cd` ou équivalent). |
| 5.4 | Badge « Scan SecureOps » | Documenter le badge dans le README du repo action et dans la doc utilisateur (§7). |

---

### Phase 6 : Intégration dans le monorepo SecureOps (si action locale)

Si l'action reste dans le monorepo SecureOps plutôt que dans un repo dédié :

| Étape | Tâche | Détails |
|-------|-------|---------|
| 6.1 | Emplacement | Créer `.github/actions/secureops-scan/` à la racine du monorepo. |
| 6.2 | Réutiliser dans la CI SecureOps | Ajouter un workflow dans SecureOps qui teste l'action en conditions réelles (ex. scan du site de démo après déploiement). |
| 6.3 | Référence pour les users | Les utilisateurs externes ne pourront pas utiliser `uses: secureops/secureops-scan@v1` tant que l'action n'est pas dans un repo public dédié. Documenter l'option B (workflow manuel §4) en attendant. |

---

### Phase 7 : Checklist finale avant publication

- [ ] Action testée contre `POST /scan/api/scan/async` + polling status/result
- [ ] Secret `SECUREOPS_API_KEY` configuré dans le repo (pour les tests CI)
- [ ] Tag `v1` créé et poussé
- [ ] README à jour avec exemples
- [ ] Lien vers la doc dans `docs/INTEGRATION-GITHUB-ACTION.md`
- [ ] Workflow de build vert
- [ ] (Optionnel) Action publiée sur le Marketplace

---

### Récapitulatif des fichiers à créer (repo dédié)

| Fichier | Rôle |
|---------|------|
| `action.yml` | Métadonnées, inputs, outputs, `runs` |
| `package.json` | Dépendances (minimales), script build |
| `src/index.js` | Script principal (create job async, polling, fetch result) |
| `dist/index.js` | Build (ou généré en CI) |
| `README.md` | Usage, exemples, liens |
| `.gitignore` | node_modules, .env, etc. |
| `.github/workflows/build.yml` | Build et vérification |
| `.github/workflows/release.yml` | (Optionnel) Release sur tag |
