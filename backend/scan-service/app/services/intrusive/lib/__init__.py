"""Composants mutualisables pour les checks intrusifs.

Modules :
- http_client      : IntrusiveHTTPClient (injection credentials, jitter, toutes méthodes)
- param_extractor  : extraction de paramètres (query, body, HTML)
- payload_engine   : bibliothèque de payloads par catégorie
- detector         : détection par signatures, timing et diff
- redirect_module  : detection redirections ouvertes
- domain_page_split: constantes domain-phase / per-page
"""
