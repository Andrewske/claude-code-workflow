---
description: Run /plan:best-idea with both Claude and GPT in parallel, compare picks, debate ties, log run for retrospective lift analysis
argument-hint: <problem statement, or proposed plan to evaluate>
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Dual Best Idea

Two independent reviewers (Claude + GPT via codex CLI) run the `/plan:best-idea`
framework on the same problem in parallel. If they pick the same solution → fast
path with "both agreed" signal. If they differ → invoke best-idea Debate Mode
to break the tie. Every run is logged for retrospective comparison vs solo runs.

For codex execution patterns, see `~/.claude/commands/ask-gpt.md`. For the
best-idea framework + Output Format, both reviewers read
`~/.claude/commands/plan/best-idea.md` directly — no slicing, no template files.

`best-idea.md` is installed from `~/dev/tools/claude-code-workflow` by
`scripts/install-commands.sh`, which blind-copies over the destination. The
pick sentinels and Debate Mode this command depends on live in that repo's
copy — **edit the spec there, then reinstall.** A local-only edit to
`~/.claude/commands/plan/best-idea.md` is silently lost on the next install.

---

## Phase 1: Capture problem

If `$ARGUMENTS` is non-empty, treat it as the problem statement.

If empty, look back in the conversation for a recent best-idea-shaped exchange
(a question of the form "should I X or Y?", a proposed plan asking for review,
etc.) and use it. If unclear, ask the user to restate the problem and any
proposed plan in one message before continuing.

Capture for telemetry:
- `PROBLEM_SUMMARY` — first ~200 chars of the problem statement (single line,
  whitespace-collapsed).
- `WORKDIR` — current working directory (used for codex `-C` flag and the
  ask-gpt context-prefix logic). If CWD is not a git repo, `--skip-git-repo-check`
  is required.

Set `TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)`. Use `/tmp/dual-best-idea-${TIMESTAMP}-`
prefix for all temp files.

---

## Phase 2: Parallel run

Tell user: "Running Claude and GPT independently on this problem."

### Start GPT in background first

Build the prompt:

```
{{CONTEXT_PREFIX}}

Read this file: ~/.claude/commands/plan/best-idea.md

Apply the Decision Philosophy, Evaluation Process, and Output Format sections
to the problem below. Output exactly the format spec'd there
(Problem / Proposed Plan / Top 3 Solutions / Recommendation), ending with the
<<<FINAL_PICK>>> and <<<FINAL_PICK_REASON>>> sentinel tail lines defined in
its "Pick sentinels" section.

This is an initial evaluation pass — do NOT use Debate Mode format.

PROBLEM:
{{PROBLEM_STATEMENT}}
```

`{{CONTEXT_PREFIX}}`: if `AGENTS.md` / `CLAUDE.md` / `README.md` exist in
`$WORKDIR`, prepend the standard "read these for project context" preamble
(same logic as `~/.claude/commands/ask-gpt.md` step 3). Otherwise omit.

`Write` the rendered prompt to `/tmp/dual-best-idea-${TIMESTAMP}-gpt-prompt.txt`.

Run codex in the background with `run_in_background: true`, `timeout: 300000`:

```bash
TMPERR=$(mktemp /tmp/dual-best-idea-${TIMESTAMP}-err-XXXXXX)
GPT_OUT=/tmp/dual-best-idea-${TIMESTAMP}-gpt-out.txt
cat /tmp/dual-best-idea-${TIMESTAMP}-gpt-prompt.txt | codex exec \
  -m gpt-5.4 -c model_reasoning_effort=medium --skip-git-repo-check --sandbox read-only --json --ephemeral \
  -C "$WORKDIR" - 2>"$TMPERR" > "$GPT_OUT"
echo "EXIT=$?"
```

**Why these flags:**
- No `--search` — disable web access for cleaner Claude-vs-GPT comparison.
- `--sandbox read-only` — eval task, no writes needed.
- `--skip-git-repo-check` — required when CWD isn't a git repo (e.g. `~`).
- Stderr to `$TMPERR` — surface diagnostics on failure, don't `2>/dev/null`.

### Claude side runs in foreground

While GPT runs in the background, Claude (the host of this command) reads
`~/.claude/commands/plan/best-idea.md` and follows its instructions on the
captured problem statement. NOT a sub-process spawn — same agent, same context,
just inlined skill instructions.

The Claude output ends with `<<<FINAL_PICK>>>` and `<<<FINAL_PICK_REASON>>>`
sentinel lines per best-idea.md's "Pick sentinels" section.

`Write` Claude's output to `/tmp/dual-best-idea-${TIMESTAMP}-claude-out.txt`
for parity with GPT's output (so both extract the same way in Phase 3).

### Wait for GPT and parse

After Claude side finishes, fetch the GPT background result.

If exit code != 0:
- Read `$TMPERR`. Surface to user verbatim.
- If error indicates capacity / quota, drop GPT side: set `GPT_PICK=null`,
  `AGREEMENT=gpt-unavailable`, skip Phase 3 comparison, jump to Phase 4a
  (use Claude's pick as final), then Phase 5.

If exit code == 0, parse the JSONL output:
```bash
~/.claude/scripts/parse-codex-output.sh "$GPT_OUT" > /tmp/dual-best-idea-${TIMESTAMP}-gpt-parsed.txt
```

Extract from the parsed `=== RESPONSE ===` section the GPT prose output (which
contains the `<<<FINAL_PICK>>>` tail).

Capture token counts from the `=== USAGE ===` section (parser-dependent;
silently `null` if fields are absent).

---

## Phase 3: Compare picks

Extract the resolved pick from each output:

```bash
CLAUDE_PICK=$(grep '^<<<FINAL_PICK>>>' /tmp/dual-best-idea-${TIMESTAMP}-claude-out.txt | tail -n 1 | sed 's/^<<<FINAL_PICK>>> //')
CLAUDE_REASON=$(grep '^<<<FINAL_PICK_REASON>>>' /tmp/dual-best-idea-${TIMESTAMP}-claude-out.txt | tail -n 1 | sed 's/^<<<FINAL_PICK_REASON>>> //')

GPT_PICK=$(grep '^<<<FINAL_PICK>>>' /tmp/dual-best-idea-${TIMESTAMP}-gpt-parsed.txt | tail -n 1 | sed 's/^<<<FINAL_PICK>>> //')
GPT_REASON=$(grep '^<<<FINAL_PICK_REASON>>>' /tmp/dual-best-idea-${TIMESTAMP}-gpt-parsed.txt | tail -n 1 | sed 's/^<<<FINAL_PICK_REASON>>> //')
```

**Extraction failure** — if either `CLAUDE_PICK` or `GPT_PICK` is empty:
- Set `AGREEMENT=extraction-failed`.
- Surface to user: "One reviewer's output did not include a `<<<FINAL_PICK>>>`
  sentinel line. Falling back to Claude-only result. Re-run if needed."
- Use Claude's pick as `final_pick` if available; otherwise abort cleanly.
- Skip to Phase 5 (telemetry write).
- Do NOT silently bury — this is a real failure that signals best-idea.md drift
  (e.g. the sentinel spec went missing) or model misformatting.

**Note on this tripwire's reach:** it only catches a *missing* sentinel. It
does not catch the spec itself being wrong or absent, because this command
names the sentinel format inline in the Phase 2 prompt — so both sides emit
sentinels even when `best-idea.md` has no "Pick sentinels" section at all.
That is exactly how this went unnoticed for 46 debated runs. If you move or
rewrite the spec, verify Phase 4b by hand; Phase 3 will not fail for you.

**Normalize for comparison** (`trim` and `lowercase` only — do NOT strip
punctuation; that creates false agreement on `SQLite + files` vs `SQLite/files`):

```bash
NORM_CLAUDE=$(printf '%s' "$CLAUDE_PICK" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
NORM_GPT=$(printf '%s' "$GPT_PICK" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
```

If `NORM_CLAUDE == NORM_GPT` → Phase 4a (fast path, agreement=same).
Otherwise → Phase 4b (debate).

---

## Phase 4a: Agreement fast path

Present to user:

```
## Both Claude and GPT picked: {CLAUDE_PICK}

**Why** (Claude): {CLAUDE_REASON}
**Why** (GPT): {GPT_REASON}

[full Claude output: Top 3 Solutions + Recommendation block]

### GPT's alternative perspectives
[GPT's Top 3 entries that differ from Claude's — one-bullet summary each]
```

Set `AGREEMENT=same`, `DEBATE_INVOKED=false`, `FINAL_PICK={name: CLAUDE_PICK,
why: CLAUDE_REASON}`. Proceed to Phase 5.

---

## Phase 4b: Debate

Build a `DEBATE_CONTEXT` block:

```
DEBATE_CONTEXT:
FINDING: {one-sentence problem restatement}

CLAUDE_RECOMMENDATION:
- Action: fix
- Pick: {CLAUDE_PICK}
- Why: {one-line from Claude's "Why this wins"}
- Trade-offs: {one-line from Claude's "Trade-offs accepted"}

GPT_RECOMMENDATION:
- Action: fix
- Pick: {GPT_PICK}
- Why: {one-line from GPT's "Why this wins"}
- Trade-offs: {one-line from GPT's "Trade-offs accepted"}
```

Re-Read `~/.claude/commands/plan/best-idea.md` and follow its **Debate Mode**
section with the `DEBATE_CONTEXT` block as `$ARGUMENTS`. Debate Mode activates
on the presence of both `CLAUDE_RECOMMENDATION:` and `GPT_RECOMMENDATION:`,
which the block above supplies.

The output includes a `VERDICT:` line, an `Action:` field, and the
`<<<FINAL_PICK>>>` / `<<<FINAL_PICK_REASON>>>` sentinels.

Determine `AGREEMENT` from the resolved pick (the `VERDICT:` line records the
same thing — if the two disagree, trust the resolved pick):
- If resolved pick name matches `CLAUDE_PICK` (normalized) → `debated-claude-won`
- If matches `GPT_PICK` → `debated-gpt-won`
- Otherwise (third option) → `debated-third-option`

**Same-option-different-name check:** before recording a debate outcome,
confirm the two picks were actually different options and not one option
under two names. If they name the same thing, record `agreement=same` and
`debate_invoked=false` instead, and note the wording difference in `notes`.

Present to user:

```
## Picks differed — debate resolved

**Claude picked**: {CLAUDE_PICK} — {CLAUDE_REASON}
**GPT picked**: {GPT_PICK} — {GPT_REASON}

[full debate output from best-idea Debate Mode, including VERDICT]

**Final pick**: {resolved pick from <<<FINAL_PICK>>>}
```

Set `DEBATE_INVOKED=true`, `FINAL_PICK={resolved}`. Proceed to Phase 5.

---

## Phase 5: Telemetry write

Always write a log entry — agreement-fast-path, debate-path, GPT-unavailable,
and extraction-failed all log.

```bash
mkdir -p ~/.local/state/claude/best-idea-log
LOG_PATH="$HOME/.local/state/claude/best-idea-log/${TIMESTAMP}-dual.json"
```

`Write` JSON to `$LOG_PATH` matching this schema:

```json
{
  "timestamp": "<ISO 8601 UTC, derived from $TIMESTAMP>",
  "mode": "dual",
  "problem_summary": "<PROBLEM_SUMMARY, ≤200 chars>",
  "claude_pick": { "name": "<CLAUDE_PICK>", "why": "<CLAUDE_REASON>" },
  "gpt_pick": { "name": "<GPT_PICK>", "why": "<GPT_REASON>" } | null,
  "final_pick": { "name": "<resolved>", "why": "<resolved reason>" },
  "agreement": "<same | debated-claude-won | debated-gpt-won | debated-third-option | gpt-unavailable | extraction-failed>",
  "debate_invoked": <true|false>,
  "gpt_model": "<gpt-5.4 | null>",
  "gpt_tokens_in": <number | null>,
  "gpt_tokens_out": <number | null>,
  "notes": "<string | null>"
}
```

If GPT was unavailable, set `gpt_pick=null`, `gpt_model=null`, both token
fields `null`.

**`notes` is filled at write time, not later.** Write it whenever the run
produced something the pick names alone do not carry: one reviewer caught a
factual error the other missed, the two picks were the same option under
different names, a reviewer's stated confidence was misplaced, or the
resolution rested on evidence neither initial pass had. Otherwise `null` —
do not pad it with a restatement of the picks.

> The schema previously carried an `outcome` field, intended to be
> back-filled during a retrospective. It was `null` on all 290 records ever
> written and the retrospective never ran; `notes` at write time replaced it
> because that is what actually got filled. Old records still carry
> `outcome` — treat it as dead and do not read it.

Tell user: `Logged: {LOG_PATH}`.

---

## Cleanup

```bash
rm -f /tmp/dual-best-idea-${TIMESTAMP}-*
```

---

## Reading the log (any time)

No scheduled review, no back-fill step. The question "is the second reviewer
earning its cost" is answered directly by the agreement mix — the share of
runs whose final pick was **not** Claude's:

```bash
jq -s '{
  total: length,
  by_agreement: (group_by(.agreement) | map({(.[0].agreement): length}) | add),
  changed_the_pick: ([.[] | select(.agreement == "debated-gpt-won" or .agreement == "debated-third-option")] | length)
}' ~/.local/state/claude/best-idea-log/*-dual.json
```

`changed_the_pick / total` is the headline number. As of 2026-07-28 it was
33/173 (19%) — GPT flipped the pick 25 times and forced a third option 8
times. Read the `notes` field on those runs for the qualitative version:

```bash
jq -s -r '.[] | select(.notes != null)
  | "\(.timestamp)  [\(.agreement)]\n  \(.notes)\n"' \
  ~/.local/state/claude/best-idea-log/*-dual.json
```

Revisit the keep/change/kill decision if `changed_the_pick` drops toward
zero over a sustained stretch, or if debates start resolving on
coin-flip grounds rather than on evidence one side actually had.

**Solo mode is retired.** `*-solo.json` records stop at 2026-05-29; dual
absorbed the same daily volume from 2026-05-30 on and this command has been
the only entry point since. Nothing writes `-solo.json` any more — the old
records are kept as history, not as a live baseline.

---

## Notes

- The whole point of this command is the parallel + comparison flow. If you
  just want a single GPT pick, use `/plan:best-idea` solo or `/ask-gpt`.
- Cost: each run is one extra GPT codex call (~5K-10K input tokens, single-shot).
  At gpt-5.4 prices that's a fraction of a cent. No retry storms.
- Privacy: problem text and pick reasons may contain repo names, plan content,
  or pasted-in client material. Logs stay local under
  `~/.local/state/claude/best-idea-log/` (no sync). If pasting sensitive info,
  be aware it lands here.
- Token telemetry assumes `parse-codex-output.sh` exposes `tokens_in`/`tokens_out`.
  If absent, fields silently become `null` — informational only, not load-bearing.
