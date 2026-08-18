#!/usr/bin/env python3
"""
Local dev server - runs the REAL Lambda handler (lambda_function.py) behind
a plain HTTP server, so you can exercise the actual backend code on your
machine without deploying anything to AWS.

Requires a MongoDB reachable at MONGO_HOST/MONGO_PORT. Easiest way to get
one locally:

    docker run -d --name notice-mongo -p 27017:27017 mongo:7

Then run this server:

    cd backend
    pip install -r requirements.txt
    python local_server.py

And point the frontend dev server at it (in another terminal):

    cd frontend
    npm install
    VITE_API_URL=http://localhost:8000 npm run dev
"""
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_PORT", "27017")
os.environ.setdefault("MONGO_DB", "noticeboard")

import lambda_function  # noqa: E402  (import after env defaults are set)

PORT = int(os.environ.get("PORT", 8000))


class Handler(BaseHTTPRequestHandler):
    def _invoke(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        path_params = {}

        # naive route match for /notices/{id}
        parts = [p for p in path.split("/") if p]
        if len(parts) == 2 and parts[0] == "notices":
            path_params["id"] = parts[1]
            path = "/notices"

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else None

        event = {
            "requestContext": {"http": {"method": method, "path": path}},
            "pathParameters": path_params,
            "body": body,
        }
        response = lambda_function.handler(event, None)

        self.send_response(response["statusCode"])
        for key, value in response.get("headers", {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write((response.get("body") or "").encode())

    def do_GET(self):
        self._invoke("GET")

    def do_POST(self):
        self._invoke("POST")

    def do_PUT(self):
        self._invoke("PUT")

    def do_DELETE(self):
        self._invoke("DELETE")

    def do_OPTIONS(self):
        self._invoke("OPTIONS")

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print(
        f"Local Notice Board API on http://localhost:{PORT} "
        f"(Mongo: {os.environ['MONGO_HOST']}:{os.environ['MONGO_PORT']})"
    )
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()