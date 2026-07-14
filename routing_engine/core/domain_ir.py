"""Immutable canonical domain-list IR consumed by v2 backends."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class DomainKind(str, Enum):
    DOMAIN = "domain"
    FULL = "full"
    KEYWORD = "keyword"
    REGEXP = "regexp"


@dataclass(frozen=True)
class CanonicalDomain:
    kind: DomainKind
    value: str
    attributes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalDomainSet:
    id: str
    entries: tuple[CanonicalDomain, ...]


@dataclass(frozen=True)
class CanonicalDomainIR:
    sets: Mapping[str, CanonicalDomainSet]

    @classmethod
    def create(cls, sets: Mapping[str, CanonicalDomainSet]) -> "CanonicalDomainIR":
        return cls(MappingProxyType(dict(sets)))

    def require(self, set_id: str) -> CanonicalDomainSet:
        try:
            return self.sets[set_id]
        except KeyError as error:
            raise ValueError(f"canonical IR lacks domain set {set_id!r}") from error
