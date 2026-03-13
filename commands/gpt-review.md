---
description: Get a GPT code review of branch changes or a PR, then Claude reviews and presents findings
argument-hint: [commit-range | branch | #PR | PR-URL]
---

<!-- Pricing config (verify periodically at https://platform.openai.com/docs/pricing):
  gpt-5.2-codex: $1.75/1M input, $14.00/1M output
-->

Get GPT-5.2-Codex to review code changes, then Claude critically evaluates the findings and presents actionable results.

## Phase 1: Determine Review Scope

Determine the working directory first: use the git repo root of the current directory (where `.git` lives).

### If argument is a PR reference (`#123` or a GitHub PR URL):
1. Extract the PR number (from `#123` or parse from URL like `github.com/org/repo/pull/123`)
2. Use `gh pr view <number> --json baseRefName,headRefName,title,body` for metadata
3. Use `gh pr diff <number>` to get the diff
4. Use `gh pr view <number> --json commits` for the commit list
5. Store the diff in `/tmp/gpt-review-diff.txt` for codex to reference

### If argument is a commit range or branch:
- Single commit hash → review that commit
- Commit range (`abc123..def456`) → review that range
- Branch name → review diff against main/master

### If no argument:
1. Check if on a feature branch (not main/master)
   - If yes → review all commits since branching from main: run `git merge-base HEAD main`, then use that hash as the base
2. If on main → review HEAD commit only

### Gather orientation data:
Run git commands to collect (these go into the GPT prompt, NOT the full diff):
- `git log --oneline <range>` — commit list (skip for PR reviews, use PR metadata instead)
- `git diff --stat <range>` — file summary with line counts (or parse from PR diff)

## Phase 2: Send to GPT

### Build the context prefix
Check which of these files exist in the working directory: `AGENTS.md`, `CLAUDE.md`, `README.md`. If any exist, include them in the prompt prefix:

```
This project has the following context files in the repo root: [list files that exist]. Read them first to understand project conventions before reviewing.
```

### Build the review prompt

Write the full prompt to `/tmp/gpt-review-prompt.txt` (avoids shell escaping issues). Combine the context prefix, orientation data, and review instructions:

```
[context prefix if applicable]

You are reviewing code changes for a pull request. Your job is to find real issues — bugs, security holes, performance problems, and architectural concerns.

REVIEW SCOPE:
- Git range: <range> [or: PR #<number> — <title>]
- Working directory: <dir>

COMMITS:
<commit log>

FILES CHANGED:
<output from git diff --stat>

INSTRUCTIONS:
1. Run `git diff <range>` to get the full diff [or: read /tmp/gpt-review-diff.txt for the PR diff]
2. For files with substantive changes, read the full file for context (not just the diff hunk)
3. Review thoroughly and report findings

For each issue found, use this format:

FINDING:
- Severity: CRITICAL | IMPORTANT | SUGGESTION
- File: <path>
- Line: <line number in the actual file, not the diff>
- Category: security | bug | performance | type-safety | error-handling | architecture | code-quality
- Issue: <specific description>
- Code: <quote the problematic code>
- Fix: <suggested fix with code if applicable>

Also report:
- Positive patterns or well-crafted solutions worth calling out (prefix with POSITIVE:)
- Cross-file concerns spanning multiple files (prefix with CROSS-FILE:)

Do NOT flag: style nits, formatting preferences, or minor naming opinions.
Focus on: things that could cause bugs, security issues, data loss, or performance problems in production.
```

### Run codex

Use the Bash tool with `run_in_background: true` and a 300000ms timeout:

```
cat /tmp/gpt-review-prompt.txt | codex exec -m gpt-5.2-codex --full-auto --search --json --ephemeral -C <working_directory> - 2>/dev/null
```

Tell the user GPT is reviewing and they can continue working.

### If codex fails

If codex returns an error, times out, or produces unparseable output:
1. Surface the raw error to the user
2. Suggest: "Codex failed — run `/plan:code-review` for a Claude-only review instead, or retry with `/gpt-review`"
3. Do NOT silently fall back to a Claude review

## Phase 3: Claude Reviews GPT's Findings

Parse the JSONL output following the same pattern as `ask-gpt`: concatenate `text` from all `item.completed` events where `type` is `agent_message`, sum `usage` from all `turn.completed` events.

**Critically evaluate** GPT's findings. For each issue GPT raised:
- **Validate**: Use the Read tool to read the flagged file at the cited line numbers. Confirm the issue exists in the actual code. Tag each finding with Claude's confidence (e.g., "Confirmed 95%", "Likely valid 80%", "Probable false positive 30%").
- **Dismiss false positives**: If GPT misunderstood the code, flagged something that's intentional, or cited wrong line numbers — drop it with a note in "What Claude Corrected".
- **Upgrade/downgrade severity**: Adjust if GPT over- or under-estimated impact given the project context.
- **Add missed issues**: If Claude spots something GPT missed while reading the flagged files, add it (tag as "Claude addition").
- **Enrich suggestions**: Improve GPT's fix suggestions with knowledge of the codebase conventions (from AGENTS.md, CLAUDE.md).

## Phase 4: Present Results

```
## Code Review: <range description>

**Reviewer**: GPT-5.2-Codex (reviewed by Claude)
**Scope**: [N] commits, [M] files
**Verdict**: APPROVE | REQUEST CHANGES | COMMENT
**Risk**: LOW | MEDIUM | HIGH

### Findings

#### CRITICAL (must fix)
| # | File:Line | Category | Confidence | Issue | Suggestion |
|---|-----------|----------|------------|-------|------------|
| 1 | `path:line` | [type] | [X%] | [issue] | [fix] |

#### IMPORTANT (should fix)
| # | File:Line | Category | Confidence | Issue | Suggestion |
|---|-----------|----------|------------|-------|------------|
| 2 | `path:line` | [type] | [X%] | [issue] | [fix] |

#### SUGGESTION (consider)
| # | File:Line | Category | Confidence | Issue | Suggestion |
|---|-----------|----------|------------|-------|------------|
| 3 | `path:line` | [type] | [X%] | [issue] | [fix] |

### Cross-File Concerns
[If any]

### What GPT Got Right
[Notable valid catches]

### What Claude Corrected
[False positives dismissed, severities adjusted, context GPT missed]

---

**GPT-5.2-Codex Usage Report**
- Input tokens: X,XXX (cached: X,XXX)
- Output tokens: X,XXX
- Estimated cost: $X.XX
  - Input: X,XXX × $1.75/1M = $X.XXXX
  - Output: X,XXX × $14.00/1M = $X.XXXX

---

> Say **go** to walk through findings, or pick numbers to discuss.
```

Omit empty severity sections. If zero findings after Claude's review: APPROVE with a clean summary, skip Phase 5.

## Phase 5: One-at-a-Time Resolution

When user says "go":

1. **Categorize**: Autosolve (≥90% confidence) vs. Discussion (<90%)
2. **Discussion items first** — present ONE at a time with options A/B/C and a recommendation. **STOP after each. Wait for user response.**
3. **Autosolve batch** — present all high-confidence fixes for confirmation.
4. **Apply** — Edit approved fixes, verify syntax.
5. **Commit** — ask user, commit with "fix: address code review findings from GPT review"

Clean up temp files (`/tmp/gpt-review-prompt.txt`, `/tmp/gpt-review-diff.txt`) after execution.
