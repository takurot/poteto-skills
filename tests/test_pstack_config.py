import unittest
from pathlib import Path

from scripts import build_skills


ROOT = Path(__file__).resolve().parents[1]
CONSUMERS = (
    "arena",
    "interrogate",
    "poteto-help",
    "poteto-mode",
    "swarm",
)
CONFIG_PATHS = {
    "claude-code": "~/.claude/pstack-models.md",
    "codex": "~/.codex/pstack-models.md",
}
CURRENT_ROLES = {
    "feature, refactoring",
    "bug-fix",
    "perf-issue",
    "hillclimb",
    "judgment and prose",
    "arena runners",
    "arena cross-judge pool",
    "swarm workers",
    "interrogate reviewers",
}
SETUP_SOURCE = """\
Write `~/.cursor/rules/pstack-models.mdc`, an always-applied rule that sets pstack's model per role.

### 1. Detect available models

Enumerate the model slugs you can pass to a `Task` subagent in this session. That is the dependable source. If Cursor also exposes a models API or CLI that lists the user's entitled models, prefer it for completeness. If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

Drop the retired `hardest tasks` role. Replace old Grok entries with `claude-opus-5-5-high-fast` and old Gemini entries with `gemini-4-neon-xhigh`.

### 3. Budget, map, and confirm

**(b) Apply it.** Choose a Cursor model slug by budget.

**(c) Show the roles and confirm.** Confirm the selected roles.

### 5. Write the rule

Write `~/.cursor/rules/pstack-models.mdc` with `alwaysApply: true`, the `# defaults: 3` line, a `# budget` line with the chosen label and the effort that label names, and one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape:

```
---
description: pstack per-role model choices
alwaysApply: true
---
# defaults: 3
# budget: large (xhigh)
arena runners: claude-opus-5-5-high-fast, gemini-4-neon-xhigh
swarm workers: claude-opus-5-5-high-fast
```

### 6. Confirm

Tell the user the rule was written and that it applies to new sessions. Re-running this skill updates it.
"""


class PstackConfigTests(unittest.TestCase):
    def skill_text(self, target: str, name: str) -> str:
        root = ROOT / "skills" / target
        if target == "claude-code":
            root /= "skills"
        return (root / name / "SKILL.md").read_text()

    def test_setup_writes_explicitly_consumed_host_config(self) -> None:
        for target, config_path in CONFIG_PATHS.items():
            with self.subTest(target=target):
                text = self.skill_text(target, "setup-pstack")
                self.assertIn(config_path, text)
                self.assertIn("is not loaded automatically by the host", text)
                self.assertIn("Do not construct a model identifier by editing a suffix", text)
                self.assertIn("only exact identifiers accepted by the current host", text)
                self.assertNotIn("alwaysApply", text)
                self.assertNotIn("applies to new sessions", text)

    def test_setup_converts_v3_without_migrating_to_cursor_models(self) -> None:
        for target, config_path in CONFIG_PATHS.items():
            with self.subTest(target=target):
                source = SETUP_SOURCE.replace("~/.cursor/rules/pstack-models.mdc", config_path)
                text = build_skills.adapt_pstack_config("setup-pstack", source, config_path)
                state = text.split("### 2.", 1)[1].split("### 3.", 1)[0]
                self.assertIn("`inherit-parent`", state)
                self.assertIn("`auto`", state)
                self.assertIn("retired", state)
                self.assertRegex(state, r"(?i)\b(keep|preserve)\b")
                self.assertNotIn("claude-opus-5-5-high-fast", text)
                self.assertNotIn("gemini-4-neon-xhigh", text)
                self.assertNotIn("alwaysApply", text)
                self.assertIn("# defaults: 3", text.split("\n```\n")[1].splitlines())

    def test_setup_sample_lists_only_current_roles(self) -> None:
        for target in CONFIG_PATHS:
            with self.subTest(target=target):
                text = self.skill_text(target, "setup-pstack")
                sample = text.split("\n```\n")[1]
                self.assertNotIn("---", sample.splitlines())
                self.assertIn("# defaults: 3", sample.splitlines())
                role_lines = [line for line in sample.splitlines() if not line.startswith("#")]
                self.assertCountEqual(
                    role_lines, [f"{role}: inherit-parent" for role in CURRENT_ROLES]
                )

    def test_each_consumer_reads_the_same_host_config(self) -> None:
        for target, config_path in CONFIG_PATHS.items():
            for name in CONSUMERS:
                with self.subTest(target=target, name=name):
                    text = self.skill_text(target, name)
                    self.assertIn(f"Read `{config_path}`", text)
                    self.assertNotIn("pstack-models.mdc", text)

    def test_help_explains_when_saved_model_choices_apply(self) -> None:
        for target in CONFIG_PATHS:
            with self.subTest(target=target):
                text = self.skill_text(target, "poteto-help")
                self.assertIn("reads it when invoked", text)
                self.assertNotIn("applies to new chats", text)

    def test_fresh_generated_consumer_contract_uses_saved_role(self) -> None:
        for target, config_path in CONFIG_PATHS.items():
            setup = self.skill_text(target, "setup-pstack")
            consumer = self.skill_text(target, "swarm")
            with self.subTest(target=target):
                self.assertIn("swarm workers: inherit-parent", setup)
                self.assertIn(f"Read `{config_path}`", consumer)
                self.assertIn("`swarm workers` line", consumer)
                self.assertIn("omit `model`", consumer)


if __name__ == "__main__":
    unittest.main()
