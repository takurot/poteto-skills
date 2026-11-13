---
name: ralph-loop
description: Start a finite, session-scoped Codex Stop iteration loop only when explicitly requested.
license: MIT
---

# ralph-loop

The optional codex-hooks plugin runs a native Stop hook. Python 3 is required. This variant is distinct from the manual default Skills. State belongs only to the current project and CODEX_THREAD_ID. Never proceed when CODEX_THREAD_ID is absent. Resolve the runtime script relative to this installed SKILL.md file. From this Skill folder, `../../scripts/runtime.py` is the plugin runtime. Resolve that path to an absolute path before invoking it. Never depend on an ambient PLUGIN_ROOT environment variable in agent shell commands. Use the resolved absolute path as the script argument in this command prefix, with shell quoting preserved and arguments passed as data.

```bash
python3 "<resolved absolute plugin runtime path>" --project "$PWD" --session "$CODEX_THREAD_ID"
```

Append the domain and action below to that prefix. Do not execute an incomplete prefix. Report command errors. Hook state is stored in `.poteto-hooks/<sha256(session_id)>/`.

Run `ralph start --prompt "<user task>" --max-iterations 10`. A positive finite limit is mandatory; the default is 10 and values must be at most 10000. Add `--completion-promise "<exact text>"` only when requested. Then work on the task. The first non-active Stop binds this loop to its turn. Subsequent Stops in the same session and turn may continue until the finite budget or exact `<promise>text</promise>` completion marker is reached. Do not emit the marker unless completion is verified. `ralph status` reports state; `ralph cancel` ends it. This is a bounded Codex adaptation, without unlimited mode or upstream trials.
