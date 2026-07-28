<!-- dual-review-protocol section file. Command-specific: /dual-code-review Phase 6 resolution flow. Loaded lazily — read this only when the user says "go" after Phase 5. Content is verbatim from the pre-split dual-code-review.md command body. -->

# /dual-code-review — Phase 6 resolution flow

Followed when the user says **go** after Phase 5. Steps 1–5 below.

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
