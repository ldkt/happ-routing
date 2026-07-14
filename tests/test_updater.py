from __future__ import annotations

import json
from pathlib import Path
import subprocess
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from homeassistant.updater_client import UpdaterClient
from updater.pipeline import DockerPipeline, UpdateError
from updater.server import create_server


class RecordingRunner:
    def __init__(self, *, fail_first_rollout: bool = False) -> None:
        self.commands: list[list[str]] = []
        self.fail_first_rollout = fail_first_rollout

    def __call__(self, command):
        value = list(command)
        self.commands.append(value)
        if value[:3] == ["docker", "inspect", "--format"]:
            return subprocess.CompletedProcess(value, 0, "sha256:old\n", "")
        if (
            self.fail_first_rollout
            and "--wait" in value
            and "--force-recreate" not in value
        ):
            self.fail_first_rollout = False
            raise subprocess.CalledProcessError(1, value)
        return subprocess.CompletedProcess(value, 0, "", "")


class DockerPipelineTest(unittest.TestCase):
    def test_update_pulls_and_waits_for_healthy_container(self):
        runner = RecordingRunner()
        pipeline = self._pipeline(runner)

        pipeline.update()

        self.assertIn(
            ["docker", "pull", "ghcr.io/ldkt/happ-routing:latest"],
            runner.commands,
        )
        rollout = runner.commands[-1]
        self.assertIn("--wait", rollout)
        self.assertNotIn("--force-recreate", rollout)

    def test_failed_healthcheck_restores_previous_image(self):
        runner = RecordingRunner(fail_first_rollout=True)
        pipeline = self._pipeline(runner)

        with self.assertRaisesRegex(UpdateError, "previous healthy image restored"):
            pipeline.update()

        self.assertIn(
            [
                "docker",
                "image",
                "tag",
                "ghcr.io/ldkt/happ-routing:latest-rollback",
                "ghcr.io/ldkt/happ-routing:latest",
            ],
            runner.commands,
        )
        self.assertIn("--force-recreate", runner.commands[-1])
        self.assertIn("--wait", runner.commands[-1])

    def test_restart_only_restarts_api_container(self):
        runner = RecordingRunner()
        self._pipeline(runner).restart()

        self.assertEqual(runner.commands, [["docker", "restart", "urdb-api"]])

    @staticmethod
    def _pipeline(runner: RecordingRunner) -> DockerPipeline:
        return DockerPipeline(
            image="ghcr.io/ldkt/happ-routing:latest",
            compose_file=Path("/deployment/docker-compose.yml"),
            runner=runner,
        )


class ImmediateQueue:
    def submit(self, name, operation) -> bool:
        operation()
        return True


class FakePipeline:
    def __init__(self) -> None:
        self.operations: list[str] = []

    def update(self) -> None:
        self.operations.append("update")

    def restart(self) -> None:
        self.operations.append("restart")


class UpdaterIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = FakePipeline()
        self.server = create_server(
            ("127.0.0.1", 0),
            self.pipeline,
            "test-secret",
            queue=ImmediateQueue(),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_api_client_schedules_update_through_authenticated_sidecar(self):
        response = UpdaterClient(self.base_url, "test-secret").update()

        self.assertEqual(response, {"accepted": True, "message": "Update scheduled"})
        self.assertEqual(self.pipeline.operations, ["update"])

    def test_api_client_schedules_restart(self):
        response = UpdaterClient(self.base_url, "test-secret").restart()

        self.assertEqual(response, {"accepted": True, "message": "Restart scheduled"})
        self.assertEqual(self.pipeline.operations, ["restart"])

    def test_sidecar_rejects_unauthenticated_operation(self):
        request = Request(self.base_url + "/update", method="POST")
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)

        self.assertEqual(context.exception.code, 401)
        self.assertEqual(json.load(context.exception), {"error": "unauthorized"})


if __name__ == "__main__":
    unittest.main()
