# Planning Workflow Commands

Commands for the full planning-to-implementation pipeline.

## Workflow

```
/discuss → plan mode → /plan:handoff → /clear → /plan:review → /plan:improve-idea
    → /clear → /plan:start-implementation → /clear → /plan:code-review
```

Each `/clear` resets context for fresh-eyes review. This is intentional - the reviewer shouldn't have the planner's context.

## Commands

| Command | Purpose | Status Filter |
|---------|---------|---------------|
| `/discuss` | Requirements discovery with structured handoff | - |
| `/plan:handoff` | Transform plan into task files for sub-agents | - |
| `/plan:review` | Adversarial technical review | `ready` |
| `/plan:improve-idea` | Brainstorm through 4 lenses | `ready` |
| `/plan:best-idea` | Evaluate options, recommend solution | (inline interrupt) |
| `/plan:start-implementation` | Orchestrate parallel Sonnet sub-agents | `ready` |
| `/plan:code-review` | Review implementation commits | `implementing` or `complete` |

## State Management

All commands share `./.claude/workflow-state.json`:

```json
{
  "plans": {
    "my-plan": {
      "path": ".claude/tasks/my-plan/",
      "status": "ready|implementing|complete|failed",
      "preImplCommit": "abc123",
      "handoffAt": "ISO timestamp",
      "completedAt": "ISO timestamp"
    }
  }
}
```

**Status lifecycle:** `ready` → `implementing` → `complete` | `failed`

Completed entries auto-delete after 30 days. Task files in `.claude/tasks/` are preserved as audit trail.

## Plan Selection Pattern

Used by: `/plan:review`, `/plan:improve-idea`, `/plan:start-implementation`, `/plan:code-review`

1. Read `./.claude/workflow-state.json`
   - Auto-cleanup: delete entries where `completedAt` > 30 days ago
   - Filter by required status (varies by command)
   - If 0 matching: show appropriate error
   - If 1 matching: auto-select, announce selection
   - If multiple: show selector with names and timestamps

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
