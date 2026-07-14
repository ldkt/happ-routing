from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from routing_engine.service_registry import (
    ServiceCategory,
    ServiceRegistryError,
    load_service_registry,
)


ROOT = Path(__file__).resolve().parents[1]


class ServiceRegistryTest(unittest.TestCase):
    def test_repository_registry_loads_all_services(self):
        registry = load_service_registry(ROOT / "services")

        self.assertEqual(
            set(registry),
            {"youtube", "telegram", "whatsapp", "github", "chatgpt"},
        )
        self.assertEqual(registry["youtube"].name, "YouTube")
        self.assertEqual(registry["youtube"].category, ServiceCategory.VIDEO)
        self.assertEqual(registry["youtube"].geosite, ("youtube",))
        self.assertEqual(registry["youtube"].extra_domains, ("gvt1.com",))
        self.assertEqual(registry["youtube"].ip_source, ("opencck:youtube",))
        self.assertEqual(registry["youtube"].status, "stable")

    def test_registry_order_is_deterministic(self):
        registry = load_service_registry(ROOT / "services")

        self.assertEqual(
            list(registry),
            ["chatgpt", "github", "telegram", "whatsapp", "youtube"],
        )

    def test_duplicate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_service(root / "duplicate", service_id="duplicate")
            self._write_service(root / "second", service_id="duplicate")

            with self.assertRaisesRegex(ServiceRegistryError, "duplicate service id"):
                load_service_registry(root)

    def test_unknown_category_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_service(root / "example", category="unknown")

            with self.assertRaisesRegex(ServiceRegistryError, "unknown category"):
                load_service_registry(root)

    def test_each_required_field_is_enforced(self):
        required_fields = (
            "id",
            "name",
            "category",
            "geosite",
            "extra_domains",
            "ip_source",
            "status",
        )
        for field in required_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._write_service(root / "example", omitted_field=field)

                with self.assertRaisesRegex(
                    ServiceRegistryError, f"missing required fields: {field}"
                ):
                    load_service_registry(root)

    def test_service_id_must_match_directory_name(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_service(root / "directory-name", service_id="other-id")

            with self.assertRaisesRegex(ServiceRegistryError, "directory name"):
                load_service_registry(root)

    def test_unknown_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._write_service(root / "example", extra_line="backend: happ")

            with self.assertRaisesRegex(ServiceRegistryError, "unknown fields: backend"):
                load_service_registry(root)

    def test_list_fields_require_lists_of_unique_non_empty_strings(self):
        invalid_values = ("youtube", [""], ["youtube", "youtube"])
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._write_service(root / "example", geosite=value)

                with self.assertRaises(ServiceRegistryError):
                    load_service_registry(root)

    @staticmethod
    def _write_service(
        directory: Path,
        *,
        service_id: str = "example",
        category: str = "video",
        omitted_field: str | None = None,
        extra_line: str | None = None,
        geosite: object = None,
    ) -> None:
        directory.mkdir(parents=True)
        values: dict[str, object] = {
            "id": service_id,
            "name": "Example",
            "category": category,
            "geosite": ["example"] if geosite is None else geosite,
            "extra_domains": [],
            "ip_source": [],
            "status": "stable",
        }
        if omitted_field is not None:
            del values[omitted_field]

        lines: list[str] = []
        for key, value in values.items():
            if isinstance(value, list):
                if value:
                    lines.append(f"{key}:")
                    lines.extend(f"  - {item}" for item in value)
                else:
                    lines.append(f"{key}: []")
            else:
                lines.append(f"{key}: {value}")
        if extra_line is not None:
            lines.append(extra_line)
        (directory / "service.yaml").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    unittest.main()
