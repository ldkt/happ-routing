#!/usr/bin/env python3
"""Create machine-readable provenance for a generated release."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--geosite-source", required=True)
    args = parser.parse_args()
    files = ("geoip.dat", "geosite.dat", "happ-routing.json", "3x-ui-routing.json")
    metadata = {
        "schemaVersion": 1,
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "sources": {
            "geosite": {
                "repository": "v2fly/domain-list-community",
                "commit": args.geosite_source,
            },
            "geoip": {
                "repository": "Loyalsoldier/v2ray-rules-dat",
                "channel": "latest",
            },
        },
        "files": {
            name: {"sha256": digest(args.dist / name), "size": (args.dist / name).stat().st_size}
            for name in files
        },
    }
    (args.dist / "release.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
