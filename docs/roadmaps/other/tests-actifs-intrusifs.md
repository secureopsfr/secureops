# Catalogue complet des tests actifs intrusifs (scanner intrusif)

Ce document sert de reference de developpement pour le **scanner actif intrusif**.
Objectif: couvrir de facon exhaustive les families de tests a implementer, en les classant du **plus commun** au **moins commun**.

> Important: ces tests sont intrusifs. Ils doivent etre executes **uniquement** sur des cibles autorisees.

---

## 1) Definitions utiles

- **Passif**: observe les reponses sans provoquer de comportement anormal.
- **Actif intrusif**: envoie des requetes craftes (parametres, methodes, en-tetes, sequences) pour provoquer un signal de vulnerabilite.
- **Destructif**: modifie ou degrade la cible (a eviter par defaut dans un scanner SaaS).

### Niveaux de risque d'execution

- `L1` intrusif leger: impact tres faible (ex: OPTIONS, CORS probe).
- `L2` intrusif modere: charge faible a moyenne (ex: injections basiques, auth probing).
- `L3` intrusif eleve: risque de perturbation (ex: stress tests, race conditions).
- `L4` intrusif critique: potentiellement destabilisant ou destructif (desactive par defaut).

---

## 2) Garde-fous obligatoires du scanner actif

- **Autorisation forte**: preuve de controle du domaine (DNS TXT), audit trail, acceptance explicite.
- **Kill switch global**: arret immediat d'un scan.
- **Rate limit strict** par hote, endpoint et categorie de test.
- **Budget de requetes** par test, par endpoint et par scan.
- **Timeouts courts** et retries limites.
- **Methodes interdites par defaut**: `PUT`, `PATCH`, `DELETE`, `POST` non idempotent sauf mode explicite.
- **Payload safety**: pas d'exfiltration reelle, pas de shell payload destructif, pas d'ecriture persistante.
- **Journalisation complete**: requete envoyee, cible, timestamp, statut, evidence.
- **Scopes explicites**: frontend URL, backend URL optionnelle, exclusions.
- **Protection SSRF non negociable** cote scanner.

---

## 3) Priorisation produit (du plus commun au moins commun)

## P0 - Indispensable (common et forte valeur)

### 3.1 Authentification et session

- Bruteforce protection (login):
  - Verifier lockout, backoff, captcha, 429.
  - Niveau: `L2`.
- Enumeration utilisateur:
  - Messages differencies "user inexistant" vs "mot de passe invalide".
  - Niveau: `L1`.
- Session fixation:
  - Verifier rotation d'identifiant de session apres login.
  - Niveau: `L2`.
- Invalidation de session:
  - Logout invalide bien le token/cookie.
  - Niveau: `L2`.
- JWT basique:
  - Acceptance d'algorithmes faibles/non attendus, validation exp/nbf/aud/iss.
  - Niveau: `L2`.

### 3.2 Autorisation (IDOR / BOLA / escalation)

- Horizontal privilege escalation:
  - Changer identifiant de ressource (ex: `/users/{id}`) et verifier acces interdit.
  - Niveau: `L2`.
- Vertical privilege escalation:
  - Endpoint admin accessible depuis role non admin.
  - Niveau: `L2`.
- BOLA/BFLA API:
  - Controle d'objet et de fonction manquant sur endpoints API.
  - Niveau: `L2`.

### 3.3 Injections les plus courantes

- SQL injection (error-based + time-based leger):
  - Chercher erreurs SQL, delais anormaux controles.
  - Niveau: `L2`.
- NoSQL injection basique:
  - Operateurs logiques/injection de structures dans parametres JSON.
  - Niveau: `L2`.
- XSS reflechi (detection de reflexion):
  - Marqueur unique, contexte HTML/attribut/JS.
  - Niveau: `L2`.
- Path traversal:
  - Sequences de remontee de repertoire, variations encodees.
  - Niveau: `L2`.
- Command injection basique:
  - Detection d'erreurs et comportements anormaux, sans execution destructive.
  - Niveau: `L2`.

### 3.4 Web/API classiques

- Open redirect actif:
  - Parametres `redirect`, `next`, `url`, `returnUrl`, etc.
  - Niveau: `L1`.
- CORS actif:
  - Origin reflechie + credentials, wildcard sensible.
  - Niveau: `L1`.
- Methodes HTTP:
  - OPTIONS/Allow, TRACE/XST, HEAD.
  - Niveau: `L1`.
- CSRF (presence et enforcement):
  - Absence de token sur actions sensibles + test de rejection sans token.
  - Niveau: `L2`.
- Rate limiting endpoint:
  - Burst court controle pour detecter absence de limite.
  - Niveau: `L2`.

---

## P1 - Tres recommande (encore frequent)

### 3.5 Upload et contenu utilisateur

- Upload de type non autorise:
  - MIME spoofing, extension double, contenu malforme.
  - Niveau: `L2`.
- Execution de fichier upload:
  - Verifier acces direct et execution serveur.
  - Niveau: `L3`.
- Traversal via nom de fichier:
  - Nom de fichier avec sequences traversal.
  - Niveau: `L2`.

### 3.6 APIs modernes

- GraphQL actif:
  - Introspection, depth/alias abuse, batching abuse, erreurs schema.
  - Niveau: `L2`.
- Mass assignment:
  - Champs sensibles accepts cote API sans whitelisting.
  - Niveau: `L2`.
- Validation schema:
  - Type confusion, champs inattendus, arrays excessifs.
  - Niveau: `L2`.
- Pagination abuse:
  - `limit` excessif, absence de bornes.
  - Niveau: `L1`.

### 3.7 SSRF applicative

- SSRF via parametres URL:
  - Variantes de parsing URL, schemas acceptes, redirections serveur.
  - Niveau: `L2`.
- Metadata cloud probes (safe mode):
  - Detection d'exposition potentielle sans exfiltration.
  - Niveau: `L3`.

### 3.8 XML/Template/Deserialize

- XXE:
  - Entites externes et parser insecure.
  - Niveau: `L2`.
- SSTI:
  - Signatures d'evaluation template.
  - Niveau: `L2`.
- Insecure deserialization:
  - Vecteurs communs selon techno.
  - Niveau: `L3`.

---

## P2 - Avance (moins frequent, fort impact potentiel)

### 3.9 HTTP et cache avances

- HTTP request smuggling / desync:
  - Mismatch `Content-Length` / `Transfer-Encoding`.
  - Niveau: `L3`.
- Cache poisoning:
  - Pollution via en-tetes non normalises.
  - Niveau: `L3`.
- Web cache deception:
  - URL confusee et mise en cache de contenu prive.
  - Niveau: `L3`.
- Host header injection:
  - Generation de liens absolus, reset password poisoning.
  - Niveau: `L2`.

### 3.10 Conditions de course (race conditions)

- Double spend / double action:
  - Requetes concurrentes sur action critique.
  - Niveau: `L3`.
- TOCTOU:
  - Verification puis usage avec etat change.
  - Niveau: `L3`.

### 3.11 Business logic abuse

- Bypass workflow:
  - Saut d'etapes de paiement/validation.
  - Niveau: `L2`.
- Abuse de coupons/credits:
  - Reutilisation illegitime, cumul non prevu.
  - Niveau: `L3`.
- Actions hors fenetre metier:
  - Endpoint accepte operation hors regles.
  - Niveau: `L2`.

---

## P3 - Specialises (moins commun)

### 3.12 Temps reel et protocoles

- WebSocket authz:
  - Action non autorisee apres handshake.
  - Niveau: `L2`.
- GraphQL subscriptions abuse:
  - Ecoute non autorisee de flux sensibles.
  - Niveau: `L3`.
- gRPC abuse:
  - Methodes sensibles exposees sans controle.
  - Niveau: `L2`.

### 3.13 Infra/cloud ciblee

- Bucket/object storage exposure test actif:
  - Lecture non autorisee via patterns d'URL.
  - Niveau: `L2`.
- Service mesh/internal API exposure:
  - Endpoints internes accidentellement routables.
  - Niveau: `L3`.

### 3.14 Auth avancee

- OAuth/OIDC misconfig:
  - `redirect_uri` laxiste, state faible, PKCE non enforce.
  - Niveau: `L2`.
- SSO relay state abuse:
  - Rebond non valide.
  - Niveau: `L2`.

---

## P4 - Rare / recherche / a activer explicitement

### 3.15 DoS applicatif controle

- Burst test court:
  - Detection absence de protections.
  - Niveau: `L3`.
- Slow request / slow headers:
  - Timeout serveur.
  - Niveau: `L3`.
- Payload amplification:
  - Inputs volumineux sur endpoints couteux.
  - Niveau: `L3`.

### 3.16 Vecteurs tres avances

- HTTP/2 abuse patterns (selon stack).
- Unicode normalization confusion sur authz.
- DNS rebinding scenarios applicatifs.
- Parser differential attacks multi-proxy.

Niveau: `L3-L4`, usage expert uniquement.

---

## 4) Matrice "test -> preuve -> risque"

Pour chaque test, stocker:

- **Preuve (evidence)**: reponse, code HTTP, extrait, delai mesure.
- **Confiance**: faible / moyenne / forte.
- **Risque execution**: `L1` a `L4`.
- **Impact potentiel cible**: faible / moyen / eleve.
- **Action recommandee**: corrective immediate ou revue manuelle.

---

## 5) Exigences techniques minimales par famille

### 5.1 Moteur de requetes

- Rejouer methodes, headers, query, body.
- Support encodages: URL, double URL, unicode, JSON.
- Session stateful (cookies, tokens), puis isolation par test.
- Retry intelligent (pas aveugle) et jitter.

### 5.2 Moteur de payloads

- Payloads parametrables par categorie.
- Mutations automatiques (case, encoding, wrappers).
- Payload IDs uniques pour tracer la reflexion.

### 5.3 Detection

- Regex signatures erreur (SQL, template, parser).
- Diff de reponse (baseline vs probe).
- Detection temporelle (time-based) robuste au bruit.
- Heuristiques anti faux positifs.

### 5.4 Reporting

- Requete envoyee (redactee), endpoint, parametre, payload id.
- Observation brute et interpretation.
- Reproduction minimale.
- Recommandation concrete.

---

## 6) Ordre de developpement recommande (pragmatique)

### Phase A (MVP intrusif)

- Open redirect actif
- Methodes HTTP (OPTIONS/TRACE/HEAD)
- CORS actif
- Reflection params (base XSS vector)
- SQL error-based basique
- Path traversal basique
- CSRF enforcement basique
- IDOR simple sur endpoints detectes

### Phase B

- NoSQLi, SSTI, XXE
- Upload abuse
- Mass assignment API
- Rate limiting checks et auth abuse (lockout, enumeration)
- Session tests (fixation/invalidation)

### Phase C

- Request smuggling/desync
- Cache poisoning/deception
- Race conditions
- WebSocket/gRPC/OAuth avances
- DoS controle (toujours borne)

---

## 7) "Exhaustive checklist" des families a couvrir

- [ ] Auth brute force / lockout / enumeration
- [ ] Session fixation / invalidation / token lifecycle
- [ ] Horizontal + vertical authorization (IDOR/BOLA/BFLA)
- [ ] CSRF enforcement
- [ ] CORS actif (origin reflection, credentials)
- [ ] Open redirect
- [ ] Methodes HTTP (OPTIONS/TRACE/HEAD)
- [ ] SQLi (error/time)
- [ ] NoSQLi
- [ ] XSS reflechi (detection)
- [ ] Command injection basique
- [ ] Path traversal
- [ ] File inclusion (LFI/RFI selon techno)
- [ ] XXE
- [ ] SSTI
- [ ] Insecure deserialization
- [ ] Upload abuse (MIME, extension, execution)
- [ ] Mass assignment
- [ ] GraphQL abuse (introspection/depth/alias/batch)
- [ ] API schema validation abuse
- [ ] SSRF applicative
- [ ] Host header injection
- [ ] Cache poisoning / web cache deception
- [ ] HTTP request smuggling / desync
- [ ] Race conditions
- [ ] Business logic abuse
- [ ] WebSocket authz
- [ ] OAuth/OIDC misuse
- [ ] DoS controle (borne)

---

## 8) Ce qui doit rester desactive par defaut

- Tests potentiellement destructifs.
- Scenarios impliquant ecriture irreversible.
- Flood haute frequence longue duree.
- Exploitation complete (RCE, data exfiltration).

Activation uniquement en mode expert, avec opt-in explicite et limites strictes.

---

## 9) Notes produit SecureOps

- Conserver la separation claire:
  - **Scanner passif** (non intrusif)
  - **Scanner actif intrusif** (intrusif, non destructif par defaut)
- Exiger un disclaimer fort cote UI avant lancement actif.
- Montrer un indicateur de risque (`L1-L4`) par test dans le rapport.
- Journaliser toutes les requetes actives pour audit.
