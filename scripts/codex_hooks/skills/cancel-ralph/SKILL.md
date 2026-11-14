---
name: cancel-ralph
description: Cancel the current session Codex Ralph loop when explicitly requested.
license: MIT
---

# cancel-ralph

The optional codex-hooks plugin runs a native Stop hook. Python 3 is required. This variant is distinct from the manual default Skills. State belongs only to the current project and CODEX_THREAD_ID. Never proceed when CODEX_THREAD_ID is absent. Resolve the runtime script relative to this installed SKILL.md file. From this Skill folder, `../../scripts/runtime.py` is the plugin runtime. Resolve that path to an absolute path before invoking it. Never depend on an ambient PLUGIN_ROOT environment variable in agent shell commands. Use the resolved absolute path as the script argument in this command prefix, with shell quoting preserved and arguments passed as data.

```bash
python3 "<resolved absolute plugin runtime path>" --project "$PWD" --session "$CODEX_THREAD_ID"
```

Append the domain and action below to that prefix. Do not execute an incomplete prefix. Report command errors. Hook state is stored in `.poteto-hooks/<sha256(session_id)>/`.

Run `ralph cancel`, then `ralph status` and verify the result is `{}`. Only this session is cancelled.
