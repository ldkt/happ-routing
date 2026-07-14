from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from routing_engine.coverage import analyze_coverage, coverage_report
from routing_engine.service_registry import load_service_registry


ROOT = Path(__file__).resolve().parents[1]


class CoverageEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_service_registry(ROOT / "services")

    def test_counts_registered_services_and_categories(self):
        result = analyze_coverage(self.registry, ROOT / "data")

        self.assertEqual(result.registered, 5)
        self.assertEqual(result.total, 22)
        self.assertAlmostEqual(result.percentage, 22.7272727)
        self.assertEqual(
            {category.value: count for category, count in result.registered_by_category.items()},
            {"video": 1, "messenger": 2, "ai": 1, "developer": 1},
        )

    def test_compares_registry_with_current_proxy_lists(self):
        result = analyze_coverage(self.registry, ROOT / "data")
        statuses = {
            item.service.id: (item.registered, item.in_current_proxy)
            for item in result.services
        }

        self.assertEqual(statuses["youtube"], (True, True))
        self.assertEqual(statuses["whatsapp"], (True, False))
        self.assertEqual(statuses["claude"], (False, True))
        self.assertEqual(statuses["signal"], (False, False))

    def test_missing_legacy_directory_is_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            result = analyze_coverage(self.registry, Path(directory))

        self.assertTrue(all(not item.in_current_proxy for item in result.services))

    def test_report_matches_golden_file(self):
        result = analyze_coverage(self.registry, ROOT / "data")
        actual = coverage_report(result)
        expected = (ROOT / "tests" / "golden" / "coverage.txt").read_text(
            encoding="utf-8"
        )

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
