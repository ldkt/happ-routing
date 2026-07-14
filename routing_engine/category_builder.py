"""Build backend-independent category domain lists from URDB services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .service_registry import Service, ServiceCategory


@dataclass(frozen=True)
class CategoryDomainList:
    """A deterministic domain list assembled from one service category."""

    category: ServiceCategory
    services: tuple[str, ...]
    domains: tuple[str, ...]


def build_category_lists(
    registry: Mapping[str, Service],
) -> dict[ServiceCategory, CategoryDomainList]:
    """Group services by category and convert them to canonical domain entries."""

    grouped: dict[ServiceCategory, list[Service]] = {}
    for service in registry.values():
        grouped.setdefault(service.category, []).append(service)

    result: dict[ServiceCategory, CategoryDomainList] = {}
    for category in ServiceCategory:
        services = sorted(grouped.get(category, ()), key=lambda service: service.id)
        if not services:
            continue
        result[category] = CategoryDomainList(
            category=category,
            services=tuple(service.id for service in services),
            domains=_unique_domains(services),
        )
    return result


def _unique_domains(services: Iterable[Service]) -> tuple[str, ...]:
    domains: list[str] = []
    seen: set[str] = set()
    for service in services:
        entries = (f"include:{name}" for name in service.geosite)
        for entry in (*entries, *service.extra_domains):
            if entry not in seen:
                seen.add(entry)
                domains.append(entry)
    return tuple(domains)
