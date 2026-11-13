# pstack in Codex

pstack skills use Cursor names. In Codex, read this file once per session, then map each Cursor name in a skill with the tables below. `<skills>` means the Skill root that holds this Skill: `.agents/skills/` in the workspace, `~/.codex/skills/`, or the plugin folder that holds this Skill's siblings. If a Cursor field has no row, drop it and say so. Never pass a field or value the tool schema rejects. Never report a skipped or unavailable step as run.

The tool names below were checked against the schemas of Codex CLI 0.169.0. When the tool schemas in your session differ, follow the schemas and say what you changed.

Codex has no stop hooks in a plain Skill install, so keep the autonomy inside the turn: follow the playbook to its end, and pause only for a blocker the skill itself names or for a permission the host asks you to confirm.

## Tools

| Cursor | Codex |
| --- | --- |
| `Task` | `spawn_agent`. It requires `task_name` (lowercase letters, digits, underscores) and `message`, the full brief. Spawn independent workers in the same turn. Pass `fork_turns: "none"` unless the skill says the worker needs this conversation: the default, `all`, copies the whole parent history into the worker. |
| Wait for a worker | `wait_agent`. It takes only `timeout_ms` and returns when an agent reports. Call it only when the next critical-path step is blocked on a result. If the session offers `close_agent`, call it when a worker is no longer needed. |
| `AskQuestion` | `request_user_input` when the session offers it. It is unavailable in `codex exec` and in subagents, so ask in plain text there. |
| Open a todolist | `update_plan` when the session offers it, copying the playbook steps in verbatim and updating at each phase. Otherwise keep the list in your reply and update it at each phase. |
| Run another pstack skill (`/name` or "the **name** skill") | Read `<skills>/<name>/SKILL.md` and follow it. When you tell the user to type it, write `$<name>`, or `$<plugin>:<name>` when this Skill came from a plugin, as its name in the Skill list shows. |
| `Grep`, `Glob` | Shell `rg` and `rg --files`. |

## Subagent fields

| Cursor | Codex |
| --- | --- |
| `subagent_type: generalPurpose` | Omit it. `spawn_agent` starts the default agent. |
| `poteto-agent`, `comment-sicko` | `spawn_agent` has no agent-type parameter in the checked schema, so spawn the default agent and paste the bundled definition into `message` as its instructions: `<skills>/poteto-mode/references/cursor-agents/poteto-agent.md` or `<skills>/no-comments/references/cursor-agents/comment-sicko.md`. Use a registered agent type only when your `spawn_agent` schema offers a parameter for it. |
| `readonly: true` | `spawn_agent` has no sandbox parameter. Write "do not edit files" in `message`, and check `git status` afterward. |
| `readonly: false` | The default agent. |
| `environment: "cloud"` | A separate `git worktree` that the worker uses. Name the branch or commit it checks out. |
| `environment: "local"` | Omit. |
| `cloud_base_branch: <b>` | Tell the worker to check out `<b>` first. |
| `run_in_background: true` | Omit. `spawn_agent` returns at once. |
| `resume` | `followup_task` with `target` set to the agent's task name and the new instructions in `message`, only in the cases the skill names. `send_message` only queues a note and starts no turn. If the agent is gone, spawn a new one and paste the earlier result into its `message`. |
| `file_attachments` | List the paths in `message`. |

## Models

| Cursor | Codex |
| --- | --- |
| A model slug such as `claude-opus-5-5-xhigh`, `grok-4.7-xhigh-fast`, or `gpt-*` | Pass `model` only when it is one of the overrides that the `spawn_agent` description lists. Otherwise omit `model` so the agent runs on the session model, and say so in one line. Never edit a suffix to build an identifier. |
| The effort token in a slug, or a role value `<model> <effort>` | Pass the effort through `reasoning_effort` only when the description lists that effort for the model. Otherwise omit it and say so. Drop `-fast`. |
| `auto` or `inherit-parent` | Omit `model`. |
| The `pstack-models.mdc` rule, `~/.cursor/rules/pstack-models.mdc` | `~/.codex/pstack-models.md`. Codex does not load it. Read it yourself before choosing any model. If the file or the role's line is missing, use the skill's default and apply the model rows above. |

## setup-pstack

Follow its steps with these changes:

- Detect. The detected models are the overrides, each with its efforts, that the `spawn_agent` description lists. If it lists none, ask the user to name identifiers they know work, or use `inherit-parent`. Never write an identifier you did not confirm.
- Defaults. Map each default slug with the Models rows. A slug the host does not list becomes `inherit-parent`.
- Budget. Treat the budget as a target for `reasoning_effort`, not as text inside a model name. Choose only identifiers and efforts the host lists.
- Write. Write `~/.codex/pstack-models.md` as plain Markdown with no frontmatter, then the comment lines, the `# budget` line, and one line per role from step 5. Overwrite the whole file. Say that Codex does not load it and that pstack skills read it when invoked. Do not put the role lines in `AGENTS.md`.

## Paths

| Cursor | Codex |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | `.agents/skills/`, `~/.codex/skills/` |
| `~/.cursor/plugins/`, `.cursor-plugin/plugin.json` | The Skill root above. Codex has no plugin folder for these Skills. |
| `.cursor/rules/*.mdc`, always-applied rules | `AGENTS.md`. Codex never reads `.mdc` files. The model file is the exception. See Models. |
| `https://github.com/cursor/plugins/blob/main/pstack/<path>` | The bundled copy under `<skills>/` when it exists. Give the user the URL when they need a link. |
| Transcripts in `~/.cursor/projects/<slug>/agent-transcripts/` | `~/.codex/sessions/YYYY/MM/DD/rollout-<time>-<thread-id>.jsonl`. The current session is the file whose name ends with `$CODEX_THREAD_ID`. Read only that file, and only when the skill needs the current session. Never scan other sessions. |

## Cursor-only features

Codex has no Cursor Automations, Bugbot, Cursor cloud agents, or built-in PR tool. When a step needs one, put one line in your reply, `Skipped in Codex: <step>. <reason>.`, then go on to the next step. Do not stop, ask, or retry. When a later step needs what the skipped step made, such as a URL or a key, leave a placeholder and name it in the line.

| Cursor | Codex |
| --- | --- |
| Cursor Automations: routines, `update_state` routine calls, `api2.cursor.sh/automations` webhooks, routine wakes, and `SendToUser` secret requests | Skip with the line. |
| `/loop` | Skip with the line. Continue the playbook in this turn instead. |
| Bugbot | Bugbot comments on a GitHub PR are ordinary review threads, so triage them with the forge command that the step gives. Skip a step that starts, waits for, or configures Bugbot when the PR has no Bugbot check or comment. |
| Cursor cloud agents | `environment: "cloud"` maps to a worktree, as in Subagent fields. Skip a step that needs the cloud agent itself, such as its dashboard status or its own machine. |
| A built-in PR tool | Use the forge command that the step gives, such as `gh pr create`. That is not a skip, so write no line. |
