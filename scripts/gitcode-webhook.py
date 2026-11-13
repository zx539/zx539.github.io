#!/usr/bin/env python3
"""Small GitCode push webhook that starts the local deployment script.

It intentionally uses only the Python standard library so it can run on a
minimal Ubuntu server. Put it behind a firewall or reverse proxy and set a
long random WEBHOOK_SECRET before starting it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HOST = os.environ.get("WEBHOOK_HOST", "127.0.0.1")
PORT = int(os.environ.get("WEBHOOK_PORT", "9001"))
SECRET = os.environ.get("WEBHOOK_SECRET", "")
BRANCH = os.environ.get("DEPLOY_BRANCH", "codex/sakura-template-layout")
DEPLOY_SCRIPT = Path(os.environ.get("DEPLOY_SCRIPT", str(Path(__file__).with_name("deploy.sh"))))
DEPLOY_LOG = Path(os.environ.get("DEPLOY_LOG", "/var/log/myblog/deploy.log"))
MAX_BODY_BYTES = int(os.environ.get("WEBHOOK_MAX_BODY_BYTES", "1048576"))
PENDING_DEPLOYMENT = threading.Event()


def _constant_time_match(value: str, expected: str) -> bool:
    return bool(value) and hmac.compare_digest(value.encode("utf-8"), expected.encode("utf-8"))


def _authorized(handler: BaseHTTPRequestHandler, body: bytes) -> bool:
    if not SECRET:
        return False

    if _constant_time_match(handler.headers.get("X-GitCode-Token", ""), SECRET):
        return True
    expected = "sha256=" + hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return _constant_time_match(handler.headers.get("X-GitCode-Signature-256", ""), expected)


def deployment_worker() -> None:
    while True:
        PENDING_DEPLOYMENT.wait()
        # Pushes during the build set this again and trigger another fetch.
        PENDING_DEPLOYMENT.clear()
        try:
            with DEPLOY_LOG.open("ab") as log_file:
                result = subprocess.run(
                    ["/bin/bash", str(DEPLOY_SCRIPT)],
                    stdin=subprocess.DEVNULL,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            if result.returncode:
                logging.error("deployment failed (exit %s); see %s", result.returncode, DEPLOY_LOG)
        except OSError:
            logging.exception("could not start deployment")


def _json_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "GitCodeWebhook/1.0"

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(15)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            _json_response(self, HTTPStatus.OK, {"ok": True})
            return
        _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/gitcode-webhook":
            _json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            _json_response(self, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid body size"})
            return

        body = self.rfile.read(length)
        if not _authorized(self, body):
            _json_response(self, HTTPStatus.UNAUTHORIZED, {"error": "invalid webhook secret"})
            return

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "body must be JSON"})
            return

        if not isinstance(payload, dict):
            _json_response(self, HTTPStatus.BAD_REQUEST, {"error": "body must be a JSON object"})
            return

        event = payload.get("object_kind") or payload.get("event_name")
        if event and event != "push":
            _json_response(self, HTTPStatus.OK, {"ok": True, "ignored": "event"})
            return
        if payload.get("ref") != f"refs/heads/{BRANCH}":
            _json_response(self, HTTPStatus.OK, {"ok": True, "ignored": "branch"})
            return
        if payload.get("deleted") or payload.get("after") == "0" * 40:
            _json_response(self, HTTPStatus.OK, {"ok": True, "ignored": "deleted branch"})
            return

        PENDING_DEPLOYMENT.set()
        _json_response(self, HTTPStatus.ACCEPTED, {"ok": True, "deployment": "queued"})


def main() -> None:
    if not SECRET:
        raise SystemExit("WEBHOOK_SECRET must be set")
    if not DEPLOY_SCRIPT.is_file():
        raise SystemExit(f"deployment script not found: {DEPLOY_SCRIPT}")
    DEPLOY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DEPLOY_LOG.open("ab"):
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = ThreadingHTTPServer((HOST, PORT), WebhookHandler)
    threading.Thread(target=deployment_worker, daemon=True).start()
    print(f"listening on http://{HOST}:{server.server_address[1]}/gitcode-webhook", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
