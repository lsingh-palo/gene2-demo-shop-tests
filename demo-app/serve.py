#!/usr/bin/env python3
"""Serve the Gen-e2 Demo Shop locally: one site, two builds.

    python evals/demo-app/serve.py --variant v1 --port 8801     # legacy (the oracle)
    python evals/demo-app/serve.py --variant v2 --port 8802     # replacement (planted regressions)

/config.js is served from variants/<variant>/config.js; everything else from site/.
/promo.json alternates {"show": true} / {"show": false} on every request (a server-side counter),
so a test that asserts the promo banner is visible passes, then fails - deterministically flaky,
for the admission filter's "stable" stage.
/requirements.html serves the requirements page (real <s> strikethrough) for offline source reading.
Standard library only.
"""
import argparse
import functools
import http.server
import itertools
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    variant = "v1"
    promo = itertools.cycle([True, False])

    def log_message(self, *args):
        pass

    def _send(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/config.js":
            return self._send((HERE / "variants" / self.variant / "config.js").read_bytes(), "text/javascript")
        if path == "/promo.json":
            return self._send(json.dumps({"show": next(self.promo)}).encode(), "application/json")
        if path == "/requirements.html":
            return self._send((HERE / "requirements" / "shop-rules.html").read_bytes(), "text/html")
        if path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variant", choices=["v1", "v2"], default="v1")
    p.add_argument("--port", type=int, default=8801)
    p.add_argument("--host", default="127.0.0.1")
    a = p.parse_args()
    Handler.variant = a.variant
    handler = functools.partial(Handler, directory=str(HERE / "site"))
    with http.server.ThreadingHTTPServer((a.host, a.port), handler) as srv:
        print(f"Gen-e2 Demo Shop {a.variant} on http://{a.host}:{a.port}", flush=True)
        srv.serve_forever()


if __name__ == "__main__":
    main()
