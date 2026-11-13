---
name: advisor
description: Enable or manage explicitly requested advisor Stop nudges for this Codex session.
license: MIT
---

# advisor

The optional codex-hooks plugin runs a native Stop hook. Python 3 is required. This variant is distinct from the manual default Skills. State belongs only to the current project and CODEX_THREAD_ID. Never proceed when CODEX_THREAD_ID is absent. Resolve the runtime script relative to this installed SKILL.md file. From this Skill folder, `../../scripts/runtime.py` is the plugin runtime. Resolve that path to an absolute path before invoking it. Never depend on an ambient PLUGIN_ROOT environment variable in agent shell commands. Use the resolved absolute path as the script argument in this command prefix, with shell quoting preserved and arguments passed as data.

```bash
python3 "<resolved absolute plugin runtime path>" --project "$PWD" --session "$CODEX_THREAD_ID"
```

Append the domain and action below to that prefix. Do not execute an incomplete prefix. Report command errors. Hook state is stored in `.poteto-hooks/<sha256(session_id)>/`.

Run `advisor enable` only at the user's request. After edits needing review, explicitly run `advisor pending`; no PostToolUse automatic edit tracking is provided. Consult the configured independent reviewer and inspect justified findings. Never claim a consultation occurred without evidence. After consultation run `advisor consulted`. `advisor off` removes state and `advisor status` inspects it. Stop nudges once per pending review, skips questions ending in `?` and active Stops, and cannot supply a reviewer or unavailable model itself. If a reviewer is unavailable report it and explicitly clear pending; do not claim review passed.
