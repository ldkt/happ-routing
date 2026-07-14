"""Measure Service Registry coverage against an explicit service baseline."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .service_registry import Service, ServiceCategory, load_service_registry


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ExpectedService:
    """A service expected by the first URDB coverage baseline."""

    id: str
    name: str
    category: ServiceCategory
    legacy_rules: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ServiceCoverage:
    """Registration and legacy-list status for one expected service."""

    service: ExpectedService
    registered: bool
    in_current_proxy: bool


@dataclass(frozen=True)
class CoverageResult:
    """Complete, deterministic result of a coverage analysis."""

    services: tuple[ServiceCoverage, ...]
    registered_by_category: dict[ServiceCategory, int]

    @property
    def registered(self) -> int:
        return sum(item.registered for item in self.services)

    @property
    def total(self) -> int:
        return len(self.services)

    @property
    def percentage(self) -> float:
        return 100 * self.registered / self.total if self.total else 100.0


_EXPECTED_SERVICES = (
    ExpectedService(
        "youtube", "YouTube", ServiceCategory.VIDEO, (("proxy-video", "include:youtube"),)
    ),
    ExpectedService(
        "telegram",
        "Telegram",
        ServiceCategory.MESSENGER,
        (("proxy-social", "include:telegram"),),
    ),
    ExpectedService("whatsapp", "WhatsApp", ServiceCategory.MESSENGER),
    ExpectedService("signal", "Signal", ServiceCategory.MESSENGER),
    ExpectedService("discord", "Discord", ServiceCategory.MESSENGER),
    ExpectedService("viber", "Viber", ServiceCategory.MESSENGER),
    ExpectedService(
        "chatgpt", "ChatGPT", ServiceCategory.AI, (("proxy-ai", "chatgpt.com"),)
    ),
    ExpectedService(
        "claude", "Claude", ServiceCategory.AI, (("proxy-ai", "claude.ai"),)
    ),
    ExpectedService(
        "gemini", "Gemini", ServiceCategory.AI, (("proxy-ai", "gemini.google.com"),)
    ),
    ExpectedService(
        "copilot",
        "Copilot",
        ServiceCategory.AI,
        (("proxy-ai", "copilot.microsoft.com"),),
    ),
    ExpectedService(
        "perplexity",
        "Perplexity",
        ServiceCategory.AI,
        (("proxy-ai", "perplexity.ai"),),
    ),
    ExpectedService(
        "github", "GitHub", ServiceCategory.DEVELOPER, (("proxy-dev", "include:github"),)
    ),
    ExpectedService(
        "reddit", "Reddit", ServiceCategory.SOCIAL, (("proxy-social", "include:reddit"),)
    ),
    ExpectedService(
        "x", "X", ServiceCategory.SOCIAL, (("proxy-social", "include:x"),)
    ),
    ExpectedService("instagram", "Instagram", ServiceCategory.SOCIAL),
    ExpectedService("facebook", "Facebook", ServiceCategory.SOCIAL),
    ExpectedService("steam", "Steam", ServiceCategory.GAMING),
    ExpectedService("epic", "Epic", ServiceCategory.GAMING),
    ExpectedService("battlenet", "Battle.net", ServiceCategory.GAMING),
    ExpectedService("netflix", "Netflix", ServiceCategory.STREAMING),
    ExpectedService("disney", "Disney", ServiceCategory.STREAMING),
    ExpectedService("prime-video", "Prime Video", ServiceCategory.STREAMING),
)


def analyze_coverage(
    registry: Mapping[str, Service], data_directory: Path
) -> CoverageResult:
    """Compare registered services with the baseline and current proxy lists."""

    current_lists = _load_current_proxy_lists(data_directory)
    services = tuple(
        ServiceCoverage(
            service=expected,
            registered=expected.id in registry,
            in_current_proxy=any(
                rule in current_lists.get(filename, ())
                for filename, rule in expected.legacy_rules
            ),
        )
        for expected in _EXPECTED_SERVICES
    )
    counts = Counter(service.category for service in registry.values())
    return CoverageResult(
        services=services,
        registered_by_category={
            category: counts[category] for category in ServiceCategory if counts[category]
        },
    )


def coverage_report(result: CoverageResult) -> str:
    """Render a human-readable coverage and legacy comparison report."""

    lines = [
        "Registry coverage",
        "",
        "Services registered:",
        f"{result.registered} / {result.total}",
        f"{result.percentage:.1f} %",
        "",
        "Services by category:",
    ]
    for category, count in result.registered_by_category.items():
        name = _category_name(category)
        dots = "." * (17 - len(name))
        lines.append(f"{name} {dots} {count}")

    lines.extend(("", "Coverage by service:"))
    for category in _coverage_categories(result):
        lines.extend(("", _category_name(category)))
        for item in result.services:
            if item.service.category == category:
                marker = "✓" if item.registered else "✗"
                lines.append(f"{marker} {item.service.name}")

    both = _names(result, registered=True, in_current_proxy=True)
    registry_only = _names(result, registered=True, in_current_proxy=False)
    current_only = _names(result, registered=False, in_current_proxy=True)
    missing_both = _names(result, registered=False, in_current_proxy=False)
    lines.extend(
        (
            "",
            "Legacy proxy comparison:",
            f"Registry and current: {_format_names(both)}",
            f"Registry only: {_format_names(registry_only)}",
            f"Current only: {_format_names(current_only)}",
            f"Missing from both: {_format_names(missing_both)}",
        )
    )
    return "\n".join(lines) + "\n"


def _load_current_proxy_lists(data_directory: Path) -> dict[str, frozenset[str]]:
    result: dict[str, frozenset[str]] = {}
    for path in sorted(data_directory.glob("proxy-*")):
        result[path.name] = frozenset(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    return result


def _coverage_categories(result: CoverageResult) -> tuple[ServiceCategory, ...]:
    present = {item.service.category for item in result.services}
    return tuple(category for category in ServiceCategory if category in present)


def _names(
    result: CoverageResult, *, registered: bool, in_current_proxy: bool
) -> tuple[str, ...]:
    return tuple(
        item.service.name
        for item in result.services
        if item.registered is registered and item.in_current_proxy is in_current_proxy
    )


def _format_names(names: tuple[str, ...]) -> str:
    return ", ".join(names) if names else "none"


def _category_name(category: ServiceCategory) -> str:
    if category == ServiceCategory.AI:
        return "AI"
    return category.value.replace("-", " ").title()


def main() -> None:
    registry = load_service_registry(ROOT / "services")
    result = analyze_coverage(registry, ROOT / "data")
    print(coverage_report(result), end="")


if __name__ == "__main__":
    main()
