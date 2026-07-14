from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "urdb"


class HACSIntegrationStructureTest(unittest.TestCase):
    def test_manifest_declares_ui_config_entry_integration(self):
        manifest = self._json(COMPONENT / "manifest.json")

        self.assertEqual(manifest["domain"], "urdb")
        self.assertTrue(manifest["config_flow"])
        self.assertEqual(manifest["integration_type"], "service")
        self.assertEqual(manifest["iot_class"], "local_polling")
        for required in (
            "name",
            "version",
            "documentation",
            "issue_tracker",
            "codeowners",
        ):
            self.assertIn(required, manifest)

    def test_all_runtime_modules_are_valid_python(self):
        for path in COMPONENT.glob("*.py"):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_config_flow_validates_api_before_creating_entry(self):
        source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")

        self.assertIn("await URDBAPIClient(", source)
        self.assertIn(").status()", source)
        self.assertIn("async_create_entry", source)
        self.assertIn("_abort_if_unique_id_configured", source)

    def test_entities_device_and_diagnostics_are_present(self):
        sensor = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        button = (COMPONENT / "button.py").read_text(encoding="utf-8")
        entity = (COMPONENT / "entity.py").read_text(encoding="utf-8")

        self.assertIn("URDBStatusSensor", sensor)
        self.assertIn("URDBChangesSensor", sensor)
        for action in ("check", "update", "restart"):
            self.assertIn(f'key="{action}"', button)
        self.assertIn("DeviceInfo(", entity)
        self.assertTrue((COMPONENT / "diagnostics.py").is_file())

    def test_hacs_metadata_and_translations_are_valid(self):
        hacs = self._json(ROOT / "hacs.json")
        strings = self._json(COMPONENT / "strings.json")
        english = self._json(COMPONENT / "translations" / "en.json")
        russian = self._json(COMPONENT / "translations" / "ru.json")

        self.assertEqual(hacs["name"], "Universal Routing Database")
        self.assertEqual(strings.keys(), english.keys())
        self.assertEqual(strings.keys(), russian.keys())
        self.assertTrue((COMPONENT / "brand" / "icon.png").is_file())

    def test_manual_yaml_installation_files_are_removed(self):
        self.assertFalse((ROOT / "packages" / "urdb.yaml").exists())
        self.assertFalse((ROOT / "homeassistant" / "dashboard" / "rest.yaml").exists())
        self.assertFalse(
            (ROOT / "homeassistant" / "dashboard" / "rest_commands.yaml").exists()
        )

    @staticmethod
    def _json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
