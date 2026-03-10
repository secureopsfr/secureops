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
| `POST /scan/api/scan` | Optionnel (clé API recommandée) | Scan réel — analyse posture sécurité |
| `POST /scan/api/scan/fake` | Requise (JWT ou clé API) | Scan factice — score 100, 0 finding (tests) |

Pour la CI/CD, utilisez **`POST /scan/api/scan`** avec une **clé API** pour :
- sauvegarder le scan dans l’historique
- garantir la compatibilité avec les futurs quotas et rate limiting

### Format de réponse (SSE)

L’API renvoie un **flux Server-Sent Events (SSE)**. Les événements pertinents sont :

- **`step`** : progression du scan (validation, TLS, headers, etc.)
- **`result`** : résultat final avec score et findings
- **`error`** : erreur (site inaccessible, timeout, etc.)

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

1. Connectez-vous à [SecureOps](https://secureops.io) (ou votre instance)
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
    description: "URL de base de l'API SecureOps (par défaut https://api.secureops.io)"
    required: false
    default: 'https://api.secureops.io'
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
  const baseUrl = (process.env.INPUT_BASE_URL || 'https://api.secureops.io').replace(/\/$/, '');
  const failOnScoreBelow = parseInt(process.env.INPUT_FAIL_ON_SCORE_BELOW || '80', 10);
  const failOnCritical = process.env.INPUT_FAIL_ON_CRITICAL !== 'false';

  const scanUrl = `${baseUrl}/scan/api/scan`;
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

      let buffer = '';
      res.on('data', (chunk) => {
        buffer += chunk.toString();
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (!block.trim()) continue;
          const eventMatch = block.match(/^event:\s*(.+)$/m);
          const dataMatch = block.match(/^data:\s*(.+)$/m);
          if (!eventMatch || !dataMatch) continue;

          const event = eventMatch[1].trim();
          const data = dataMatch[1];

          if (event === 'error') {
            try {
              const err = JSON.parse(data);
              reject(new Error(err.message || data));
            } catch {
              reject(new Error(data));
            }
          } else if (event === 'result') {
            try {
              const result = JSON.parse(data);
              const score = result.score ?? 0;
              const findings = result.findings || [];
              const hasCritical = findings.some(f => (f.severity || '').toLowerCase() === 'critical');

              // Outputs pour les steps suivants
              if (process.env.GITHUB_OUTPUT) {
                const fs = require('fs');
                fs.appendFileSync(process.env.GITHUB_OUTPUT, `score=${score}\n`);
                fs.appendFileSync(process.env.GITHUB_OUTPUT, `passed=${!(hasCritical || score < failOnScoreBelow)}\n`);
              }

              if (hasCritical && failOnCritical) {
                const criticalList = findings.filter(f => (f.severity || '').toLowerCase() === 'critical');
                reject(new Error(
                  `Scan échoué : ${criticalList.length} finding(s) critical détecté(s). ` +
                  `Score : ${score}/100. ` +
                  `Findings: ${criticalList.map(f => f.title || f.evidence).join('; ')}`
                ));
              }
              if (score < failOnScoreBelow) {
                reject(new Error(
                  `Scan échoué : score ${score}/100 < seuil ${failOnScoreBelow}. ` +
                  `Findings: ${findings.length}`
                ));
              }

              console.log(`✅ SecureOps Scan : score ${score}/100 (${findings.length} finding(s))`);
              resolve();
            } catch (e) {
              reject(new Error(`Parse result: ${e.message}`));
            }
          }
        }
      });

      res.on('end', () => {
        if (buffer && !buffer.includes('event:')) {
          reject(new Error('Réponse incomplète — pas d\'événement result reçu'));
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
          BASE_URL: "https://api.secureops.io"
          FAIL_ON_SCORE_BELOW: "80"
          FAIL_ON_CRITICAL: "true"
        run: |
          node << 'SCRIPT'
          const https = require('https');
          const body = JSON.stringify({ url: process.env.SCAN_URL });
          const req = https.request(
            `${process.env.BASE_URL}/scan/api/scan`,
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
          BASE_URL: "https://api.secureops.io"
          FAIL_ON_SCORE_BELOW: "80"
        run: |
          set -e
          # --max-time 300 : scan long possible (30-90 s typiquement)
          curl -sN --max-time 300 -X POST "${BASE_URL}/scan/api/scan" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: ${API_KEY}" \
            -d "{\"url\": \"${SCAN_URL}\"}" | tee /tmp/sse.log > /dev/null

          # Extraire le dernier événement "result" du flux SSE
          RESULT=$(grep -A1 '^event: result$' /tmp/sse.log | grep '^data:' | tail -1 | sed 's/^data: //')
          if [ -z "$RESULT" ]; then
            echo "Erreur : aucun résultat de scan reçu"
            exit 1
          fi

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

### 5.3 Scan factice (test de l’intégration)

Pour tester que l’API et la clé fonctionnent sans lancer un vrai scan :

```yaml
- name: Test SecureOps API (fake scan)
  run: |
    curl -s -X POST "https://api.secureops.io/scan/api/scan/fake" \
      -H "X-API-Key: ${{ secrets.SECUREOPS_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{"url":"https://example.com"}' | head -20
```

Le flux SSE renvoyé doit contenir un événement `result` avec `score: 100` et `findings: []`.

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
![SecureOps Score](https://img.shields.io/endpoint?url=https://api.secureops.io/badge/score/YOUR_PROJECT_ID)
```

### 7.3 Badge GitHub Actions (statut du workflow)

```markdown
![SecureOps Scan](https://github.com/VOTRE_ORG/VOTRE_REPO/actions/workflows/secureops-scan.yml/badge.svg)
```

Exemple complet dans le README :

```markdown
# Mon projet

[![SecureOps Scan](https://github.com/mon-org/mon-repo/actions/workflows/secureops-scan.yml/badge.svg)](https://github.com/mon-org/mon-repo/actions/workflows/secureops-scan.yml)

Ce projet est scanné par [SecureOps](https://secureops.io) à chaque push sur `main`.
```

---

## 8. Dépannage

| Erreur | Cause probable | Solution |
|--------|----------------|----------|
| `HTTP 401` | Clé API invalide ou expirée | Vérifier le secret `SECUREOPS_API_KEY`, régénérer une clé |
| `HTTP 404` | URL de l’API incorrecte | Vérifier `base_url` (ex. `https://api.secureops.io`) |
| `Pas d'événement result` | Site cible inaccessible ou timeout | Vérifier que l’URL est joignable depuis GitHub (réseau public) |
| `Parse result: ...` | Format SSE inattendu | Mettre à jour l’action ou le script vers la dernière version |

---

## 9. Références

- [API publique SecureOps](./API-PUBLIQUE.md) — authentification et clés API
- [Roadmap MVP 0.3.0](./roadmaps/ROADMAP-MVP-0.3.0.md) — section 3 (Intégration CI/CD)
