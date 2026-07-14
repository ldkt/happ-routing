import base64
import json
import tempfile
import unittest
from pathlib import Path

from routing_engine.cli import generate_all
from routing_engine.loader import load_policy
from routing_engine.model import Action, PolicyError


ROOT = Path(__file__).resolve().parents[1]
PROXY_MODULES = (
    "proxy-ai",
    "proxy-video",
    "proxy-dev",
    "proxy-social",
    "proxy-ipcheck",
)


def active_data_rules(name: str) -> list[str]:
    return [
        line.strip()
        for line in (ROOT / "data" / name).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


class RoutingEngineTest(unittest.TestCase):
    def test_routing_proxy_is_only_a_module_aggregate(self):
        self.assertEqual(
            active_data_rules("routing-proxy"),
            [f"include:{name}" for name in PROXY_MODULES],
        )

    def test_proxy_modules_cover_required_services(self):
        self.assertEqual(active_data_rules("proxy-video"), ["include:youtube", "gvt1.com"])
        self.assertEqual(active_data_rules("proxy-dev"), ["include:github"])
        self.assertEqual(
            active_data_rules("proxy-social"),
            ["include:telegram", "include:reddit", "include:x"],
        )
        self.assertIn("chatgpt.com", active_data_rules("proxy-ai"))
        self.assertIn("2ip.io", active_data_rules("proxy-ipcheck"))
        self.assertEqual(active_data_rules("proxy-games"), ["full:proxy-games.invalid"])
        self.assertEqual(active_data_rules("proxy-media"), ["full:proxy-media.invalid"])

    def test_policy_owns_precedence_and_fallback(self):
        policy = load_policy(ROOT / "policy")
        self.assertEqual(
            [action for action, _ in policy.ordered_rules()],
            [Action.BLOCK, Action.DIRECT, Action.PROXY],
        )
        self.assertEqual(policy.fallback, Action.DIRECT)

    def test_all_current_targets_are_generated(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(ROOT / "policy", ROOT / "targets", output)
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"happ-routing.json", "happ-routing-link.txt", "3x-ui-routing.json"},
            )

    def test_happ_link_contains_generated_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(ROOT / "policy", ROOT / "targets", output)
            profile = json.loads((output / "happ-routing.json").read_text())
            link = (output / "happ-routing-link.txt").read_text().strip()
            payload = link.removeprefix("happ://routing/onadd/")
            self.assertEqual(profile, json.loads(base64.b64decode(payload)))

    def test_happ_uses_google_remote_and_yandex_domestic_dns(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(ROOT / "policy", ROOT / "targets", output)
            profile = json.loads((output / "happ-routing.json").read_text())
            self.assertEqual(profile["RemoteDNSDomain"], "https://dns.google/dns-query")
            self.assertEqual(profile["RemoteDNSIP"], "8.8.8.8")
            self.assertEqual(
                profile["DomesticDNSDomain"], "https://dns.yandex.net/dns-query"
            )
            self.assertEqual(profile["DomesticDNSIP"], "77.88.8.8")
            self.assertEqual(
                profile["DnsHosts"],
                {"dns.google": "8.8.8.8", "dns.yandex.net": "77.88.8.8"},
            )

    def test_xray_generator_preserves_policy_order(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(ROOT / "policy", ROOT / "targets", output)
            routing = json.loads((output / "3x-ui-routing.json").read_text())
            tags = [rule["outboundTag"] for rule in routing["rules"]]
            self.assertEqual(tags[0], "block")
            self.assertEqual(tags[-1], "direct")

    def test_duplicate_policy_rule_is_rejected_by_core(self):
        with tempfile.TemporaryDirectory() as directory:
            policy_dir = Path(directory)
            for source in (ROOT / "policy").glob("*.yaml"):
                (policy_dir / source.name).write_text(source.read_text())
            (policy_dir / "direct.yaml").write_text(
                "domains:\n  - example.com\n  - example.com\nips: []\n"
            )
            with self.assertRaisesRegex(PolicyError, "duplicate domain rule"):
                load_policy(policy_dir)


if __name__ == "__main__":
    unittest.main()
