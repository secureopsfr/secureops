# Classification des tests web: passif, intrusif, destructeur

Ce document explique **toutes les grandes categories de tests** pour une application web et indique **ou chaque categorie se place**:

- `Passif`
- `Intrusif` (actif non destructif)
- `Destructeur`

Objectif: avoir une taxonomie unique pour SecureOps (produit, backend, frontend, reporting, legal/disclaimer).

---

## 1) Definitions simples

## 1.1 Passif

- Observe les reponses sans provoquer de comportement anormal.
- Pas de payload offensif, pas de sequence agressive, pas d'action d'ecriture.
- Risque operationnel: tres faible.

## 1.2 Intrusif (actif non destructif)

- Envoie des requetes craftes pour provoquer un signal de faille.
- Peut declencher WAF/logs/alertes, mais ne doit pas modifier durablement l'etat.
- Risque operationnel: faible a modere selon intensite.

## 1.3 Destructeur

- Peut affecter disponibilite, integrite, ou provoquer des effets irreversibles.
- Exemples: stress agressif, operations d'ecriture risquee, exploitation poussee.
- Risque operationnel: eleve.

---

## 2) Regle de placement d'un test

Utiliser ces 4 questions:

1. Le test envoie-t-il des payloads anormaux?
   - Non -> plutot passif.
2. Le test change-t-il potentiellement l'etat metier/technique?
   - Oui -> destructeur (ou intrusif a haut risque selon contexte).
3. Le test repose-t-il sur volume/concurrence/epuisement?
   - Oui -> destructeur probable.
4. Le test est-il purement "lecture + verification de reaction"?
   - Oui -> intrusif non destructif.

---

## 3) Cartographie complete des categories de tests

## 3.1 TLS, transport, configuration HTTP

- TLS versions/certificats/HSTS: `Passif`
- Security headers (CSP, XFO, XCTO, etc.): `Passif`
- Methodes HTTP (OPTIONS/TRACE/HEAD): `Intrusif`
- Open redirect actif: `Intrusif`
- Chaines de redirection: `Passif` (si observation) ou `Intrusif` (si forcee par payload)

## 3.2 CORS et cross-origin

- Analyse CORS sur reponse courante: `Passif`
- Probes `Origin` craftes (GET/OPTIONS): `Intrusif`
- Scenarios cross-origin agressifs multi-origines haute cadence: `Destructeur` (rare)

## 3.3 Authentification, session, controle d'acces

- Verification policy visible (cookies, flags, expirations): `Passif`
- Enumeration utilisateur: `Intrusif`
- Brute force/credential stuffing controle: `Intrusif`
- Brute force agressif longue duree: `Destructeur`
- Session fixation/invalidation tests: `Intrusif`
- IDOR/BOLA/BFLA (tests de ressources inter-comptes): `Intrusif`

## 3.4 CSRF

- Detection presence token dans HTML: `Passif`
- Test enforcement (requete sans token / token invalide): `Intrusif`
- Enchainement CSRF sur actions irreversibles sans garde-fous: `Destructeur` potentiel

## 3.5 Injections serveur

- SQLi (error-based/time-based leger): `Intrusif`
- SQLi agressif, payloads lourds/aveugles massifs: `Destructeur`
- NoSQLi: `Intrusif`
- Command injection basique (detection): `Intrusif`
- Tentatives d'execution poussee impactante: `Destructeur`
- SSTI: `Intrusif`
- XXE: `Intrusif` (peut devenir destructeur selon parser/cible)
- Deserialization abuse: `Intrusif` a `Destructeur` selon profondeur

## 3.6 XSS et client-side

- Reflection simple de marqueur: `Intrusif`
- DOM XSS runtime instrumentation (sans exploitation): `Intrusif`
- Exploitation XSS avec actions reelles en session victime: `Destructeur` potentiel (a eviter en auto)
- Prototype pollution client (detection): `Intrusif`
- CSP bypass contextuel (preuve de contournement): `Intrusif`

## 3.7 Fichiers, chemins, ressources

- Exposition fichiers connus (`/.env`, `.git/config`) via lecture: `Intrusif` leger
- Directory listing check: `Intrusif` leger
- Path traversal lecture (`../`): `Intrusif`
- Traversal ecriture/modification: `Destructeur`
- Upload abuse (MIME/extension bypass detection): `Intrusif`
- Upload avec execution ou persistance malveillante: `Destructeur`

## 3.8 API modernes

- GraphQL endpoint exposure (observation): `Passif`/`Intrusif leger`
- GraphQL introspection active: `Intrusif`
- Depth/alias/batch abuse agressif: `Destructeur` possible
- Mass assignment: `Intrusif`
- Schema abuse (type confusion, huge payload): `Intrusif` a `Destructeur`

## 3.9 SSRF, Host header, cache attacks

- SSRF detection via URL params craftes: `Intrusif`
- SSRF vers cibles internes sensibles (sans garde-fous): `Destructeur` potentiel
- Host header injection: `Intrusif`
- Cache poisoning/deception: `Intrusif` a `Destructeur` selon impact prod
- Request smuggling/desync: `Intrusif` eleve (souvent traite comme quasi destructeur)

## 3.10 Business logic et chaines d'attaque

- Verification d'invariants metier sans action irreversible: `Intrusif`
- Abuse workflow avec impacts transactionnels reels: `Destructeur` potentiel
- Chaines d'attaque "preuve de concept" limitee: `Intrusif`
- Chaine complete avec impact reel (fraude/takeover effectif): `Destructeur`

## 3.11 Protocoles speciaux

- WebSocket authz par message: `Intrusif`
- gRPC method authz tests: `Intrusif`
- OAuth/OIDC edge cases (redirect_uri/state/nonce/PKCE): `Intrusif`
- Flood websocket/gRPC pour saturation: `Destructeur`

## 3.12 Disponibilite (DoS)

- Detection absence rate limit sur burst tres court: `Intrusif`
- Slow request leger (1-2 connexions, duree bornee): `Intrusif` eleve
- Stress/flood/saturation: `Destructeur`
- DDoS (multi-source): `Destructeur` critique (hors scope scanner standard)

---

## 4) Tableau resume (placement rapide)

| Categorie | Placement par defaut | Peut devenir destructeur ? |
|---|---|---|
| TLS/headers/cookies (lecture) | Passif | Non |
| Methodes HTTP, CORS probes, redirect actif | Intrusif | Rarement |
| Auth/Authz/IDOR/BOLA | Intrusif | Oui (si abuse reel) |
| CSRF enforcement | Intrusif | Oui |
| SQLi/NoSQLi/SSTI/XXE/Traversal | Intrusif | Oui |
| XSS/DOM/proto pollution | Intrusif | Oui |
| Upload abuse | Intrusif | Oui |
| SSRF/smuggling/cache poisoning | Intrusif eleve | Oui |
| Business logic chaining | Intrusif | Oui |
| DoS/stress/flood | Destructeur | Oui (natif) |

---

## 5) Politique d'execution recommandee SecureOps

## 5.1 Mode Passif

- Uniquement `Passif`.
- Cible: scans frequents, CI, pre-prod/prod avec risque minimal.

## 5.2 Mode Actif Intrusif

- `Passif` + `Intrusif` borne.
- Budgets stricts: nombre de requetes, timeout, concurrence.
- Avertissement legal explicite.

## 5.3 Mode Expert (Risque eleve)

- Inclut certaines families proches `Destructeur`.
- Opt-in fort + autorisation explicite + fenetre de tir.
- Journalisation exhaustive et kill switch.

---

## 6) Checklist de classification pour chaque nouveau test

- [ ] Quel est l'objectif du test?
- [ ] Quelle methode HTTP et quel payload sont utilises?
- [ ] Peut-il modifier des donnees ou etats?
- [ ] Quel est le volume maximal genere?
- [ ] Impact cible possible (disponibilite/integrite/confidentialite)?
- [ ] Classe finale: `Passif` / `Intrusif` / `Destructeur`
- [ ] Garde-fous associes implementes?

---

## 7) Conseils pratiques de reporting

Dans chaque finding, afficher:

- classe du test (`passif`, `intrusif`, `destructeur`),
- niveau de risque execution (`L1` a `L4`),
- evidence technique,
- impact potentiel,
- recommandation corrective.

Cela evite la confusion entre:

- gravite de la faille detectee, et
- risque operationnel du test qui l'a detectee.

---

## 8) Conclusion

Oui, tu peux structurer tout ton produit autour de **3 categories top-level**:

- `Passif`
- `Intrusif`
- `Destructeur`

Puis garder des sous-categories techniques (auth, injections, API, client-side, etc.) pour le detail d'implementation.
