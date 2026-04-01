# Vérification DNS du domaine — Guide utilisateur

Ce guide décrit le **parcours utilisateur** pour prouver le contrôle d’un domaine avant un scan **non passif**. La spécification technique (API, schéma SQL, assert scan-service) est dans [VERIFICATION-AUTORISATION.md](VERIFICATION-AUTORISATION.md).

**Dans l’application :** le même contenu est disponible dans le hub Scanner sous la page d’aide « Vérification DNS » (`/fr/scanner/docs/verification-dns`).

## En bref

1. Vous saisissez l’URL à scanner pour un scanner autre que le scanner passif (intrusif, personnalisé, destructeur, …).
2. Vous générez des **instructions DNS** : nom d’hôte `_secureops-verify.<domaine>` et **valeur TXT** unique.
3. Vous publiez l’enregistrement **TXT** chez votre fournisseur DNS et attendez la propagation.
4. Vous cliquez sur **Vérifier le TXT** dans SecureOps : le service interroge le DNS public et valide la preuve.
5. Tant que la vérification est valide (non expirée) et associée à votre compte, les scans non passifs correspondants peuvent être lancés (le scan passif, lui, n’exige pas cette preuve).

## Liens utiles

- [Documentation des scans intrusifs (hub)](verifications/intrusive/README.md) — inclut un renvoi vers ce flux.
- [Variables d’environnement](VARIABLES-ENVIRONNEMENT.md) — flags et TTL associés.
