"""Command-line interface for the URDB Orchestrator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from .github_release import (
    DEFAULT_CURRENT_VERSION,
    DEFAULT_REPOSITORY,
    GitHubReleaseClient,
    OrchestratorError,
    token_from_environment,
)


def main(
    argv: Sequence[str] | None = None, *, client: GitHubReleaseClient | None = None
) -> int:
    parser = argparse.ArgumentParser(prog="urdb")
    parser.add_argument(
        "--repository", default=os.environ.get("URDB_REPOSITORY", DEFAULT_REPOSITORY)
    )
    parser.add_argument(
        "--current-version",
        default=os.environ.get("URDB_CURRENT_VERSION", DEFAULT_CURRENT_VERSION),
    )
    parser.add_argument("command", choices=("check", "info", "download"))
    args = parser.parse_args(argv)

    release_client = client or GitHubReleaseClient(
        repository=args.repository,
        current_version=args.current_version,
        token=token_from_environment(),
    )
    try:
        if args.command == "check":
            result: object = release_client.check_updates()
        elif args.command == "info":
            result = release_client.get_release_info()
        else:
            directory = release_client.download_release()
            result = {
                "directory": str(directory),
                "artifacts": sorted(path.name for path in directory.iterdir()),
            }
    except OrchestratorError as error:
        print(f"urdb: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
