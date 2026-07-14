"""Load and validate the Universal Routing Database service registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

import yaml


class ServiceRegistryError(ValueError):
    """Raised when a service registry entry violates its contract."""


class ServiceCategory(str, Enum):
    """Categories currently recognized by the service registry."""

    AI = "ai"
    DEVELOPER = "developer"
    MESSENGER = "messenger"
    VIDEO = "video"


@dataclass(frozen=True)
class Service:
    """A validated, backend-independent service description."""

    id: str
    name: str
    category: ServiceCategory
    geosite: tuple[str, ...]
    extra_domains: tuple[str, ...]
    ip_source: tuple[str, ...]
    status: str


_REQUIRED_FIELDS = frozenset(
    {
        "id",
        "name",
        "category",
        "geosite",
        "extra_domains",
        "ip_source",
        "status",
    }
)


def load_service_registry(directory: Path) -> dict[str, Service]:
    """Load every ``*/service.yaml`` entry from *directory*.

    The returned mapping is ordered deterministically by service directory name.
    """

    if not directory.is_dir():
        raise ServiceRegistryError(f"service registry directory does not exist: {directory}")

    registry: dict[str, Service] = {}
    paths = sorted(directory.glob("*/service.yaml"), key=lambda path: path.parent.name)
    for path in paths:
        service = load_service(path)
        if service.id in registry:
            raise ServiceRegistryError(f"duplicate service id: {service.id}")
        if service.id != path.parent.name:
            raise ServiceRegistryError(
                f"{path}: service id {service.id!r} must match directory name "
                f"{path.parent.name!r}"
            )
        registry[service.id] = service
    return registry


def load_service(path: Path) -> Service:
    """Parse and validate one service manifest."""

    raw = _load_yaml_mapping(path)
    missing = sorted(_REQUIRED_FIELDS - raw.keys())
    if missing:
        raise ServiceRegistryError(
            f"{path}: missing required fields: {', '.join(missing)}"
        )

    unknown = sorted(raw.keys() - _REQUIRED_FIELDS)
    if unknown:
        raise ServiceRegistryError(f"{path}: unknown fields: {', '.join(unknown)}")

    service_id = _required_string(raw["id"], "id", path)
    name = _required_string(raw["name"], "name", path)
    status = _required_string(raw["status"], "status", path)

    category_value = _required_string(raw["category"], "category", path)
    try:
        category = ServiceCategory(category_value)
    except ValueError as error:
        categories = ", ".join(category.value for category in ServiceCategory)
        raise ServiceRegistryError(
            f"{path}: unknown category {category_value!r}; expected one of: {categories}"
        ) from error

    return Service(
        id=service_id,
        name=name,
        category=category,
        geosite=_string_list(raw["geosite"], "geosite", path),
        extra_domains=_string_list(raw["extra_domains"], "extra_domains", path),
        ip_source=_string_list(raw["ip_source"], "ip_source", path),
        status=status,
    )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ServiceRegistryError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ServiceRegistryError(f"{path}: service manifest must be a YAML mapping")
    return value


def _required_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ServiceRegistryError(f"{path}: {field} must be a non-empty string")
    normalized = value.strip()
    if normalized != value:
        raise ServiceRegistryError(f"{path}: {field} must not contain outer whitespace")
    return normalized


def _string_list(value: Any, field: str, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ServiceRegistryError(f"{path}: {field} must be a list")

    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        normalized = _required_string(item, f"{field} item", path)
        if normalized in seen:
            raise ServiceRegistryError(
                f"{path}: duplicate value in {field}: {normalized}"
            )
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)
