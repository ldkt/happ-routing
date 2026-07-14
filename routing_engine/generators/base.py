"""Generator contract used by current and future client adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, Any

from ..model import RoutingPolicy


@dataclass(frozen=True)
class GeneratedFile:
    name: str
    content: str


class Generator(Protocol):
    def generate(
        self, policy: RoutingPolicy, settings: Mapping[str, Any]
    ) -> Sequence[GeneratedFile]: ...
