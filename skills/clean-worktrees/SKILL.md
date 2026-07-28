---
name: clean-worktrees
description: >
  Clean up stale worktrees and branches across Glade repos.
  Use when the user asks to clean up worktrees, stale branches, or dev
  environment clutter. Also suggest when you notice 5+ worktrees in a repo.
---

# Clean Worktrees

Clean up stale git worktrees and their associated branches. Handles multi-repo sweep from the dev root or single-repo cleanup when inside a repo.

## Preferred path: the helper script

A script implements the full discover → classify → clean logic so you don't have
to drive dozens of git calls by hand: `clean-worktrees.sh` (next to this file).

```bash
# Dry-run (default): classify and print the summary, remove nothing.
/Users/kevinandrews/.claude/skills/clean-worktrees/clean-worktrees.sh

# Remove the SAFE items (gone-from-remote or merged), leave needs-confirm + locked.
/Users/kevinandrews/.claude/skills/clean-worktrees/clean-worktrees.sh --safe-only

# Limit scope to specific repos; skip fetch for speed.
/Users/kevinandrews/.claude/skills/clean-worktrees/clean-worktrees.sh --safe-only --no-fetch /path/to/repo
```

Workflow:
1. Run it with **no flags** (dry-run) to get the classification.
2. Show the user the SAFE / NEEDS-CONFIRM / LOCKED summary.
3. On approval, re-run with `--safe-only`. (`--all` also removes needs-confirm —
   destructive, unpushed commits lost; only on explicit request.)

It auto-detects scope (current repo vs. dev-root sweep), picks the default branch
per repo via `origin/HEAD`, classifies each worktree as gone / merged
(`merge-base --is-ancestor` against `origin/<default>`) / stale / locked /
needs-confirm, finds orphan branches, and guards the main checkout + CWD. Targets
bash 3.2 (macOS default).

The phases below are the spec the script implements — follow them by hand only if
the script is unavailable or you need to deviate.

## Execution Guidelines

- Simple command chaining with `&&` is fine
- Avoid command substitution like `$(git ...)` -- run commands directly in separate Bash calls
- Never wrap commands in `bash -c "..."` -- run them directly
- Use parallel Bash tool calls for independent repos
- Store repo paths once and reuse them

## Phase 1: Discover

### Step 1: Detect Scope

Run `git rev-parse --git-dir 2>/dev/null` to determine scope:

- **Inside a git repo**: Clean only this repo. Store its absolute path.
- **NOT inside a git repo** (dev root): Discover all main checkouts. For each direct child directory of CWD, check if it has a `.git` **directory** (not a `.git` file, which indicates a worktree). Store the paths of all main checkouts found.

### Step 2: Detect Default Branch (per repo)

For each repo, determine the default branch:

```bash
cd /path/to/repo && git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null
```

Extract the branch name from `refs/remotes/origin/{name}`. If this fails, fall back:

```bash
cd /path/to/repo && git rev-parse --verify origin/main 2>/dev/null
```

If that fails, try `origin/master`. Use the result as `{default}` in all subsequent commands for this repo.

### Step 3: Fetch and Gather Data (parallel across repos)

For each repo, run as a single chained command:

```bash
cd /path/to/repo && git fetch --prune 2>&1 | tail -3; echo "FETCH_EXIT:$?"
```

**Important**: Use `;` (not `&&`) after fetch so the remaining commands run even if fetch exits non-zero (it does when pruning deleted branches). If FETCH_EXIT is non-zero, warn: "Fetch failed for {repo} -- classification may use stale remote data" but continue.

Then gather data (chain per repo with `;` separators to avoid cascade failures):

```bash
cd /path/to/repo; echo "---WORKTREES---"; git worktree list --porcelain; echo "---BRANCH-VV---"; git branch -vv --no-color; echo "---MERGED---"; git branch --merged {default} --no-color
```

Run these in parallel across repos (one Bash call per repo).

### Step 4: Classify

For each worktree found in the porcelain output (excluding the main checkout itself), extract:
- **Branch name** from the `branch refs/heads/...` line
- **Locked status** from the `locked` line (if present)
- **Worktree path** from the `worktree /path/...` line

For each branch (both worktree-associated and standalone), classify using this priority order (first match wins):

| Priority | Category | Condition | Tag | Action |
|----------|----------|-----------|-----|--------|
| 1 | Locked | `locked` in porcelain output | `[locked]` | Skip, inform |
| 2 | Safe: gone | `git branch -vv` shows `[origin/...: gone]` for this branch | `[gone]` | Auto-remove |
| 3 | Safe: merged | Verified with `git merge-base --is-ancestor` (see below) | `[merged]` | Auto-remove |
| 4 | Safe: stale ref | Worktree path in porcelain does not exist on disk | `[stale ref]` | Prune only |
| 5 | Needs confirmation | Everything else (unmerged, ahead of remote, detached HEAD) | `[unmerged]` | Ask user |

**Merged verification (critical)**: `git branch --merged` gives **false positives** for branches checked out in worktrees. Before classifying ANY branch as `[merged]`, verify with:
```bash
cd /path/to/repo && git merge-base --is-ancestor {branch_name} {default}; echo "EXIT:$?"
```
Only classify as merged if EXIT is 0. If non-zero, the branch has commits not on the default branch — classify as "needs confirmation". Prefer `[gone]` over `[merged]` in priority order since gone is a stronger signal (remote was explicitly deleted).

**Orphan branches**: Also scan `git branch -vv` for branches that have NO associated worktree. If they are merged or gone, classify them the same way with an additional `[orphan]` tag (e.g., `[orphan, merged]`). If they are neither merged nor gone, skip them (this skill focuses on cleanup, not branch management).

**Age-based staleness flag**: For items classified as "needs confirmation", check the age of the last commit:

```bash
cd /path/to/repo && git log -1 --format='%ai' {branch_name}
```

If the last commit is older than 14 days, add a `[stale 14d+]` tag. This is informational only and does not change the classification.

**CWD safety check**: Check if the current working directory is inside any worktree path that will be removed. If so, warn and exclude that worktree from cleanup.

## Phase 2: Present

Display a grouped summary for each repo that has worktrees or orphan branches to clean.

### Format

For each repo:

```
=== {repo-name} ({N} worktrees, {M} orphan branches) ===

SAFE TO REMOVE (will proceed automatically):
  1. [merged]      noodle-api-efiling-dashboard -> kev/DEV-21221-dashboard
  2. [gone]        noodle-api-sentry-fix -> claude/sentry-fix
  3. [stale ref]   .claude/worktrees/pr-6860 -> fix/emit-event (dir missing)
  4. [orphan, merged] kev/old-feature-branch
  5. [orphan, gone]   claude/closed-pr-branch

NEEDS CONFIRMATION (has unmerged/unpushed work):
  6. [unmerged]           noodle-api-mixpanel-refactor -> kevin/mixpanel
     Last commit: 2026-03-28 "fix: isolate person lookup..."
  7. [unmerged, stale 14d+] us-gov-dev-21597 -> kev/dev-21597
     Last commit: 2026-03-15 "wip: initial attempt..."

LOCKED (skipping):
  8. [locked]      us-gov-pr-358 -> kev/pr-358
     Reason: "initializing"
```

For each entry, show:
- Classification tags in brackets
- Worktree directory name (relative to dev root) or `[orphan]` for branch-only items
- Branch name (after `->`)
- For "needs confirmation" items: last commit date and first line of commit message

### User Confirmation

After presenting the summary, ask the user in chat markdown (do not call any tool to ask):

**If only safe-to-remove items exist**: "Found {N} items safe to remove (branches merged or gone from remote). Proceed?"
- **Clean all safe** -- remove merged/gone worktrees and branches
- **Cancel** -- do nothing

**If items needing confirmation also exist**: "Found {N} safe items and {M} needing confirmation. How to proceed?"
- **Clean safe only** -- remove merged/gone, leave unmerged untouched
- **Clean all** -- remove everything (warn: data loss for unmerged branches)
- **Let me pick** -- present each "needs confirmation" item individually for yes/no
- **Cancel** -- do nothing

**If "Let me pick"**: Present each "needs confirmation" worktree as its own chat-markdown question with Remove/Keep options; STOP and wait for a reply on each.

### Dry-Run Mode

If the user invoked with "just show me", "dry run", or "what would be cleaned", stop after displaying the summary. Do NOT ask for confirmation or proceed to Phase 3. The summary is the output.

## Phase 3: Clean

Execute the approved removals. Use parallel Bash calls across repos.

### Per repo, in order:

**Step 1 -- Prune stale references:**
```bash
cd /path/to/repo && git worktree prune
```

**Step 2 -- Remove approved worktrees** (one per Bash call, or chain with `&&`):
```bash
cd /path/to/repo && git worktree remove --force /path/to/worktree-dir
```

Use `--force` by default -- most worktrees have untracked files (node_modules, build artifacts) that cause the non-force version to fail. This is safe because we already classified the branch as merged/gone before reaching this step.

**Step 3 -- Delete associated branches** (after worktree is removed):
```bash
cd /path/to/repo && git branch -D {branch-name}
```

For orphan branches (no worktree), just delete the branch directly.

**Step 4 -- Final prune:**
```bash
cd /path/to/repo && git worktree prune
```

**Step 5 -- Clean up empty directories:**
```bash
cd /path/to/repo && rmdir .claude/worktrees 2>/dev/null; true
```

### Report Results

After cleanup, show:

```
Cleanup complete:

  noodle-api: 3 worktrees removed, 1 orphan branch deleted
  us-government-integrations: 8 worktrees removed, 2 orphan branches deleted
  noodle-frontend: 1 worktree removed

  Total: 12 worktrees removed, 3 orphan branches deleted
  Kept: 2 (user chose to keep), 1 (locked)
```

## Edge Cases

- **Never remove the main checkout** or the default branch (main/master)
- **Detached HEAD worktrees**: Classify as "needs confirmation" since there is no branch to check merge status
- **Non-worktree directories**: Dirs that exist in the dev root but are NOT in any repo's `git worktree list` output are regular directories, not worktrees. Ignore them.
- **CWD inside a worktree**: If CWD is inside a worktree being cleaned, warn and skip that worktree
- **Fetch failure**: Warn but continue. Classification may be stale (branches that were deleted on remote won't show as [gone])
- **Branch checked out in another worktree**: `git branch -D` will fail. Remove the worktree first, then delete the branch.
- **Repo uses master instead of main**: Default branch detection handles this via symbolic-ref fallback
