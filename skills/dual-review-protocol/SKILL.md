---
name: dual-review-protocol
description: Shared protocol for dual-agent reviews (Claude + GPT) — finding format, triage, debate, codex execution, result presentation. Used by /dual-code-review, /dual-plan-review, /ask-gpt, /gpt-review. Invoke via `Read` from a command and follow the relevant section.
---

# Dual Review Protocol

Shared knowledge for any command that runs Claude + GPT as parallel reviewers,
negotiates findings, and presents results to the user. Commands `Read` this
file and follow the relevant section. Templates live in `templates/`.

## How commands consume this

Commands `Read` this file at the start of their workflow and use it as a
reference while they orchestrate. Commands keep their workflow logic
(argument parsing, human gates, queue routing, file I/O); this skill keeps
the *content* (prompts, formats, rules).

## 0. Voice setup — always run first

`Read` `~/.claude/skills/outbound-prose-setup/SKILL.md` and follow it as the first action of the calling command, before any codex invocation, finding generation, triage, debate, presentation, or POST step. Applies to every invocation, including resumed runs and Phase 5/6 re-renders.

Internal prose (findings produced by codex, triage/debate verdicts) is NOT outbound — it stays in-line. Only review bodies and inline comments posted to GitHub go through `voice-writer`.

## 1. Codex Execution

### Invocation

Background, parallel, with session persisted for resume:

```
cat /tmp/{prefix}-{TIMESTAMP}-gpt-prompt.txt | codex exec -m gpt-5.5 -c model_reasoning_effort=medium --sandbox workspace-write --json --output-schema <schema-path> -C <working_directory> - 2>/dev/null
```

**`-c model_reasoning_effort=medium`** is the default for all Phase 2/3/4
calls. Override via tier (§12): `--high` bumps Phase 2 to `high`, `--lite`
drops it to `low`. Triage and debate phases stay on `medium` regardless of
tier — the extra reasoning cost isn't justified for structured cross-eval.

**`--output-schema` is required for Phase 2** initial reviews. Use:
- `~/.claude/skills/dual-review-protocol/schemas/findings-code.json` — code reviews
- `~/.claude/skills/dual-review-protocol/schemas/findings-plan.json` — plan reviews

The model's final `agent_message` will be a single JSON object matching the
schema (see §2). Triage/debate phases (resume calls) do NOT use a schema —
they emit prose verdicts/recommendations.

For plan reviews add `--search` **before `exec`** (top-level flag, not on `exec`):
`codex --search exec -m ...`. For code reviews omit `--search` unless the lens
requires verifying assumptions in the diff context.

Run via `Bash` with `run_in_background: true` and `timeout: 300000`.

### Model selection

All phases use `gpt-5.5`. The cost lever is `model_reasoning_effort`,
set per tier (§12):

| Phase | Reasoning effort | Why |
|-------|------------------|-----|
| Initial review (Phase 2) | `medium` (default) / `high` (--high) / `low` (--lite) | Tier-driven; see §12. |
| Triage (Phase 3) | `medium` | Structured cross-eval; deeper thinking adds little. |
| Debate (Phase 4) | `medium` | Best-idea framework eval; same rationale. |

`gpt-5.5` accepts verbosity values `low|medium|high` — no `-c
model_verbosity=medium` flag needed. Verbosity defaults from
`~/.codex/config.toml`.

> **Model note:** We run `gpt-5.5`. The `-codex` variants (`gpt-5.3-codex`,
> `gpt-5.2-codex`) were retired from ChatGPT-account access on 2026-06-02 and
> now require API-key billing. `gpt-5.5` is the entitled flagship on a ChatGPT
> Business sub. Do not revert to a `-codex` model without switching codex auth
> to an API key.

### Resume

Subsequent turns (triage, debate) reuse the same session. **`codex exec resume`
does NOT accept `-C`** — the cwd is the session's recorded cwd. To run from a
different directory, `cd` in the same shell command:

```
cat /tmp/{prefix}-{TIMESTAMP}-{phase}.txt | codex exec resume <SESSION_ID> --json - 2>/dev/null
```

`timeout: 120000` is enough for resumes.

### JSONL parsing

Use the dedicated parser:

```
~/.claude/scripts/parse-codex-output.sh <output_file>
```

Output format:
- `=== USAGE ===` — `{"input": N, "output": N, "cached": N}` (token totals)
- `=== RESPONSE ===` — concatenated `agent_message` text

To extract the `thread_id` (session ID) for resumes: read the first
`thread.started` event from the JSONL. The parser doesn't surface it; grep
for `"thread.started"` and pull `.thread_id`.

### Background retry + fallback model protocol

After every `codex exec` (initial or resume), parse the JSONL for `error`
events. Classify by error message:

| Error substring | Class | Action |
|---|---|---|
| `Selected model is at capacity` | **capacity** | Drop GPT lens for this run; continue Claude-only. No alt-model fallback. |
| `429` / `rate_limit_exceeded` | **rate** | Retry once with `run_in_background: true`. |
| `5xx` / network / timeout | **transient** | Retry once with `run_in_background: true`. |
| anything else | **unknown** | Surface raw error; continue Claude-only. |

**Fallback chain** (per phase):

| Phase | Primary | Fallback |
|-------|---------|----------|
| Phase 2 review | `gpt-5.5` | Claude-only |
| Phase 3 triage | `gpt-5.5` | Claude-only triage |
| Phase 4 debate | `gpt-5.5` | mark `[unresolved]` |

**Retry sequence on capacity:**

1. Print: "gpt-5.5 at capacity. Continuing Claude-only."
2. Skip GPT lens for the remainder of the run.

**Transient retry (rate / 5xx / timeout):**

1. Print: "GPT review timed out. Retrying in background..."
2. Start a SECOND `codex exec` with the SAME payload + same model, `run_in_background: true`, `timeout: 300000`
3. Continue immediately to Claude's review and subsequent phases as Claude-only
4. If the background retry completes BEFORE Phase 5 presentation: merge GPT findings (run context-aware triage on them first)
5. If retry completes DURING Phase 6 resolution: print "GPT results arrived late — [N] findings. Review after current findings?"
6. If retry also fails: silently continue Claude-only

**Error detection from JSONL:**

```
jq -r 'select(.type == "error") | .message' <output.jsonl>
jq -r 'select(.type == "turn.failed") | .error.message' <output.jsonl>
```

Both event types carry the OpenAI error JSON. Capacity error structure:
```json
{"type":"error","code":"...","message":"Selected model is at capacity. Please try a different model."}
```

### Pricing (verified 2026-05-19)

- gpt-5.5: $5.00/1M input, $0.50/1M cached input, $30.00/1M output (API rate; flat on ChatGPT-sub auth)

Reasoning tokens bill as output. Higher `model_reasoning_effort` → more
reasoning tokens → higher run cost (same per-token rate). Verify periodically
at https://developers.openai.com/codex/pricing.

## 2. Finding Format

GPT (Phase 2): output is a JSON object validated against
`schemas/findings-{code,plan}.json`. Field names are lowercase
(`id`, `severity`, `file`, `line`, `category`, `issue`, `evidence`, `fix`,
`confidence`; plan variant uses `section`/`title`/`problem`/`impact` instead
of `file`/`line`/`category`/`issue`/`evidence`).

Claude emits findings in markdown (no schema enforcement on local
generation):

```
FINDING:
- ID: {C|G}{N}
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- File: <path>
- Line: <line>
- Category: <lens-specific>
- Issue: <specific description>
- Evidence: <quoted code or doc reference>
- Fix: <concrete actionable change>
- Confidence: <XX>%
```

For plan reviews, replace `File`/`Line` with `Section: <task-file or section ref>` and add `- Title: <short title>`, `- Problem: <description>`, `- Impact: <what breaks>`.

**Minimum viable finding:** ID + Severity + (File or Section) + Issue/Problem.
Schema-enforced GPT output won't be malformed; for Claude markdown, extract
what's parseable from malformed findings and warn about discards.

Findings are ID'd `C1, C2, ...` for Claude and `G1, G2, ...` for GPT.

### Parsing GPT JSON output

`parse-codex-output.sh` returns the raw `agent_message` text in the
`=== RESPONSE ===` section. For schema-enforced calls, parse it as JSON:

```
schema_response=$(~/.claude/scripts/parse-codex-output.sh <output> | sed -n '/=== RESPONSE ===/,$p' | tail -n +2)
echo "$schema_response" | jq -r '.findings[] | "G\(.id): \(.severity) \(.file // .section): \(.issue // .problem)"'
```

## 3. Review Lenses

### Code-review lenses

**GPT (production resilience):** Error handling. Defensive coding. Failure modes.
Performance. Security. Race conditions. Resource management. DRY (>20 line
duplications). Architecture layers (logic in wrong layer). See
`templates/gpt-prompt-code.md` for the full reviewer prompt.

**Claude (correctness & architecture):** Logic errors. Defensive coding.
Edge cases. Type safety. Architecture layers. DRY violations. Design system
compliance (frontend). Simplicity. Dependency ordering. CI/CD safety.

**Structural maintainability:** orthogonal maintainability/simplification axis —
see `structural-lens.md`. Applied by `/dual-code-review` and `/plan:code-review`
(self-review surfaces); **NOT** `/review-pr`. Mechanical checks (Block A)
always-on for those commands; the ambition lens + approval bar (Blocks B/C)
gate behind `--thermo`. See §14.

**High-frequency Glade patterns** (mined from accepted PR feedback — bots catch
these on ~91% of diffs that ship them; hunt them explicitly, grep can't):

- **Comment / error-message vs code drift** — every comment, doc line, error
  string, and hard-coded `file:line` ref must still match what the code does.
- **Empty is not absent** — guards on missing/`null` that a present-but-empty or
  whitespace-only string slips past (`!v?.trim()`, not just `v == null`).
- **Side-effect before validation** — anything persisted/uploaded/emitted before
  its PII/`sha256`/auth guard runs.
- **Incomplete flag plumbing** — a new flag/param declared in one layer but not
  threaded end-to-end, so a selector requires a value nothing ever sets.
- **Inverted clamp / unit mismatch** — `Math.max` where `min` was meant (a cap
  that allows oversize); `.length` (UTF-16 units) used where bytes are intended.
- **Behavior change under a `refactor` label** — an empty-return that now throws,
  an auth path silently narrowed. See `~/.claude/rules/glade-backend.md`.

### Plan-review lenses

**GPT (implementation feasibility):** Unstated prerequisites. Dependency
ordering. Simplification. Integration risks. Missing error handling. Code
verification (use `--search`). See `templates/gpt-prompt-plan.md` for the
full reviewer prompt.

**Claude (adversarial):** Assumption stress test. Failure mode exploration.
Simplicity audit. Architecture check. Dependency ordering.

### Universal rules for both reviewers

- Technical only. Skip docs style, formatting, naming opinions.
- Specific or silent — every finding cites file+line (or section).
- Every criticism gets a concrete fix — not "consider X" but "in file.ts line 42, change Y to Z".
- Quality over quantity. Aim for ≤8 findings unless systemic issues.
- Use `--search` to verify assumptions before citing them.

After all findings, output:
```
WHAT WORKS:
[2-5 specific strengths the author got right]
```

## 4. Triage Protocol

Two-part prompt sent to GPT via resume. See `templates/triage.md` for the
full template with placeholders.

### Part 1: GPT self-evaluation

```
SELF-DISMISS: G[N]
REASON: [why context invalidates this finding]
```

If none invalidated: `SELF-DISMISS: NONE`.

### Part 2: GPT cross-evaluates Claude's findings

For each Claude finding, exactly one block:

```
FINDING: C[N]
VERDICT: AGREE | DISAGREE
PREVIEW: [N/A on AGREE; 2 sentences max on DISAGREE with code-evidence rebuttal]
```

After per-finding blocks, GPT notes overlaps:

```
OVERLAP: G2 <-> C3
```

### Self-dismiss handling

- Parse `SELF-DISMISS` entries.
- Claude evaluates each. If Claude agrees the finding is invalid given conversation context, move to "Dismissed (Context)" — skip autosolve and debate.
- If Claude disagrees, keep in normal triage flow.
- **Fast-exit:** if GPT self-dismisses ALL findings AND Claude agrees with all dismissals, skip debate entirely.

### Claude triage of remaining GPT findings

For each non-dismissed GPT finding, Claude assesses AGREE or DISAGREE based
on whether the issue is real and material. Read the cited file at the
cited lines using `Read` to verify. Claude-agreed GPT findings enter the
autosolve queue.

### Triage failure

If the resume call fails: present findings side-by-side without negotiation.
Claude triages all GPT findings alone (agree/disagree based on overlap and
merit + conversation context).

## 5. Deduplication

Match by: same file AND overlapping line range AND similar problem domain.
(For plans: same section AND overlapping problem domain.) Claude makes the
call and explains reasoning.

- Exact same issue → merge, tag `[both-found]`, auto-agree
- Partial overlap → keep separate with cross-references
- Overlapping findings with same fix → auto-agree

## 6. Debate Protocol

Only Phase 3 disagreements enter debate. **Cap: 5 findings** (priority by
severity: CRITICAL → HIGH → MEDIUM → LOW). Beyond cap: tag
`[unresolved-no-debate]`, present both positions in Phase 5.

Debate delegates to `/plan:best-idea` (Debate Mode). See
`templates/debate.md` for the wrapper prompt that calls best-idea with
debate context.

### Round 1

Claude runs `/plan:best-idea` internally with debate context (the disagreed
finding + its own original position). Output is a RECOMMENDATION block:

```
RECOMMENDATION:
- Action: fix | skip
- Pick: <solution name, or "skip" if Action is skip>
- Why: <2-3 sentences>
- Trade-offs: <what's given up>
```

`Action: fix` = code change warranted. `Action: skip` = finding is real but
not worth fixing now (micro-opt, low ROI, scope-out).

The wrapper prompt is sent to GPT via `codex exec resume`. GPT runs the
same evaluation through `/plan:best-idea` lenses (Eliminate / Reuse /
Standard / Minimal / Strategic) and emits its own RECOMMENDATION + a
final `VERDICT: AGREE | DISAGREE`.

**If GPT AGREE:** finding moves to autosolve, tag `[debate-agreed]`,
action verdict from Claude's `Action:` field.

### Round 2 (only if GPT DISAGREE)

Claude considers GPT's Round 1 recommendation, re-runs `/plan:best-idea`
debate-mode, emits a fresh RECOMMENDATION:

- Concede → autosolve using GPT's rec, tag `[debate-agreed]`, action verdict from GPT's `Action:`
- Hold → tag `[unresolved]`, both RECOMMENDATION blocks preserved for Phase 6 best-idea tiebreaker

### Resume failure during debate

Mark the finding `[unresolved]` with both original positions. Continue.

## 7. Routing

Each agreed finding gets an `agreed-fix` or `agreed-skip` action verdict:

- Triage-agreed and `[both-found]` default to `agreed-fix`.
- Debate-agreed inherits from the agreed RECOMMENDATION's `Action:` field.

Then split into three queues:

- **Safe-autosolve queue**: LOW/MEDIUM agreements (both `fix` and `skip`) → batch confirm in Phase 6 Step 1
- **Review-required queue**: HIGH/CRITICAL agreements (both `fix` and `skip`) → individual confirm in Phase 6 Step 2
- **Debate queue**: disagreements from triage → Phase 4 debate; survivors → Phase 6 Step 3 best-idea tiebreaker

Always parse the structured `Action:` tag. Never parse `Pick:` free-text to
determine fix vs skip.

## 8. Result Presentation

Standard layout for Phase 5 (consult command for queue contents and stats):

```
## {Dual Review Title}: <range or plan>

**Reviewers**: Claude (<lens>) + gpt-5.5 (<lens>)

### Agreement Stats
- Total findings: [N] (Claude: [N], GPT: [N], Both found: [N])
- Auto-resolve queue: [N] (LOW/MEDIUM agreements)
- Individual review: [N] (HIGH/CRITICAL agreements + unresolved disagreements)

### Auto-resolve queue (batch)
#### Will apply (agreed-fix)
1. **{Title}** [{tag}] `{ref}` — Found by: {Claude|GPT|Both}
   - Fix: ...

#### Will skip (agreed-skip)
2. **{Title}** [debate-agreed] `{ref}` — Found by: {Claude|GPT|Both}
   - Reason: ...

### Individual review

#### HIGH/CRITICAL agreements (Step 2)
**{ID}: {Title}** [{tag}] `{ref}` — Severity: {LEVEL}
- Both agents agree:
  - Pick: ...
  - Why: ...
  - Trade-offs: ...

#### Unresolved disagreements (Step 3 — best-idea tiebreaker)
**{ID}: {Title}** [{tag}] `{ref}` — Severity: {LEVEL}
- Issue: ...
- Evidence: `<snippet>`
- Claude's recommendation: Action / Pick / Why / Trade-offs
- GPT's recommendation: Action / Pick / Why / Trade-offs

### What Works
[Strengths from either or both agents]

**GPT Usage Report (cumulative)**

| Phase | Model | Effort | Input | Cached | Output | Notes |
|-------|-------|--------|-------|--------|--------|-------|
| 2 review | gpt-5.5 | {low|medium|high} | X | X (Y%) | X | {tier} |
| 3 triage | gpt-5.5 | medium | X | X (Y%) | X | resume |
| 4 debate | gpt-5.5 | medium | X | X (Y%) | X | resume |
| total | | | X | X (Y%) | X | |

**Estimated cost: ~$X.XX**
- Per-phase = (uncached × $1.75/1M) + (cached × $0.175/1M) + (output × $14/1M)
- All phases use gpt-5.5; reasoning tokens bill as output.

Always include `cached_pct` from `parse-codex-output.sh`. If `cached_pct < 50%`
on a resume phase, surface it as a warning — usually means the session
fragmented and is being re-billed at full price.
```

Say **go** to proceed with resolution.

### Leverage summary (final-confirmation block)

Rendered at the command's **final confirmation point** — immediately before
the irreversible/apply action (POST preview in `/review-pr`, apply-fixes
confirm in `/dual-code-review`, apply step in `/dual-plan-review`). It ranks
the surviving findings by leverage so the user can trim before committing.

One block per queued finding, separated by a `────` rule:

```
#: {N}
Comment: {file}:{line} — {short title}        (plan reviews: "Finding: {section} — {title}")
Importance: {High | Medium | Low | Low–Medium | Medium–High}
Confidence: {XX}%
Notes: {2–4 sentences}
```

Field semantics:

- **Importance ≠ severity.** Importance is the *leverage of acting on this
  finding*: blast radius × actionability. A factually-wrong comment with a
  trivial fix can outrank a vague HIGH. Ranges (`Low–Medium`) are allowed
  when the leverage depends on repo context.
- **Confidence** is belief the finding is *correct*, carried over from the
  finding's confidence score, adjusted by what was verified during
  triage/debate.
- **Notes** must state, concretely:
  1. What was **verified directly** (cite `file:line` of the proof) vs.
     inferred.
  2. The real-world **consequence** if unaddressed (or why it's mild).
  3. What the **residual doubt** is about — impact vs. mechanics (e.g.
     "the 10% doubt is impact, not mechanics").
  Both-reviewer agreement is worth noting ("both reviewers found it
  independently").

Close the block list with a ranking line and trim guidance:

```
Ranking by leverage: {N} > {N} > ... If trimming, drop {N} first — {one-clause reason}.
```

Rules:

- Rank by importance first, confidence as tiebreaker.
- Trim guidance names the *lowest-leverage* item and why it goes first —
  note when a low-importance item still carries a small functional payoff
  beyond the cosmetic fix (those outrank pure nits).
- Skipped/agreed-skip findings do not appear; this summarizes only what's
  about to be posted/applied.
- ≤2 queued findings: skip the table, print only the ranking line.

## 9. Phase 6 Best-Idea Tiebreaker

For each unresolved disagreement, run `/plan:best-idea` debate-mode with both
RECOMMENDATIONs as input. Output:

- **Concrete-fix rule (novel picks):** if best-idea picks a third option, it must produce a concrete fix description. If it cannot, downgrade — pick between Claude's and GPT's only.
- **Research-before-ask gate:** if evaluation hits a factual gap ("does this codebase already use library X?"), spawn an `Agent` (subagent_type=Explore) to answer before producing the pick. Only ask the user directly if the question is taste/preference, or research came back inconclusive.

Present:

```
**Finding {N}/{total}: {Title}** `{ref}` — Severity: {LEVEL}
- Issue: ...
- Evidence: `<snippet>`
- Claude's recommendation: Action / Pick / Why / Trade-offs
- GPT's recommendation: Action / Pick / Why / Trade-offs
- Best-idea pick: [Claude's | GPT's | <Third option>]
  - Action / Why / Trade-offs / Fix sketch (third option only)

Confirm best-idea pick (Y), prefer Claude's (claude), prefer GPT's (gpt), describe own approach, or skip.
```

**Best-idea failure** (model error, timeout, malformed output, can't read cited file): print `Best-idea unavailable for this finding — falling back to manual choice.` and present A/B/C/D for that finding only:

```
A: Claude's recommendation — ...
B: GPT's recommendation — ...
C: Your own approach — describe what you'd prefer
D: Skip — leave as-is
```

## 10. Error Handling Table

| Error | Handling |
|-------|----------|
| Codex initial review timeout/fail (transient) | Background retry (same payload, same model). Claude proceeds immediately. |
| Codex returns "at capacity" | Drop GPT lens for the run; continue Claude-only. No alt-model fallback. |
| Background retry fails | Silent — Claude-only already in progress. |
| GPT response unparseable (Phase 2) | Schema enforces JSON shape — if `jq` parse fails, retry once with same payload; if still failing, fall back to Claude-only. |
| GPT response unparseable (triage/debate) | Extract what's usable from prose; fall back to Claude-only for rest. |
| `invalid_json_schema` 400 from API | Schema file diverged from OpenAI strict-mode rules (`additionalProperties:false` + every key in `required` + null-union for optional). Fix schema and retry. |
| Resume fails (triage) | Claude triages all GPT findings alone (with conversation context). |
| Resume fails (debate round) | Mark finding `[unresolved]` with both positions; continue. |
| Session ID not found | Claude triages all GPT findings alone. |
| No findings from either agent | Clean APPROVE with summary. |
| All GPT findings dismissed by context | Skip debate, Claude-only with dismissed section. |
| More than 5 disagreements | Debate top 5 by severity; remaining marked `[unresolved-no-debate]`. |

## 11. Fairness Protocol

The best-idea framework enforces fairness structurally — both agents
evaluate alternatives on merit (pros/cons/effort/risk), not just defend
original positions. After all debates, report agreement stats. Flag if one
agent never conceded across all debates.

## 12. Tier Selection (Phase 1.6 cost policy)

All tiers run `gpt-5.5`. The cost lever is `model_reasoning_effort`.
Commands invoking this protocol classify each review as `lite`, `normal`, or
`high` before Phase 2 and emit `MODEL_FLAGS` accordingly. Higher effort →
more reasoning tokens (billed as output) → higher cost on the same diff.

### Resolution order

1. **`--lite` flag** from the calling command → `TIER=lite`.
2. **`--high` flag** from the calling command → `TIER=high`.
3. **Auto-classify** (no flag):
   - `lines_changed` = sum of `+`/`-` from `git diff --shortstat <range>`
   - `files_changed` = files count from same `--shortstat`
   - `paths` = `git diff --name-only <range>`
   - **Sensitive-path regex** (any match → `high`):
     ```
     migrations/|auth/|billing/|payments/|infrastructure/|\.github/workflows/|webhooks/|scheduledEvents/|src/utils/crypto/|court-api/
     ```
   - **UI-file regex** (any match → `high`):
     ```
     \.(tsx|jsx|scss)$
     ```
   - **Large diff** (any match → `high`): `lines_changed ≥ 1500` OR `files_changed ≥ 20`.
   - **Lite tier** iff: `lines_changed < 200` AND `files_changed ≤ 5` AND no sensitive/UI/large match.
   - Else → `TIER=normal`.

   Rationale: pricing is uniform across reasoning levels at the per-token
   rate, but high effort consumes meaningfully more reasoning-output tokens.
   Reserve `high` for diffs that need deeper exploration (sensitive paths,
   UI surface, or sheer size). Default `normal` (medium effort) handles the
   bulk of code review with strong fidelity. `lite` is the cost floor for
   trivial diffs.

### MODEL_FLAGS by tier

For Phase 2 code reviews, derive `MODEL_FLAGS` from `TIER` and use it in
place of the inline `-m gpt-5.5 -c model_reasoning_effort=medium`
example in §1. The rest of the `codex exec` invocation (sandbox, `--json`,
`--output-schema`, `-C <workdir>`) is unchanged.

| Tier | MODEL_FLAGS |
|---|---|
| `lite` | `-m gpt-5.5 -c model_reasoning_effort=low` |
| `normal` | `-m gpt-5.5 -c model_reasoning_effort=medium` |
| `high` | `-m gpt-5.5 -c model_reasoning_effort=high` |

Phase 3 triage and Phase 4 debate stay on
`gpt-5.5 -c model_reasoning_effort=medium` regardless of tier.

### Print convention

After classification, the calling command prints one line:

```
Tier: {lite|normal|high} (reason: <reason-string>)
```

Reason strings (first matching reason in this order wins):

| Source | Reason string |
|---|---|
| `--lite` flag | `--lite override` |
| `--high` flag | `--high override` |
| sensitive-path match | `sensitive-path:<matched-token>` (e.g., `sensitive-path:webhooks/`) |
| UI-file match | `ui-files:<count>` |
| lines ≥ 1500 | `large-diff:<N>-lines` |
| files ≥ 20 | `large-diff:<N>-files` |
| all-clear lite | `small-diff` |
| else | `default-normal` |

### Scope

§12 applies to commands that invoke code-review GPT phases:
`/dual-code-review` and `/review-pr`. Plan-review commands (`/dual-plan-review`,
`/gpt-review`, `/ask-gpt`) default to `normal` (medium effort) and accept
`--high` for adversarial deep dives.

## 13. Low-Finding Triage Policy (Phase 3 short-circuit)

Commands invoking this protocol skip the Phase 3 codex resume call when
total findings (Claude + GPT) ≤ 3. Claude performs the dedup and routing
in-context with no cost change to fidelity for that small a finding list.
Typical savings: ~$2.74 per run when triggered.

### Trigger

After Phase 2 emits Claude findings and GPT findings (parsed via
`~/.claude/scripts/parse-codex-output.sh` then `jq -r '.findings | length'`
on the `=== RESPONSE ===` JSON):

```
total = claude_count + gpt_count
```

- If `total ≤ 3` → **skip codex resume triage call**. Apply §13 short-circuit (below).
- Else → existing Phase 3 codex flow (§4 Triage Protocol) unchanged.

### Short-circuit procedure

1. Print: `Triage: Claude-only (low-finding policy, total=N).`
2. Apply §5 (Deduplication): same file + overlapping line range + similar
   problem domain → merge. Tag `[both-found]`, auto-`agreed-fix`.
3. For each remaining (un-merged) GPT finding, Claude assigns
   `AGREE | DISAGREE` based on cited code. **Read each cited file/line first**
   to verify the issue is real before deciding.
4. Treat GPT-agree findings as triage-agreed (autosolve queue entry,
   default `agreed-fix`).
5. Treat GPT-disagree findings as `[unresolved]` and route to the debate
   queue. Note: with ≤3 total findings, debate-queue entries will usually be
   0–1; debate may run anyway per §6, or §6's cap-of-5 will fast-exit naturally.
6. Route per §7 (Routing).

### Distinction from §10 "Triage failure" fallback

§10 fires on **codex error** and presents findings side-by-side without
dedup. §13 is a **policy-driven** short-circuit on small finding counts.
§13 performs full §5 dedup and §7 routing — same fidelity as full triage
minus GPT's self-dismiss cross-eval, which adds little signal at ≤3 findings.

### Scope

§13 applies to the same commands as §12: `/dual-code-review` and
`/review-pr`. Plan-review commands keep full Phase 3 codex triage.

## 14. Structural Maintainability & `--thermo`

Canonical content lives in `structural-lens.md` (sibling file). This section
defines *when* each block applies and the orchestration mechanics. Scope:
`/dual-code-review` and `/plan:code-review` only — **`/review-pr` does not
apply this axis** (no maintainability opinions on a teammate's incoming PR).

### Block application

| Block | Content | When |
|---|---|---|
| A | Mechanical checks (file-size budget, spaghetti-growth, refactor-didn't-reduce, thin-wrapper) | Always-on for self-review commands |
| B | Ambition / code-judo lens | `--thermo` only |
| C | Approval bar / presumptive blockers | `--thermo` only |
| D | GPT-prompt addendum (A always; A+B under `--thermo`) | `/dual-code-review` GPT side |

Claude `Read`s `structural-lens.md` and applies the in-scope blocks as extra
lenses alongside §3. Findings use the same FINDING schema (§2) and the same
universal rules (§3): cite file:line, concrete fix, ≤8 findings, high-conviction
over nit-flood.

### GPT side (`/dual-code-review` only)

After rendering `templates/gpt-prompt-code.md` and substituting placeholders,
**append** Block D to the prompt file (Block A always; Block A+B under
`--thermo`). This reaches the GPT reviewer without editing the shared template
(which `/review-pr` also renders). Mirrors the existing large-PR "FOCUS FILES"
append mechanic.

### `--thermo` → tier

`--thermo` is orthogonal to the §12 reasoning-effort tier but implies deep
exploration. Resolution: when `--thermo` is set and `--lite` is **not** present,
force `TIER=high` (reason string `thermo`). An explicit `--lite` wins — tier
stays `lite`, but the ambition lens still applies (the lens is independent of
reasoning effort). `--high` and `--thermo` together are redundant but harmless.

### Effect on routing / verdict

`/dual-code-review` has no GitHub verdict. Under `--thermo`, elevate
structural-regression findings to HIGH so they route to the individual-review
queue (§7) rather than silent autosolve-skip, and surface the Block C approval
bar in the Phase 5 presentation. `/plan:code-review` (which does emit a verdict)
may return `REQUEST CHANGES` on a structural regression under `--thermo` even
when behavior is correct.
