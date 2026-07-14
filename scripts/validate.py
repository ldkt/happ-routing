#!/usr/bin/env python3
"""Validate generated artifacts without third-party dependencies."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--allow-missing-dat", action="store_true")
    args = parser.parse_args()
    required = ["happ-routing.json", "happ-routing-link.txt", "3x-ui-routing.json"]
    for name in required:
        if not (args.dist / name).is_file():
            fail(f"missing {name}")

    profile = json.loads((args.dist / "happ-routing.json").read_text(encoding="utf-8"))
    link = (args.dist / "happ-routing-link.txt").read_text(encoding="utf-8").strip()
    prefix = "happ://routing/onadd/"
    if not link.startswith(prefix):
        fail("invalid Happ link scheme")
    decoded = json.loads(base64.b64decode(link[len(prefix):], validate=True))
    if decoded != profile:
        fail("Happ link payload differs from profile")
    for key in ("Geoipurl", "Geositeurl", "DirectSites", "ProxySites", "BlockSites"):
        if key not in profile:
            fail(f"Happ profile lacks {key}")

    routing = json.loads((args.dist / "3x-ui-routing.json").read_text(encoding="utf-8"))
    if not routing.get("rules") or not routing.get("domainStrategy"):
        fail("3x-ui routing is incomplete")

    for name in ("geoip.dat", "geosite.dat"):
        path = args.dist / name
        if not path.exists():
            if args.allow_missing_dat:
                continue
            fail(f"missing {name}")
        if path.stat().st_size < 1024:
            fail(f"{name} is unexpectedly small")

    sums = args.dist / "SHA256SUMS"
    # Config-only generation may intentionally leave checksums from an older
    # full geodata build in dist. Full builds always validate every digest.
    if sums.exists() and not args.allow_missing_dat:
        for line in sums.read_text(encoding="utf-8").splitlines():
            expected, name = line.split(maxsplit=1)
            path = args.dist / name
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                fail(f"checksum mismatch for {name}")

    print("all artifacts are valid")


if __name__ == "__main__":
    main()
