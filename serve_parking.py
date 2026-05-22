"""Serve the SMART_PARK web map and data files locally."""

import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8080


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def main() -> None:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving SMART_PARK at http://127.0.0.1:{PORT}/web/")
        print("Open that URL, then click graph nodes to route to free spots.")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
