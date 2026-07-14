from __future__ import annotations

from datetime import datetime, timezone
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from homeassistant.api import StatusService, extract_changes
from homeassistant.server import create_server
from orchestrator.github_release import OrchestratorError


CHECKED_AT = datetime(2026, 7, 14, 21, 0, tzinfo=timezone.utc)


class FakeReleaseClient:
    def __init__(
        self,
        *,
        has_update: bool = True,
        error: Exception | None = None,
    ) -> None:
        self.has_update = has_update
        self.error = error
        self.info_calls = 0

    def check_updates(self) -> dict[str, object]:
        if self.error is not None:
            raise self.error
        return {
            "current_version": "routing-20260713",
            "latest_version": "routing-20260714",
            "has_update": self.has_update,
            "release_url": "https://example.invalid/release",
        }

    def get_release_info(self) -> dict[str, object]:
        self.info_calls += 1
        return {
            "version": "routing-20260714",
            "date": "2026-07-14T20:00:00Z",
            "artifacts": [],
            "checksum": {},
            "notes": "## Changes\n- YouTube\n- GitHub\n- ChatGPT\n",
        }


class StatusServiceTest(unittest.TestCase):
    def test_status_contains_update_and_release_changes(self):
        service = StatusService(FakeReleaseClient(), clock=lambda: CHECKED_AT)

        self.assertEqual(
            service.get_status(),
            {
                "current_version": "routing-20260713",
                "latest_version": "routing-20260714",
                "has_update": True,
                "changes": ["YouTube", "GitHub", "ChatGPT"],
                "checked_at": "2026-07-14T21:00:00Z",
                "health": "ok",
            },
        )

    def test_no_update_does_not_request_release_notes(self):
        client = FakeReleaseClient(has_update=False)
        service = StatusService(client, clock=lambda: CHECKED_AT)

        result = service.get_status()

        self.assertEqual(result["changes"], [])
        self.assertEqual(client.info_calls, 0)

    def test_changes_require_an_explicit_release_note_section(self):
        self.assertEqual(extract_changes("Updated YouTube and GitHub."), [])
        self.assertEqual(
            extract_changes("## Изменения\n* Telegram\n* Telegram\n* WhatsApp\n"),
            ["Telegram", "WhatsApp"],
        )


class StatusHTTPTest(unittest.TestCase):
    def setUp(self) -> None:
        service = StatusService(FakeReleaseClient(), clock=lambda: CHECKED_AT)
        self.server = create_server(("127.0.0.1", 0), service)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_get_status_returns_json(self):
        with urlopen(self.base_url + "/api/status", timeout=2) as response:
            payload = json.load(response)

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(payload["changes"], ["YouTube", "GitHub", "ChatGPT"])
        self.assertEqual(payload["health"], "ok")

    def test_unknown_endpoint_returns_404(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(self.base_url + "/unknown", timeout=2)

        self.assertEqual(context.exception.code, 404)

    def test_post_returns_405(self):
        request = Request(self.base_url + "/api/status", method="POST")
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)

        self.assertEqual(context.exception.code, 405)
        self.assertEqual(context.exception.headers["Allow"], "GET")

    def test_orchestrator_error_returns_503(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        service = StatusService(
            FakeReleaseClient(error=OrchestratorError("GitHub unavailable")),
            clock=lambda: CHECKED_AT,
        )
        self.server = create_server(("127.0.0.1", 0), service)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address

        with self.assertRaises(HTTPError) as context:
            urlopen(f"http://{host}:{port}/api/status", timeout=2)

        self.assertEqual(context.exception.code, 503)
        payload = json.load(context.exception)
        self.assertEqual(payload["health"], "error")


if __name__ == "__main__":
    unittest.main()
