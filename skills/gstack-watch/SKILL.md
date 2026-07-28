---
name: gstack-watch
description: Watch upstream gstack for changes to the skills ported into this repo and suggest updates. Use when asked to check for gstack updates, sync the ported skills, see what changed upstream in gstack, or update plan-eng/plan-ceo/plan-design/browse from gstack.
allowed-tools:
  - Read
  - Edit
  - Bash
triggers:
  - check for gstack updates
  - sync ported skills
  - what changed in gstack
  - update ports from gstack
---

## What this is

gstack was uninstalled from this machine, but the skills ported from it
(`plan-eng`, `plan-ceo`, `plan-design`, and `browse`) can drift from upstream.
This skill diffs upstream gstack against the commit the ports were taken from and
surfaces methodology changes worth pulling in. It is deliberately **lean**: read
a manifest, run plain `git`, interpret the diff, ask per change. No helper
script, no automated baseline mutation.

Manifest: `skills/gstack-watch/port-manifest.json` (in this repo). It holds the
upstream clone path, `baseline_sha` (the gstack commit the ports came from), and,
per ported skill, the upstream file paths to diff.

## Workflow

**1. Load the manifest.** Read `skills/gstack-watch/port-manifest.json`. Note
`upstream_clone`, `baseline_sha`, and the `ports` list. Expand `~` in the clone
path to `$HOME`.

**2. Ensure the clone exists and is current.**
- If the clone dir is missing, tell the user to create it once:
  `git clone https://github.com/garrytan/gstack.git ~/dev/tools/gstack-upstream && git -C ~/dev/tools/gstack-upstream remote set-head origin -a`
  then stop.
- Otherwise: `git -C <clone> fetch origin` then
  `git -C <clone> remote set-head origin -a` (resolve the default branch
  explicitly — do not assume `origin/HEAD` is fresh).
- Read the latest SHA: `git -C <clone> rev-parse origin/HEAD`.

**3. Up to date?** If the latest SHA equals `baseline_sha`, report
"Ports are current with gstack `<version>` (`<sha[:12]>`). Nothing to review."
and stop.

**4. Diff each port.** For each entry in `ports`, run:
`git -C <clone> diff <baseline_sha>..origin/HEAD -- <paths...>`
- **Missing-path guard:** if a listed path no longer exists upstream (rename or
  reorg), the diff for it will be empty or error. Verify with
  `git -C <clone> ls-tree -r --name-only origin/HEAD -- <path>`. If the path is
  gone, **flag it explicitly**: "upstream `<path>` is gone (renamed/moved) —
  manual recheck needed for `<ported>`." Never treat a vanished path as
  "no changes."

**5. Classify the hunks — do NOT pre-filter.** Read every non-trivial hunk and
label it:
- `runtime-only` — changes confined to the gstack plumbing that was stripped
  during porting (the `## Preamble`, telemetry, brain/gbrain, artifacts-sync,
  question-tuning, model-overlay, GStack `## Voice` sections). These don't exist
  in the ports, so they're **informational** — count them, don't action them.
- `methodology` — changes to the actual review content the ports preserve: the
  body below `# Plan Review Mode`, `sections/review-sections.md`, Step 0 scope
  challenge, cognitive patterns, the question-asking format, completeness rules.
  These are **actionable**.

Be careful at the boundary: a change in a "runtime-looking" region that alters
review behavior is `methodology`, not `runtime-only`. When unsure, classify as
`methodology` and let the user decide.

**6. Present actionable changes one at a time.** For each `methodology` change,
present in chat markdown: show the upstream hunk, explain what it changes,
recommend whether to port it into the corresponding `skills/<ported>/...` file
(with a confidence %), then STOP and wait for a reply. One change per question.
On accept, make the edit (re-applying the port's
transformations: drop gstack runtime, keep kg-plan wiring, keep the renamed
`## PLAN REVIEW REPORT`, keep the new skill name). After edits, run
`bash scripts/install-skills.sh` to reinstall.

**7. After the review, bump the baseline.** Tell the user to update
`baseline_sha` (and `baseline_version` from the upstream `VERSION` file) in
`port-manifest.json` to the new `origin/HEAD`, then commit. This is a one-line
manual edit — there is intentionally no auto-mutation.

## Notes

- `browse` tracks only `browse/SKILL.md` upstream. Its engine diverged to the
  browseros MCP, so most upstream browse changes are runtime-only — but QA
  methodology changes in the prose are still worth seeing. Never port gstack
  browse daemon/runtime details into the browseros skill.
- This is local-only (no external posts), so applying edits is autonomous beyond
  the per-change chat-markdown gate.
- Bash rules: use plain sequential `git` calls. No `$()`, backticks, heredocs, or
  process substitution.
