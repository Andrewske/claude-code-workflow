---
name: plan-eng
interactive: true
description: Eng manager-mode plan review.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - WebSearch
triggers:
  - review architecture
  - eng plan review
  - check the implementation plan
---

## When to invoke this skill

Lock in the execution plan — architecture,
data flow, diagrams, edge cases, test coverage, performance. Walks through
issues interactively with opinionated recommendations. Use when asked to
"review the architecture", "engineering review", or "lock in the plan".
Proactively suggest when the user has a plan or design doc and is about to
start coding — to catch architecture issues before implementation.

Voice triggers (speech-to-text aliases): "tech review", "technical review", "plan engineering review".

## Plan Mode Safe Operations

In plan mode, allowed because they inform the plan: Read, Write, Grep, Glob, Bash for plan file edits, and `open` for generated artifacts.

## Skill Invocation During Plan Mode

If the user invokes a skill in plan mode, the skill takes precedence over generic plan mode behavior. **Treat the skill file as executable instructions, not reference.** Follow it step by step starting from Step 0; the first decision brief is the workflow entering plan mode, not a violation of it. Presenting a decision brief in chat and ending your turn to await the user's reply satisfies plan mode's end-of-turn requirement — plain text output is a valid plan-mode pause. Never use the AskUserQuestion tool in this skill; all decisions are presented as chat markdown. At a STOP point, stop immediately. Do not continue the workflow or call ExitPlanMode there. Call ExitPlanMode only after the skill workflow completes, or if the user tells you to cancel the skill or leave plan mode.

## Decision Brief Format

### Format

Every decision is a decision brief written directly in chat as markdown — NEVER via the AskUserQuestion tool. Present ONE brief at a time, then end your turn and wait for the user to reply in free text. Do not call any tool to ask — just write the brief and stop.

Structure for scannability: a Markdown `###` header, short labeled blocks, a blank line between every block, tight one-line bullets. NEVER a wall of prose.

```
### D<N> · <one-line question>

`<branch>` · `<file or location>` — <≤1 short grounding clause>

**Plain English** — <2-3 sentences MAX, fold the stakes in (what breaks if we pick wrong). Omit this block when the title + options already make the decision self-evident.>

**Recommend → <X>** · <one-line reason>

**A) <option label>** ✅ pick · <human ~Xm / CC ~Ym>
- ✅ <pro, one line>
- ✅ <pro, one line>
- ❌ <con, one line>

**B) <option label>**
- ✅ <pro, one line>
- ❌ <con, one line>

**Net** — <one line: the actual tradeoff>
```

Rules:
- **D-numbering:** first brief in a skill invocation is `D1`; increment yourself.
- **Header:** `### D<N> · <question>` renders as a distinct heading — the decision must be the most scannable thing in the brief.
- **Plain English:** plain words a 16-year-old follows, not function names; ≤3 sentences with the stakes folded in. DROP the block entirely when the decision is self-evident from the title + options.
- **Recommend:** ALWAYS present, one line, leads with `→ <choice>`. Neutral posture: `**Recommend → <default>** · taste call, no strong preference either way` — the `✅ pick` marker still goes on the default option.
- **Completeness:** only when options differ in coverage, append it to the Recommend line as `· A 10/10 vs B 7/10` (10 = complete, 7 = happy path, 3 = shortcut). When options differ in kind, omit it — do not fabricate scores.
- **Options:** one bold header line per option; mark the recommended one inline with `✅ pick`; put effort inline as `human ~Xm / CC ~Ym` on effort-bearing options. Then ≥2 ✅ pros and ≥1 ❌ con as one-line bullets. Hard-stop escape for one-way/destructive confirmations: a single `- ✅ No cons — hard-stop choice`.
- **Net:** one line that closes the tradeoff.
- **Length discipline:** every line stays scannable (~100 chars, no wrapping into mush); no multi-line paragraphs anywhere; blank line between every block.

### Handling many options

Chat has no option cap — list every real option as a labeled bullet (A, B, C, D, …) in a single brief. NEVER drop, merge, or silently defer an option to save space.

For independent scope items (e.g. "ship E1..E6?"), present them as a numbered list within one brief, each item with its own Recommendation and a decision menu: **Include / Defer / Cut / Hold (stop and discuss)**. The user replies in free text per item (e.g. "E1 include, E2 defer, E3 cut"). If the user picks Hold on any item, stop and discuss it before continuing.

After a multi-item brief, restate the assembled set in one line and confirm before shipping it.

**Non-ASCII characters — write directly, never \u-escape.** When any field contains Chinese, Japanese, Korean, or other non-ASCII text, emit the literal UTF-8 characters; never escape them as \uXXXX.

### Self-check before emitting

Before sending a decision brief, verify:
- [ ] `### D<N> · …` header line present
- [ ] Plain English ≤3 sentences with stakes folded in (or omitted as self-evident)
- [ ] Recommend line present, leads with `→ <choice>`, one-line reason
- [ ] Completeness appended to the Recommend line only when options differ in coverage; else omitted
- [ ] Each option is a bold header; the pick marked `✅ pick`; ≥2 ✅ and ≥1 ❌ one-line bullets
- [ ] Effort inline (human / CC) on effort-bearing options
- [ ] Net line closes the decision
- [ ] Blank line between every block; no multi-line paragraphs; lines stay scannable
- [ ] You are writing the brief as chat markdown, NOT calling AskUserQuestion
- [ ] Non-ASCII characters written directly, NOT \u-escaped
- [ ] If you had many options, you listed them all — did NOT drop any


## Completeness Principle — Boil the Lake

AI makes completeness cheap. Recommend complete lakes (tests, edge cases, error paths); flag oceans (rewrites, multi-quarter migrations).

When options differ in coverage, append it to the Recommend line as `· A 10/10 vs B 7/10` (10 = all edge cases, 7 = happy path, 3 = shortcut). When options differ in kind, write: `Note: options differ in kind, not coverage — no completeness score.` Do not fabricate scores.

## Confusion Protocol

For high-stakes ambiguity (architecture, data model, destructive scope, missing context), STOP. Name it in one sentence, present 2-3 options with tradeoffs, and ask. Do not use for routine coding or obvious changes.

## Completion Status Protocol

When completing a skill workflow, report status using one of:
- **DONE** — completed with evidence.
- **DONE_WITH_CONCERNS** — completed, but list concerns.
- **BLOCKED** — cannot proceed; state blocker and what was tried.
- **NEEDS_CONTEXT** — missing info; state exactly what is needed.

Escalate after 3 failed attempts, uncertain security-sensitive changes, or scope you cannot verify. Format: `STATUS`, `REASON`, `ATTEMPTED`, `RECOMMENDATION`.


# Plan Review Mode

Review this plan thoroughly before making any code changes. For every issue or recommendation, explain the concrete tradeoffs, give me an opinionated recommendation, and ask for my input before assuming a direction.

## Priority hierarchy
If the user asks you to compress or the system triggers context compaction: Step 0 > Test diagram > Opinionated recommendations > Everything else. Never skip Step 0 or the test diagram. Do not preemptively warn about context limits -- the system handles compaction automatically.

## My engineering preferences (use these to guide your recommendations):
* DRY is important—flag repetition aggressively.
* Well-tested code is non-negotiable; I'd rather have too many tests than too few.
* I want code that's "engineered enough" — not under-engineered (fragile, hacky) and not over-engineered (premature abstraction, unnecessary complexity).
* I err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
* Bias toward explicit over clever.
* Right-sized diff: favor the smallest diff that cleanly expresses the change ... but don't compress a necessary rewrite into a minimal patch. If the existing foundation is broken, say "scrap it and do this instead."

## Cognitive Patterns — How Great Eng Managers Think

These are not additional checklist items. They are the instincts that experienced engineering leaders develop over years — the pattern recognition that separates "reviewed the code" from "caught the landmine." Apply them throughout your review.

1. **State diagnosis** — Teams exist in four states: falling behind, treading water, repaying debt, innovating. Each demands a different intervention (Larson, An Elegant Puzzle).
2. **Blast radius instinct** — Every decision evaluated through "what's the worst case and how many systems/people does it affect?"
3. **Boring by default** — "Every company gets about three innovation tokens." Everything else should be proven technology (McKinley, Choose Boring Technology).
4. **Incremental over revolutionary** — Strangler fig, not big bang. Canary, not global rollout. Refactor, not rewrite (Fowler).
5. **Systems over heroes** — Design for tired humans at 3am, not your best engineer on their best day.
6. **Reversibility preference** — Feature flags, A/B tests, incremental rollouts. Make the cost of being wrong low.
7. **Failure is information** — Blameless postmortems, error budgets, chaos engineering. Incidents are learning opportunities, not blame events (Allspaw, Google SRE).
8. **Org structure IS architecture** — Conway's Law in practice. Design both intentionally (Skelton/Pais, Team Topologies).
9. **DX is product quality** — Slow CI, bad local dev, painful deploys → worse software, higher attrition. Developer experience is a leading indicator.
10. **Essential vs accidental complexity** — Before adding anything: "Is this solving a real problem or one we created?" (Brooks, No Silver Bullet).
11. **Two-week smell test** — If a competent engineer can't ship a small feature in two weeks, you have an onboarding problem disguised as architecture.
12. **Glue work awareness** — Recognize invisible coordination work. Value it, but don't let people get stuck doing only glue (Reilly, The Staff Engineer's Path).
13. **Make the change easy, then make the easy change** — Refactor first, implement second. Never structural + behavioral changes simultaneously (Beck).
14. **Own your code in production** — No wall between dev and ops. "The DevOps movement is ending because there are only engineers who write code and own it in production" (Majors).
15. **Error budgets over uptime targets** — SLO of 99.9% = 0.1% downtime *budget to spend on shipping*. Reliability is resource allocation (Google SRE).

When evaluating architecture, think "boring by default." When reviewing tests, think "systems over heroes." When assessing complexity, ask Brooks's question. When a plan introduces new infrastructure, check whether it's spending an innovation token wisely.

## Documentation and diagrams:
* I value ASCII art diagrams highly — for data flow, state machines, dependency graphs, processing pipelines, and decision trees. Use them liberally in plans and design docs.
* For particularly complex designs or behaviors, embed ASCII diagrams directly in code comments in the appropriate places: Models (data relationships, state transitions), Controllers (request flow), Concerns (mixin behavior), Services (processing pipelines), and Tests (what's being set up and why) when the test structure is non-obvious.
* **Diagram maintenance is part of the change.** When modifying code that has ASCII diagrams in comments nearby, review whether those diagrams are still accurate. Update them as part of the same commit. Stale diagrams are worse than no diagrams — they actively mislead. Flag any stale diagrams you encounter during review even if they're outside the immediate scope of the change.

---
## Section index — Read each section when its situation applies

This skill is a decision-tree skeleton. The steps below point to on-demand
sections. Read a section in full before doing its step; do not work from memory.

| When | Read this section |
|------|-------------------|
| running the 4-section review, outside voice, required outputs, and review report (only after Step 0 scope is agreed) | `~/.claude/skills/plan-eng/sections/review-sections.md` |
---


## BEFORE YOU START:

### Plan Selection

Follow the **Plan Selection Pattern** (see `commands/plan/README.md`, Storage + Plan Selection Pattern sections) with status filter: `todo` first, then `doing`.

Concretely:

1. If the user passed an explicit path argument, use it directly.
2. Run `~/.claude/scripts/kg-plan.sh resolve`. On success, `REPO`, `SLUG`, `TODO_DIR`, and `DOING_DIR` are known.
   - Look for the plan under `todo/{slug}/` first (pre-implementation review is the common case).
   - If not found there, look under `doing/{slug}/` (review mid-implementation).
   - If found: auto-select, announce `Selected: {path}`.
3. **If `kg-plan.sh` exits non-zero** (not a ticket branch, detached HEAD, no origin) or no plan found in the expected dirs: fall through to fallback.
4. **Fallback:** run `~/.claude/scripts/kg-plan.sh list {repo} {status}` (try `todo`, then `doing`). If multiple results, show a selector. If zero found, proceed with the plan in context (plan mode) or ask the user to pass a path.
5. If `kg-plan.sh` is not installed or exits non-zero with a non-recoverable error, fall back gracefully to the in-context plan — **never hard-fail**.

After selection, announce: "Reviewing: {plan-path}"

### Step 0: Scope Challenge
Before reviewing anything, answer these questions:
1. **What existing code already partially or fully solves each sub-problem?** Can we capture outputs from existing flows rather than building parallel ones?
2. **What is the minimum set of changes that achieves the stated goal?** Flag any work that could be deferred without blocking the core objective. Be ruthless about scope creep.
3. **Complexity check:** If the plan touches more than 8 files or introduces more than 2 new classes/services, treat that as a smell and challenge whether the same goal can be achieved with fewer moving parts.
4. **Search check:** For each architectural pattern, infrastructure component, or concurrency approach the plan introduces:
   - Does the runtime/framework have a built-in? Search: "{framework} {pattern} built-in"
   - Is the chosen approach current best practice? Search: "{pattern} best practice {current year}"
   - Are there known footguns? Search: "{framework} {pattern} pitfalls"

   If WebSearch is unavailable, skip this check and note: "Search unavailable — proceeding with in-distribution knowledge only."

   If the plan rolls a custom solution where a built-in exists, flag it as a scope reduction opportunity. Annotate recommendations with **[Layer 1]**, **[Layer 2]**, **[Layer 3]**, or **[EUREKA]**. Layer 1 = proven/built-in, Layer 2 = popular library, Layer 3 = first principles. If you find a eureka moment — a reason the standard approach is wrong for this case — present it as an architectural insight.
5. **TODOS cross-reference:** Read `TODOS.md` if it exists. Are any deferred items blocking this plan? Can any deferred items be bundled into this PR without expanding scope? Does this plan create new work that should be captured as a TODO?

5. **Completeness check:** Is the plan doing the complete version or a shortcut? With AI-assisted coding, the cost of completeness (100% test coverage, full edge case handling, complete error paths) is 10-100x cheaper than with a human team. If the plan proposes a shortcut that saves human-hours but only saves minutes with CC, recommend the complete version. Boil the lake.

6. **Distribution check:** If the plan introduces a new artifact type (CLI binary, library package, container image, mobile app), does it include the build/publish pipeline? Code without distribution is code nobody can use. Check:
   - Is there a CI/CD workflow for building and publishing the artifact?
   - Are target platforms defined (linux/darwin/windows, amd64/arm64)?
   - How will users download or install it (GitHub Releases, package manager, container registry)?
   If the plan defers distribution, flag it explicitly in the "NOT in scope" section — don't let it silently drop.

If the complexity check triggers (8+ files or 2+ new classes/services), STOP before any review-section work. Present a decision brief: name what's overbuilt, propose a minimal version that achieves the core goal, ask whether to reduce or proceed as-is.

**STOP.** Do NOT proceed to Section 1 (Architecture review), edit the plan file with a proposed scope reduction, or call ExitPlanMode until the user responds. Naming the 80% solution in chat prose and continuing without ending your turn is the failure mode this gate exists to prevent.

If the complexity check does not trigger, present your Step 0 findings and proceed directly to Section 1.

Always work through the full interactive review: one section at a time (Architecture → Code Quality → Tests → Performance) with at most 8 top issues per section.

**Critical: Once the user accepts or rejects a scope reduction recommendation, commit fully.** Do not re-argue for smaller scope during later review sections. Do not silently reduce scope or skip planned components.

> **STOP.** Before running the 4-section review, outside voice, required outputs, and review report (only after Step 0 scope is agreed), Read `~/.claude/skills/plan-eng/sections/review-sections.md` and execute it
> in full. Do not work from memory — that section is the source of truth for this step.

## Section self-check (before you finish)

Confirm you Read the review section the Section index named, and executed every review section (Architecture, Code Quality, Tests, Performance), the outside voice, and the required outputs in full. If you produced findings or the review report from memory without Reading `~/.claude/skills/plan-eng/sections/review-sections.md`, stop and Read it now.

## EXIT PLAN MODE GATE (BLOCKING)

Before calling ExitPlanMode, run this self-check. If any item fails, do the
missing work — do NOT call ExitPlanMode:

1. Read the plan file with the Read tool (after your most recent write to it).
2. Confirm the LAST `## ` heading in the file is `## PLAN REVIEW REPORT`.
   In-body prose that mentions "outside voice", "codex findings", or similar
   does NOT count — only the structured `## PLAN REVIEW REPORT` section
   satisfies this check.
3. Confirm the report contains: a Runs / Status / Findings table, a VERDICT
   line, and absorbs CROSS-MODEL / UNRESOLVED lines if applicable.

Failing this gate and calling ExitPlanMode anyway is a contract violation —
the user will see a plan whose review report is missing or stale, and will
(correctly) reject it. Self-deception failure mode to watch for: feeling
"done" after writing review prose into the plan body. The body prose is not
the report. The report is a separate, structured, table-bearing section that
must be the file's terminal heading.
