"""Serialize canonical domain sets as Keenetic import lists."""

from __future__ import annotations

from ..core.domain_ir import CanonicalDomainIR, DomainKind
from .base import GeneratedArtifact


KEENETIC_DOMAIN_SETS = (
    "proxy-video",
    "proxy-ai",
    "proxy-dev",
    "proxy-social",
    "proxy-ipcheck",
    "routing-proxy",
)


class KeeneticBackend:
    """Pure canonical IR consumer; it never reads source files."""

    def generate(self, policy: CanonicalDomainIR) -> tuple[GeneratedArtifact, ...]:
        artifacts: list[GeneratedArtifact] = []
        for set_id in KEENETIC_DOMAIN_SETS:
            domains: set[str] = set()
            for entry in policy.require(set_id).entries:
                if entry.kind not in {DomainKind.DOMAIN, DomainKind.FULL}:
                    raise ValueError(
                        f"Keenetic domain export cannot represent {entry.kind.value} "
                        f"rule {entry.value!r} in {set_id!r}"
                    )
                domains.add(entry.value)
            content = "".join(f"{domain}\n" for domain in sorted(domains)).encode("utf-8")
            artifacts.append(GeneratedArtifact(f"keenetic/{set_id}.txt", content))
        return tuple(artifacts)
