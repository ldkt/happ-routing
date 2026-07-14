#!/usr/bin/env python3
"""Backward-compatible script entry point for Keenetic domain exports."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from routing_engine.keenetic_cli import main  # noqa: E402


if __name__ == "__main__":
    main()
