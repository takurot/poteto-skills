import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts/codex_hooks/runtime.py"


class StopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        self.state = (
            self.project / ".poteto-hooks" / hashlib.sha256(b"session").hexdigest()
        )

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args):
        return subprocess.run(
            [
                sys.executable,
                str(RUNTIME),
                "--project",
                str(self.project),
                "--session",
                "session",
                *args,
            ],
            capture_output=True,
            text=True,
        )

    def stop(self, **changes):
        event = dict(
            session_id="session",
            turn_id="turn",
            cwd=str(self.project),
            hook_event_name="Stop",
            stop_hook_active=False,
            last_assistant_message="Done.",
        )
        event.update(changes)
        result = subprocess.run(
            [sys.executable, str(RUNTIME), "stop"],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_ralph_budget_and_active_stop(self):
        self.assertEqual(
            self.cli(
                "ralph", "start", "--prompt", "Finish", "--max-iterations", "4"
            ).returncode,
            0,
        )
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(self.stop(stop_hook_active=True)["decision"], "block")
        self.assertEqual(self.stop(stop_hook_active=True)["decision"], "block")
        self.assertEqual(self.stop(stop_hook_active=True), {})
        self.assertFalse((self.state / "ralph.json").exists())

    def test_ralph_wrong_turn_and_session_and_promise(self):
        self.cli("ralph", "start", "--prompt", "Finish", "--completion-promise", "DONE")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(self.stop(turn_id="other", stop_hook_active=True), {})
        self.assertEqual(self.stop(session_id="other"), {})
        self.assertEqual(
            self.stop(
                last_assistant_message="<promise>DONE</promise>", stop_hook_active=True
            ),
            {},
        )

    def test_advisor_nudges_once_and_skips_questions_and_active(self):
        self.cli("advisor", "enable")
        self.cli("advisor", "pending")
        self.assertEqual(self.stop(last_assistant_message="Choose?"), {})
        self.assertEqual(self.stop(stop_hook_active=True), {})
        self.assertEqual(self.stop()["decision"], "block")
        self.assertEqual(self.stop(), {})
        self.cli("advisor", "consulted")
        self.assertEqual(self.stop(), {})

    def test_wrong_turn_ralph_does_not_suppress_advisor_or_learning(self):
        transcript = self.project / "session.jsonl"
        transcript.write_text("review me")
        self.cli("ralph", "start", "--prompt", "Finish", "--max-iterations", "4")
        self.cli("advisor", "enable")
        self.cli("advisor", "pending")
        self.cli("learning", "enable", "--turns", "1")
        self.assertIn("Ralph iteration 2/4", self.stop()["reason"])
        with self.subTest(domain="advisor"):
            self.assertIn(
                "Advisor",
                self.stop(turn_id="second", transcript_path=str(transcript)).get("reason", ""),
            )
        with self.subTest(domain="learning"):
            self.assertIn(
                "Continual",
                self.stop(turn_id="second", transcript_path=str(transcript)).get("reason", ""),
            )
        self.assertEqual(self.stop(turn_id="second", transcript_path=str(transcript)), {})

    def test_learning_deduplicates_and_requires_ack(self):
        transcript = self.project / "session.jsonl"
        transcript.write_text('{"text":"untrusted"}\n')
        self.cli("learning", "enable", "--turns", "2")
        self.assertEqual(self.stop(transcript_path=str(transcript)), {})
        self.assertEqual(self.stop(transcript_path=str(transcript)), {})
        result = self.stop(turn_id="second", transcript_path=str(transcript))
        self.assertEqual(result["decision"], "block")
        state = json.loads((self.state / "learning.json").read_text())
        self.assertEqual(state["processed"], 0)
        self.assertEqual(state["pending"], 2)
        self.cli("learning", "ack")
        self.assertEqual(
            json.loads((self.state / "learning.json").read_text())["processed"], 2
        )

    def test_malformed_inputs_and_missing_identity(self):
        for value in [
            "{",
            "[]",
            "null",
            '{"session_id": 1}',
            '{"session_id":"x","cwd":3}',
        ]:
            result = subprocess.run(
                [sys.executable, str(RUNTIME), "stop"],
                input=value,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {})
        result = subprocess.run(
            [sys.executable, str(RUNTIME), "ralph", "status"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.cli("ralph", "start", "--prompt", "Finish")
        self.assertEqual(self.stop(stop_hook_active="false"), {})

    def test_ralph_cancel_and_invalid_budget(self):
        for value in ("0", "-1", "10001"):
            self.assertNotEqual(
                self.cli(
                    "ralph", "start", "--prompt", "Task", "--max-iterations", value
                ).returncode,
                0,
            )
        self.cli("ralph", "start", "--prompt", "Task")
        self.assertEqual(self.cli("ralph", "cancel").returncode, 0)
        self.assertEqual(json.loads(self.cli("ralph", "status").stdout), {})
        self.assertEqual(self.stop(), {})

    def test_corrupt_and_wrong_identity_state_is_inert(self):
        self.cli("ralph", "start", "--prompt", "Task")
        path = self.state / "ralph.json"
        original = json.loads(path.read_text())
        for changes in (
            {"session_id": "wrong"},
            {"project": "/"},
            {"version": True},
            {"iteration": "1"},
            {"max_iterations": 0},
            {"prompt": []},
        ):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}))
                self.assertEqual(self.stop(), {})
        path.write_text("{")
        self.assertEqual(self.stop(), {})

    def test_state_symlinks_are_never_followed(self):
        outside = self.project / "outside"
        outside.mkdir()
        (self.project / ".poteto-hooks").symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.cli("advisor", "enable").returncode, 0)
        self.assertEqual(self.stop(), {})
        self.assertEqual(list(outside.iterdir()), [])
        (self.project / ".poteto-hooks").unlink()
        self.cli("advisor", "enable")
        path = self.state / "advisor.json"
        path.unlink()
        target = outside / "secret"
        target.write_text("preserve")
        path.symlink_to(target)
        self.assertEqual(self.stop(), {})
        self.assertNotEqual(self.cli("advisor", "enable").returncode, 0)
        self.assertEqual(target.read_text(), "preserve")

    def test_learning_requires_both_thresholds_after_first_checkpoint(self):
        transcript = self.project / "session.jsonl"
        transcript.write_text("first\n")
        self.cli("learning", "enable", "--turns", "2", "--minutes", "120")
        self.assertEqual(self.stop(transcript_path=str(transcript)), {})
        self.assertEqual(
            self.stop(turn_id="two", transcript_path=str(transcript))["decision"],
            "block",
        )
        self.cli("learning", "ack")
        transcript.write_text("first\nsecond\n")
        self.assertEqual(
            self.stop(turn_id="three", transcript_path=str(transcript)), {}
        )
        self.assertEqual(self.stop(turn_id="four", transcript_path=str(transcript)), {})
        path = self.state / "learning.json"
        state = json.loads(path.read_text())
        state["updated"] = 0
        path.write_text(json.dumps(state))
        self.assertEqual(
            self.stop(turn_id="four", transcript_path=str(transcript))["decision"],
            "block",
        )

    def test_learning_ack_does_not_skip_appended_unreviewed_bytes(self):
        transcript = self.project / "session.jsonl"
        transcript.write_text("first\n")
        self.cli("learning", "enable", "--turns", "1")
        self.assertEqual(
            self.stop(transcript_path=str(transcript))["decision"], "block"
        )
        transcript.write_text("first\nunreviewed\n")
        self.assertEqual(
            self.stop(turn_id="second", transcript_path=str(transcript)), {}
        )
        self.cli("learning", "ack")
        state = json.loads((self.state / "learning.json").read_text())
        record = next(iter(state["transcripts"].values()))
        self.assertEqual(record["processed"]["size"], len("first\n"))
        self.assertEqual(record["observed"]["size"], len("first\nunreviewed\n"))
        self.assertEqual(state["processed"], 1)
        state["updated"] = 0
        (self.state / "learning.json").write_text(json.dumps(state))
        self.assertEqual(
            self.stop(turn_id="second", transcript_path=str(transcript))["decision"],
            "block",
        )

    def test_learning_does_not_scan_or_mark_missing_transcript_processed(self):
        self.cli("learning", "enable", "--turns", "1")
        self.assertEqual(self.stop(transcript_path=str(self.project / "missing")), {})
        self.assertEqual(self.stop(turn_id="second", stop_hook_active=True), {})
        self.cli("learning", "ack")
        state = json.loads((self.state / "learning.json").read_text())
        self.assertEqual(state["processed"], 0)
        self.assertEqual(state["transcripts"], {})
        self.assertEqual(state["turn_ids"], ["turn"])

    def test_priority_does_not_discard_learning_turns(self):
        transcript = self.project / "session.jsonl"
        transcript.write_text("review me")
        self.cli("learning", "enable", "--turns", "1")
        self.cli("advisor", "enable")
        self.cli("advisor", "pending")
        self.assertIn("Advisor", self.stop(transcript_path=str(transcript))["reason"])
        self.assertIn("Continual", self.stop(transcript_path=str(transcript))["reason"])
        self.assertEqual(self.stop(transcript_path=str(transcript)), {})
        self.assertEqual(
            self.stop(session_id="other", transcript_path=str(transcript)), {}
        )


class InstalledHookSkillTests(unittest.TestCase):
    def test_every_installed_skill_resolves_and_executes_its_runtime_without_plugin_root(self):
        import os
        import re
        import shutil
        import yaml

        with tempfile.TemporaryDirectory(prefix="hook install ") as temporary:
            installed = Path(temporary) / "plugin"
            shutil.copytree(ROOT / "skills/codex-plugins/codex-hooks", installed)
            environment = dict(os.environ)
            environment.pop("PLUGIN_ROOT", None)
            for folder in sorted((installed / "skills").iterdir()):
                with self.subTest(skill=folder.name):
                    text = (folder / "SKILL.md").read_text()
                    relative = re.search(r"From this Skill folder, `([^`]+)`", text).group(1)
                    runtime = (folder / relative).resolve()
                    result = subprocess.run(
                        [sys.executable, str(runtime), "--project", temporary,
                         "--session", "installed-session", "ralph", "status"],
                        env=environment, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout), {})
                    policy = yaml.safe_load((folder / "agents/openai.yaml").read_text())
                    self.assertIs(policy["policy"]["allow_implicit_invocation"], False)
                    frontmatter = yaml.safe_load(text.split("---", 2)[1])
                    self.assertEqual(frontmatter["license"], "MIT")
                    self.assertNotIn("disable-model-invocation", frontmatter)
