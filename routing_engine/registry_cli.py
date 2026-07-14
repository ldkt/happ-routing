"""Inspect and compare the shadow URDB category compilation pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

from .category_builder import CategoryDomainList, build_category_lists
from .service_registry import Service, ServiceCategory, load_service_registry


ROOT = Path(__file__).resolve().parents[1]
_LEGACY_PROXY_NAMES = {
    ServiceCategory.DEVELOPER: "proxy-dev",
}


def registry_report(
    registry: Mapping[str, Service],
    categories: Mapping[ServiceCategory, CategoryDomainList],
) -> str:
    lines = ["Registry", f"Services: {len(registry)}", "", "Categories:"]
    for category, domain_list in categories.items():
        dots = "." * (15 - len(category.value))
        lines.append(f"{category.value} {dots} {len(domain_list.services)}")
    return "\n".join(lines) + "\n"


def compare_registry_report(
    categories: Mapping[ServiceCategory, CategoryDomainList], data_directory: Path
) -> str:
    sections: list[str] = []
    for category, domain_list in categories.items():
        current_name = _LEGACY_PROXY_NAMES.get(category, f"proxy-{category.value}")
        current_path = data_directory / current_name
        current = _load_current_list(current_path) if current_path.is_file() else None
        registry_domains = domain_list.domains

        lines = [f"Category: {category.value}", ""]
        if current is None:
            lines.append(f"Current: unavailable ({current_path.name})")
            current_values: tuple[str, ...] = ()
        else:
            lines.append(f"Current: {len(current)} entries")
            current_values = current
        lines.append(f"Registry: {len(registry_domains)} entries")

        current_set = set(current_values)
        registry_set = set(registry_domains)
        missing = tuple(value for value in current_values if value not in registry_set)
        registry_only = tuple(
            value for value in registry_domains if value not in current_set
        )

        if current is not None and not missing and not registry_only:
            lines.extend(("", "Match"))
        else:
            if missing:
                lines.extend(("", "Missing from Registry:", *missing))
            if registry_only:
                lines.extend(("", "Only in Registry:", *registry_only))
            if current is None and not registry_only:
                lines.extend(("", "Registry category is empty"))
        sections.append("\n".join(lines))
    return "\n\n".join(sections) + "\n"


def _load_current_list(path: Path) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("summary", "compare"))
    parser.add_argument("--services", type=Path, default=ROOT / "services")
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    registry = load_service_registry(args.services)
    categories = build_category_lists(registry)
    if args.command == "summary":
        print(registry_report(registry, categories), end="")
    else:
        print(compare_registry_report(categories, args.data), end="")


if __name__ == "__main__":
    main()
