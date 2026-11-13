import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = "references/codex-adapter.md"


class PstackCodexAdapterTests(unittest.TestCase):
    def pstack_names(self) -> list[str]:
        manifest = json.loads((ROOT / "skills" / "manifest.json").read_text())
        return [s["name"] for s in manifest["skills"] if s["plugin"] == "pstack"]

    def test_every_codex_pstack_skill_bundles_and_points_to_adapter(self) -> None:
        names = self.pstack_names()
        self.assertIn("poteto-mode", names)
        source = (ROOT / "scripts" / "adapters" / "pstack-codex.md").read_text()
        for name in names:
            with self.subTest(name=name):
                root = ROOT / "skills" / "codex" / name
                self.assertEqual((root / ADAPTER).read_text(), source)
                self.assertIn(f"`{ADAPTER}`", (root / "SKILL.md").read_text())

    def test_claude_and_other_plugins_do_not_get_the_codex_adapter(self) -> None:
        for name in self.pstack_names():
            with self.subTest(name=name):
                root = ROOT / "skills" / "claude-code" / "skills" / name
                self.assertFalse((root / ADAPTER).exists())
        other = next(
            s["name"]
            for s in json.loads((ROOT / "skills" / "manifest.json").read_text())["skills"]
            if s["plugin"] != "pstack"
        )
        self.assertFalse((ROOT / "skills" / "codex" / other / ADAPTER).exists())

    def test_adapter_maps_cursor_controls_to_verified_codex_tools(self) -> None:
        text = (ROOT / "scripts" / "adapters" / "pstack-codex.md").read_text()
        for needle in (
            "spawn_agent",
            "wait_agent",
            "close_agent",
            "send_message",
            "update_plan",
            "request_user_input",
            "~/.codex/pstack-models.md",
            "$CODEX_THREAD_ID",
            "Skipped in Codex:",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertNotIn("Claude", text)

    def test_adapter_matches_the_checked_codex_tool_surface(self) -> None:
        text = (ROOT / "scripts" / "adapters" / "pstack-codex.md").read_text()
        for needle in (
            "task_name",
            'fork_turns: "none"',
            "followup_task",
            "`timeout_ms`",
            "$<plugin>:<name>",
            "0.169.0",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        for removed in ('agent_type: "poteto-agent"', "Call `close_agent`"):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, text)
        resume_row = next(line for line in text.splitlines() if line.startswith("| `resume` |"))
        self.assertIn("followup_task", resume_row)

    def test_poteto_agent_definition_resolves_codex_skill_roots(self) -> None:
        text = (
            ROOT / "skills" / "codex" / "poteto-mode" / "references" / "cursor-agents" / "poteto-agent.md"
        ).read_text()
        self.assertNotIn("~/.cursor/plugins/", text)
        self.assertIn(".agents/skills/poteto-mode/SKILL.md", text)
        self.assertIn("~/.codex/skills/poteto-mode/SKILL.md", text)


if __name__ == "__main__":
    unittest.main()
