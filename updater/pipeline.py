"""Health-checked Docker rollout with automatic image rollback."""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Callable, Sequence


LOGGER = logging.getLogger("urdb.updater")
CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class UpdateError(RuntimeError):
    """Raised after a failed rollout has been rolled back."""


class DockerPipeline:
    def __init__(
        self,
        *,
        image: str,
        compose_file: Path,
        service: str = "urdb-api",
        container: str = "urdb-api",
        runner: CommandRunner | None = None,
    ) -> None:
        self.image = image
        self.compose_file = compose_file
        self.service = service
        self.container = container
        self._runner = runner or self._run

    def update(self) -> None:
        old_image = self._output(
            ["docker", "inspect", "--format", "{{.Image}}", self.container]
        )
        rollback_tag = f"{self.image}-rollback"
        self._execute(["docker", "image", "tag", old_image, rollback_tag])
        try:
            self._execute(["docker", "pull", self.image])
            self._compose_up(force=False)
        except subprocess.CalledProcessError as error:
            LOGGER.error("URDB rollout failed; restoring image %s", old_image)
            try:
                self._execute(["docker", "image", "tag", rollback_tag, self.image])
                self._compose_up(force=True)
            except subprocess.CalledProcessError as rollback_error:
                raise UpdateError(
                    "update and automatic rollback both failed"
                ) from rollback_error
            raise UpdateError("update failed; previous healthy image restored") from error
        LOGGER.info("URDB rollout completed with healthy container")

    def restart(self) -> None:
        self._execute(["docker", "restart", self.container])
        LOGGER.info("URDB API container restarted")

    def _compose_up(self, *, force: bool) -> None:
        command = [
            "docker",
            "compose",
            "--project-directory",
            str(self.compose_file.parent),
            "--file",
            str(self.compose_file),
            "up",
            "--detach",
            "--no-deps",
            "--wait",
            "--wait-timeout",
            "120",
        ]
        if force:
            command.append("--force-recreate")
        command.append(self.service)
        self._execute(command)

    def _output(self, command: Sequence[str]) -> str:
        result = self._execute(command)
        output = result.stdout.strip()
        if not output:
            raise UpdateError(f"command returned empty output: {' '.join(command)}")
        return output

    def _execute(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return self._runner(command)

    @staticmethod
    def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
