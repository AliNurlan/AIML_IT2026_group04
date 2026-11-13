"""Local-only web interface for Gemini website generation."""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

from generator import MAX_HTML, generate_site, validate_site

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def _allowed_host(self) -> bool:
        return self.headers.get("Host", "") in {f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}"}

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not self._allowed_host():
            self.send_error(403)
            return
        paths = {"/": ("index.html", "text/html"), "/app.css": ("app.css", "text/css"), "/app.js": ("app.js", "text/javascript")}
        item = paths.get(urlsplit(self.path).path)
        if item is None:
            self.send_error(404)
            return
        body = (WEB / item[0]).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", item[1] + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        expected_origin = "http://" + self.headers.get("Host", "")
        if not self._allowed_host() or self.headers.get("Origin") != expected_origin:
            # Drain small rejected bodies so Windows does not reset the connection
            # before the client can read the 403 response.
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if 0 < length <= MAX_HTML * 6:
                    self.connection.settimeout(5)
                    self.rfile.read(length)
            except (ValueError, OSError):
                self.close_connection = True
            self._json(403, {"error": "Request must come from the local app."})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "Expected application/json."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_HTML * 6:
                raise ValueError("Invalid request size.")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            if self.path == "/api/generate":
                prompt = data.get("prompt", "")
                model = data.get("model", "gemini-3.5-flash-lite")
                if not isinstance(prompt, str) or not 10 <= len(prompt.strip()) <= 5000:
                    raise ValueError("Description must contain 10–5,000 characters.")
                if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", model):
                    raise ValueError("Invalid model name.")
                site = generate_site(prompt.strip(), model)
                self._json(200, {"title": site.title[:150], "html": site.html, "tests": validate_site(site.html)})
            elif self.path == "/api/validate":
                self._json(200, {"tests": validate_site(data.get("html"))})
            else:
                self._json(404, {"error": "Unknown endpoint."})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            logging.error("Request failed: %s", type(exc).__name__)
            code = re.search(r"\b(429|503|504)\b", str(exc))
            if code:
                detail = f"Gemini returned {code.group(1)} (rate limit or temporary unavailability). Try again or select another model."
            else:
                detail = "Gemini request failed. Check model access, API quota, network, and server logs."
            self._json(502, {"error": detail})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local website generator.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Website generator: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
