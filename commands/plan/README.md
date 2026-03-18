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
| `/plan:handoff` | Transform plan into task files for sub-agents | - |
| `/plan:review` | Adversarial technical review | `ready` |
| `/plan:improve-idea` | Brainstorm through 4 lenses | `ready` |
| `/plan:best-idea` | Evaluate options, recommend solution | (inline interrupt) |
| `/plan:start-implementation` | Orchestrate parallel Sonnet sub-agents | `ready` |
| `/plan:code-review` | Review implementation commits | `review` |

## Storage Root

All workflow state and task files are stored outside the project directory to avoid `.claude/` permission prompts:

```
STORAGE_ROOT = ~/.claude-workflow/projects/{dir-name}/
```

Where `{dir-name}` is the basename of the current working directory (e.g., `noodle-api`, `claude-code-workflow`). If the directory doesn't exist, create it (including parents).

At execution start, print the resolved path: `Using storage: ~/.claude-workflow/projects/{dir-name}/`

## State Management

All commands share `{STORAGE_ROOT}/workflow-state.json`:

```json
{
  "plans": {
    "my-plan": {
      "path": "tasks/my-plan/",
      "status": "ready|implementing|review|complete|failed",
      "preImplCommit": "abc123",
      "handoffAt": "ISO timestamp",
      "completedAt": "ISO timestamp"
    }
  }
}
```

**Status lifecycle:** `ready` → `implementing` → `review` → `complete` | `failed`

Completed entries auto-delete after 30 days. Task files in `{STORAGE_ROOT}/tasks/` are preserved as audit trail.

## Plan Selection Pattern

Used by: `/plan:review`, `/plan:improve-idea`, `/plan:start-implementation`, `/plan:code-review`

1. Read `{STORAGE_ROOT}/workflow-state.json`
   - **If file is missing:** fall back to directory scan (step 1b)
   - Auto-cleanup: delete entries where `completedAt` > 30 days ago
   - Filter by required status (varies by command)
   - If 0 matching: fall back to directory scan (step 1b)
   - If 1 matching: auto-select, announce selection
   - If multiple: show selector with names and timestamps

1b. **Fallback: Directory Scan** (when workflow-state.json is missing or has no matches)
   - Scan `{STORAGE_ROOT}/tasks/*/README.md` for task directories
   - If 0 found: error "No plans found. Run /plan:handoff first."
   - If 1 found: auto-select, announce selection
   - If multiple found: show selector with directory names
   - **After selection, create/update `{STORAGE_ROOT}/workflow-state.json`** with the selected plan entry (status based on command's filter, e.g., `ready`)

2. Verify selected plan path exists
   - If missing: offer to remove stale entry, re-run selection

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
