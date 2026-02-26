"""Constantes partagées pour les messages d'erreur de connexion."""

# Message générique pour échec de connexion (réutilisé dans checks et normalizers)
MSG_CONNECTION_REFUSED_OR_TIMEOUT = "connexion refusée ou timeout"

MSG_HEADERS_UNAVAILABLE = f"Impossible de récupérer les en-têtes ({MSG_CONNECTION_REFUSED_OR_TIMEOUT})."
MSG_COOKIES_UNAVAILABLE = f"Impossible d'analyser les cookies ({MSG_CONNECTION_REFUSED_OR_TIMEOUT})."
MSG_ROBOTS_TXT_UNAVAILABLE = f"Impossible de récupérer robots.txt ({MSG_CONNECTION_REFUSED_OR_TIMEOUT})."
MSG_HEADERS_ANALYSIS_UNAVAILABLE = f"Impossible d'analyser les en-têtes ({MSG_CONNECTION_REFUSED_OR_TIMEOUT})."
MSG_HTTPS_UNAVAILABLE = f"HTTPS non activé ({MSG_CONNECTION_REFUSED_OR_TIMEOUT}). Risque d'interception."
