"""Messages partagés pour les findings (source unique : app/errors/messages.json).

Dépréciation de la duplication : tous les messages sont chargés depuis messages.json.
"""

import json
from pathlib import Path

_MESSAGES_PATH = Path(__file__).resolve().parent / "errors" / "messages.json"
with _MESSAGES_PATH.open(encoding="utf-8") as f:
    _M = json.load(f)

# Alias pour compatibilité (checks, normalizers)
MSG_CONNECTION_REFUSED_OR_TIMEOUT = _M["connection_refused_or_timeout"]
MSG_HEADERS_UNAVAILABLE = _M["headers_unavailable"]
MSG_COOKIES_UNAVAILABLE = _M["cookies_unavailable"]
MSG_ROBOTS_TXT_UNAVAILABLE = _M["robots_txt_unavailable"]
MSG_HEADERS_ANALYSIS_UNAVAILABLE = _M["headers_analysis_unavailable"]
MSG_HTTPS_UNAVAILABLE = _M["https_unavailable"]
