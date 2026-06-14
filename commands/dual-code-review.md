---
description: Dual-agent code review — Claude and GPT independently review, then negotiate findings one at a time
argument-hint: [commit-range | branch | #PR | PR-URL]
allowed-tools: Bash(git:*), Bash(gh:*), Bash(cat:*), Bash(rm:*), Bash(date:*), Read, Grep, Glob, Edit, Write
---

Two independent reviewers — Claude (correctness & architecture) and GPT
(production resilience) — review code changes separately, then negotiate
findings through a structured triage and debate protocol. Agreed fixes are
autosolved; unresolved disagreements are escalated for human review one at a time.

`Read` `~/.claude/skills/dual-review-protocol/SKILL.md` and follow it for the
non-orchestration substance: codex execution, finding format, lenses, triage,
debate (via `/plan:best-idea`), routing, presentation, error handling.
GPT prompt template: `templates/gpt-prompt-code.md`.

### Flags

Parse from `$ARGUMENTS` before resolving the positional argument:

- `--lite` → `TIER_OVERRIDE=lite` (force low reasoning effort)
- `--high` → `TIER_OVERRIDE=high` (force high reasoning effort)
- `--thermo` → `THERMO=1` (structural ambition lens + approval bar, SKILL.md §14).
  When set and `--lite` is **not** present, also set `TIER_OVERRIDE=high`
  (reason string `thermo`). Explicit `--lite` wins on tier; the ambition lens
  still applies.

Strip the flags from arguments; remainder is the positional commit-range,
branch, or PR ref. If no tier flag is present, leave `TIER_OVERRIDE` unset
so Phase 1.6 auto-classifies. `THERMO` defaults to unset (mechanical
structural checks — SKILL.md §14 Block A — are always-on regardless).

---

## Phase 1: Determine review scope

Working directory = git repo root of CWD. Set `TIMESTAMP` = `date +%s`. All temp
files use prefix `/tmp/dual-code-review-{TIMESTAMP}-`.

### Argument resolution

- **PR ref (`#123` or GitHub PR URL):**
  1. Extract PR number.
  2. `gh pr view <N> --json baseRefName,headRefName,title,body` for metadata.
  3. `gh pr diff <N>` → store at `/tmp/dual-code-review-{TIMESTAMP}-diff.txt`.
  4. `gh pr view <N> --json commits` for commit list.
- **Commit range / branch:**
  - Single hash → that commit. `abc..def` → that range. Branch → diff vs main/master.
- **No argument:**
  - On feature branch: `git merge-base HEAD main` → use that hash as base.
  - On main: HEAD only.

### Orientation data

- `git log --oneline <range>` (skip for PRs — use PR metadata)
- `git diff --stat <range>` (or parse from PR diff)

### Print summary

```
Reviewing: <range description>
Commits: [N]
Files changed: [N] (+[additions] -[deletions])
```

---

## Phase 1.5: Pre-flight

Invoke the `pre-commit-check` skill on the diff. Surface any FAIL items as
"Must Fix before review" and any WARN items (UI changes, design-system
anti-patterns) as review hints for Claude's Phase 2.

---

## Phase 1.6: Tier selection

Apply SKILL.md §12 to set `TIER` ∈ {`lite`, `normal`, `high`} and derive
`MODEL_FLAGS`. Use `TIER_OVERRIDE` from the Flags block if set; otherwise
auto-classify from `git diff --shortstat <range>` and
`git diff --name-only <range>` per §12. Per SKILL.md §14, `--thermo` (without
`--lite`) resolves `TIER=high` with reason string `thermo`.

Print the tier line per §12 convention:

```
Tier: {lite|normal|high} (reason: <reason-string>)
```

Hand `MODEL_FLAGS` to Phase 2 below in place of the §1 inline example flags.

---

## Phase 2: Parallel independent reviews

Tell user: "Both agents are reviewing the code independently."

1. Start GPT background-first (`run_in_background: true`).
2. Claude reviews while GPT works.
3. After Claude finishes, wait for GPT background result.

### GPT review (production resilience)

Prompt prefix: if `AGENTS.md`/`CLAUDE.md`/`README.md` exist in workdir,
prepend the standard "read these for project conventions" preamble.

**Context Brief** (mechanical metadata only, no interpretation):
- `CHANGE SUMMARY` — 1–2 sentences from commit log + diff stat
- `PR/ISSUE CONTEXT` — PR body / Linear issue title+description if fetched in Phase 1
- `REPO SUPPRESSIONS` — contents of `## GPT Review Suppressions` section in workdir AGENTS.md (verbatim) if present

Omit any field with no source. Omit the entire brief if no metadata.

`Read` `templates/gpt-prompt-code.md`. Substitute placeholders
(`{{CONTEXT_PREFIX}}`, `{{CONTEXT_BRIEF}}`, `{{RANGE_OR_PR}}`, `{{WORKDIR}}`,
`{{COMMIT_LOG}}`, `{{DIFF_STAT}}`, `{{RANGE}}`, `{{PR_DIFF_OVERRIDE}}` —
empty string for non-PR reviews; for PR reviews:
` [or: read /tmp/dual-code-review-{TIMESTAMP}-diff.txt for the PR diff]`).
After substitution, **append the structural addendum** (SKILL.md §14 Block D
from `structural-lens.md`): the Block A section always; the Block B (`THERMO`)
section additionally when `THERMO=1`. `Write` the rendered prompt + addendum to
`/tmp/dual-code-review-{TIMESTAMP}-gpt-prompt.txt`.

Run codex per SKILL.md Section 1 (no `--search` for code reviews unless verifying
a specific assumption). **Use `MODEL_FLAGS` from Phase 1.6 / §12 in place of the
`-m gpt-5.5 -c model_reasoning_effort=medium` example in §1** — `lite`
resolves to `low`, `high` to `high`, default (`normal`) matches the §1 default.
Note `thread_id` from the `thread.started` event for Phase 3 resume.

If codex fails: SKILL.md Section 1 background-retry protocol. Capacity error
→ drop GPT lens, continue Claude-only.

### Claude review (correctness & architecture)

Apply the **Claude code-review lenses** from SKILL.md Section 3:
logic errors, defensive coding (top reviewer-feedback category), edge cases,
type safety, architecture layers, DRY, design system, simplicity, dependency
ordering, CI/CD safety, **structural maintainability** (`Read`
`~/.claude/skills/dual-review-protocol/structural-lens.md` — Block A always;
+ Block B under `--thermo`). Universal rules (technical only, specific or
silent, concrete fixes, ≤8 findings unless systemic) also from Section 3.

Output Claude's findings using the **code-review variant** of the FINDING
schema (SKILL.md Section 2): `ID`, `Severity`, `File`, `Line`, `Category`,
`Issue`, `Evidence`, `Fix`, `Confidence`. Read each cited file/line before
emitting to verify the issue is real. Capture POSITIVE notes too.

---

## Phase 3: Triage & deduplication

Print: "Triaging findings from both reviews..."

Parse GPT findings via `~/.claude/scripts/parse-codex-output.sh` — response is
JSON per `findings-code.json` schema; extract via `jq -r '.findings[]'`. Apply
SKILL.md Section 2 minimum-viable rules.

**Apply SKILL.md §13 (low-finding triage policy).** If `claude_count + gpt_count ≤ 3`,
short-circuit per §13: print `Triage: Claude-only (low-finding policy, total=N).`,
skip the codex resume call below, perform §5 dedup and §7 routing in-context, and
proceed to Phase 4. Otherwise continue with the full triage flow below.

`Read` `templates/triage.md`. Substitute `{{CONVERSATION_SUMMARY}}` (factual
recap of pre-review user discussion, or "No prior conversation context."),
`{{REVIEW_SUBJECT}}` ("code changes"), `{{CLAUDE_FINDINGS}}` (verbatim Claude
findings), `{{EVIDENCE_SOURCE}}` ("code"). `Write` to
`/tmp/dual-code-review-{TIMESTAMP}-triage.txt`.

Send via `codex exec resume <SESSION_ID>` on gpt-5.5 at medium effort
per SKILL.md Section 1 model-selection table (structured cross-eval doesn't
need higher reasoning depth):

```
cat /tmp/dual-code-review-{TIMESTAMP}-triage.txt | codex exec resume <SESSION_ID> -m gpt-5.5 -c model_reasoning_effort=medium --json - 2>/dev/null
```

Timeout 120000. Apply SKILL.md Section 4: parse SELF-DISMISS, Claude-evaluates
each, fast-exit if all dismissed AND Claude agrees, resume-fail fallback to
Claude-only triage.

Deduplicate per SKILL.md Section 5. Route per SKILL.md Section 7
(safe-autosolve LOW/MEDIUM, review-required HIGH/CRITICAL, debate queue
for triage disagreements).

---

## Phase 4: Best-idea debate

Per SKILL.md Section 6. Cap 5 findings (CRITICAL → LOW). Excess →
`[unresolved-no-debate]`.

Print "Debating finding {ID} ({N}/{total})..." before each, "{ID}: {AGREED|UNRESOLVED}" after.

Claude runs `/plan:best-idea` Debate Mode internally for its position. Then
`Read` `templates/debate.md`, substitute `{{REVIEW_SUBJECT}}` ("code"),
`{{FINDING_FULL}}`, `{{GPT_ORIGINAL}}`, `{{CLAUDE_ORIGINAL}}`,
`{{CLAUDE_ACTION}}`/`{{CLAUDE_PICK}}`/`{{CLAUDE_WHY}}`/`{{CLAUDE_TRADEOFFS}}`
(from Claude's RECOMMENDATION), `{{EVIDENCE_SOURCE}}` ("code"). `Write` to
`/tmp/dual-code-review-{TIMESTAMP}-debate-{N}.txt`.

Send via resume with `-m gpt-5.5 -c model_reasoning_effort=medium`
(timeout 120000). Apply Round 1 / Round 2 logic from SKILL.md Section 6. Action verdict
(`agreed-fix` / `agreed-skip`) per SKILL.md Section 7.

---

## Phase 5: Present results

Use SKILL.md Section 8 layout. Title: `Dual Code Review: <range>`. Reviewers:
`Claude (correctness & architecture) + gpt-5.5 (production resilience)`.

**Under `THERMO`** (SKILL.md §14): elevate structural-regression findings to
HIGH so they route to the individual-review queue (§7) instead of silent
autosolve-skip, and print the Block C approval-bar line above the queues —
`Thermo mode: structural regressions are presumptive blockers; correct-but-messy is not a pass.`

Say **go** to proceed with resolution.

---

## Phase 6: Auto-resolve + tiebreaker resolution

When user says **go**:

### Pre-check: empty queues

If both auto-resolve and individual-review queues are empty:
```
No findings to resolve. Review complete.
```
Skip to Phase 7. No commit prompt.

### Step 1: Auto-resolve batch (LOW/MEDIUM agreements)

```
**Auto-resolve queue:** [N] findings (LOW/MEDIUM, both agents agree)

**Will apply (agreed-fix):**
  1. `file:line` — [Title] → [Fix] [{tag}]
  ...
**Will skip (agreed-skip):**
  3. `file:line` — [Title] (skip reason) [{tag}]
  ...

Reply Y to apply all, N to skip whole batch, or list numbers (e.g. "2,4" or "1-3,5")
to pull those into individual review.
```

**STOP. Wait for response.**

**Input grammar (strict):**
- `Y` / `y` / empty (Enter) → apply all fixes, no-op the skips
- `N` / `n` → skip entire batch, do not enter individual review
- One or more comma- or space-separated tokens, each `<int>` or `<int>-<int>` →
  those findings move to the front of the individual-review queue (Step 3 best-idea
  format if user wants reconsideration). Rest of batch applies/no-ops as Y.
- Anything else → re-prompt **once** with `Couldn't parse "<input>". Use Y / N / number list (e.g. 2,4 or 1-3).`
  Second parse failure → abort with `Aborting resolution. Run /dual-code-review again to retry.` (no commit; Phase 7 cleanup)

**Range expansion:** `1-3` = `1,2,3`. Out-of-range integers dropped with
`Ignoring N — only X findings in batch.` If all integers drop, treat as empty
list and re-prompt.

### Step 2: Individual review — HIGH/CRITICAL agreements (confirm-only)

For each finding in the review-required queue (HIGH/CRITICAL agreements):

```
**Finding {N}/{total}: {Title}** `{file}:{line}` — Severity: {LEVEL} [{agreed-fix | agreed-skip}]

- Issue / Evidence

**Both agents agree:**
- Pick: ...
- Why: ...
- Trade-offs: ...

Confirm to apply (Y), describe alternative, or skip.
```

**STOP after each.** For `agreed-skip`, "apply" = acknowledge skip, no code change.

### Step 3: Individual review — disagreements (best-idea tiebreaker)

For each unresolved finding, Claude runs `/plan:best-idea` Debate Mode internally
with both Phase 4 RECOMMENDATIONs as input. Apply SKILL.md Section 9
(concrete-fix rule for novel picks; research-before-ask gate via Explore subagent).

Present per SKILL.md Section 9 layout. Default Y = best-idea pick. `claude` /
`gpt` to prefer originals. **STOP after each.**

**Best-idea failure** → fall back to A/B/C/D per SKILL.md Section 9.

### Step 4: Apply fixes

Before applying, render the **leverage summary** per SKILL.md Section 8
(final-confirmation block) over the approved findings, then confirm.

For each approved finding (auto-resolve batch + Step 2 + Step 3):
1. Propose specific text edit.
2. Apply via Edit tool.
3. Verify syntax.

`agreed-skip` and user-`skip` choices apply no code change — recorded as acknowledged skips.

### Step 5: Commit prompt

```
All issues addressed.

Files modified: [list]
Skipped (acknowledged): [N findings]

Commit these fixes? (y/n)
```

If yes: commit with message `fix: address dual code review findings`.
If no files modified (all-skip outcome): print `No changes to commit.` → Phase 7.

---

## Phase 7: Cleanup

```
rm -f /tmp/dual-code-review-{TIMESTAMP}-diff.txt
rm -f /tmp/dual-code-review-{TIMESTAMP}-gpt-prompt.txt
rm -f /tmp/dual-code-review-{TIMESTAMP}-triage.txt
rm -f /tmp/dual-code-review-{TIMESTAMP}-debate-*.txt
```

Run on completion or any error exit.

Error handling: SKILL.md Section 10.
