"""Minimal HTTP server exposing the Home Assistant-facing URDB API."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from typing import Type
from urllib.parse import urlsplit

from orchestrator.github_release import (
    DEFAULT_CURRENT_VERSION,
    DEFAULT_REPOSITORY,
    GitHubReleaseClient,
    OrchestratorError,
    token_from_environment,
)

from .api import StatusAPIError, StatusService
from .updater_client import UpdaterClient, UpdaterClientError


def create_server(
    address: tuple[str, int], service: StatusService
) -> ThreadingHTTPServer:
    """Create an HTTP server without starting its event loop."""

    return ThreadingHTTPServer(address, make_handler(service))


def make_handler(service: StatusService) -> Type[BaseHTTPRequestHandler]:
    class StatusRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/status":
                operation = service.get_status
            elif path == "/api/changes":
                operation = service.get_changes
            elif path in {"/api/check", "/api/update", "/api/restart"}:
                self._method_not_allowed("POST")
                return
            else:
                self._not_found()
                return
            try:
                response = operation()
            except (OrchestratorError, StatusAPIError) as error:
                self._json_response(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"health": "error", "error": str(error)},
                )
                return
            self._json_response(HTTPStatus.OK, response)

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/check":
                operation = service.check_now
                status = HTTPStatus.OK
            elif path == "/api/update":
                operation = service.request_update
                status = HTTPStatus.ACCEPTED
            elif path == "/api/restart":
                operation = service.request_restart
                status = HTTPStatus.ACCEPTED
            elif path in {"/api/status", "/api/changes"}:
                self._method_not_allowed("GET")
                return
            else:
                self._not_found()
                return
            try:
                response = operation()
            except (OrchestratorError, StatusAPIError, UpdaterClientError) as error:
                self._json_response(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"health": "error", "error": str(error)},
                )
                return
            self._json_response(status, response)

        def _not_found(self) -> None:
            self._json_response(
                HTTPStatus.NOT_FOUND,
                {"health": "error", "error": "not found"},
            )

        def _method_not_allowed(self, allow: str) -> None:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", allow)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _json_response(
            self, status: HTTPStatus, payload: dict[str, object]
        ) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args: object) -> None:
            return

    return StatusRequestHandler


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(prog="urdb-api")
    parser.add_argument("--host", default=os.environ.get("URDB_API_HOST", "0.0.0.0"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("URDB_API_PORT", "8080"))
    )
    parser.add_argument(
        "--repository", default=os.environ.get("URDB_REPOSITORY", DEFAULT_REPOSITORY)
    )
    parser.add_argument(
        "--current-version",
        default=os.environ.get("URDB_CURRENT_VERSION", DEFAULT_CURRENT_VERSION),
    )
    args = parser.parse_args()

    client = GitHubReleaseClient(
        repository=args.repository,
        current_version=args.current_version,
        token=token_from_environment(),
    )
    updater = UpdaterClient(
        os.environ.get("URDB_UPDATER_URL", "http://urdb-updater:8081"),
        os.environ.get("URDB_UPDATER_TOKEN", ""),
    )
    server = create_server(
        (args.host, args.port), StatusService(client, updater=updater)
    )
    try:
        print(f"URDB status API listening on http://{args.host}:{args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
