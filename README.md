# poteto-skills

[日本語](README_JP.md)

**Last updated:** 2026-11-14

A distribution of Skills from the official [`cursor/plugins`](https://github.com/cursor/plugins) collection, converted into formats that Claude Code and Codex can load.

## Contents

- `skills/claude-code/skills/` — Skills for Claude Code; its parent directory is also a validatable Claude Code plugin
- `skills/codex/` — Skills for Codex, including `agents/openai.yaml`
- `skills/codex-plugins/` and `.agents/plugins/marketplace.json` — the same Codex Skills packaged as one Codex plugin per upstream Cursor plugin, and the marketplace catalog that lists them
- `install.sh` — Installer for user-level or project-level installation
- `scripts/build_skills.py` — Conversion script that regenerates the distributions from `ref/plugins`
- `skills/manifest.json` — Manifest recording source paths, licenses, versions, compatibility notes, and generated-file checksums

Only Skills declared by each Cursor plugin's `plugin.json` are converted. Plugins that contain only MCP configuration are not converted because they are not Skills. Two duplicate Skill pairs are consolidated by selecting either the more self-contained copy or the copy from the canonical plugin. The current source revision generates 110 Skills for each host.

## Installation

Clone the repository:

```bash
git clone https://github.com/takurot/poteto-skills.git
cd poteto-skills
```

Install all Skills for both hosts at the user level:

```bash
./install.sh
```

Install for only one host:

```bash
./install.sh --target claude
./install.sh --target codex
```

Install into a project:

```bash
./install.sh --target both --scope project --project-dir /path/to/project
```

Claude Code Skills are installed in `<project>/.claude/skills/`. Codex Skills are installed in `<project>/.agents/skills/`.

You can also select individual Skills:

```bash
./install.sh --list
./install.sh --target codex --skill thermos --skill tdd
```

Each `--skill` value must be a non-empty, exact Skill name. Repeat the option to
select multiple Skills; omit it entirely to install all Skills.

The default set currently installs 109 production-ready Skills. `docs-canvas` is
listed in `--list` but excluded because its upstream workflow is still a
placeholder. To evaluate its host-specific fallback and bundled smoke artifact,
select it explicitly with `--skill docs-canvas`; the installer prints an
experimental warning.

Main options:

- `--dry-run` — Show planned operations without writing files
- `--force` — Move conflicting Skills to timestamped backups before updating
- `--scope user|project` — Select the installation scope
- `--target claude|codex|both` — Select the target host

By default, an existing Skill with the same name is not overwritten and is reported as `skipped`. Identical installations are reported as `unchanged`.

Backups are kept outside active Skill discovery directories:

- Claude Code: `~/.claude/skill-backups/` for user installs and `<project>/.claude/skill-backups/` for project installs. `CLAUDE_CONFIG_DIR` replaces `~/.claude` when set.
- Codex: `~/.codex/skill-backups/` for user installs and `<project>/.agents/skill-backups/` for project installs. `CODEX_HOME` replaces `~/.codex` when set.

Forced updates are staged on the destination filesystem. If activation fails after the existing Skill is backed up, the installer restores that original Skill automatically and removes its temporary staging directory.

## Codex plugins

The Codex Skills are also packaged as Codex plugins, one per upstream Cursor plugin (22 plugins, 109 Skills), and listed in `.agents/plugins/marketplace.json`. This is an alternative to `install.sh`.

```bash
codex plugin marketplace add takurot/poteto-skills
codex plugin list
codex plugin add pstack@poteto-skills
```

- Skills from a plugin are named `<plugin>:<skill>`, so pstack's mode is `$pstack:poteto-mode`. Only Skills that allow implicit invocation appear in the model's Skill list. The explicit-only ones run when you name them.
- Upgrade with `codex plugin marketplace upgrade poteto-skills`. Remove with `codex plugin remove pstack@poteto-skills`.
- A plugin's version is `<upstream version>+poteto.<content hash>`, so any regenerated content installs as a new version.
- Do not install the same Skill with both `install.sh` and a plugin. The two copies share names and the plugin one is namespaced.
- `dyl-stack` expects the `pstack` plugin, which it finds beside `setup-pstack`.
- These 22 plugins have no hooks. `ralph-loop`, `advisor`, and `continual-learning` keep their manual fallbacks.
- The experimental `docs-canvas` Skill is not packaged. Named Cursor subagents are not registered.

### Enable optional Codex hooks

Install the separate `codex-hooks` plugin for native Codex `Stop` hooks. It requires Python 3 and includes five Skill variants.

```bash
codex plugin add codex-hooks@poteto-skills
```

This package uses only `.codex-plugin/plugin.json`. Codex CLI 0.169.0 does not discover its hooks when a root `plugin.json` is also present.

Review and trust its scripts in `/hooks` before use. Installation alone does not activate trusted hooks. Review changed scripts again after an update. Plugins with hooks are not eligible for the public plugin directory.

Invoke `$codex-hooks:ralph-loop`, `$codex-hooks:advisor`, or `$codex-hooks:continual-learning` to enable the corresponding feature for the current session. Use `$codex-hooks:cancel-ralph` to cancel a loop and `$codex-hooks:ralph-loop-help` for its limits. Avoid installing the matching manual Skills through `install.sh` or their ordinary plugins alongside these variants.

- Ralph repeats the saved task until its exact completion promise appears or its finite iteration limit is reached. The default is 10 attempts, including the first. Unlimited loops are rejected.
- Advisor uses explicit pending and successful-consult markers from its Skill. It sends one reminder for pending work and suppresses recursive reminders and questions. It does not automatically detect edits or subagent completion.
- Continual learning counts ordinary turns and requests processing of the current session's host-exposed transcript after its turn threshold and the interval since the last acknowledged review pass. Defaults are 10 turns and 120 minutes. The first review requires only the turn threshold. Its index advances only after explicit acknowledgement. It does not scan other sessions or treat transcript text as instructions.

State stays under the project's `.poteto-hooks/`, separated by session identity. Do not commit that state. Activation requires the host's `CODEX_THREAD_ID`. Ralph has priority over advisor, followed by continual learning. The latter two do not issue reminders on hook-generated continuations. Hook trust, plugin installation, and feature activation are separate steps.

Remove the plugin with `codex plugin remove codex-hooks@poteto-skills`. This removes its executable hooks, while project state remains available for inspection.

## Conversion policy

Claude Code and Codex use different Skill frontmatter formats, so this repository provides separate distributions.

| Cursor element | Claude Code | Codex |
|---|---|---|
| `name`, `description` | Normalized to the supported format | Normalized to the supported format |
| `disable-model-invocation` | Preserved | Converted to `allow_implicit_invocation: false` in `agents/openai.yaml` |
| `icon`, `color`, `mode`, `reminder`, `paths` | Unsupported fields removed | Unsupported fields removed |
| Skill scripts, references, and assets | Preserved | Preserved |
| Cursor-specific agent definitions | Bundled under `references/cursor-agents/` | Bundled under `references/cursor-agents/` |
| References to `.cursor/skills/` | Converted to `.claude/skills/` | Converted to `.agents/skills/` or `~/.codex/skills/` |
| Relative links that leave the Skill folder (plugin README, guides) | Rewritten to a permalink at the pinned upstream revision | Rewritten to a permalink at the pinned upstream revision |

Names are normalized to lowercase kebab-case. The converter parses frontmatter with
PyYAML, rejects duplicate or unknown fields and invalid values, and emits valid YAML.
The known legacy form of an unquoted plain `description` containing a colon is
normalized explicitly. Support trees reject symlinks, secrets, caches, and dependency
directories. A declared MIT license and a matching upstream `LICENSE` file are required.

## Compatibility boundaries

Skill instructions and local resources can be converted, but Cursor-specific runtime capabilities are not bundled.

- Ordinary Claude Code and Codex installs use manual fallbacks for Cursor hook workflows. The optional `codex-hooks` plugin ports bounded continuation, advisor reminders, and continual-learning indexing to Codex. It requires hook trust review and explicit session activation.
- Skills that use Cursor Canvas include a fallback to a standalone HTML artifact when Canvas is unavailable.
- Skills that use MCP require the corresponding MCP server to be configured separately in Claude Code or Codex.
- Skills that operate the Cursor SDK or Cursor Cloud Agents still require Cursor credentials and services.
- Named Cursor subagents are not registered automatically. Their original definitions are bundled under `references/cursor-agents/` for use as prompts with an available general-purpose subagent.
- pstack on Codex: every converted pstack Skill bundles `references/codex-adapter.md` (source: `scripts/adapters/pstack-codex.md`). It maps `Task` to `spawn_agent` (with `task_name`, and `fork_turns: "none"` for fresh-context workers) and `wait_agent`, `resume` to `followup_task`, `AskQuestion` to `request_user_input`, todo lists to `update_plan` when offered (else the reply), named subagents to a brief that embeds the bundled definition, and the current transcript to the `$CODEX_THREAD_ID` rollout file. Cursor Automations, `/loop`, and Cursor cloud agents are skipped with a one-line note instead of being reported as run. The tool names were checked against Codex CLI 0.169.0; the adapter tells the agent to follow the session's own tool schemas when they differ.
- `setup-pstack` writes a shared per-host Markdown file. The host does not load it as configuration; converted pstack Skills read it explicitly when invoked and use only model identifiers accepted by that host.

Each converted Skill also starts with a compatibility note that prevents unavailable host capabilities from being reported as executed. See `skills/manifest.json` for per-Skill constraints.

## Regeneration

Fetch or update the source plugins, then run the builder:

```bash
git clone https://github.com/cursor/plugins.git ref/plugins
python3 -m pip install --requirement requirements.txt
python3 scripts/build_skills.py
python3 scripts/validate_generated.py skills
```

The `ref/` directory is not included in this repository. If `ref/plugins` already exists, update that repository before converting. The builder discovers only the `skills` directories declared by `plugin.json` and deterministically regenerates `skills/` and `.agents/plugins/marketplace.json`.

The manifest and its sidecar checksum protect the generated tree. A normal rebuild
refuses modified, added, or missing generated files. Review and preserve local work;
use `--force` only when intentionally replacing a recognized generated tree. Output
activation uses a rollback-safe rename. CI rebuilds both host distributions from the
pinned upstream revision and compares them with the committed tree.

## License

The repository-authored installer, converter, and documentation are available under the [MIT License](LICENSE).

Converted Skills retain their upstream MIT licenses. The applicable source license is bundled in each Skill's `LICENSE` file, with copyright notices belonging to Cursor, Lauren Tan, or Anysphere, Inc. The root license does not replace those notices. Keep each corresponding Skill `LICENSE` file when redistributing converted content.
