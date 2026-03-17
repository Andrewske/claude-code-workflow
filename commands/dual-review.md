---
description: Dual-agent plan review — Claude and GPT independently review, then negotiate findings
argument-hint: [<path>] (optional - auto-detects from workflow state)
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

<!-- Pricing config (verify periodically at https://platform.openai.com/docs/pricing):
  gpt-5.2-codex: $1.75/1M input, $14.00/1M output
-->

Two independent reviewers — Claude (adversarial lens) and GPT (implementation feasibility lens) — review a plan separately, then negotiate findings through a structured triage and debate protocol. Agreed fixes are autosolved; unresolved disagreements are escalated for human review.

---

## Phase 1: Plan Selection

If an explicit path argument was provided, use it directly.

Otherwise, follow the **Plan Selection Pattern** (see `commands/plan/README.md`) with status filter: `ready`.

**Important:** If `.claude/workflow-state.json` is missing, use the fallback directory scan — scan `.claude/tasks/*/README.md` to find plans. Do NOT search `docs/` or other directories.

After selection, announce: "Reviewing: {plan-path}"

### Reviewability Check

Before proceeding, scan the plan for minimum structure:
- Does it have an objective, approach, and task breakdown?
- Are core requirements stated?

If the plan lacks minimum structure, output:
```
**Insufficient detail for review.**
Missing: [list what's needed]
Recommendation: Return to planning phase to define [X, Y, Z]
```

Record a `TIMESTAMP` value for this session (e.g., Unix epoch in seconds via `date +%s`). All temp files for this session use the prefix `/tmp/dual-review-{TIMESTAMP}-`.

---

## Phase 2: Parallel Independent Reviews

Tell the user: "Both agents are reviewing the plan independently."

**Parallelism strategy:**
1. Start GPT's review with `run_in_background: true` FIRST (see GPT review instructions below)
2. While GPT works, Claude performs its own review (see Claude review instructions below)
3. After Claude finishes, wait for GPT's background result

### GPT Review (Implementation Feasibility Lens)

**Build the context prefix:** Check which of these files exist in the working directory: `AGENTS.md`, `CLAUDE.md`, `README.md`. If any exist, include this in the prompt prefix:

```
This project has the following context files in the repo root: [list files that exist]. Read them first to understand project conventions before reviewing.
```

**Read plan content:** Read the plan's `README.md` and all task files from the plan directory (`.claude/tasks/{plan}/`).

**Size guard:** Estimate token count before including plan content. Each character ≈ 0.25 tokens; each word ≈ 1.3 tokens. If the total plan content exceeds ~50K tokens (~200K characters), summarize each task file (objective + approach + key constraints) instead of including verbatim.

**Write the full GPT prompt to `/tmp/dual-review-{TIMESTAMP}-gpt-prompt.txt`:**

```
[context prefix if applicable]

You are reviewing an engineering plan for implementation feasibility. Your job: find issues the planner may have missed when imagining the implementation.

PLAN DIRECTORY: [plan-path]

PLAN CONTENT:
[full plan README and all task files, or summarized versions if large]

REVIEW FOCUS (implementation feasibility lens):
- Implementation feasibility: Will each step actually work as written? Are there unstated prerequisites?
- Dependency ordering: Are task dependencies correct and complete? What can be parallelized vs must be sequential?
- Simplification opportunities: Is there a simpler approach that handles 90% of the cases?
- Integration risks: What are the failure points where this plan touches existing systems?
- Missing error handling: What error paths are unaddressed?
- Code verification: For each task that references existing code (e.g., "The plan references X"), read the relevant source files and verify the assumption against the actual code.

INSTRUCTIONS:
- Technical only. Skip documentation style, formatting, stakeholder concerns.
- Specific or silent: every finding must reference the specific task file or section.
- Every criticism needs a concrete fix.
- Quality over quantity: solid plans exist. Don't invent problems.

For each issue found, use EXACTLY this format:

FINDING:
- ID: G[N]
- Title: [short title]
- Section: [task file or section reference]
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- Problem: [specific description]
- Impact: [what breaks or is at risk]
- Fix: [concrete recommendation]
- Confidence: [XX%]

After all findings, output a "What Works" section listing strengths of the plan.
```

**Run codex** (without `--ephemeral` so the session persists for resume) using `run_in_background: true` and a 300000ms timeout:

```
cat /tmp/dual-review-{TIMESTAMP}-gpt-prompt.txt | codex exec -m gpt-5.2-codex --full-auto --json -C <working_directory> - 2>/dev/null
```

Note the `thread_id` from the `thread.started` JSONL event — this is the session ID needed for Phase 3 (triage resume). Extract it after the background task completes.

**Parse JSONL output:**
- **Session ID**: extract `thread_id` from the `thread.started` event
- **Response text**: concatenate `text` from all `item.completed` events where `type` is `agent_message`
- **Usage**: sum the `usage` objects from all `turn.completed` events (accumulate `input_tokens`, `cached_input_tokens`, `output_tokens`)

**If codex fails:** Surface the error, warn the user, and offer to continue Claude-only with: "GPT review failed — continuing with Claude-only review. Use `/plan:review` for a standard review."

### Claude Review (Adversarial Lens)

You are a battle-scarred principal engineer who has watched "obvious" plans explode in production. Assume something is wrong until proven otherwise.

**Analysis Process:**

**Extraction:** From the plan, extract: Objective, Approach, Assumptions (stated and unstated), Dependencies, Scope (in/out boundaries).

**Adversarial Analysis** (minimum 3 reasoning passes per dimension):

- **Assumption Stress Test**: List every assumption (explicit + implicit). For each: "What if this is false? What breaks?" Which are validated vs hoped?
- **Failure Mode Exploration**: What inputs cause undefined behavior? What happens when each dependency fails? How does this degrade under 10x load?
- **Simplicity Audit**: Is there a 50% simpler approach that handles 90% of cases? What existing patterns/libraries are being ignored?
- **Architecture Check**: Does this create coupling that will hurt? Will this be debuggable at 3am?
- **Dependency Ordering**: Are task dependencies correct? What can be parallelized?

**Strengthen Findings:** For each finding, challenge: "Is this actually a problem, or am I pattern-matching?" Upgrade weak findings to specific, actionable issues. Discard findings that don't survive scrutiny.

**Classification:** Assign severity per Severity Levels (see `commands/plan/README.md`).

**Output Claude's findings in structured format:**

```
FINDING:
- ID: C[N]
- Title: [short title]
- Section: [task file or section reference]
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- Problem: [specific description]
- Impact: [what breaks]
- Fix: [recommendation]
- Confidence: [XX%]
```

---

## Phase 3: Triage & Deduplication

Print: "Triaging findings from both reviews..."

### Parse GPT's Findings

Parse GPT's review output from Phase 2. Extract findings in the structured format. **Minimum viable finding:** a finding is usable if it has at least an ID, severity, and problem description. Extract what's parseable from malformed findings; warn about any that are discarded.

### Bulk Triage via Resume

**Write the triage prompt to `/tmp/dual-review-{TIMESTAMP}-triage.txt`:**

```
You previously reviewed a plan and produced findings. The other reviewer (Claude) independently produced these findings:

[Claude's findings in structured format — all findings C1, C2, ... listed verbatim]

For each of Claude's findings, respond with:
FINDING: [Claude's finding ID]
VERDICT: AGREE | DISAGREE
PREVIEW: [If DISAGREE: 2-sentence summary of your counter-argument. If AGREE: N/A]

Also note any of YOUR own findings that overlap with Claude's (same issue, different angle):
OVERLAP: [Your finding ID] ↔ [Claude's finding ID]

Respond in plain text using the exact format above. No extra prose.
```

**Send via resume** (using the session ID from Phase 2):

```
cat /tmp/dual-review-{TIMESTAMP}-triage.txt | codex exec resume <SESSION_ID> --json -C <working_directory> - 2>/dev/null
```

Use `timeout: 120000` for this call. Accumulate usage tokens.

**If resume fails:** Present findings side-by-side without negotiation. Claude triages all GPT findings alone (agree/disagree based on overlap and merit).

**Claude independently triages GPT's findings:** For each GPT finding, Claude assesses AGREE or DISAGREE based on whether the issue is real and material. Claude-agreed GPT findings enter the autosolve queue.

### Deduplication

Match findings by: same section reference AND overlapping problem domain. Claude makes the matching call and explains reasoning. Rules:
- Exact same issue → merge into one finding, tag as `[both-found]`, auto-agree
- Partial overlap → keep separate with cross-references
- Overlapping findings with same fix → auto-agree

### Routing

- **Autosolve queue**: findings where both agents agree (triage-agreed or both-found)
- **Debate queue**: findings where agents disagree (from triage DISAGREE verdicts), prioritized by severity

---

## Phase 4: Best-Idea Debate Protocol

Only disagreements from Phase 3 enter debate. **Cap: 5 findings max** (prioritize by severity — CRITICAL first, then HIGH, MEDIUM, LOW). Remaining disagreements beyond the cap are marked `[unresolved-no-debate]` and presented with both positions in Phase 5.

For each debated finding, print status before starting: "Debating finding {ID} ({N}/{total})..."

After each debate, print: "Finding {ID}: {AGREED|UNRESOLVED}"

### Debate Process (Max 2 Rounds per Finding)

Each agent evaluates the disagreed finding using the best-idea framework from `commands/plan/best-idea.md`.

**Round 1:** Claude runs the best-idea evaluation first, then sends its recommendation to GPT.

**Claude's evaluation (internal):**
1. Frame the problem — restate constraints from the plan in 1-3 bullets
2. Generate alternatives through 5 lenses: Eliminate, Reuse, Standard, Minimal, Strategic
3. Compare top 3 solutions (approach, pros, cons, effort S/M/L, risk Low/Med/High)
4. Pick one

**Write debate prompt to `/tmp/dual-review-{TIMESTAMP}-debate-{N}.txt`:**

```
We disagree on this finding from the plan review:

FINDING: [full finding text — ID, section, problem, impact, severity]
YOUR POSITION: [GPT's original finding text or triage preview]
MY POSITION: [Claude's original finding text or triage assessment]

I evaluated this using a structured decision framework and my recommendation is:

RECOMMENDATION:
- Pick: [Solution name]
- Why: [2-3 sentences]
- Trade-offs: [What's given up]

Now evaluate this finding yourself using the same framework. Consider my recommendation but form your own view.

EVALUATION FRAMEWORK:
1. Frame the problem — restate constraints in 1-3 bullets
2. Generate alternatives through these lenses:
   - Eliminate: Can we avoid/defer/simplify the problem itself?
   - Reuse: What does this codebase already do in similar situations?
   - Standard: Is there a well-maintained library that solves this?
   - Minimal: What's the boring, safe, smallest-change solution?
   - Strategic: Is there a higher-effort option with 3x+ long-term payoff?
3. Compare top 3 solutions (approach, pros, cons, effort S/M/L, risk Low/Med/High)
4. Pick one and respond with:

RECOMMENDATION:
- Pick: [Your chosen solution name]
- Why: [2-3 sentences]
- Trade-offs: [What's given up]
VERDICT: AGREE | DISAGREE
```

Send via resume with `timeout: 120000`. Accumulate usage tokens.

**If GPT AGREEs in Round 1:** Finding moves to autosolve with tag `[debate-agreed]`.

**Round 2 (only if GPT DISAGREEs):** Claude considers GPT's Round 1 recommendation and re-evaluates using the best-idea framework. Claude makes a final call:
- If Claude concedes: finding moves to autosolve using GPT's recommendation, tagged `[debate-agreed]`
- If Claude still disagrees: finding is marked `[unresolved]` — both recommendations are preserved for Phase 5

**If a resume call fails during debate:** Mark the finding as `[unresolved]` with both original positions, continue to next finding.

### Debate Transcript

After all debate rounds complete, save the full transcript to `.claude/tasks/{plan}/dual-review-transcript.md`:

```markdown
# Dual Review Transcript — {plan-name}

Generated: {date}

## Agreement Stats
- Triage agreed: {N} findings
- Debate resolved: {N} findings
- Unresolved: {N} findings
- Concession flag: [Claude never conceded | GPT never conceded | Both conceded]

## Debated Findings

### Finding {ID}: {Title}

**Claude's position:** ...
**GPT's position:** ...

**Round 1:**
- Claude recommendation: ...
- GPT verdict: AGREE | DISAGREE
- GPT recommendation (if DISAGREE): ...

**Round 2 (if applicable):**
- Claude final call: CONCEDE | HOLD
- Outcome: AGREED | UNRESOLVED

[Repeat for each debated finding]
```

### Fairness Protocol

The best-idea framework enforces fairness structurally — both agents evaluate alternatives on merit (pros/cons/effort/risk), not just defend their original position. After all debates, report agreement stats. Flag if one agent never conceded across all debates.

---

## Phase 5: Present Results

```
## Dual Plan Review: [Plan Name]

**Reviewers**: Claude (adversarial) + GPT-5.2-Codex (implementation feasibility)

### Agreement Stats
- Total findings: [N] (Claude: [N], GPT: [N], Both found: [N])
- Triage agreed: [N] findings autosolved
- Debated: [N] findings ([N] resolved, [N] unresolved)
- Needs Review: [N] findings

---

### Needs Review (Unresolved Disagreements)

[For each unresolved finding:]

**{ID}: {Title}** [{both-found | unresolved | unresolved-no-debate}] [Section: X] — Severity: {LEVEL}

- **Problem**: ...
- **Impact**: ...

**Claude's recommendation:**
- Pick: [solution]
- Why: [reasoning]
- Trade-offs: [what's given up]

**GPT's recommendation:**
- Pick: [solution]
- Why: [reasoning]
- Trade-offs: [what's given up]

---

### Autosolved Findings

#### CRITICAL
1. **{Title}** [{triage-agreed | debate-agreed | both-found}] [Section: X] — Found by: {Claude | GPT | Both}
   - Fix: ...

#### HIGH
[...]

#### MEDIUM
[...]

#### LOW
[...]

---

### What Works
[Strengths noted by either or both agents]

---

**GPT-5.2-Codex Usage Report (cumulative)**
- Input tokens: X,XXX (cached: X,XXX)
- Output tokens: X,XXX
- Estimated cost: $X.XX
  - Input: X,XXX × $1.75/1M = $X.XXXX
  - Output: X,XXX × $14.00/1M = $X.XXXX
```

Say **go** to proceed with resolution.

---

## Phase 6: One-at-a-Time Resolution

When user says "go", follow the Resolution Flow from `commands/plan/README.md`:

### Step 1: Needs-Review Items First (One at a Time)

For each unresolved finding, present:

```
**Finding {N}/{total}: {Title}** [Section: X] — Severity: {LEVEL}

- **Problem**: ...
- **Impact**: ...

- **A: Claude's recommendation** — [solution name]
  - Why: [reasoning]
  - Trade-offs: [what's given up]

- **B: GPT's recommendation** — [solution name]
  - Why: [reasoning]
  - Trade-offs: [what's given up]

- **C: Your own approach** — describe what you'd prefer
- **D: Skip** — leave as-is
```

**STOP after each. Wait for user response.** Do not present the next finding until the user responds.

### Step 2: Autosolve Batch

After all needs-review items are resolved, present the autosolve batch:

```
**Autosolved Findings:**
1. [Title] → [Fix] ({confidence}%) [Section: X] — {triage-agreed | debate-agreed | both-found}
2. [...]

Confirm to apply all, or say "review" to discuss individually.
```

### Step 3: Apply

For each approved finding:
1. Propose the specific text edit
2. Apply via Edit tool
3. Verify coherence

### After Complete

**STOP HERE. Do NOT start implementation or make further changes.** Tell the user:

```
STOP. Run /clear then /plan:start-implementation
```

---

## Cleanup

After resolution is complete (or on any error exit), remove all temp files for this session:

```
rm -f /tmp/dual-review-{TIMESTAMP}-gpt-prompt.txt
rm -f /tmp/dual-review-{TIMESTAMP}-triage.txt
rm -f /tmp/dual-review-{TIMESTAMP}-debate-*.txt
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| Codex initial review fails | Surface error; offer to continue with Claude-only review; suggest `/plan:review` as fallback |
| Codex timeout | Offer to continue Claude-only with warning |
| GPT response unparseable | Extract what's usable; fall back to Claude-only with warning |
| Resume fails (triage) | Present findings side-by-side without triage; Claude triages all findings alone |
| Resume fails (debate round) | Mark finding as `[unresolved]` with both positions; continue to next finding |
| Session ID not found | Present findings side-by-side without negotiation |
| No findings from either agent | Clean APPROVE with summary |
| More than 5 disagreements | Debate top 5 by severity; remaining marked `[unresolved-no-debate]` with both positions |
