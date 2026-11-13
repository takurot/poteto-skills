# pstack in Codex

pstack skills use Cursor names. In Codex, read this file once per session, then map each Cursor name in a skill with the tables below. `<skills>` means the Skill root that holds this Skill: `.agents/skills/` in the workspace, or `~/.codex/skills/`. If a Cursor field has no row, drop it and say so. Never pass a field or value the tool schema rejects. Never report a skipped or unavailable step as run.

Codex has no stop hooks, so keep the autonomy inside the turn: follow the playbook to its end, and pause only for a blocker the skill itself names or for a permission the host asks you to confirm.

## Tools

| Cursor | Codex |
| --- | --- |
| `Task` | `spawn_agent`. Spawn independent workers in the same turn. Call `wait_agent` only when the next critical-path step is blocked on the result. Call `close_agent` when a worker is no longer needed. |
| `AskQuestion` | `request_user_input` when the session offers it. It is unavailable in `codex exec` and in subagents, so ask in plain text there. |
| Open a todolist | `update_plan`. Copy the playbook steps in verbatim and update the plan at each phase. |
| Run another pstack skill (`/name` or "the **name** skill") | Read `<skills>/<name>/SKILL.md` and follow it, or use the host's `$name` mention. When you tell the user to type it, write `$<name>`. |
| `Grep`, `Glob` | Shell `rg` and `rg --files`. |

## Subagent fields

| Cursor | Codex |
| --- | --- |
| `subagent_type: generalPurpose` | Omit `agent_type`. The default agent runs. |
| `poteto-agent`, `comment-sicko` | Use `agent_type: "poteto-agent"` or `"comment-sicko"` only when `~/.codex/agents/<name>.toml` or `.codex/agents/<name>.toml` registers it. Otherwise spawn the default agent and paste the bundled definition, `<skills>/poteto-mode/references/cursor-agents/poteto-agent.md` or `<skills>/no-comments/references/cursor-agents/comment-sicko.md`, into its brief as its instructions. Skills that bundle a definition list it under their own `references/cursor-agents/`. |
| `readonly: true` | Use a registered read-only agent such as `explorer` when one exists. Otherwise spawn the default agent, write "do not edit files" in the brief, and check `git status` afterward. |
| `readonly: false` | The default agent. |
| `environment: "cloud"` | A separate `git worktree` that the worker uses. Name the branch or commit it checks out. |
| `environment: "local"` | Omit. |
| `cloud_base_branch: <b>` | Tell the worker to check out `<b>` first. |
| `run_in_background: true` | Omit. `spawn_agent` returns at once. |
| `resume` | `send_message` to the same agent while it is still open, only in the cases the skill names. Otherwise spawn a new agent and paste the earlier result into its brief. |
| `file_attachments` | List the paths in the brief. |

## Models

| Cursor | Codex |
| --- | --- |
| A model slug such as `claude-opus-5-5-xhigh`, `grok-4.7-xhigh-fast`, or `gpt-*` | Pass `model` only when `spawn_agent` accepts that exact identifier in this session. Otherwise omit `model` so the agent runs on the session model, and say so in one line. Never edit a suffix to build an identifier. |
| The effort token in a slug, or a role value `<model> <effort>` | Pass the effort through `reasoning_effort` only when the tool schema lists it. Otherwise drop it and say so. Drop `-fast`. |
| `auto` or `inherit-parent` | Omit `model`. |
| The `pstack-models.mdc` rule, `~/.cursor/rules/pstack-models.mdc` | `~/.codex/pstack-models.md`. Codex does not load it. Read it yourself before choosing any model. If the file or the role's line is missing, use the skill's default and apply the model rows above. |

## setup-pstack

Follow its steps with these changes:

- Detect. The detected models are the `model` identifiers that the current `spawn_agent` schema lists or that a rejected call's error names, each with the `reasoning_effort` values it lists. If neither is available, ask the user to name identifiers they know work, or use `inherit-parent`. Never write an identifier you did not confirm.
- Defaults. Map each default slug with the Models rows. A slug the host does not accept becomes `inherit-parent`.
- Budget. Treat the budget as a target for `reasoning_effort`, not as text inside a model name. Choose only identifiers and efforts the host accepts.
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
