# Codex plugin verification

Verified on 2026-11-14 JST with Codex CLI 0.169.0. These checks complete the
phase-1 evidence for Issue #20 and exercise the hook variants for Issue #25.
All installations and live runs used isolated Codex homes. Authentication was
referenced through temporary symlinks, without copying credentials. No real
Codex configuration or hook trust was changed.

## Marketplace and pstack

The GitHub marketplace at commit
`95207f4b40aee1e8896392b9638f9f128a0b4182` installed all 22 ordinary plugins.
`codex debug prompt-input` discovered all 42 implicit Skills. The other 67 default
Skills retained their explicit-only policy.

The live pstack run read the installed adapter and full Skill. Its recorded
collaboration calls contain exactly one `spawn_agent`, followed by a completed
wait. The spawn omitted model and reasoning overrides because the model file was
absent. `update_plan` was unavailable, so the run used the documented checklist
in its reply. The TUI's `update_plan` availability was not tested.

See [the summary](issue-20-summary.json) and
[the recorded collaboration calls](issue-20-collaboration.json). The summary
records prompt truncation, sandbox cache warnings, and encrypted worker-brief
limitations. The full installed Skill was read after prompt truncation.

## Native Stop hooks

The final installed hook package was `1.0.0+poteto.a1ae961`, generated from clean
upstream revision `6e359ce0aba9e927914d8a940510aa2ef66a8f23`.
The following command form ran each synthetic task in its own project.

```bash
CODEX_HOME=<isolated-home> codex exec --json \
  --dangerously-bypass-hook-trust --skip-git-repo-check \
  -C <isolated-project> '<synthetic task>'
```

The test configuration used `sandbox_mode = "workspace-write"` and
`approval_policy = "never"`. The inspected hook scripts ran with trust bypassed
for these invocations only. Persisted trust through `/hooks` was not tested.
Normal users must review the scripts through `/hooks` before enabling them.

| Case | Observed native continuation | Final check |
| --- | --- | --- |
| Ralph limit | Two hook prompts requested attempts 2 and 3 | Exactly three attempts, then Ralph state removed |
| Ralph promise | One hook prompt requested attempt 2 | Exact promise stopped a four-attempt budget early and removed state |
| Advisor | One pending-review reminder | Explicit acknowledgement cleared pending state without a second reminder |
| Continual learning | One current-transcript checkpoint | Acknowledgement advanced the processed cursor and cleared its pending snapshot |
| Installed Skill | Namespaced Skill initialized a two-attempt loop | Relative runtime resolution worked and the loop stopped after two attempts |

The advisor fixture explicitly cleared a synthetic review marker. It did not
evaluate a separate reviewer model. The learning fixture read its current
transcript and found no recurring preferences. Every fixture left project
`AGENTS.md` absent and unchanged. Successful hook delivery does not prove the
quality of future reviews or memory updates.

See [the run summary](issue-25-summary.json) and
[the transcript extracts](issue-25-codex-hooks.jsonl). The extracts contain actual
assistant messages, native `<hook_prompt>` continuations from the corresponding
session rollouts, and final persisted state. Personal paths and session identities
are replaced with placeholders. No other sessions or raw transcript contents are
included.

## Compatibility findings and regression checks

Live `hooks/list` comparisons showed no registered hook with both root and
compatibility manifests, even when both declared hooks. Removing root
`plugin.json` registered the compatibility manifest's hook as `untrusted`.
The optional hook package therefore ships only `.codex-plugin/plugin.json`.

An initial live run also showed that the default sandbox rejects state creation
under `.codex/`. The final runtime uses project `.poteto-hooks/`. The final live
checks passed under the same sandbox policy.

The regression suite passed all 94 tests, including malformed payloads and state,
session separation, active Stop handling, finite limits, promises, interrupted
Ralph dispatch, explicit advisor markers, transcript snapshots, and installed
Skill paths with spaces and no `PLUGIN_ROOT` variable. The initial hook tests
failed before the runtime existed. The interrupted-loop regression also failed
before its one-line dispatcher fix.

Two fresh builds matched each other, the candidate generated tree, and the
marketplace byte for byte. The ordinary 22 packages and both flat distributions
retained their existing Skill bytes. Generated validation, Python compilation,
shellcheck, JSON parsing, installer regression tests, and Claude plugin validation
passed. Independent reviews found the relative path, first-checkpoint wording,
and interrupted-loop bugs. All three were resolved before the final live runs.
