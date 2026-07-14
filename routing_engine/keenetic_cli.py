"""Generate Keenetic domain-list artifacts from a prepared source snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

from .backends.keenetic import KEENETIC_DOMAIN_SETS, KeeneticBackend
from .core.domain_source import compile_domain_ir


ROOT = Path(__file__).resolve().parents[1]


def generate_keenetic(source: Path, output: Path) -> None:
    policy = compile_domain_ir(source, KEENETIC_DOMAIN_SETS)
    for artifact in KeeneticBackend().generate(policy):
        destination = output / artifact.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(artifact.content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / ".cache" / "domain-list-community" / "data",
        help="prepared domain-list-community data snapshot (run make build first)",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    generate_keenetic(args.source, args.output)


if __name__ == "__main__":
    main()
