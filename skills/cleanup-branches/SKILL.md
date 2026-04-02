---
name: cleanup-branches
description: Clean up stale git worktrees and local branches across Glade repos. Use when the user asks to "clean up branches", "remove stale worktrees", "prune branches", "clean up git", or similar. Discovers worktrees and branches, checks PR status, and presents findings repo-by-repo for user decisions.
---

# Cleanup Branches & Worktrees

Interactive cleanup of stale worktrees and local branches across all Glade development repositories. Discovers what exists, classifies by PR status, and presents findings repo-by-repo for user decisions.

## Prerequisites

Determine the dev root directory (typically `~/dev/glade` or the current working directory). Find all git repos by checking for `.git` directories:

```bash
# Check each known repo — use direct paths, don't use command substitution
ls -d /path/to/dev-root/noodle-api/.git 2>/dev/null
ls -d /path/to/dev-root/noodle-frontend/.git 2>/dev/null
# ... etc for each repo
```

Store the list of found repo paths for use throughout the workflow.

## Phase 1: Discovery

Run these in **parallel Bash calls** (one per repo):

### Worktrees
For each repo:
```bash
cd /path/to/repo && git worktree list
```

Also check for:
- `.claude/worktrees/` directories within each repo
- Standalone worktree directories in the dev root (directories that aren't in the known repo list but are git worktrees of a known repo)

### Local Branches
For each repo:
```bash
cd /path/to/repo && git branch
```

**Skip repos that only have `main`** — nothing to clean.

### Fetch
Run `git fetch origin --prune` once per repo (can be parallelized) to ensure remote tracking is up to date.

## Phase 2: Classify

For each worktree and local branch (excluding `main`), check PR status:

```bash
gh pr list --repo glade-ai/<repo-name> --head <branch-name> --state all --json number,title,state,mergedAt --limit 1
```

Classify each into:

| Category | Criteria | Default Action |
|----------|----------|----------------|
| **MERGED** | PR exists and state is MERGED | Delete (safe) |
| **CLOSED** | PR exists and state is CLOSED (not merged) | Delete (likely abandoned) |
| **OPEN** | PR exists and state is OPEN | Keep (active work) |
| **NO_PR** | No PR found for this branch | Ask user — could be WIP or abandoned |

For worktrees specifically, also check:
- `git status --short` in the worktree to detect uncommitted changes
- Whether untracked files are just artifacts (e.g., `.dual-code-review-transcript.md`) vs real work

## Phase 3: Present (Repo by Repo)

Present findings **one repo at a time**. For each repo with cleanup candidates:

1. Show a table of worktrees and branches grouped by status
2. Include branch name, PR number/title, and status
3. For NO_PR branches, show the last commit date and message to help the user decide
4. Recommend deletions for MERGED and CLOSED items
5. Ask the user what to do before proceeding

**Example presentation:**

```
### noodle-frontend (4 branches to clean)

| Branch | PR | Status | Recommendation |
|--------|-----|--------|----------------|
| `cancel-filing-modal` | #10562 MERGED | Safe to delete |
| `worktree-fix-race-condition` | #10625 MERGED | Safe to delete |
| `worktree-DEV-20597-toggle` | #10705 OPEN | Keep |
| `experiment-branch` | None | Created Mar 15 — "WIP: test approach" | Your call |

Delete the 2 merged branches? What about `experiment-branch`?
```

Wait for user confirmation before executing deletions for each repo.

## Phase 4: Execute

After user approves deletions for a repo:

### Remove Worktrees First
```bash
cd /path/to/repo && git worktree remove /path/to/worktree
```

- If the worktree has **only untracked files**: use `--force` (artifacts, not real work)
- If the worktree has **modified tracked files**: stop and warn the user — do not force
- After removing all worktrees: `git worktree prune`

### Switch Current Checkout If Needed
If a branch to delete is the current checkout:
```bash
cd /path/to/repo && git checkout main && git branch -D <branch-name>
```

### Delete Branches
```bash
cd /path/to/repo && git branch -D <branch1> <branch2> <branch3>
```

### Clean Up Empty Directories
```bash
rmdir /path/to/repo/.claude/worktrees 2>/dev/null
rmdir /path/to/dev-root/worktrees 2>/dev/null
```

## Important Rules

- **Never delete remote branches** — only clean up local worktrees and local branches
- **Never force-delete worktrees with modified tracked files** without explicit user approval
- **Always present before executing** — no silent deletions
- **One repo at a time** — don't dump all repos at once
- **Parallel discovery, sequential presentation** — gather data fast, present interactively
- **No `$()` command substitution** — break into sequential Bash calls per global instructions
- **Use `gh pr list` with `--json`** for structured data, not human-readable output
