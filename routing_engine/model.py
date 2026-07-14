"""Typed, client-neutral routing policy model and invariants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class PolicyError(ValueError):
    """Raised when the source policy violates a core invariant."""


class Action(str, Enum):
    DIRECT = "direct"
    PROXY = "proxy"
    BLOCK = "block"


@dataclass(frozen=True)
class ActionRules:
    domains: tuple[str, ...] = ()
    ips: tuple[str, ...] = ()

    @classmethod
    def create(cls, domains: Iterable[str], ips: Iterable[str]) -> "ActionRules":
        return cls(_normalize(domains, "domain"), _normalize(ips, "IP"))


@dataclass(frozen=True)
class RoutingPolicy:
    version: int
    name: str
    domain_strategy: str
    action_order: tuple[Action, ...]
    fallback: Action
    rules: dict[Action, ActionRules]

    def __post_init__(self) -> None:
        if self.version != 1:
            raise PolicyError(f"unsupported policy version: {self.version}")
        if not self.name.strip():
            raise PolicyError("policy name must not be empty")
        if set(self.action_order) != set(Action) or len(self.action_order) != len(Action):
            raise PolicyError("action_order must contain direct, proxy and block exactly once")
        if set(self.rules) != set(Action):
            raise PolicyError("rules must be provided for every action")

    def ordered_rules(self) -> tuple[tuple[Action, ActionRules], ...]:
        """Return rules in policy-owned first-match order."""
        return tuple((action, self.rules[action]) for action in self.action_order)


def _normalize(values: Iterable[str], label: str) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if not isinstance(raw, str) or not raw.strip():
            raise PolicyError(f"{label} rule must be a non-empty string")
        value = raw.strip()
        if value in seen:
            raise PolicyError(f"duplicate {label} rule: {value}")
        seen.add(value)
        result.append(value)
    return tuple(result)
