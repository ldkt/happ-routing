import base64
import hashlib
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from routing_engine.cli import generate_all
from routing_engine.loader import load_policy
from routing_engine.model import (
    Action,
    AllMatcher,
    CategoryRef,
    DestinationCIDR,
    DestinationIP,
    Domain,
    DomainRegex,
    DomainSuffix,
    NotMatcher,
    ObjectRef,
    PolicyError,
    Port,
    PortRange,
    ResolvedAll,
    ResolvedAny,
    ResolvedDomainSet,
    ResolvedNot,
    RoutingPolicy,
)
from routing_engine.normalize import normalize_policy


ROOT = Path(__file__).resolve().parents[1]
LEGACY_POLICY = ROOT / "tests" / "fixtures" / "legacy"
COMPATIBILITY_HASHES = {
    "happ-routing.json": "725d5cb79686a3b671922d37286974ad1d2878724e51f247e6a00bfe66145061",
    "happ-routing-link.txt": "b5e4c2b2e130d74a693be38ad98e1c7b943b974aefe947bced6b46b5bf39793f",
    "3x-ui-routing.json": "783b97c97578135dc64dd195e5d1ae6bfb7c88cbc94f3f855a9e1622968f29b3",
}


def write_policy(directory: Path, content: str) -> Path:
    path = directory / "policy.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def minimal_policy(match: str = "domain: example.com", extra: str = "") -> str:
    return textwrap.dedent(f"""
        schema_version: 1
        kind: RoutingPolicy
        metadata:
          name: Test Policy
        egresses:
          internet: {{}}
          vpn: {{}}
        {extra}
        rules:
          - id: test-rule
            match:
              {match}
            action:
              egress: vpn
        fallback: internet
    """)


class CanonicalPolicyTest(unittest.TestCase):
    def test_legacy_policy_loads_as_canonical_schema_v1(self):
        policy = load_policy(LEGACY_POLICY)
        self.assertIsInstance(policy, RoutingPolicy)
        self.assertEqual(policy.schema_version, 1)
        self.assertEqual(policy.kind, "RoutingPolicy")
        self.assertTrue(all(isinstance(rule.action, Action) for rule in policy.rules))
        self.assertEqual(normalize_policy(policy).fallback, "internet")

    def test_legacy_policy_produces_byte_identical_happ_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(LEGACY_POLICY, ROOT / "targets", output)
            for name in ("happ-routing.json", "happ-routing-link.txt"):
                actual = hashlib.sha256((output / name).read_bytes()).hexdigest()
                self.assertEqual(actual, COMPATIBILITY_HASHES[name], name)

    def test_legacy_policy_produces_byte_identical_xray_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(LEGACY_POLICY, ROOT / "targets", output)
            name = "3x-ui-routing.json"
            actual = hashlib.sha256((output / name).read_bytes()).hexdigest()
            self.assertEqual(actual, COMPATIBILITY_HASHES[name], name)

    def test_schema_v1_is_the_only_canonical_language(self):
        canonical = load_policy(ROOT / "policy")
        migrated = load_policy(LEGACY_POLICY)
        self.assertEqual(type(canonical), RoutingPolicy)
        self.assertEqual(type(migrated), RoutingPolicy)
        legacy_bucket_names = {"direct.yaml", "proxy.yaml", "block.yaml"}
        self.assertFalse(
            any(path.name in legacy_bucket_names for path in (ROOT / "policy").iterdir())
        )

    def test_repository_policy_is_schema_v1_and_deterministically_ordered(self):
        policy = load_policy(ROOT / "policy")
        normalized = normalize_policy(policy)
        self.assertEqual(policy.schema_version, 1)
        self.assertEqual(policy.kind, "RoutingPolicy")
        self.assertEqual(normalized.fallback, "internet")
        self.assertEqual(
            [rule.id for rule in normalized.enabled_rules()],
            [
                "block-advertising",
                "block-custom-domains",
                "direct-private-domains",
                "direct-custom-domains",
                "direct-private-addresses",
                "proxy-custom-domains",
            ],
        )

    def test_generated_outputs_are_byte_identical_to_pre_phase_1(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_all(ROOT / "policy", ROOT / "targets", output)
            self.assertEqual({path.name for path in output.iterdir()}, set(COMPATIBILITY_HASHES))
            for name, expected in COMPATIBILITY_HASHES.items():
                actual = hashlib.sha256((output / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected, name)

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

    def test_unknown_fields_are_rejected_at_every_parsed_level(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(Path(directory), minimal_policy() + "unknown: true\n")
            with self.assertRaisesRegex(PolicyError, "unknown fields"):
                load_policy(path)

    def test_duplicate_yaml_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory), minimal_policy().replace("fallback: internet", "fallback: internet\nfallback: vpn")
            )
            with self.assertRaisesRegex(PolicyError, "duplicate YAML key"):
                load_policy(path)

    def test_wrong_scalar_types_are_not_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(Path(directory), minimal_policy().replace("schema_version: 1", "schema_version: '1'"))
            with self.assertRaisesRegex(PolicyError, "must be an integer"):
                load_policy(path)

    def test_priority_then_source_order_and_disabled_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory),
                """
                schema_version: 1
                kind: RoutingPolicy
                metadata: {name: Ordering}
                egresses: {internet: {}, vpn: {}}
                rules:
                  - id: first-zero
                    match: {domain: first.example}
                    action: {egress: internet}
                  - id: disabled-high
                    priority: 100
                    enabled: false
                    match: {domain: disabled.example}
                    action: {egress: vpn}
                  - id: high
                    priority: 10
                    match: {domain: high.example}
                    action: {egress: vpn}
                  - id: second-zero
                    match: {domain: second.example}
                    action: {egress: internet}
                fallback: internet
                """,
            )
            normalized = normalize_policy(load_policy(path))
            self.assertEqual(
                [rule.id for rule in normalized.rules],
                ["disabled-high", "high", "first-zero", "second-zero"],
            )
            self.assertEqual(
                [rule.id for rule in normalized.enabled_rules()],
                ["high", "first-zero", "second-zero"],
            )

    def test_objects_and_categories_resolve_to_typed_sets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory),
                """
                schema_version: 1
                kind: RoutingPolicy
                metadata: {name: References}
                egresses: {internet: {}, vpn: {}}
                domain_sets:
                  example-domains:
                    entries:
                      - domain: EXAMPLE.COM.
                      - domain_suffix: пример.рф
                objects:
                  example:
                    domain_sets: [example-domains]
                categories:
                  examples:
                    objects: [example]
                rules:
                  - id: category-rule
                    match: {category: examples}
                    action: {egress: vpn}
                fallback: internet
                """,
            )
            policy = load_policy(path)
            entries = policy.domain_sets["example-domains"].entries
            self.assertEqual(entries[0], Domain("example.com"))
            self.assertEqual(entries[1], DomainSuffix("xn--e1afmkfd.xn--p1ai"))
            matcher = normalize_policy(policy).rules[0].matcher
            self.assertIsInstance(matcher, ResolvedDomainSet)

    def test_any_all_not_are_parsed_and_deterministically_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory),
                """
                schema_version: 1
                kind: RoutingPolicy
                metadata: {name: Logic}
                egresses: {internet: {}, vpn: {}}
                rules:
                  - id: logic
                    match:
                      all:
                        - any:
                            - domain: one.example
                            - domain_suffix: two.example
                        - not:
                            source_cidr: 10.0.0.0/8
                    action: {egress: vpn}
                fallback: internet
                """,
            )
            parsed = load_policy(path).rules[0].matcher
            self.assertIsInstance(parsed, AllMatcher)
            self.assertIsInstance(parsed.children[1], NotMatcher)
            resolved = normalize_policy(load_policy(path)).rules[0].matcher
            self.assertIsInstance(resolved, ResolvedAll)
            self.assertIsInstance(resolved.children[0], ResolvedAny)
            self.assertIsInstance(resolved.children[1], ResolvedNot)

    def test_typed_matcher_boundaries_are_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory),
                """
                schema_version: 1
                kind: RoutingPolicy
                metadata: {name: Matchers}
                egresses: {internet: {}, vpn: {}}
                rules:
                  - id: matchers
                    match:
                      any:
                        - destination_ip: 2001:0db8::1
                        - destination_cidr: 203.0.113.0/24
                        - port: {direction: destination, value: 443}
                        - port_range: {direction: source, from: 1000, to: 2000}
                        - protocol: tls
                        - network: tcp
                        - domain_regex: {pattern: '(^|\\.)example\\.com$', dialect: re2}
                    action: {egress: vpn}
                fallback: internet
                """,
            )
            children = load_policy(path).rules[0].matcher.children
            self.assertEqual(children[0], DestinationIP("2001:db8::1"))
            self.assertEqual(children[1], DestinationCIDR("203.0.113.0/24"))
            self.assertEqual(children[2].value, 443)
            self.assertEqual((children[3].start, children[3].end), (1000, 2000))
            self.assertIsInstance(children[6], DomainRegex)

    def test_country_asn_process_and_package_nodes_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory),
                """
                schema_version: 1
                kind: RoutingPolicy
                metadata: {name: Future Matchers}
                egresses: {internet: {}, vpn: {}}
                rules:
                  - id: future-disabled
                    enabled: false
                    match:
                      any:
                        - country: {code: ru, direction: destination, ip_set: geo-country}
                        - asn: {number: AS15169, direction: destination, ip_set: geo-asn}
                        - process: {name: firefox}
                        - package_name: org.telegram.messenger
                    action: {egress: vpn}
                fallback: internet
                """,
            )
            policy = load_policy(path)
            children = policy.rules[0].matcher.children
            self.assertEqual(children[0].code, "RU")
            self.assertEqual(children[1].number, 15169)
            self.assertFalse(policy.rules[0].enabled)

    def test_missing_references_and_egresses_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_policy(
                Path(directory), minimal_policy(match="object: missing")
            )
            with self.assertRaisesRegex(PolicyError, "missing Object"):
                normalize_policy(load_policy(path))
            path = write_policy(
                Path(directory), minimal_policy().replace("egress: vpn", "egress: missing")
            )
            with self.assertRaisesRegex(PolicyError, "undeclared egress"):
                normalize_policy(load_policy(path))

    def test_invalid_cidr_port_range_and_re2_construct_are_rejected(self):
        cases = [
            ("domain: invalid_domain.example", "invalid in a domain label"),
            ("destination_cidr: 192.0.2.1/24", "canonical CIDR"),
            (
                "port_range: {direction: destination, from: 9000, to: 8000}",
                "less than or equal",
            ),
            (
                "domain_regex: {pattern: '(?=example)', dialect: re2}",
                "unsupported by RE2",
            ),
            (
                "country: {code: ZZ, direction: destination, ip_set: geo-country}",
                "ISO alpha-2",
            ),
        ]
        for matcher, message in cases:
            with self.subTest(matcher=matcher), tempfile.TemporaryDirectory() as directory:
                path = write_policy(Path(directory), minimal_policy(match=matcher))
                with self.assertRaisesRegex(PolicyError, message):
                    load_policy(path)


if __name__ == "__main__":
    unittest.main()
