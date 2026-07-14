import tempfile
import unittest
from pathlib import Path

from routing_engine.backends.keenetic import (
    KEENETIC_DOMAIN_SETS,
    KeeneticBackend,
)
from routing_engine.core.domain_ir import (
    CanonicalDomain,
    CanonicalDomainIR,
    CanonicalDomainSet,
    DomainKind,
)
from routing_engine.core.domain_source import DomainSourceError, compile_domain_ir
from routing_engine.keenetic_cli import generate_keenetic


class KeeneticBackendTest(unittest.TestCase):
    def test_backend_consumes_only_canonical_ir(self):
        sets = {
            set_id: CanonicalDomainSet(
                set_id,
                (
                    CanonicalDomain(DomainKind.DOMAIN, f"{set_id}.example"),
                    CanonicalDomain(DomainKind.FULL, f"exact.{set_id}.example"),
                ),
            )
            for set_id in KEENETIC_DOMAIN_SETS
        }
        artifacts = KeeneticBackend().generate(CanonicalDomainIR.create(sets))
        self.assertEqual(
            [artifact.relative_path for artifact in artifacts],
            [f"keenetic/{set_id}.txt" for set_id in KEENETIC_DOMAIN_SETS],
        )
        self.assertTrue(all(artifact.content.endswith(b"\n") for artifact in artifacts))

    def test_source_compiler_resolves_includes_filters_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "child").write_text(
                "example.com\nfull:api.example.net\ntracked.example @ads\n",
                encoding="utf-8",
            )
            (source / "parent").write_text(
                "include:child @-ads\nexample.com\n",
                encoding="utf-8",
            )
            policy = compile_domain_ir(source, ("parent",))
            self.assertEqual(
                [(entry.kind, entry.value) for entry in policy.require("parent").entries],
                [
                    (DomainKind.DOMAIN, "example.com"),
                    (DomainKind.FULL, "api.example.net"),
                ],
            )

    def test_source_compiler_rejects_include_cycles(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "one").write_text("include:two\n", encoding="utf-8")
            (source / "two").write_text("include:one\n", encoding="utf-8")
            with self.assertRaisesRegex(DomainSourceError, "circular"):
                compile_domain_ir(source, ("one",))

    def test_keenetic_rejects_regex_instead_of_weakening_it(self):
        sets = {
            set_id: CanonicalDomainSet(
                set_id,
                (CanonicalDomain(DomainKind.REGEXP, r"^example\\.com$"),),
            )
            for set_id in KEENETIC_DOMAIN_SETS
        }
        with self.assertRaisesRegex(ValueError, "cannot represent regexp"):
            KeeneticBackend().generate(CanonicalDomainIR.create(sets))

    def test_end_to_end_writes_required_release_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            output = root / "release"
            source.mkdir()
            for set_id in KEENETIC_DOMAIN_SETS:
                (source / set_id).write_text(
                    f"{set_id}.example\n",
                    encoding="utf-8",
                )
            generate_keenetic(source, output)
            self.assertEqual(
                {
                    path.relative_to(output).as_posix()
                    for path in output.rglob("*.txt")
                },
                {f"keenetic/{set_id}.txt" for set_id in KEENETIC_DOMAIN_SETS},
            )


if __name__ == "__main__":
    unittest.main()
