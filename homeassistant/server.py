"""Minimal HTTP server exposing the read-only URDB status endpoint."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
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


def create_server(
    address: tuple[str, int], service: StatusService
) -> ThreadingHTTPServer:
    """Create an HTTP server without starting its event loop."""

    return ThreadingHTTPServer(address, make_handler(service))


def make_handler(service: StatusService) -> Type[BaseHTTPRequestHandler]:
    class StatusRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if urlsplit(self.path).path != "/api/status":
                self._json_response(
                    HTTPStatus.NOT_FOUND,
                    {"health": "error", "error": "not found"},
                )
                return
            try:
                response = service.get_status()
            except (OrchestratorError, StatusAPIError) as error:
                self._json_response(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"health": "error", "error": str(error)},
                )
                return
            self._json_response(HTTPStatus.OK, response)

        def do_POST(self) -> None:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", "GET")
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
    server = create_server((args.host, args.port), StatusService(client))
    try:
        print(f"URDB status API listening on http://{args.host}:{args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
