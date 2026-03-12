# Taxonomie complete des tests web (produit + moteur)

Ce document unifie la classification des tests de SecureOps en **2 niveaux**:

1. **Macro-categories produit** (pilotage, UX, roadmap, reporting)
2. **Categories techniques moteur** (implementation scanner)

Il ajoute aussi un placement operationnel par classe:

- `passif`
- `intrusif` (actif non destructif)
- `destructeur` (a activer en mode expert uniquement)

---

## 1) Niveau 1: Macro-categories produit (6)

Ces 6 categories servent de structure principale cote produit, roadmap, dashboard et PDF.

### 1. Business logic

- But: detecter les contournements de regles metier.
- Exemples: bypass workflow, limites tarifaires, abus de credit/coupon.
- Nature dominante: `intrusif` (certains scenarios peuvent devenir `destructeur`).

### 2. Auth / session / roles (stateful)

- But: verifier authn/authz sur parcours complets et contextuels.
- Exemples: lockout, session fixation, IDOR/BOLA/BFLA, CSRF enforcement.
- Nature dominante: `intrusif`.

### 3. Chaines d'attaque (multi-faiblesses)

- But: combiner plusieurs signaux en scenario d'impact reel.
- Exemples: open redirect -> OAuth token abuse, XSS -> session abuse.
- Nature dominante: `intrusif` (peut devenir `destructeur` selon profondeur).

### 4. Client-side avance

- But: couvrir les failles navigateur/front non visibles uniquement cote backend.
- Exemples: DOM XSS complexe, prototype pollution, CSP bypass contextuel.
- Nature dominante: `intrusif`.

### 5. Protocoles speciaux

- But: traiter les stacks moins "HTTP classique".
- Exemples: WebSocket authz fine, gRPC, OAuth/OIDC edge cases.
- Nature dominante: `intrusif` (certaines variantes stress peuvent etre `destructeur`).

### 6. Validation humaine (triage/exploitabilite reelle)

- But: confirmer/infirmer l'exploitabilite et l'impact metier.
- Exemples: reproduction guidee, triage faux positifs, chaines realistes.
- Nature: hors classification technique (processus humain complementaire).

---

## 2) Niveau 2: Categories techniques de tests actifs (29 familles)

Ces families correspondent au moteur scanner et a la checklist technique.

## 2.1 Identite et acces

1. Auth bruteforce / lockout
2. Session management (fixation, invalidation, rotation)
3. IDOR/BOLA/BFLA (horizontal/vertical authz)
4. CSRF

## 2.2 Web/API classiques

5. CORS actif
6. Open redirect
7. Methodes HTTP (OPTIONS/TRACE/HEAD)

## 2.3 Injections

8. SQL injection
9. NoSQL injection
10. XSS (reflected/DOM detection)
11. Command injection
12. Path traversal
13. File inclusion (LFI/RFI selon stack)
14. XXE
15. SSTI
16. Insecure deserialization

## 2.4 API et donnees

17. Upload abuse
18. Mass assignment
19. GraphQL abuse (introspection/depth/alias/batch)
20. Schema abuse (type confusion, validation gaps)

## 2.5 Infrastructure HTTP

21. SSRF
22. Host header injection
23. Cache poisoning/deception
24. Request smuggling/desync

## 2.6 Avance

25. Race conditions
26. Business logic abuse
27. WebSocket authz
28. OAuth/OIDC misuse
29. DoS controle

---

## 3) Mapping: 29 familles -> 6 macro-categories

## 3.1 Auth / session / roles (stateful)

- 1 Auth bruteforce/lockout
- 2 Session management
- 3 IDOR/BOLA/BFLA
- 4 CSRF

## 3.2 Client-side avance

- 10 XSS (partie DOM et contexte navigateur)
- 15 SSTI (selon rendu front/server templates)

## 3.3 Protocoles speciaux

- 19 GraphQL abuse
- 27 WebSocket authz
- 28 OAuth/OIDC misuse

## 3.4 Business logic

- 26 Business logic abuse
- 17 Upload abuse (quand impact metier)
- 18 Mass assignment (sur objets metier)
- 20 Schema abuse (selon regles metier)

## 3.5 Chaines d'attaque

- 21 SSRF
- 23 Cache poisoning/deception
- 24 Request smuggling/desync
- 25 Race conditions
- + combinaisons multi-familles (ex: 5+28, 10+2, 3+26)

## 3.6 Validation humaine

- Couvre transversalement les 29 familles pour confirmation d'exploitabilite.

---

## 4) Mapping: familles -> passif / intrusif / destructeur

Regle pratique:

- `passif`: observation sans payload offensif ni sequence agressive
- `intrusif`: payloads/requetes actives bornees, sans impact irreversible
- `destructeur`: risque de perturbation/ecriture/exploitation poussee

### 4.1 Par defaut en scanner actif

- Familles 1 a 29: classe par defaut `intrusif`
- Exception operationnelle:
  - 29 DoS controle: `intrusif` si strictement borne, sinon `destructeur`
  - 24 Request smuggling/desync: `intrusif eleve` (proche destructeur en prod)
  - 25 Race conditions: `intrusif` a `destructeur` selon action ciblee

### 4.2 Equivalent passif possible (quand applicable)

Certaines familles ont une version "signal passif":

- CORS (lecture headers) -> `passif`
- CSRF (presence token) -> `passif`
- GraphQL endpoint exposure -> `passif`
- Methodes HTTP observees via reponse existante -> `passif` partiel

Mais la verification forte reste `intrusif`.

---

## 5) Utilisation concrete dans le produit

## 5.1 UI/UX

- Filtre 1: Macro-categorie (6)
- Filtre 2: Famille technique (29)
- Badge execution: `passif`, `intrusif`, `destructeur`

## 5.2 Reporting

Pour chaque finding:

- macro-categorie
- famille technique
- classe execution
- gravite faille (separee de la classe execution)
- evidence + confiance + recommandations

## 5.3 Governance

- `destructeur` desactive par defaut
- activation explicite mode expert + garde-fous
- audit trail obligatoire pour intrusif/destructeur

---

## 6) Checklist d'adoption

- [ ] Les 6 macro-categories sont exposees partout (frontend, API, PDF)
- [ ] Les 29 familles ont un identifiant stable cote backend
- [ ] Chaque test a un champ `execution_class` (`passif|intrusif|destructeur`)
- [ ] Les disclaimers UI sont alignes avec `execution_class`
- [ ] Les exports (CSV/JSON/PDF) incluent les 3 niveaux: macro, famille, execution

---

## 7) Resume

Ta structure cible est:

- **Niveau produit:** 6 macro-categories
- **Niveau moteur:** 29 familles techniques
- **Niveau risque operationnel:** passif / intrusif / destructeur

C'est une base solide, scalable, et lisible pour les devs, le produit et les clients.
