# Planning Workflow Commands

Commands for the full planning-to-implementation pipeline.

## Workflow

```
/plan:discuss → plan mode → /plan:handoff → /clear → /plan:review → /plan:improve-idea
    → /clear → /plan:start-implementation → /clear → /plan:code-review
```

Each `/clear` resets context for fresh-eyes review. This is intentional - the reviewer shouldn't have the planner's context.

## Commands

| Command | Purpose | Status Filter |
|---------|---------|---------------|
| `/plan:discuss` | Requirements discovery with structured handoff | - |
| `/plan:handoff` | Transform plan into task files for sub-agents | - (creates in `todo`) |
| `/plan:review` | Adversarial technical review | `todo` |
| `/plan:improve-idea` | Brainstorm through 4 lenses | `todo` |
| `/plan:best-idea` | Evaluate options, recommend solution | (inline interrupt) |
| `/plan:start-implementation` | Orchestrate parallel Sonnet sub-agents | `todo` → moves to `doing` |
| `/plan:code-review` | Review implementation commits | `doing` |

## Storage

Plans live in a dedicated local git repo, the `kg` knowledge repo:

```
KG_ROOT = ~/dev/kg
```

Plan folders are laid out by **repo** and **status**, with status encoded by folder location:

```
~/dev/kg/
  plans/
    {repo}/                  # e.g. noodle-api — from `git remote get-url origin`
      todo/   {slug}/  README.md  NN-task.md ...
      doing/  {slug}/  README.md  NN-task.md  progress.md ...
      done/   {slug}/  ...        # moved here manually after the PR merges
  initiatives/               # durable KB layer (rest of KB system lands here later)
```

- **`{slug}`** (`issue-id-title`): the current branch with its leading `user/` prefix stripped, e.g. `kevin/dev-23587-switch-firm-x` → `dev-23587-switch-firm-x`.
- **`{repo}`**: parsed from the cwd's `origin` remote (`glade-ai/noodle-api` → `noodle-api`).
- **Status = folder**: `todo` / `doing` / `done`. There is **no `workflow-state.json`**.

All path/slug/move logic is centralized in the **`kg-plan.sh`** helper (installed to `~/.claude/scripts/kg-plan.sh`). Commands call it rather than embedding bash:

| Invocation | Does |
|------------|------|
| `kg-plan.sh resolve` | from cwd, prints `REPO`, `BRANCH`, `SLUG`, `LINEAR_ID`, and the `TODO_DIR`/`DOING_DIR`/`DONE_DIR` paths. **Exits non-zero** if not in a git repo, detached HEAD, no origin, or the branch has no `<team>-<num>-` ticket pattern (e.g. `feat/…`, `fix-…`). |
| `kg-plan.sh create-todo <repo> <slug>` | auto-inits `kg` if needed; **collision-guarded** (fails if `<slug>` already exists in `todo`/`doing`/`done`); prints the new `todo/<slug>/` path. |
| `kg-plan.sh move <repo> <slug> <from> <to>` | `git mv` between status dirs + commit (`plan: move <slug> <from>-><to>`). Refuses to clobber an existing target. |
| `kg-plan.sh list <repo> <status>` | prints slug dirs under `plans/<repo>/<status>/`. |

## Status

**Lifecycle:** `todo` → `doing` → `done`. `doing` means *anything in progress* — it absorbs the old `implementing` and `review` states. `done` is reached only after the PR merges (currently a manual `kg-plan.sh move … doing done`).

**Audit trail:** every transition is a commit in `~/dev/kg`. Use `git -C ~/dev/kg log` to see when a plan moved between states — this replaces the old `workflow-state.json` timestamps.

## Plan Selection Pattern

Used by: `/plan:review`, `/plan:improve-idea`, `/plan:start-implementation`, `/plan:code-review`

1. If an explicit path argument is provided, use it directly.
2. Run `kg-plan.sh resolve`.
   - **On success:** `{repo}` + `{slug}` are known. Look for `plans/{repo}/{status}/{slug}/` where `{status}` is the command's filter (varies by command).
     - If it exists: auto-select, announce `Selected: {path}`.
     - If it doesn't: the plan may be in another status — report where the slug currently lives (via the status dirs), or fall through to step 3.
   - **On non-zero exit** (no ticket-bearing branch, detached, no origin): fall through to step 3.
3. **Fallback selector:** `kg-plan.sh list {repo} {status}` (use `{repo}` from resolve if available, else ask the user which repo).
   - 0 found: error `No plans in {status}. Run /plan:handoff first.`
   - 1 found: auto-select, announce.
   - Multiple: show a selector with the slug names.
4. Verify the selected plan path exists before proceeding.

## Shared Definitions

### Severity Levels

| Level | Definition | Examples |
|-------|------------|----------|
| **CRITICAL** | Implementation will fail or cause data loss | Missing error handling, race condition, unbounded resource |
| **HIGH** | Significant rework required later | Wrong abstraction, missing edge case, O(n²) where O(n) possible |
| **MEDIUM** | Suboptimal but functional | Unnecessary complexity, missed parallelization |
| **LOW** | Worth noting, easy to defer | Minor inefficiency, potential future issue |

### Resolution Flow

Used by: `/plan:review`, `/plan:improve-idea`, `/plan:code-review`

1. Categorize findings into **Autosolve** (≥90% confidence) vs **Discussion** (<90%)
2. Present discussion items one-at-a-time with options A/B and recommendation
3. After all discussions resolved, present autosolve batch for confirmation
4. Apply approved changes
