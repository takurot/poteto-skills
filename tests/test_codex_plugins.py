import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_skills, codex_plugins
from tests.test_converter import ConverterFixture

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"^\d+\.\d+\.\d+\+poteto\.[0-9a-f]{7}$")


def tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class PluginGenerationTests(ConverterFixture):
    def build(self, **kwargs: object) -> dict:
        with mock.patch.object(build_skills, "source_revision", return_value=None):
            build_skills.build(self.source, self.output, **kwargs)
        return json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))

    def plugin(self, name: str) -> Path:
        return self.output / "codex-plugins" / name

    def test_each_upstream_plugin_becomes_a_plugin_with_both_manifests(self) -> None:
        self.add_plugin("alpha", "one")
        (self.source / "alpha" / "skills" / "two").mkdir()
        (self.source / "alpha" / "skills" / "two" / "SKILL.md").write_text(
            "---\nname: two\ndescription: Test two workflow\n---\n\n# Two\n", encoding="utf-8"
        )
        self.add_plugin("beta", "three")
        self.build()
        for name, skills in (("alpha", {"one", "two"}), ("beta", {"three"})):
            with self.subTest(plugin=name):
                root = self.plugin(name)
                root_manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
                compat = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
                self.assertEqual(root_manifest["name"], name)
                self.assertEqual(compat["name"], name)
                self.assertEqual(root_manifest["version"], compat["version"])
                self.assertRegex(root_manifest["version"], VERSION)
                self.assertEqual(compat["skills"], "./skills/")
                self.assertEqual(compat["interface"]["category"], "Developer Tools")
                self.assertTrue((root / "LICENSE").is_file())
                self.assertEqual({p.name for p in (root / "skills").iterdir()}, skills)

    def test_plugin_skills_are_the_converted_codex_skills(self) -> None:
        self.add_plugin("alpha", "one")
        self.build()
        self.assertEqual(
            tree(self.plugin("alpha") / "skills" / "one"), tree(self.output / "codex" / "one")
        )

    def test_version_tracks_the_content_and_is_deterministic(self) -> None:
        directory = self.add_plugin("alpha", "one")
        first = self.build()
        again = self.build(force=True)
        (directory / "SKILL.md").write_text(
            "---\nname: one\ndescription: Test one workflow\n---\n\n# Changed\n", encoding="utf-8"
        )
        changed = self.build(force=True)
        versions = [m["codex_plugins"][0]["version"] for m in (first, again, changed)]
        self.assertEqual(versions[0], versions[1])
        self.assertNotEqual(versions[0], versions[2])
        self.assertTrue(all(v.startswith("1.0.0+poteto.") for v in versions))

    def test_unknown_upstream_version_is_not_copied_into_the_plugin_version(self) -> None:
        self.add_plugin("alpha", "one")
        manifest = self.source / "alpha" / ".cursor-plugin" / "plugin.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        del data["version"]
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.build()
        version = json.loads((self.plugin("alpha") / "plugin.json").read_text())["version"]
        self.assertRegex(version, r"^0\.0\.0\+poteto\.[0-9a-f]{7}$")

    def test_experimental_skills_get_no_plugin(self) -> None:
        self.add_plugin("alpha", "one")
        self.add_plugin("docs-canvas", "docs-canvas")
        manifest = self.build()
        self.assertEqual([p["name"] for p in manifest["codex_plugins"]], ["alpha"])
        self.assertFalse(self.plugin("docs-canvas").exists())

    def test_marketplace_lists_every_plugin_with_required_policy_and_category(self) -> None:
        self.add_plugin("alpha", "one")
        self.add_plugin("beta", "two")
        manifest = self.build()
        document = codex_plugins.marketplace_document(manifest["codex_plugins"])
        self.assertEqual(document["name"], "poteto-skills")
        self.assertEqual([p["name"] for p in document["plugins"]], ["alpha", "beta"])
        for entry in document["plugins"]:
            with self.subTest(plugin=entry["name"]):
                self.assertEqual(
                    entry["source"],
                    {"source": "local", "path": f"./skills/codex-plugins/{entry['name']}"},
                )
                self.assertEqual(
                    entry["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
                )
                self.assertTrue(entry["category"])

    def test_marketplace_file_is_written_only_when_requested(self) -> None:
        self.add_plugin("alpha", "one")
        target = self.root / "out" / ".agents" / "plugins" / "marketplace.json"
        self.build()
        self.assertFalse(target.exists())
        self.build(force=True, marketplace_output=target)
        self.assertEqual(json.loads(target.read_text())["plugins"][0]["name"], "alpha")

    def test_verification_rejects_a_plugin_skill_that_differs_from_the_codex_skill(self) -> None:
        self.add_plugin("alpha", "one")
        self.build()
        edited = self.plugin("alpha") / "skills" / "one" / "SKILL.md"
        edited.write_text(edited.read_text() + "\nlocal edit\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_skills.verify_generated_output(self.output)


class ValidateMarketplaceTests(ConverterFixture):
    def run_validate(self, marketplace: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_generated.py"), str(self.output),
             "--marketplace", str(marketplace)],
            capture_output=True,
            text=True,
        )

    def test_validate_checks_the_catalog_against_the_generated_plugins(self) -> None:
        self.add_plugin("alpha", "one")
        catalog = self.root / "marketplace.json"
        with mock.patch.object(build_skills, "source_revision", return_value=None):
            build_skills.build(self.source, self.output, marketplace_output=catalog)
        self.assertEqual(self.run_validate(catalog).returncode, 0)

        stale = json.loads(catalog.read_text())
        stale["plugins"].append({**stale["plugins"][0], "name": "ghost"})
        catalog.write_text(json.dumps(stale), encoding="utf-8")
        result = self.run_validate(catalog)
        self.assertEqual(result.returncode, 2)
        self.assertIn("marketplace", result.stderr)

        catalog.unlink()
        self.assertEqual(self.run_validate(catalog).returncode, 2)


class CommittedPluginTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads((ROOT / "skills" / "manifest.json").read_text())
        self.marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text()
        )

    def test_marketplace_matches_the_generated_plugins(self) -> None:
        self.assertEqual(
            self.marketplace, codex_plugins.marketplace_document(self.manifest["codex_plugins"])
        )
        for entry in self.marketplace["plugins"]:
            with self.subTest(plugin=entry["name"]):
                root = ROOT / entry["source"]["path"]
                self.assertEqual((root / "plugin.json").is_file(), entry["name"] != "codex-hooks")
                self.assertTrue((root / ".codex-plugin" / "plugin.json").is_file())
                self.assertTrue((root / "LICENSE").is_file())

    def test_every_converted_skill_ships_in_exactly_one_default_plugin(self) -> None:
        shipped: dict[str, str] = {}
        for plugin in self.manifest["codex_plugins"]:
            if plugin.get("variant") == "hooks":
                continue
            for skill in plugin["skills"]:
                self.assertNotIn(skill, shipped)
                shipped[skill] = plugin["name"]
        expected = {
            s["name"]: s["plugin"] for s in self.manifest["skills"] if s["default_install"]
        }
        self.assertEqual(shipped, expected)

    def test_plugin_skills_match_the_codex_distribution(self) -> None:
        for plugin in self.manifest["codex_plugins"]:
            if plugin.get("variant") == "hooks":
                continue
            root = ROOT / "skills" / "codex-plugins" / plugin["name"]
            for skill in plugin["skills"]:
                with self.subTest(plugin=plugin["name"], skill=skill):
                    self.assertEqual(
                        tree(root / "skills" / skill), tree(ROOT / "skills" / "codex" / skill)
                    )


class HookPluginGenerationTests(PluginGenerationTests):
    def add_hook_plugins(self):
        ralph = self.add_plugin('ralph-loop', 'ralph-loop')
        for name in ('cancel-ralph', 'ralph-loop-help'):
            directory = ralph.parent / name
            directory.mkdir()
            (directory / 'SKILL.md').write_text('---\nname: ' + name + '\ndescription: Test workflow\n---\n')
        self.add_plugin('advisor', 'advisor')
        self.add_plugin('continual-learning', 'continual-learning')

    def test_hook_variant_is_separate_and_default_skills_stay_equal(self):
        self.add_hook_plugins()
        manifest = self.build()
        entry = next(e for e in manifest['codex_plugins'] if e['name'] == 'codex-hooks')
        self.assertEqual(entry['variant'], 'hooks')
        self.assertEqual(len(entry['skills']), 5)
        self.assertEqual(tree(self.plugin('ralph-loop') / 'skills/ralph-loop'), tree(self.output / 'codex/ralph-loop'))
        compat = json.loads((self.plugin('codex-hooks') / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(compat['hooks'], './hooks/hooks.json')
        self.assertFalse((self.plugin('codex-hooks') / 'plugin.json').exists())
        build_skills.verify_generated_output(self.output)

    def test_runtime_changes_update_hook_version(self):
        self.add_hook_plugins()
        first = self.build()
        source = self.root / 'hook-resources'
        import shutil
        shutil.copytree(codex_plugins.HOOK_SOURCE, source, ignore=shutil.ignore_patterns('__pycache__'))
        runtime = source / 'runtime.py'
        runtime.write_text(runtime.read_text() + '\n')
        with mock.patch.object(codex_plugins, 'HOOK_SOURCE', source):
            changed = self.build(force=True)
        version = lambda document: next(e['version'] for e in document['codex_plugins'] if e['name'] == 'codex-hooks')
        self.assertNotEqual(version(first), version(changed))

    def test_validator_rejects_unregistered_variant_and_altered_hooks(self):
        self.add_hook_plugins()
        manifest = self.build()
        entry = next(e for e in manifest['codex_plugins'] if e['name'] == 'codex-hooks')
        entry['variant'] = 'other'
        with self.assertRaises(ValueError):
            codex_plugins.verify_plugins(self.output, manifest['codex_plugins'])
        entry['variant'] = 'hooks'
        hookfile = self.plugin('codex-hooks') / 'hooks/hooks.json'
        hookfile.write_text('{"hooks": {}}')
        with self.assertRaises(ValueError):
            codex_plugins.verify_plugins(self.output, manifest['codex_plugins'])


if __name__ == "__main__":
    unittest.main()
