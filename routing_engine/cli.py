"""Generate all configured client targets from one canonical policy."""

from __future__ import annotations

import argparse
from pathlib import Path

from .generators import GENERATORS
from .loader import load_policy, load_target


ROOT = Path(__file__).resolve().parents[1]


def generate_all(policy_dir: Path, targets_dir: Path, output: Path) -> None:
    policy = load_policy(policy_dir)
    output.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for target_path in sorted(targets_dir.glob("*.yaml")):
        settings = load_target(target_path)
        name = settings["generator"]
        try:
            generator = GENERATORS[name]()
        except KeyError as error:
            raise SystemExit(f"unknown generator {name!r} in {target_path}") from error
        for artifact in generator.generate(policy, settings):
            if artifact.name in seen:
                raise SystemExit(f"duplicate generated filename: {artifact.name}")
            seen.add(artifact.name)
            (output / artifact.name).write_text(artifact.content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=ROOT / "policy")
    parser.add_argument("--targets", type=Path, default=ROOT / "targets")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    generate_all(args.policy, args.targets, args.output)


if __name__ == "__main__":
    main()
