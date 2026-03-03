"""Serveur HTTP local pour tester les vérifications Information disclosure.

Endpoints volontairement « fuiteurs » pour vérifier que le scanner remonte bien
les findings (stack trace, mode debug, headers de débogage, versions, etc.).

Endpoints :
- /           : page avec stack trace + headers révélateurs (tout en un).
- /stack-trace : corps avec trace Python (stack trace).
- /debug      : corps avec message type « Development server » / DEBUG = True.
- /secret     : JSON avec pattern type api_key (valeur factice pour test uniquement).
- /headers    : uniquement en-têtes révélateurs (X-Debug, Server avec version, etc.).
"""

from http.server import HTTPServer, BaseHTTPRequestHandler


STACK_TRACE_BODY = b"""Internal Server Error

Traceback (most recent call last):
  File "/var/www/app/views.py", line 42, in get_user
    user = User.objects.get(pk=user_id)
  File "/usr/lib/python3/site-packages/django/db/models/query.py", line 404
    return self.get(*args, **kwargs)
DoesNotExist: User matching query does not exist.
"""

DEBUG_BODY = b"""<!DOCTYPE html>
<html>
<head><title>Django</title></head>
<body>
<h1>Development server</h1>
<p>You are seeing this error because you have DEBUG = True in your Django settings.</p>
<p>FLASK_DEBUG=1 is enabled. Do not use in production.</p>
</body>
</html>
"""

SECRET_BODY = b'''{"config": {"api_key": "sk_live_abcd1234efgh5678ijklmnop", "name": "test-app"}}'''

# En-têtes volontairement révélateurs (pour tests du scanner).
REVEALING_HEADERS = {
    "Server": "Apache/2.4.41 (Ubuntu)",
    "X-Powered-By": "PHP/8.2.0",
    "X-AspNet-Version": "4.0.30319",
    "X-Debug": "1",
    "X-Debug-Token": "a1b2c3d4e5",
    "X-Runtime": "0.042",
    "X-Generator": "Drupal 10",
}


class BadInformationDisclosureHandler(BaseHTTPRequestHandler):
    """Handler HTTP qui expose volontairement des fuites pour tester le scanner."""

    def do_GET(self) -> None:
        """Dispatch selon le chemin : /, /stack-trace, /debug, /secret, /headers."""
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._add_revealing_headers()
            self.end_headers()
            self.wfile.write(STACK_TRACE_BODY)
            return

        if path == "/stack-trace":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(STACK_TRACE_BODY)
            return

        if path == "/debug":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DEBUG_BODY)
            return

        if path == "/secret":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(SECRET_BODY)
            return

        if path == "/headers":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._add_revealing_headers()
            self.end_headers()
            self.wfile.write(b"OK (headers only for test)\n")
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found\n")

    def _add_revealing_headers(self) -> None:
        """Ajoute les en-têtes révélateurs (Server, X-Debug, etc.)."""
        for name, value in REVEALING_HEADERS.items():
            self.send_header(name, value)

    def log_message(self, format: str, *args: object) -> None:
        """Réduit le bruit des logs en console."""
        pass


def run() -> None:
    """Lance le serveur sur le port 8002.

    Écoute sur 0.0.0.0 pour être joignable depuis des conteneurs Docker
    (ex. scan-service) via host.docker.internal:8002.
    """
    server_address = ("0.0.0.0", 8002)
    httpd = HTTPServer(server_address, BadInformationDisclosureHandler)
    print(
        "Serving bad information disclosure server on http://127.0.0.1:8002\n"
        "  /           -> stack trace + headers\n"
        "  /stack-trace -> stack trace only\n"
        "  /debug      -> debug mode message\n"
        "  /secret     -> fake api_key in JSON\n"
        "  /headers    -> revealing headers only\n"
        "(écoute 0.0.0.0:8002)"
    )
    httpd.serve_forever()


if __name__ == "__main__":
    run()
