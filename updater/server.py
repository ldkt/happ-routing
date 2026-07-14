"""Internal authenticated HTTP facade for Docker lifecycle operations."""

from __future__ import annotations

import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
from pathlib import Path
import subprocess
import threading
import time
from typing import Callable, Type
from urllib.parse import urlsplit

from .pipeline import DockerPipeline, UpdateError


LOGGER = logging.getLogger("urdb.updater")


class OperationQueue:
    """Run one destructive Docker operation at a time in the background."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def submit(self, name: str, operation: Callable[[], None]) -> bool:
        if not self._lock.acquire(blocking=False):
            return False
        threading.Thread(
            target=self._run,
            args=(name, operation),
            daemon=True,
        ).start()
        return True

    def _run(self, name: str, operation: Callable[[], None]) -> None:
        try:
            # Let the API return HTTP 202 before a restart can terminate it.
            time.sleep(0.5)
            operation()
        except (OSError, subprocess.CalledProcessError, UpdateError) as error:
            LOGGER.error("%s operation failed: %s", name, error)
        finally:
            self._lock.release()


def create_server(
    address: tuple[str, int],
    pipeline: DockerPipeline,
    token: str,
    *,
    queue: OperationQueue | None = None,
) -> ThreadingHTTPServer:
    if not token:
        raise ValueError("URDB_UPDATER_TOKEN must not be empty")
    return ThreadingHTTPServer(address, make_handler(pipeline, token, queue=queue))


def make_handler(
    pipeline: DockerPipeline,
    token: str,
    *,
    queue: OperationQueue | None = None,
) -> Type[BaseHTTPRequestHandler]:
    operations = queue or OperationQueue()

    class UpdaterRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if urlsplit(self.path).path == "/health":
                self._json(HTTPStatus.OK, {"health": "ok"})
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {token}"):
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            path = urlsplit(self.path).path
            if path == "/update":
                name, operation, message = "update", pipeline.update, "Update scheduled"
            elif path == "/restart":
                name, operation, message = (
                    "restart",
                    pipeline.restart,
                    "Restart scheduled",
                )
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if not operations.submit(name, operation):
                self._json(
                    HTTPStatus.CONFLICT,
                    {"accepted": False, "message": "Operation already running"},
                )
                return
            self._json(HTTPStatus.ACCEPTED, {"accepted": True, "message": message})

        def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
            content = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args: object) -> None:
            return

    return UpdaterRequestHandler


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    pipeline = DockerPipeline(
        image=os.environ.get("URDB_IMAGE", "ghcr.io/ldkt/happ-routing:latest"),
        compose_file=Path(os.environ.get("URDB_COMPOSE_FILE", "/deployment/docker-compose.yml")),
    )
    server = create_server(
        ("0.0.0.0", 8081),
        pipeline,
        os.environ.get("URDB_UPDATER_TOKEN", ""),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
