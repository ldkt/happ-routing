"""Canonical schema-v1 routing domain model.

The model is intentionally backend-neutral. Backend capability checks and
backend plan types belong to later roadmap phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Union


class PolicyError(ValueError):
    """Raised when canonical policy syntax or semantics are invalid."""


class Direction(str, Enum):
    SOURCE = "source"
    DESTINATION = "destination"


@dataclass(frozen=True)
class Metadata:
    name: str
    revision: str | int | None = None
    description: str | None = None
    owners: tuple[str, ...] = ()
    labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Egress:
    id: str
    description: str | None = None


@dataclass(frozen=True)
class ResourceSource:
    provider: str
    resource: str
    revision: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class Domain:
    value: str


@dataclass(frozen=True)
class DomainSuffix:
    value: str


@dataclass(frozen=True)
class DomainKeyword:
    value: str


@dataclass(frozen=True)
class DomainRegex:
    pattern: str
    dialect: str = "re2"


DomainEntry = Union[Domain, DomainSuffix, DomainKeyword, DomainRegex]


@dataclass(frozen=True)
class DestinationIP:
    value: str


@dataclass(frozen=True)
class DestinationCIDR:
    value: str


@dataclass(frozen=True)
class SourceIP:
    value: str


@dataclass(frozen=True)
class SourceCIDR:
    value: str


@dataclass(frozen=True)
class Country:
    code: str
    direction: Direction
    dataset: str


@dataclass(frozen=True)
class ASN:
    number: int
    direction: Direction
    dataset: str


IPEntry = Union[DestinationIP, DestinationCIDR, SourceIP, SourceCIDR, Country, ASN]


@dataclass(frozen=True)
class DomainSet:
    id: str
    description: str | None = None
    entries: tuple[DomainEntry, ...] = ()
    source: ResourceSource | None = None


@dataclass(frozen=True)
class IPSet:
    id: str
    description: str | None = None
    entries: tuple[IPEntry, ...] = ()
    source: ResourceSource | None = None


@dataclass(frozen=True)
class Object:
    id: str
    description: str | None = None
    domain_sets: tuple[str, ...] = ()
    ip_sets: tuple[str, ...] = ()


@dataclass(frozen=True)
class Category:
    id: str
    description: str | None = None
    objects: tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainSetRef:
    set_id: str


@dataclass(frozen=True)
class IPSetRef:
    set_id: str


@dataclass(frozen=True)
class ObjectRef:
    object_id: str


@dataclass(frozen=True)
class CategoryRef:
    category_id: str


@dataclass(frozen=True)
class Port:
    direction: Direction
    value: int


@dataclass(frozen=True)
class PortRange:
    direction: Direction
    start: int
    end: int


@dataclass(frozen=True)
class Protocol:
    value: str


@dataclass(frozen=True)
class Network:
    value: str


@dataclass(frozen=True)
class Process:
    name: str


@dataclass(frozen=True)
class PackageName:
    value: str


@dataclass(frozen=True)
class AnyMatcher:
    children: tuple["Matcher", ...]


@dataclass(frozen=True)
class AllMatcher:
    children: tuple["Matcher", ...]


@dataclass(frozen=True)
class NotMatcher:
    child: "Matcher"


Matcher = Union[
    Domain, DomainSuffix, DomainKeyword, DomainRegex, DestinationIP,
    DestinationCIDR, SourceIP, SourceCIDR, Country, ASN, Port, PortRange,
    Protocol, Network, Process, PackageName, DomainSetRef, IPSetRef, ObjectRef,
    CategoryRef, AnyMatcher, AllMatcher, NotMatcher,
]


@dataclass(frozen=True)
class ResolvedDomainSet:
    set: DomainSet


@dataclass(frozen=True)
class ResolvedIPSet:
    set: IPSet


@dataclass(frozen=True)
class ResolvedAny:
    children: tuple["ResolvedMatcher", ...]


@dataclass(frozen=True)
class ResolvedAll:
    children: tuple["ResolvedMatcher", ...]


@dataclass(frozen=True)
class ResolvedNot:
    child: "ResolvedMatcher"


ResolvedMatcher = Union[
    Domain, DomainSuffix, DomainKeyword, DomainRegex, DestinationIP,
    DestinationCIDR, SourceIP, SourceCIDR, Country, ASN, Port, PortRange,
    Protocol, Network, Process, PackageName, ResolvedDomainSet, ResolvedIPSet,
    ResolvedAny, ResolvedAll, ResolvedNot,
]


@dataclass(frozen=True)
class Action:
    egress: str


@dataclass(frozen=True)
class Rule:
    id: str
    matcher: Matcher
    action: Action
    description: str | None = None
    priority: int = 0
    enabled: bool = True
    source_index: int = 0


@dataclass(frozen=True)
class ResolvedRule:
    id: str
    matcher: ResolvedMatcher
    action: Action
    description: str | None
    priority: int
    enabled: bool
    source_index: int


@dataclass(frozen=True)
class RoutingPolicy:
    schema_version: int
    kind: str
    metadata: Metadata
    egresses: Mapping[str, Egress]
    domain_sets: Mapping[str, DomainSet]
    ip_sets: Mapping[str, IPSet]
    objects: Mapping[str, Object]
    categories: Mapping[str, Category]
    rules: tuple[Rule, ...]
    fallback: str


@dataclass(frozen=True)
class NormalizedPolicy:
    schema_version: int
    metadata: Metadata
    egresses: Mapping[str, Egress]
    rules: tuple[ResolvedRule, ...]
    fallback: str

    def enabled_rules(self) -> tuple[ResolvedRule, ...]:
        return tuple(rule for rule in self.rules if rule.enabled)
