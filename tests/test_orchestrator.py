from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

from orchestrator.cli import main
from orchestrator.github_release import GitHubReleaseClient, OrchestratorError


API_URL = "https://api.github.com/repos/ldkt/happ-routing/releases/latest"
SUMS_URL = "https://downloads.example/SHA256SUMS"
PROFILE_URL = "https://downloads.example/happ-routing.json"
PROFILE_DIGEST = "a" * 64


def release_payload(*, tag: str = "routing-20260714") -> bytes:
    return json.dumps(
        {
            "tag_name": tag,
            "html_url": "https://github.com/ldkt/happ-routing/releases/tag/" + tag,
            "published_at": "2026-07-14T12:00:00Z",
            "body": "Immutable routing data release.",
            "assets": [
                {
                    "name": "happ-routing.json",
                    "size": 7,
                    "browser_download_url": PROFILE_URL,
                },
                {
                    "name": "SHA256SUMS",
                    "size": 84,
                    "browser_download_url": SUMS_URL,
                },
            ],
        }
    ).encode()


class FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.content


class FakeOpener:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self.responses = responses
        self.requests: list[Request] = []

    def __call__(self, request: Request, *, timeout: int) -> FakeResponse:
        self.requests.append(request)
        try:
            return FakeResponse(self.responses[request.full_url])
        except KeyError as error:
            raise URLError("not found") from error


class SequenceOpener:
    def __init__(self, responses: list[bytes | Exception]) -> None:
        self.responses = responses
        self.requests: list[Request] = []

    def __call__(self, request: Request, *, timeout: int) -> FakeResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return FakeResponse(response)


class GitHubReleaseClientTest(unittest.TestCase):
    def client(
        self, *, current_version: str = "routing-20260713"
    ) -> GitHubReleaseClient:
        opener = FakeOpener(
            {
                API_URL: release_payload(),
                PROFILE_URL: b"profile",
                SUMS_URL: f"{PROFILE_DIGEST}  happ-routing.json\n".encode(),
            }
        )
        return GitHubReleaseClient(
            current_version=current_version,
            token="test-token",
            opener=opener,
        )

    def test_check_updates_reports_latest_release(self):
        result = self.client().check_updates()

        self.assertEqual(result["current_version"], "routing-20260713")
        self.assertEqual(result["latest_version"], "routing-20260714")
        self.assertTrue(result["has_update"])
        self.assertEqual(
            result["release_url"],
            "https://github.com/ldkt/happ-routing/releases/tag/routing-20260714",
        )

    def test_check_updates_detects_equal_version(self):
        result = self.client(current_version="routing-20260714").check_updates()

        self.assertFalse(result["has_update"])

    def test_rate_limit_returns_degraded_status_instead_of_raising(self):
        error = HTTPError(API_URL, 403, "rate limit exceeded", {}, None)
        client = GitHubReleaseClient(opener=SequenceOpener([error]))

        result = client.check_updates()

        self.assertIsNone(result["latest_version"])
        self.assertFalse(result["has_update"])
        self.assertEqual(result["github_status"], "rate_limited")
        self.assertIn("403", result["github_error"])
        self.assertIn("rate limit exceeded", result["github_error"])

    def test_network_failure_returns_degraded_status(self):
        opener = SequenceOpener([URLError("network unreachable")])
        client = GitHubReleaseClient(opener=opener)

        result = client.check_updates()
        repeated = client.check_updates()

        self.assertIsNone(result["latest_version"])
        self.assertFalse(result["has_update"])
        self.assertEqual(result["github_status"], "unavailable")
        self.assertIn("network unreachable", result["github_error"])
        self.assertEqual(repeated, result)
        self.assertEqual(len(opener.requests), 1)

    def test_successful_release_is_cached_for_ten_minutes_and_used_on_failure(self):
        now = [100.0]
        opener = SequenceOpener(
            [release_payload(), URLError("network unreachable")]
        )
        client = GitHubReleaseClient(opener=opener, clock=lambda: now[0])

        first = client.check_updates()
        now[0] += 599
        cached = client.check_updates()

        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(cached, first)

        now[0] += 2
        degraded = client.check_updates()

        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(degraded["latest_version"], "routing-20260714")
        self.assertFalse(degraded["has_update"])
        self.assertEqual(degraded["github_status"], "unavailable")

        repeated_degraded = client.check_updates()
        self.assertEqual(repeated_degraded, degraded)
        self.assertEqual(len(opener.requests), 2)

    def test_github_token_environment_variable_adds_bearer_header(self):
        opener = SequenceOpener([release_payload()])
        with patch.dict("os.environ", {"GITHUB_TOKEN": "secret-token"}, clear=True):
            GitHubReleaseClient(opener=opener).check_updates()

        self.assertEqual(
            opener.requests[0].get_header("Authorization"),
            "Bearer secret-token",
        )

    def test_get_release_info_returns_normalized_json_data(self):
        result = self.client().get_release_info()

        self.assertEqual(result["version"], "routing-20260714")
        self.assertEqual(result["date"], "2026-07-14T12:00:00Z")
        self.assertEqual(result["notes"], "Immutable routing data release.")
        self.assertEqual(
            result["checksum"], {"happ-routing.json": PROFILE_DIGEST}
        )
        self.assertEqual(
            [artifact["name"] for artifact in result["artifacts"]],
            ["happ-routing.json", "SHA256SUMS"],
        )

    def test_release_info_and_checksum_are_cached(self):
        opener = FakeOpener(
            {
                API_URL: release_payload(),
                SUMS_URL: f"{PROFILE_DIGEST}  happ-routing.json\n".encode(),
            }
        )
        client = GitHubReleaseClient(opener=opener)

        first = client.get_release_info()
        second = client.get_release_info()

        self.assertEqual(second, first)
        self.assertEqual(
            [request.full_url for request in opener.requests],
            [API_URL, SUMS_URL],
        )

    def test_download_release_uses_a_new_temporary_directory(self):
        destination = self.client().download_release()
        try:
            self.assertIn("urdb-release-", destination.name)
            self.assertEqual(
                {path.name for path in destination.iterdir()},
                {"happ-routing.json", "SHA256SUMS"},
            )
            self.assertEqual((destination / "happ-routing.json").read_bytes(), b"profile")
        finally:
            shutil.rmtree(destination)

    def test_download_rejects_unsafe_asset_name_and_cleans_up(self):
        payload = json.loads(release_payload())
        payload["assets"][0]["name"] = "../install.sh"
        opener = FakeOpener({API_URL: json.dumps(payload).encode()})
        client = GitHubReleaseClient(opener=opener)

        with self.assertRaisesRegex(OrchestratorError, "unsafe release asset"):
            client.download_release()

    def test_cli_commands_emit_json(self):
        client = self.client()
        for command in ("check", "info"):
            with self.subTest(command=command):
                output = io.StringIO()
                with redirect_stdout(output):
                    status = main([command], client=client)
                self.assertEqual(status, 0)
                self.assertIsInstance(json.loads(output.getvalue()), dict)

    def test_cli_download_reports_only_temporary_artifacts(self):
        output = io.StringIO()
        with redirect_stdout(output):
            status = main(["download"], client=self.client())
        result = json.loads(output.getvalue())
        destination = Path(result["directory"])
        try:
            self.assertEqual(status, 0)
            self.assertIn("urdb-release-", destination.name)
            self.assertEqual(
                result["artifacts"], ["SHA256SUMS", "happ-routing.json"]
            )
        finally:
            shutil.rmtree(destination)

    def test_cli_reports_release_errors(self):
        client = GitHubReleaseClient(opener=FakeOpener({}))
        output = io.StringIO()

        with redirect_stdout(output):
            status = main(["check"], client=client)

        self.assertEqual(status, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["github_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
