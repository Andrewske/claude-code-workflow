<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

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

**Reviewers**: Claude (<lens>) + gpt-5.4 (<lens>)

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
| 2 review | gpt-5.4 | {low|medium|medium} | X | X (Y%) | X | {tier} |
| 3 triage | gpt-5.4 | medium | X | X (Y%) | X | resume |
| 4 debate | gpt-5.4 | medium | X | X (Y%) | X | resume |
| total | | | X | X (Y%) | X | |

**Estimated cost: ~$X.XX**
- Per-phase = (uncached × $1.75/1M) + (cached × $0.175/1M) + (output × $14/1M)
- All phases use gpt-5.4; reasoning tokens bill as output.

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

## 11. Fairness Protocol

The best-idea framework enforces fairness structurally — both agents
evaluate alternatives on merit (pros/cons/effort/risk), not just defend
original positions. After all debates, report agreement stats. Flag if one
agent never conceded across all debates.
