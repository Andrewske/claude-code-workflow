---
description: Dual-agent plan review — Claude and GPT independently review, then negotiate findings
argument-hint: [<path>] (optional - auto-detects from workflow state)
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

Two independent reviewers — Claude (adversarial lens) and GPT (implementation
feasibility lens) — review a plan separately, then negotiate findings through
a structured triage and debate protocol. Agreed fixes are autosolved;
unresolved disagreements are escalated for human review.

`Read` `~/.claude/skills/dual-review-protocol/SKILL.md` and follow it for the
non-orchestration substance: codex execution, finding format, triage, debate
(via `/plan:best-idea`), routing, presentation, and error handling. The
GPT prompt template is `templates/gpt-prompt-plan.md`.

---

## Phase 1: Plan selection

Compute `STORAGE_ROOT` per `commands/plan/README.md`. Print the resolved path.

If an explicit path argument was given, use it directly. Otherwise, follow the
**Plan Selection Pattern** (see `commands/plan/README.md`) with status filter
`ready`. If `{STORAGE_ROOT}/workflow-state.json` is missing, fall back to scanning
`{STORAGE_ROOT}/tasks/*/README.md` (do NOT search `docs/`).

Announce: "Reviewing: {plan-path}".

**Reviewability check:** Plan must have an objective, approach, and task breakdown.
If not:
```
**Insufficient detail for review.**
Missing: [list]
Recommendation: Return to planning phase to define [X, Y, Z]
```

Set `TIMESTAMP` (Unix epoch). Temp files use `/tmp/dual-review-{TIMESTAMP}-`.

---

## Phase 2: Parallel independent reviews

Tell user: "Both agents are reviewing the plan independently."

Strategy:
1. Start GPT background-first (`run_in_background: true`), see SKILL.md Section 1.
2. While GPT works, Claude performs its review (lens below).
3. After Claude finishes, wait for GPT's background result.

### GPT review (implementation feasibility)

Prompt prefix: if `AGENTS.md`/`CLAUDE.md`/`README.md` exist in workdir, prepend
the standard "read these for project conventions" preamble.

Build the **Context Brief** (mechanical metadata only — CHANGE SUMMARY for plan
content, PR/ISSUE CONTEXT if linked to a Linear issue, REPO SUPPRESSIONS from
AGENTS.md `## GPT Review Suppressions` section if present). Omit if no metadata.

**Read plan content** — README.md and all task files under `{STORAGE_ROOT}/tasks/{plan}/`.

**Size guard:** if plan content exceeds ~50K tokens (~200K chars), summarize each
task file (objective + approach + key constraints) instead of including verbatim.

`Read` `templates/gpt-prompt-plan.md`. Substitute placeholders
(`{{CONTEXT_PREFIX}}`, `{{CONTEXT_BRIEF}}`, `{{PLAN_PATH}}`, `{{PLAN_CONTENT}}`),
then `Write` rendered prompt to `/tmp/dual-review-{TIMESTAMP}-gpt-prompt.txt`.

Run codex per SKILL.md Section 1. **For plan reviews, place `--search` BEFORE
`exec`** (`codex --search exec ...`) — it is a top-level flag and `codex exec
--search` errors with `unexpected argument`. Note the `thread_id` from the
`thread.started` event for Phase 3 resume.

If codex fails: SKILL.md Section 1 background-retry protocol. Capacity
error → drop GPT lens, continue Claude-only.

### Claude review (adversarial)

You are a battle-scarred principal engineer. Assume something is wrong until proven otherwise.

**Extraction:** Objective, Approach, Assumptions (stated + unstated), Dependencies, Scope (in/out).

**Adversarial analysis** (≥3 reasoning passes per dimension):
- **Assumption stress test** — every assumption: "what if this is false? what breaks?"
- **Failure mode exploration** — undefined-behavior inputs, dependency-down behavior, 10× load
- **Simplicity audit** — is there a 50% simpler approach for 90% of cases?
- **Architecture check** — coupling, debuggability at 3am
- **Dependency ordering** — correctness, parallelism opportunities

**Strengthen findings:** "is this real or pattern-matching?" Discard weak ones. Classify severity per `commands/plan/README.md`.

Output Claude's findings using the **plan-review variant** of the FINDING schema (see SKILL.md Section 2): `ID`, `Title`, `Section`, `Severity`, `Problem`, `Impact`, `Fix`, `Confidence`.

---

## Phase 3: Triage & deduplication

Print: "Triaging findings from both reviews..."

Parse GPT findings (use `~/.claude/scripts/parse-codex-output.sh` — response is
JSON per `findings-plan.json` schema; extract via `jq -r '.findings[]'`).
Extract per SKILL.md Section 2 minimum-viable rules.

`Read` `templates/triage.md`. Substitute `{{CONVERSATION_SUMMARY}}`,
`{{REVIEW_SUBJECT}}` ("a plan"), `{{CLAUDE_FINDINGS}}`, `{{EVIDENCE_SOURCE}}`
("plan or codebase"). `Write` to `/tmp/dual-review-{TIMESTAMP}-triage.txt`.

Send via `codex exec resume <SESSION_ID>` on gpt-5.5 at medium effort
per SKILL.md Section 1 model-selection table:

```
cat /tmp/dual-review-{TIMESTAMP}-triage.txt | codex exec resume <SESSION_ID> -m gpt-5.5 -c model_reasoning_effort=medium --json - 2>/dev/null
```

Timeout 120000. Apply SKILL.md Section 4 rules (self-dismiss + cross-evaluation,
fast-exit on all-dismissed, resume-fail fallback to Claude-only triage).

Deduplication: SKILL.md Section 5 (plan variant — match by section + problem domain).

Routing:
- **Autosolve queue:** triage-agreed + both-found
- **Debate queue:** disagreements, prioritized by severity

---

## Phase 4: Best-idea debate

Per SKILL.md Section 6. Cap 5 findings (CRITICAL → LOW). Excess →
`[unresolved-no-debate]`.

Print "Debating finding {ID} ({N}/{total})..." before each, "{ID}: {AGREED|UNRESOLVED}" after.

Debate delegates to `/plan:best-idea` Debate Mode. `Read` `templates/debate.md`,
substitute `{{REVIEW_SUBJECT}}` ("plan"), `{{FINDING_FULL}}`, `{{GPT_ORIGINAL}}`,
`{{CLAUDE_ORIGINAL}}`, `{{CLAUDE_*}}` (Claude's RECOMMENDATION fields),
`{{EVIDENCE_SOURCE}}` ("plan"). `Write` to `/tmp/dual-review-{TIMESTAMP}-debate-{N}.txt`.

Send via resume with `-m gpt-5.5 -c model_reasoning_effort=medium`
(timeout 120000). Round 1 + optional Round 2 per SKILL.md.

### Debate transcript

After all debate rounds, save transcript to `{STORAGE_ROOT}/tasks/{plan}/dual-review-transcript.md`:

```markdown
# Dual Review Transcript — {plan-name}
Generated: {date}

## Agreement Stats
- Triage agreed: {N}
- Debate resolved: {N}
- Unresolved: {N}
- Concession flag: [Claude never conceded | GPT never conceded | Both conceded]

## Debated Findings

### Finding {ID}: {Title}
**Claude's position:** ...
**GPT's position:** ...

**Round 1:**
- Claude rec: ...
- GPT verdict: AGREE | DISAGREE
- GPT rec (if DISAGREE): ...

**Round 2 (if applicable):**
- Claude final: CONCEDE | HOLD
- Outcome: AGREED | UNRESOLVED
- Outcome-reason: debated | resume-failed
```

---

## Phase 5: Present results

Use SKILL.md Section 8 layout, adapted for plans:

```
## Dual Plan Review: [Plan Name]

**Reviewers**: Claude (adversarial) + gpt-5.5 (implementation feasibility)

### Agreement Stats
- Total findings: [N] (Claude: [N], GPT: [N], Both found: [N])
- Triage agreed: [N] autosolved
- Debated: [N] ([N] resolved, [N] unresolved)
- Needs Review: [N]

### Needs Review (Unresolved Disagreements)
[Per SKILL.md Section 8 unresolved layout — Claude's + GPT's RECOMMENDATIONs]

### Autosolved Findings
[Group by severity. Each: tag + section + fix]

### What Works
[Strengths]

**GPT Usage Report (cumulative)**
[per SKILL.md Section 8 cost format]
```

Say **go** to proceed with resolution.

---

## Phase 6: One-at-a-time resolution

When user says **go**, follow Resolution Flow from `commands/plan/README.md`:

### Step 1: Needs-review items first (one at a time)

For each unresolved finding, present A/B/C/D:

```
**Finding {N}/{total}: {Title}** [Section: X] — Severity: {LEVEL}

- Problem / Impact

- A: Claude's recommendation — [Pick / Why / Trade-offs]
- B: GPT's recommendation — [Pick / Why / Trade-offs]
- C: Your own approach — describe
- D: Skip — leave as-is
```

**STOP after each. Wait for user response.**

### Step 2: Autosolve batch

```
**Autosolved Findings:**
1. [Title] → [Fix] ({confidence}%) [Section: X] — {triage-agreed | debate-agreed | both-found}
2. ...

Confirm to apply all, or say "review" to discuss individually.
```

### Step 3: Apply

Before applying, render the **leverage summary** per SKILL.md Section 8
(final-confirmation block) over the approved findings, then confirm.

For each approved finding: propose edit, apply via Edit, verify coherence.

### After complete

**STOP HERE. Do NOT start implementation.**

```
STOP. Run /clear then /plan:start-implementation
```

---

## Cleanup

```
rm -f /tmp/dual-review-{TIMESTAMP}-gpt-prompt.txt
rm -f /tmp/dual-review-{TIMESTAMP}-triage.txt
rm -f /tmp/dual-review-{TIMESTAMP}-debate-*.txt
```

Error handling: SKILL.md Section 10.
