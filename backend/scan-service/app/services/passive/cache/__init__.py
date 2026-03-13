"""Vérifications Cache et performances (headers de cache et sous-ressources).

Ce package regroupe les contrôles décrits dans
``docs/verifications/cache-et-performances.md`` :

- analyse des en-têtes de cache sur la page principale (Cache-Control, Pragma,
  ETag, Last-Modified, Vary) ;
- détection des pages sensibles cacheables publiquement ;
- analyse d'un sous-ensemble de sous-ressources (scripts, CSS, images) pour
  vérifier la présence de directives de cache adaptées, en particulier pour les
  assets immuables (fichiers avec hash).
"""
