"""Load YAML sources into the canonical routing model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import Action, ActionRules, PolicyError, RoutingPolicy


def _yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise PolicyError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict):
        raise PolicyError(f"{path} must contain a YAML mapping")
    return value


def load_policy(directory: Path) -> RoutingPolicy:
    metadata = _yaml(directory / "policy.yaml")
    try:
        order = tuple(Action(item) for item in metadata["action_order"])
        fallback = Action(metadata["fallback"])
        rules = {}
        for action in Action:
            raw = _yaml(directory / f"{action.value}.yaml")
            rules[action] = ActionRules.create(raw.get("domains", []), raw.get("ips", []))
        return RoutingPolicy(
            version=int(metadata["version"]),
            name=str(metadata["name"]),
            domain_strategy=str(metadata["domain_strategy"]),
            action_order=order,
            fallback=fallback,
            rules=rules,
        )
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, PolicyError):
            raise
        raise PolicyError(f"invalid policy metadata: {error}") from error


def load_target(path: Path) -> dict[str, Any]:
    target = _yaml(path)
    if not isinstance(target.get("generator"), str):
        raise PolicyError(f"{path} must declare a generator")
    return target
