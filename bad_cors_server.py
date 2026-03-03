"""Serveur HTTP local pour tester les vérifications CORS et cross-origin.

Endpoints volontairement mal configurés pour vérifier que le scanner remonte bien
les findings (ACAO *, réflexion d'origine, méthodes dangereuses, Expose-Headers,
CORP manquant, mixed content).

Endpoints :
- /           : page HTML avec mixed content (script/link/img en http://).
                Mixed content n'est détecté que si l'URL scannée est en HTTPS.
- /index     : page d'accueil sans mixed content.
- /api/      : Access-Control-Allow-Origin: * (endpoint sensible) → finding ACAO *.
- /user/     : idem ACAO * (autre chemin sensible).
- /reflect   : reflète l'origine (ACAO = valeur de l'en-tête Origin) + ACAC: true
               → finding réflexion d'origine non validée.
- /methods   : Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
               → finding méthodes dangereuses.
- /expose    : Access-Control-Expose-Headers: X-Auth-Token, X-Request-ID
               → finding en-têtes sensibles exposés.
Aucun endpoint n'envoie Cross-Origin-Resource-Policy → finding CORP manquant.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler


# Page HTML avec ressources en http:// (mixed content si la page est servie en HTTPS).
MIXED_CONTENT_HTML = b"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Test CORS</title>
  <link rel="stylesheet" href="http://cdn.example.com/style.css">
</head>
<body>
  <h1>Test CORS / mixed content</h1>
  <script src="http://cdn.example.com/lib.js"></script>
  <img src="http://example.com/pixel.gif" alt="">
</body>
</html>
"""

# Page d'accueil minimale (sans mixed content) pour éviter le bruit si on scanne en HTTP.
INDEX_HTML = b"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Bad CORS Server</title></head>
<body>
  <h1>Bad CORS test server</h1>
  <p>Endpoints: /api/, /user/, /reflect, /methods, /expose, /mixed</p>
</body>
</html>
"""


def _send_cors_headers(
    self: BaseHTTPRequestHandler,
    acao: str | None = None,
    acac: str | None = None,
    allow_methods: str | None = None,
    expose_headers: str | None = None,
) -> None:
    """Envoie les en-têtes CORS (sans fermer les headers)."""
    if acao is not None:
        self.send_header("Access-Control-Allow-Origin", acao)
    if acac is not None:
        self.send_header("Access-Control-Allow-Credentials", acac)
    if allow_methods is not None:
        self.send_header("Access-Control-Allow-Methods", allow_methods)
    if expose_headers is not None:
        self.send_header("Access-Control-Expose-Headers", expose_headers)


class BadCorsHandler(BaseHTTPRequestHandler):
    """Handler HTTP qui expose volontairement des configs CORS dangereuses."""

    def _path(self) -> str:
        """Chemin normalisé sans query string."""
        return self.path.split("?")[0].rstrip("/") or "/"

    def _origin(self) -> str | None:
        """Valeur de l'en-tête Origin (insensible à la casse)."""
        return self.headers.get("Origin") or self.headers.get("origin")

    def _send_cors(
        self,
        acao: str | None = None,
        acac: str | None = None,
        allow_methods: str | None = None,
        expose_headers: str | None = None,
    ) -> None:
        _send_cors_headers(self, acao=acao, acac=acac, allow_methods=allow_methods, expose_headers=expose_headers)

    def do_GET(self) -> None:
        """Dispatch GET selon le chemin."""
        path = self._path()

        if path == "/":
            # Page avec mixed content (détecté uniquement si la page est servie en HTTPS).
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MIXED_CONTENT_HTML)
            return

        if path == "/index":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML)
            return

        if path == "/api" or path == "/api/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors(acao="*")
            self.end_headers()
            self.wfile.write(b'{"ok": true}\n')
            return

        if path == "/user" or path == "/user/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors(acao="*")
            self.end_headers()
            self.wfile.write(b'{"user": null}\n')
            return

        if path == "/reflect":
            origin = self._origin() or "https://evil.example.com"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._send_cors(acao=origin, acac="true")
            self.end_headers()
            self.wfile.write(b"Origin reflected (bad)\n")
            return

        if path == "/methods":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._send_cors(allow_methods="GET, POST, PUT, DELETE, PATCH")
            self.end_headers()
            self.wfile.write(b"OK\n")
            return

        if path == "/expose":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("X-Auth-Token", "secret-token-for-test")
            self.send_header("X-Request-ID", "req-123")
            self._send_cors(expose_headers="X-Auth-Token, X-Request-ID")
            self.end_headers()
            self.wfile.write(b"OK\n")
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found\n")

    def do_OPTIONS(self) -> None:
        """Répond à OPTIONS (preflight) avec les mêmes CORS que GET pour chaque chemin."""
        path = self._path()
        origin = self._origin() or "https://evil.example.com"

        self.send_response(204)
        self.send_header("Content-Length", "0")

        if path == "/api" or path == "/api/":
            self._send_cors(acao="*")
        elif path == "/user" or path == "/user/":
            self._send_cors(acao="*")
        elif path == "/reflect":
            self._send_cors(acao=origin, acac="true")
        elif path == "/methods":
            self._send_cors(allow_methods="GET, POST, PUT, DELETE, PATCH")
        elif path == "/expose":
            self._send_cors(expose_headers="X-Auth-Token, X-Request-ID")

        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Réduit le bruit des logs en console."""
        pass


def run() -> None:
    """Lance le serveur sur le port 8003.

    Écoute sur 0.0.0.0 pour être joignable depuis des conteneurs Docker
    (ex. scan-service) via host.docker.internal:8003.
    """
    server_address = ("0.0.0.0", 8003)
    httpd = HTTPServer(server_address, BadCorsHandler)
    print(
        "Serving bad CORS server on http://127.0.0.1:8003\n"
        "  /        -> HTML avec mixed content (http://) — détecté si URL scannée en HTTPS\n"
        "  /index  -> page d'accueil sans mixed content\n"
        "  /api/    -> Access-Control-Allow-Origin: * (sensible)\n"
        "  /user/   -> idem ACAO *\n"
        "  /reflect -> reflète Origin + Credentials: true\n"
        "  /methods -> Allow-Methods: GET, POST, PUT, DELETE, PATCH\n"
        "  /expose  -> Expose-Headers: X-Auth-Token, X-Request-ID\n"
        "(aucun CORP → finding CORP manquant)\n"
        "(écoute 0.0.0.0:8003)"
    )
    httpd.serve_forever()


if __name__ == "__main__":
    run()
