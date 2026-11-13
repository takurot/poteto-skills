import json
import re
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_skills
from tests.test_converter import ConverterFixture

ROOT = Path(__file__).resolve().parents[1]
RELATIVE_LINK = re.compile(r"\]\((\.{1,2}/[^)\s#]+)")
FAKE_REVISION = "0123456789abcdef0123456789abcdef01234567"


def skill_roots() -> list[tuple[str, Path]]:
    return [
        ("claude-code", ROOT / "skills" / "claude-code" / "skills"),
        ("codex", ROOT / "skills" / "codex"),
    ]


class GeneratedLinkTests(unittest.TestCase):
    def test_relative_links_stay_inside_the_skill_or_reach_a_sibling_skill(self) -> None:
        names = {s["name"] for s in json.loads((ROOT / "skills" / "manifest.json").read_text())["skills"]}
        for host, root in skill_roots():
            broken: list[str] = []
            for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
                for file in skill_dir.rglob("*.md"):
                    for link in RELATIVE_LINK.findall(file.read_text(errors="ignore")):
                        target = (file.parent / link).resolve()
                        inside = target.is_relative_to(skill_dir.resolve())
                        sibling = target.is_relative_to(root.resolve()) and target.relative_to(
                            root.resolve()
                        ).parts[0] in names
                        if not (inside or sibling) or not target.exists():
                            broken.append(f"{file.relative_to(root)} -> {link}")
            with self.subTest(host=host):
                self.assertEqual(broken, [])


class ExternalLinkConversionTests(ConverterFixture):
    def build_with_link(self, link: str, *, revision: str | None = FAKE_REVISION) -> str:
        skill_directory = self.add_plugin("alpha", "guide")
        (skill_directory / "SKILL.md").write_text(
            f"---\nname: guide\ndescription: Test guide workflow\n---\n\nSee [docs]({link}).\n",
            encoding="utf-8",
        )
        (self.source / "alpha" / "docs").mkdir()
        (self.source / "alpha" / "docs" / "page.md").write_text("# Page\n", encoding="utf-8")
        with mock.patch.object(build_skills, "source_revision", return_value=revision):
            build_skills.build(self.source, self.output)
        return (self.output / "codex" / "guide" / "SKILL.md").read_text(encoding="utf-8")

    def test_link_to_an_unbundled_upstream_file_becomes_a_pinned_permalink(self) -> None:
        text = self.build_with_link("../../docs/page.md#intro")
        self.assertIn(
            f"(https://github.com/cursor/plugins/blob/{FAKE_REVISION}/alpha/docs/page.md#intro)",
            text,
        )
        self.assertNotIn("../../docs", text)

    def test_link_to_a_missing_upstream_file_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing.md"):
            self.build_with_link("../../docs/missing.md")

    def test_external_link_without_a_source_revision_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "revision"):
            self.build_with_link("../../docs/page.md", revision=None)

    def test_links_inside_the_skill_and_to_sibling_skills_are_kept(self) -> None:
        skill_directory = self.add_plugin("alpha", "guide")
        sibling = self.source / "alpha" / "skills" / "other"
        sibling.mkdir()
        (sibling / "SKILL.md").write_text(
            "---\nname: other\ndescription: Test other workflow\n---\n\n# Other\n",
            encoding="utf-8",
        )
        (skill_directory / "references").mkdir()
        (skill_directory / "references" / "note.md").write_text("# Note\n", encoding="utf-8")
        (skill_directory / "SKILL.md").write_text(
            "---\nname: guide\ndescription: Test guide workflow\n---\n\n"
            "[note](references/note.md) and [other](../other/SKILL.md)\n",
            encoding="utf-8",
        )
        with mock.patch.object(build_skills, "source_revision", return_value=None):
            build_skills.build(self.source, self.output)
        text = (self.output / "codex" / "guide" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("(references/note.md)", text)
        self.assertIn("(../other/SKILL.md)", text)


if __name__ == "__main__":
    unittest.main()
