<!-- dual-review-protocol section file. Command-specific: /review-pr Phase 6 resolution + GitHub POST flow. Loaded lazily — read this only when the user says "go" after Phase 5, before any POST. Content is verbatim from the pre-split review-pr.md command body. -->

# /review-pr — Phase 6: Resolution & GitHub review POST

Followed when the user says **go** after Phase 5. Read this fully before Step 4 POST.

**Irreversibility contract.** `gh api .../pulls/N/reviews --method POST` (and any equivalent `gh pr review` invocation) runs **only** in Step 4, **only** after:
1. Step 4 has rendered the full preview block above the prompt (review action + body + every comment verbatim with `path`/`line`).
2. The user has replied with an explicit affirmative to the Step 4 POST gate (`post`, `yes`, `go`, `ok`, `ship it`, etc.). Silence is not consent. A "go" from Phase 5's batch-confirm gate does not carry over — the POST is its own separate gate.

Steps 1–3 build the in-memory queue only. They do not POST. **"go" from Phase 5 means "start Step 1 batch confirm" — it is never authorization to POST.** Do not invent shorthand in Phase 5 that bundles posting into "go" (e.g., "default = post APPROVE"). If you find yourself about to call `gh api` and Step 4 has not rendered, stop and re-enter Step 4.

When user says **go**:

### Step 0: Batch-draft comments via the voice-writer CLI

Before Step 1 renders excerpts, call the voice-writer CLI **once** via Bash
with all queued agreed-fix findings (auto-resolve + individual-review queues)
piped on stdin, per the `outbound-prose-setup` skill's invocation pattern.
Ask it to return a JSON array keyed by finding ID.

Cache returned drafts on each finding object. Steps 1, 2, and 3 read from this
cache for the "[draft comment excerpt]" / "**Draft comment:**" blocks. New drafts
after a Step 3 best-idea tiebreaker call the voice-writer CLI ad-hoc for just
that finding.

If the voice-writer CLI exits nonzero (backend unavailable): STOP and surface
to the user. Do not draft comments directly as a fallback.

### Pre-check: empty queues

If both auto-resolve and individual-review queues are empty AND there are
no findings at all:
```
Zero findings from both reviewers — clean APPROVE.
```
Build a one-line review body ("LGTM") with empty `comments` array, jump to
Step 4 (preview + post). Skip Steps 1–3.

### Step 1: Auto-resolve batch (LOW/MEDIUM agreements)

```
**Auto-resolve queue:** [N] findings (LOW/MEDIUM, both agents agree)

**Will comment (agreed-fix):**
  1. `file:line` — [Should Fix] [Title] → [draft comment excerpt] [{tag}]
  ...
**Will skip (agreed-skip):**
  3. `file:line` — [Title] (skip reason) [{tag}]
  ...

Reply Y to queue all comments, N to skip whole batch, or list numbers
(e.g. "2,4" or "1-3,5") to pull those into individual review.
```

**STOP. Wait for response.**

**Input grammar (strict):**
- `Y` / `y` / empty (Enter) → queue all agreed-fix comments, no-op the skips
- `N` / `n` → skip entire batch, no comments queued
- Comma- or space-separated tokens, each `<int>` or `<int>-<int>` → those
  findings move to the front of individual review (Step 3 best-idea format
  if user wants reconsideration). Rest of batch queues/no-ops as Y.
- Anything else → re-prompt **once** with `Couldn't parse "<input>". Use Y / N / number list (e.g. 2,4 or 1-3).`
  Second parse failure → abort with `Aborting resolution. Run /review-pr again to retry.` (no post; Phase 7 cleanup)

**Range expansion:** `1-3` = `1,2,3`. Out-of-range integers dropped with
`Ignoring N — only X findings in batch.`

For each agreed-fix queued: build a comment object (see Step 4 schema).

### Step 2: Individual review — HIGH/CRITICAL agreements (confirm-only)

For each finding in the review-required queue:

```
**Finding {N}/{total}: {Title}** `{file}:{line}` — Severity: [Must Fix] [{agreed-fix | agreed-skip}]

- Issue / Evidence

**Both agents agree:**
- Pick: ...
- Why: ...
- Trade-offs: ...

**Draft comment:**
> [Suggested PR comment text, severity-prefixed, written respectfully]

Confirm to queue (Y), edit comment, describe alternative, or skip.
```

**STOP after each.** For `agreed-skip`, "queue" = acknowledge skip, no comment.

If `[duplicate-existing]`: lead with "⚠️ Existing PR comment already covers
this — suggest skip."

### Step 3: Individual review — disagreements (best-idea tiebreaker)

For each unresolved finding, Claude runs `/plan:best-idea` Debate Mode
internally with both Phase 4 RECOMMENDATIONs as input. Apply SKILL.md §9
(concrete-fix rule for novel picks; research-before-ask gate via Explore
subagent).

Present per SKILL.md §9 layout. Default Y = best-idea pick. `claude` /
`gpt` to prefer originals. **STOP after each.**

**Best-idea failure** → fall back to A/B/C/D per SKILL.md §9.

### Step 4: Preview & post

Build the review payload. Comment object schema:

```json
// Single-line comment
{
  "path": "<file>",
  "line": <line in PR head version>,
  "side": "RIGHT",
  "body": "**[Severity]** Brief title\n\nExplanation.\n\n```suggestion\n<fix code>\n```"
}

// Multi-line comment (start_side is REQUIRED when start_line differs from line —
// omitting it causes a 422 "Unprocessable Entity" with a generic "internal error" message)
{
  "path": "<file>",
  "start_line": <first line>,
  "start_side": "RIGHT",
  "line": <last line>,
  "side": "RIGHT",
  "body": "..."
}
```

Use the `gh api .../contents/...?ref=<headRef>` line-number tip from the
glade plugin review-pr skill if line accuracy is in question — fetching the
PR's head version of the file ensures the line matches what GitHub expects.

**Pre-flight payload validation** (run before POST, no GitHub calls needed):
- Every comment with `start_line` must also have `start_side` AND `start_line < line` AND both `side` and `start_side` set to the same value.
- Every cited `line` (and `start_line`) must appear inside the PR diff hunks for that file (parse `/tmp/review-pr-{TIMESTAMP}-diff.txt`). Lines outside any hunk produce 422.
- Every `path` must appear in the changed-files list from Phase 1.
- Suggestion blocks (```suggestion ... ```) inside multi-line comments must contain exactly the replacement for `start_line..line`. A multi-line suggestion on a single-line anchor is rejected.
If validation fails, fix the payload locally and re-preview. Do not POST a payload that fails validation.

Determine verdict — **default `APPROVE`** (see the command's Severity-mapping
verdict rules; keep the two in sync). `REQUEST_CHANGES` only when an agreed-fix
CRITICAL/HIGH breakage needs another review pass before merge — i.e. the fix is
design-level, reworks the PR's approach, spans many call sites, or the correct
fix is genuinely uncertain. If every queued `[Must Fix]` has a concrete,
obviously-correct fix the author can apply unaided, `APPROVE` and flag the
must-fixes in the body. User can override to `COMMENT` during preview.

Compose body via the voice-writer CLI (`outbound-prose-setup` pattern). Pass the
verdict, the queued finding titles, and these tone constraints:
- Zero comments queued: `LGTM` or `Looks good`
- Only `[Consider]` items: opens with `LGTM` plus a short lead-in
- `[Should Fix]` present: opens with `Looks good` and names the fix(es)
- `[Must Fix]` present + verdict `APPROVE`: approve up front, then name the
  must-fixes as merge-blockers the author can fix without waiting on a re-review
- `[Must Fix]` present + verdict `REQUEST_CHANGES`: leads with what needs to
  change before merging, and that you'll take another look after
- Never condescending. Never "you should have". No padding, no "great work overall".
- One short paragraph; do not restate every comment.

Print the full preview verbatim:

```
Review action: <APPROVE | COMMENT | REQUEST_CHANGES>

Body:
> <body text>

Comment 1 on <path> line <N>:
> <full body>

Comment 2 on <path> line <N>:
> <full body>
...
```

After the preview, render the **leverage summary** per SKILL.md §8
(final-confirmation block): one `#/Comment/Importance/Confidence/Notes`
block per queued comment, closed by the `Ranking by leverage:` line with
trim guidance. Use it to decide whether to **edit** (drop low-leverage
comments) before posting.

Options:

```
- **post** — submit this review to GitHub
- **edit** — adjust something before posting
- **export** — print comments for manual copy-paste
- **done** — finish without posting
```

**STOP. Wait for selection.**

**If user replies with an explicit affirmative to the POST gate (`post`, `yes`, `go`, `ok`, `ship it`, etc.):**

**Pre-POST checklist (all three required, no exceptions — verify each before any `gh api` call):**
1. The full preview block above this prompt was rendered in *this* turn, including review action, body, and every comment verbatim with `path` + `line`. Recall: if you cannot point at the rendered preview in the immediately preceding assistant message, it did not happen — re-render and re-prompt.
2. The user reply was an explicit affirmative directed at this POST gate specifically. Silence does not count. A "go" or "ok" from an earlier phase (e.g., Phase 5 batch-confirm) does not carry over — the POST gate is separate. Any ambiguous or non-affirmative input routes to `edit` / `export` / `done` / re-prompt — not POST.
3. Pre-flight payload validation passed (hunk-line check, `start_side` on multi-line, `path` in changed-files list).

If any of the three is false, do **not** call `gh api`. Re-render Step 4 preview and re-prompt for `post`/`edit`/`export`/`done`.

Write the JSON payload to `/tmp/review-pr-{TIMESTAMP}-payload.json`:

```json
{
  "event": "<verdict>",
  "body": "<body text>",
  "comments": [ {...}, {...} ]
}
```

Then:

```
gh api repos/{owner}/{repo}/pulls/{N}/reviews --method POST --input /tmp/review-pr-{TIMESTAMP}-payload.json
```

This creates a single atomic review — one email to the author, not N.

**On POST failure (422 / 4xx / 5xx) — HARD RULES:**
- **Never post test data, placeholder bodies, or "test1"/"test"/"foo" content to the live PR** to diagnose. Reviews and inline comments on a real PR are visible to the author and notify them. Submitted reviews CANNOT be deleted via API (only PENDING reviews can — and `gh api .../reviews POST` always submits, never creates pending).
- **Never POST to `pulls/{N}/reviews` or `pulls/{N}/comments` on the live PR for diagnostic purposes.** This includes single-comment "is the line number valid" probes. They create timeline entries that can't be removed.
- Diagnose locally first:
  1. Re-validate the payload against the pre-flight checks above.
  2. Re-read the diff hunks at the cited file:line ranges.
  3. Inspect the JSON for missing fields (most common: `start_side` on multi-line comments).
  4. If suggestion blocks span lines outside the comment anchor range, narrow them.
- If still stuck after local diagnosis: surface the error to the user with the specific 422 message, ask whether to **fall back to `export`** (print comments for manual copy-paste) or **drop the offending comment** and retry the rest.
- A second 422 with no clear cause → fall back to `export`. Do not retry blindly.

If a test-post leak does occur (regression): inline review comments can be deleted via `DELETE /repos/{owner}/{repo}/pulls/comments/{comment_id}`. Submitted top-level reviews can only be edited (`PUT /repos/{owner}/{repo}/pulls/{N}/reviews/{review_id}` with `body`) or, if state is APPROVED/REQUEST_CHANGES, dismissed (`PUT .../reviews/{review_id}/dismissals` with `event=DISMISS`). COMMENTED reviews cannot be dismissed or deleted.

**If `export`:** print each comment in copy-paste format with `file:line`
headers and the full body. No POST.

**If `edit`:** re-prompt for what to change (body text, specific comment
text, severity, drop a comment). Loop back to preview.

**If `done`:** skip POST. Phase 7 cleanup.

### Step 5: Review history log

After post / export / done, append a JSONL entry to
`~/dev/kg/initiatives/pr-reviews/reviews.jsonl` (counts only — no comment text
or PII):

```bash
mkdir -p ~/dev/kg/initiatives/pr-reviews
```

```json
{
  "ts": "<ISO timestamp>",
  "pr": <number>,
  "repo": "<owner/repo>",
  "author": "<username>",
  "action": "APPROVE|REQUEST_CHANGES|COMMENT|EXPORT|DONE",
  "findings": {"must_fix": 0, "should_fix": 2, "consider": 1, "pass": 1},
  "posted": 2,
  "skipped": 1,
  "edited": 0,
  "gpt_dismissed": 1,
  "duplicates_existing": 0,
  "claude_only": false
}
```

