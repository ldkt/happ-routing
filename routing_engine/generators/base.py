"""Generator contract used by current and future client adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from ..model import (
    DestinationCIDR,
    DestinationIP,
    Domain,
    DomainKeyword,
    DomainRegex,
    DomainSuffix,
    NormalizedPolicy,
    PolicyError,
    ResolvedAny,
    ResolvedDomainSet,
    ResolvedIPSet,
    ResolvedMatcher,
    SourceCIDR,
    SourceIP,
)


@dataclass(frozen=True)
class GeneratedFile:
    name: str
    content: str


class Generator(Protocol):
    def generate(
        self, policy: NormalizedPolicy, settings: Mapping[str, Any]
    ) -> Sequence[GeneratedFile]: ...


def collect_compatible_rules(
    policy: NormalizedPolicy, settings: Mapping[str, Any]
) -> dict[str, dict[str, list[str]]]:
    """Project Phase-1 IR into the existing Happ/Xray list representation.

    This deliberately is not a capability framework or a backend-plan layer.
    It preserves current behavior until Phase 2 introduces those boundaries.
    """

    bindings = settings["egress_bindings"]
    buckets: dict[str, dict[str, list[str]]] = {
        role: {"domains": [], "ips": []} for role in set(bindings.values())
    }
    for rule in policy.enabled_rules():
        try:
            role = bindings[rule.action.egress]
        except KeyError as error:
            raise PolicyError(
                f"target has no binding for egress {rule.action.egress!r}"
            ) from error
        domains, ips = _compatible_values(rule.matcher)
        buckets.setdefault(role, {"domains": [], "ips": []})
        buckets[role]["domains"].extend(domains)
        buckets[role]["ips"].extend(ips)
    return buckets


def _compatible_values(matcher: ResolvedMatcher) -> tuple[list[str], list[str]]:
    if isinstance(matcher, ResolvedAny):
        domains: list[str] = []
        ips: list[str] = []
        for child in matcher.children:
            child_domains, child_ips = _compatible_values(child)
            domains.extend(child_domains)
            ips.extend(child_ips)
        return domains, ips
    if isinstance(matcher, ResolvedDomainSet):
        set_ = matcher.set
        if set_.source is not None:
            if set_.source.provider != "v2fly-geosite":
                raise PolicyError(
                    f"current generators cannot serialize Domain Set provider "
                    f"{set_.source.provider!r}"
                )
            return [f"geosite:{set_.source.resource}"], []
        return [_domain_entry(item) for item in set_.entries], []
    if isinstance(matcher, ResolvedIPSet):
        set_ = matcher.set
        if set_.source is not None:
            if set_.source.provider != "v2fly-geoip":
                raise PolicyError(
                    f"current generators cannot serialize IP Set provider "
                    f"{set_.source.provider!r}"
                )
            return [], [f"geoip:{set_.source.resource}"]
        values: list[str] = []
        for item in set_.entries:
            if isinstance(item, (DestinationIP, DestinationCIDR)):
                values.append(item.value)
            else:
                raise PolicyError(
                    f"current generators cannot serialize IP matcher {type(item).__name__}"
                )
        return [], values
    if isinstance(matcher, (Domain, DomainSuffix, DomainKeyword, DomainRegex)):
        return [_domain_entry(matcher)], []
    if isinstance(matcher, (DestinationIP, DestinationCIDR)):
        return [], [matcher.value]
    if isinstance(matcher, (SourceIP, SourceCIDR)):
        raise PolicyError("current generators cannot serialize source IP matchers")
    raise PolicyError(
        f"current generators cannot serialize matcher {type(matcher).__name__} in Phase 1"
    )


def _domain_entry(entry: Domain | DomainSuffix | DomainKeyword | DomainRegex) -> str:
    if isinstance(entry, Domain):
        return f"full:{entry.value}"
    if isinstance(entry, DomainSuffix):
        return f"domain:{entry.value}"
    if isinstance(entry, DomainKeyword):
        return f"keyword:{entry.value}"
    return f"regexp:{entry.pattern}"
