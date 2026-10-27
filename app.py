"""Local dashboard server. Run: python app.py, then open http://127.0.0.1:8000."""
from dataclasses import fields
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import mimetypes
from simulator import Config, compare

ROOT = Path(__file__).resolve().parent / "static"
USER_FIELDS = {"nodes", "duration", "seed", "scenario", "traffic", "horizon", "alpha"}


@lru_cache(maxsize=8)
def cached_run(key):
    return json.dumps(compare(Config(**json.loads(key))), allow_nan=False).encode()


def config_from_payload(payload):
    if not isinstance(payload, dict) or set(payload) - USER_FIELDS:
        raise ValueError("Unsupported configuration fields")
    for name, value in payload.items():
        if name in {"nodes", "duration", "seed", "horizon"}:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
        elif name in {"traffic", "alpha"}:
            if type(value) not in (float, int):
                raise ValueError(f"{name} must be a number")
        elif not isinstance(value, str):
            raise ValueError("scenario must be a string")
    c = Config(**payload)
    c.validate()
    return c


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, body, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/simulate":
            self.send_bytes(b'{"error":"Not found"}', status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 4096:
                raise ValueError("Request must be 1-4096 bytes")
            payload = json.loads(self.rfile.read(length))
            config_from_payload(payload)
            result = cached_run(json.dumps(payload, sort_keys=True))
            self.send_bytes(result)
        except (ValueError, TypeError, OverflowError) as exc:
            self.send_bytes(json.dumps({"error": str(exc)}).encode(), status=400)

    def do_GET(self):
        route = self.path.split("?", 1)[0]
        files = {"/": "index.html", "/index.html": "index.html",
                 "/demo_data.js": "demo_data.js"}
        if route not in files:
            self.send_bytes(b'{"error":"Not found"}', status=404)
            return
        path = ROOT / files[route]
        if not path.is_file():
            self.send_bytes(b'{"error":"File missing"}', status=404)
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_bytes(path.read_bytes(), mime + "; charset=utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    print(f"PAMR dashboard: http://127.0.0.1:{args.port}", flush=True)
    print("Local simulation; no external services. Ctrl+C stops the server.", flush=True)
    try:
        ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
