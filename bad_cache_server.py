"""Petit serveur HTTP local pour tester les vérifications cache.

Endpoints :
- /login : page sensible avec mauvaise configuration de cache
- /static/main.abc123.js : asset immuable avec cache trop court
"""

from http.server import HTTPServer, BaseHTTPRequestHandler


class BadCacheHandler(BaseHTTPRequestHandler):
    """Handler HTTP simple avec des headers de cache volontairement mauvais."""

    def do_GET(self) -> None:
        """Gère les requêtes GET pour les endpoints de test.

        - /login : page sensible avec Cache-Control public, max-age=3600
          et Pragma: no-cache (incohérent).
        - /static/main.abc123.js : asset immuable avec Cache-Control
          public, max-age=60 (cache trop court, sans immutable).
        """
        if self.path == "/login":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(
                b"""<html><body>
<h1>Login</h1>
<form action="/login" method="post">
  <input type="text" name="username" />
  <input type="password" name="password" />
</form>
<script src="/static/main.abc123.js"></script>
</body></html>
""",
            )
        elif self.path == "/static/main.abc123.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.send_header("Cache-Control", "public, max-age=60")
            self.end_headers()
            self.wfile.write(b"console.log('bad cache config');\n")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found\n")


def run() -> None:
    """Lance le serveur HTTP sur le port 8001.

    Écoute sur 0.0.0.0 pour être joignable depuis des conteneurs Docker
    (ex. scan-service) via host.docker.internal:8001.
    """
    server_address = ("0.0.0.0", 8001)
    httpd = HTTPServer(server_address, BadCacheHandler)
    print("Serving bad cache test server on http://127.0.0.1:8001 (écoute 0.0.0.0:8001) ...")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
