#!/usr/bin/env python3
"""Backward-compatible entry point for the universal routing engine."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from routing_engine.cli import generate_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=ROOT / "policy")
    parser.add_argument("--targets", type=Path, default=ROOT / "targets")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    generate_all(args.policy, args.targets, args.output)


if __name__ == "__main__":
    main()
