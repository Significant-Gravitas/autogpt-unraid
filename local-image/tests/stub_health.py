#!/usr/bin/env python3
"""Tiny health-only model stub used for the derived-image lifecycle test."""

import http.server
import json


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.rstrip("/") != "/health":
            self.send_error(404)
            return
        body = json.dumps({"status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("0.0.0.0", 8765), Handler).serve_forever()
