import base64
import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_configs import generate, load_config, xray_routing


ROOT = Path(__file__).resolve().parents[1]


class ConfigGenerationTest(unittest.TestCase):
    def test_happ_link_contains_generated_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate(ROOT / "config/routing.json", output, "https://example.test/latest")
            profile = json.loads((output / "happ-routing.json").read_text())
            link = (output / "happ-routing-link.txt").read_text().strip()
            payload = link.removeprefix("happ://routing/onadd/")
            self.assertEqual(profile, json.loads(base64.b64decode(payload)))
            self.assertEqual(profile["Geoipurl"], "https://example.test/latest/geoip.dat")

    def test_xray_rules_are_ordered_block_direct_proxy_fallback(self):
        routing = xray_routing(load_config(ROOT / "config/routing.json"))
        tags = [rule["outboundTag"] for rule in routing["rules"]]
        self.assertEqual(tags[0], "block")
        self.assertIn("proxy", tags)
        self.assertEqual(tags[-1], "direct")


if __name__ == "__main__":
    unittest.main()
