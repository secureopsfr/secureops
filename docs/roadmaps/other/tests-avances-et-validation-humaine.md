# Tests avances et validation humaine (complements scanner web)

Ce document couvre les zones qui depassent les checks unitaires "classiques" d'un scanner web:

- business logic profonde,
- tests authentifies avances par role,
- chaines d'attaque multi-faiblesses,
- client-side avance,
- protocoles/cas rares selon stack,
- validation manuelle humaine.

Objectif: definir un cadre **complet** pour augmenter la couverture securite de SecureOps sur des cas a forte valeur, souvent partiellement automatisables.

---

## 1) Business logic profonde

## 1.1 Definition

La business logic concerne les regles metier propres a l'application (prix, workflow, droits contextuels, etats de commande, credits, abonnement, facturation, moderation, etc.).
Ces failles ne sont pas toujours detectables par des signatures techniques simples.

## 1.2 Types de vulnerabilites metier a couvrir

- bypass d'etapes obligatoires (checkout, validation KYC, confirmation 2FA),
- contournement de limites (quota, montant minimum/maximum, nombre de tentatives),
- abus de coupons/promotions/credits (double application, cumul interdit),
- incoherence d'etat (action possible dans un statut non autorise),
- confusion d'identite metier (agence/client, vendeur/acheteur, owner/delegate),
- abus temporel (action hors fenetre, expiration ignoree),
- non-atomicite metier (debit sans livraison, livraison sans debit).

## 1.3 Ce qui est automatisable

- detection de transitions d'etat invalides via modeles de workflow,
- tests de bornes metier (montants, quantites, quotas),
- tests de combinaison de flags/roles pour endpoints critiques,
- fuzzing de champs metier sensibles (prix, devise, remise, statut).

## 1.4 Ce qui reste majoritairement manuel

- interpretation de l'intention metier reelle,
- validation des impacts business (fraude, perte financiere, compliance),
- verification des exceptions legitimes.

## 1.5 Recommandations d'implementation

- maintenir un "model metier securite" par domaine (paiement, commande, abonnement),
- encoder des invariants metier (ex: total >= 0, statut final immuable),
- executer des tests de transitions d'etat automatiques par scenario.

---

## 2) Tests authentifies avances par role (stateful, multi-step)

## 2.1 Definition

Tester non seulement "qui peut appeler un endpoint", mais aussi **quand** et **dans quel etat de session/parcours**.

## 2.2 Matrice de controle a couvrir

- roles (guest, user, manager, admin, support, super-admin),
- scopes (tenant, project, organization),
- etapes de session (pre-login, post-login, 2FA pending, 2FA complete),
- contexte de device (nouveau device, session expiree, remember-me),
- delegation (impersonation, sharing, invitation).

## 2.3 Scenarios critiques

- elevation verticale (user -> admin),
- elevation horizontale (acces ressources d'un autre user/tenant),
- bypass 2FA apres login partiel,
- token replay entre comptes/roles,
- confusion de contexte dans les parcours multi-step (wizard, onboarding, checkout),
- modification d'objets entre etapes sans reverification d'autorisation.

## 2.4 Automatisation recommandee

- moteur de sessions multiples (plusieurs identites paralleles),
- playback de parcours multi-step avec checkpoints,
- verification systematique des assertions authz par etape,
- tests de rehydratation session (refresh token, logout, rotation).

## 2.5 Evidence minimale dans le rapport

- role source, role attendu, endpoint, etape de parcours,
- requetes/responses cles (redactees),
- point exact de bypass.

---

## 3) Chaines d'attaque (attack chaining)

## 3.1 Pourquoi c'est critique

Beaucoup d'incidents viennent d'une combinaison:
faiblesse A (info leak) + faiblesse B (authz faible) + faiblesse C (action sensible) = impact majeur.

## 3.2 Exemples de chaines a couvrir

- info disclosure -> enumeration -> reset account abuse,
- open redirect -> vol de token OAuth -> takeover,
- XSS reflechi/DOM -> vol session -> action admin,
- IDOR lecture -> fuite secret -> action privilegiee,
- CORS mal configure + credentials -> exfiltration API.

## 3.3 Strategie de modelisation

- definir des "graphes d'attaque" par domaine applicatif,
- marquer les preconditions de chaque noeud (auth, role, data),
- tester automatiquement les transitions entre noeuds.

## 3.4 Scoring recommande

- score par weak signal unitaire,
- score majore si chaine exploitable complete,
- confidence score selon nombre de preconditions verifiees.

## 3.5 Sortie rapport attendue

- sequence reproduite (etape 1 -> 2 -> 3),
- niveau d'impact final (account takeover, fuite massive, fraude),
- mitigation defensive par etape.

---

## 4) Client-side avance

## 4.1 Surface client-side a ne pas sous-estimer

- DOM XSS contextuelle,
- prototype pollution frontend,
- CSP bypass contextuel,
- postMessage insecure handling,
- stockage navigateur (localStorage/sessionStorage/indexedDB),
- service worker abuse,
- supply chain frontend (scripts tiers, bundler artifacts).

## 4.2 DOM XSS complexe

A couvrir:

- sinks dynamiques (innerHTML, outerHTML, insertAdjacentHTML, eval-like),
- contextes mixtes (HTML -> attribute -> JS),
- routes SPA et hash-based navigation,
- templates client modifies runtime.

Automatisation:

- instrumentation navigateur (runtime hooks),
- payload IDs traces dans DOM final,
- correlation source -> sink.

## 4.3 Prototype pollution front

A tester:

- merge profonds non proteges,
- parsing d'objets depuis query/hash/storage,
- impact sur logique d'autorisation client et requetes API.

Signal:

- proprietes heritees modifiees,
- comportement applicatif altere.

## 4.4 CSP bypass contextuel

Verifier:

- directives reellement appliquees sur toutes les routes,
- presence de nonces/hashes coherents,
- faiblesses (`unsafe-inline`, wildcards, data: excessif),
- regressions CSP selon environnement build/deploy.

## 4.5 Outillage recommande

- navigateur pilote (headless + traces),
- snapshots DOM et network,
- collecteur des violations CSP,
- mode "stateful user journey" cote front.

---

## 5) Cas rares / protocoles speciaux selon stack

## 5.1 WebSocket fin

Points a couvrir:

- authn/authz par message (pas uniquement au handshake),
- validation des actions subscribe/publish,
- isolation des channels/rooms/tenants,
- replay/race sur messages sensibles,
- gestion des limites de debit.

## 5.2 gRPC complet

Points a couvrir:

- methodes exposees non documentees,
- authz par methode/service,
- metadata/headers trustes a tort,
- taille et type de message (schema abuse),
- reflection service exposure non maitrisee.

## 5.3 OAuth/OIDC edge cases exhaustifs

- validation stricte `redirect_uri`,
- enforcement `state` et `nonce`,
- PKCE obligatoire pour clients publics,
- gestion refresh token rotation/reuse detection,
- confusion d'issuer/audience,
- token leakage via referer/logs/URL fragments.

## 5.4 Autres protocoles selon contexte

- SSE auth boundaries,
- file parser APIs (CSV/XML/PDF/image) et parser abuse,
- webhook verification (signature, replay protection).

---

## 6) Validation manuelle humaine (indispensable)

## 6.1 Pourquoi l'humain reste necessaire

Un scanner automatise detecte des patterns.
Un testeur humain comprend l'intention metier, l'impact reel, et les chemins non prevus.

## 6.2 Cadre de validation manuelle recommande

- revue des findings high/critical (triage technique),
- revue des scenarios metier sensibles (triage business),
- tentative de reproduction minimale controlee,
- verification de l'exploitabilite reelle en contexte,
- red team light sur chaines d'attaque plausibles.

## 6.3 Checklist manuelle prioritaire

- [ ] takeover compte possible ?
- [ ] escalade privilege plausible ?
- [ ] fuite de donnees sensibles exploitable ?
- [ ] impact financier/fraude possible ?
- [ ] impact legal/compliance (RGPD, PCI, etc.) ?
- [ ] mitigation proposee realiste pour l'equipe dev ?

## 6.4 Livrables attendus

- rapport de validation humaine (findings confirmes/infirmes),
- niveau de confiance final par finding,
- scenario exploit bout en bout quand applicable,
- plan de remediations priorise.

---

## 7) Architecture cible pour SecureOps (hybride auto + humain)

## 7.1 Pipeline recommande

1. scan passif (baseline),
2. scan actif intrusif (checks unitaires),
3. module avance stateful (roles, workflows, client-side),
4. moteur de chaines d'attaque,
5. validation humaine assistee.

## 7.2 Separation des modes

- `mode_standard`: passif + actif leger (CI/CD friendly),
- `mode_avance`: stateful + chaines + client-side pousse,
- `mode_expert`: protocoles rares + tests a risque plus eleve.

## 7.3 Gouvernance

- activation explicite des modes avances,
- traces et audit complets,
- revues periodiques des faux positifs/faux negatifs,
- bibliotheque de scenarios metier par secteur.

---

## 8) Plan d'implementation progressif

## Phase 1 (fort ROI)

- matrice roles x endpoints critiques,
- parcours multi-step authentifies,
- chaines d'attaque simples (2-3 maillons),
- instrumentation DOM XSS de base.

## Phase 2

- prototype pollution et CSP contextuelle,
- moteur WebSocket authz,
- OAuth/OIDC edge cases principaux,
- scoring de chaines d'attaque.

## Phase 3

- gRPC complet, cas rares selon stack clients,
- catalogues metier sectoriels,
- assistant de validation manuelle integre.

---

## 9) Criteres de maturite

Niveau "bon scanner web":

- couvre OWASP techniques classiques + quelques tests actifs.

Niveau "enterprise web app":

- couvre aussi roles stateful, business logic, attack chaining, client-side avance.

Niveau "pentest-assist":

- combine automation avancee + validation humaine structuree.

---

## 10) Conclusion pratique

Pour SecureOps, la meilleure strategie n'est pas "tout automatiser", mais:

- automatiser au maximum le repetable,
- modeliser explicitement le metier et les roles,
- traiter les chaines d'attaque comme des objets de premier rang,
- garder une validation humaine formelle pour les cas a impact majeur.
