from __future__ import annotations

import unittest
from pathlib import Path

from routing_engine.category_builder import build_category_lists
from routing_engine.registry_cli import compare_registry_report, registry_report
from routing_engine.service_registry import ServiceCategory, load_service_registry


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "tests" / "golden"


class CategoryBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_service_registry(ROOT / "services")
        self.categories = build_category_lists(self.registry)

    def test_builds_categories_from_service_manifests(self):
        self.assertEqual(
            list(self.categories),
            [
                ServiceCategory.VIDEO,
                ServiceCategory.MESSENGER,
                ServiceCategory.AI,
                ServiceCategory.DEVELOPER,
            ],
        )
        self.assertEqual(
            self.categories[ServiceCategory.MESSENGER].services,
            ("telegram", "whatsapp"),
        )

    def test_category_domain_lists_match_golden_files(self):
        for category, domain_list in self.categories.items():
            with self.subTest(category=category.value):
                actual = "\n".join(domain_list.domains) + "\n"
                expected = (GOLDEN / "registry" / f"{category.value}.txt").read_text(
                    encoding="utf-8"
                )
                self.assertEqual(actual, expected)

    def test_registry_report_matches_golden_file(self):
        actual = registry_report(self.registry, self.categories)
        expected = (GOLDEN / "registry-summary.txt").read_text(encoding="utf-8")

        self.assertEqual(actual, expected)

    def test_compare_report_matches_current_data_golden_file(self):
        actual = compare_registry_report(self.categories, ROOT / "data")
        expected = (GOLDEN / "registry-compare.txt").read_text(encoding="utf-8")

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
