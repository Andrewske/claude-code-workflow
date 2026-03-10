---
description: Orchestrate parallel implementation of plan tasks via sub-agents
argument-hint: [path] [--resume]
allowed-tools: Task, Read, Write, Edit, Glob, Bash
---

# Implementation Orchestrator

Coordinate parallel Sonnet sub-agents to implement a distributed plan. Each task runs in its own `task-implementer` agent, respecting dependencies.

## Arguments

- `<path>`: Path to plan folder (optional - auto-detects from workflow-state.json)
- `--resume`: Continue from last failure point

## State Management

| File | Purpose | Updated When |
|------|---------|--------------|
| `.claude/workflow-state.json` | Plan-level status tracking | Plan starts, completes, or abandoned |
| `.claude/tasks/{plan}/progress.md` | Human-readable execution log | Each batch starts/completes |
| `.claude/tasks/{plan}/XX-task.md` | Individual task status | Task completes or fails |

**Plan status values:** `ready` | `implementing` | `complete` | `failed`
**Task status values:** `pending` | `running` | `done` | `failed`

**File locking:** Always acquire a lock on workflow-state.json before reading/writing to prevent race conditions with parallel agents. Use `flock` or equivalent.

---

## Execution Flow

### Phase 1: Prerequisites

**1.1 Auto-stash dirty working directory:**
```bash
git status --porcelain
```
- If output: Run `git stash push -m "pre-impl-{plan}-{timestamp}" --include-untracked`
- Log: "Stashed uncommitted changes. Restore with: git stash pop"

**1.2 Check for active implementation:**

Check `.claude/workflow-state.json` for any plan with `status === "implementing"`:

If found, prompt:
```
Plan "{name}" is currently implementing (started {date}).

1. Resume {name}
2. Cancel

Select (1-2):
```
- **Option 1**: Use `--resume` mode for that plan
- **Option 2**: Abort

**1.3 Select plan:**

Follow **Plan Selection Pattern** (see README) with status filter: `ready`

**1.4 Record implementation start:**

Update workflow-state.json (with lock):
```json
"{plan}": {
  "status": "implementing",
  "preImplCommit": "{git rev-parse HEAD}",
  "startedAt": "{ISO timestamp}"
}
```

Also write `preImplCommit` to progress.md header for resilience.

---

### Phase 2: Load, Build Graph & Initialize Progress

1. Verify path exists with task files
2. Read `README.md` for plan context
3. Parse each `[0-9][0-9]-*.md` file's YAML frontmatter:
   ```yaml
   task: 01-setup-auth
   status: pending
   depends: []
   files:
     - path: src/auth.ts
       action: create
   ```

4. Build dependency graph and compute batches:

```
function computeBatches(tasks):
  completed, batches = set(), []
  remaining = set(all task ids)

  while remaining:
    batch = [t for t in remaining if all deps in completed]
    if not batch: ERROR "circular dependency"
    batches.append(batch)
    completed.update(batch)
    remaining -= batch

  return batches
```

Output example:
```
Batch 1: [01-setup, 02-config]     # no deps
Batch 2: [03-routes, 04-middleware] # deps on batch 1
Batch 3: [05-tests]                 # deps on batch 2
```

5. Create `{path}/progress.md`:

```markdown
# Implementation Progress

**Plan:** {name}
**Pre-Impl Commit:** {hash}
**Started:** {timestamp}

## Tasks
- 01-setup-auth: pending
- 02-add-config: pending
- 03-create-routes: pending

## Execution Log
[Batch entries appended here]
```

---

### Phase 3: Execute Batches

For each batch:

1. **Update progress.md**: Mark batch tasks as "running"

2. **Spawn parallel agents** (single Task call with multiple invocations):
   ```
   Task(
     subagent_type: "task-implementer",
     model: "sonnet",
     prompt: "Implement task: {path}/{task-file}"
   )
   ```
   > The task-implementer agent reads the task file, implements changes, runs verification, updates status, and commits.

3. **Wait for ALL agents in batch to complete** (even if some fail)

4. **Update status** (both progress.md AND task file YAML):
   - Success: `status: done`, progress shows "done"
   - Failure: `status: failed`, progress shows "failed: {error}"

5. **Tag the batch:**
   ```bash
   git tag "impl-{plan}-batch-{N}"
   ```

6. **Continue or halt**:
   - All success → next batch
   - Any failure → stop after batch completes, show resume instructions

---

### Phase 4: Completion

**On Success:**
```
✅ Implementation complete!

Plan: {name} | Tasks: {N} | Duration: {time}

Next: Run /clear then /plan:code-review
```

Update workflow-state.json (with lock): `"status": "complete", "completedAt": "{timestamp}"`

**On Failure:**

> **Critical:** Keep plan status as `implementing` (not `failed`) so `--resume` works.

```
❌ Implementation stopped after batch {N}

✅ Completed: 01-setup-auth, 02-add-config
❌ Failed: 03-create-routes - {error}
⏸ Pending: 04-add-tests, 05-update-docs

Rollback to batch start: git checkout impl-{plan}-batch-{N-1}

Run: /plan:start-implementation --resume
```

---

## --resume Behavior

1. Read existing `progress.md`
2. Find last failed/pending task
3. Build batch sequence starting from failure point
4. Skip completed tasks
5. Continue execution

---

## Error Messages

| Error | Message |
|-------|---------|
| Invalid path | "Path not found: {path}. Run /plan:handoff first." |
| No tasks | "No task files (01-*.md) in {path}. Run /plan:handoff." |
| Missing YAML | "Task {file} missing frontmatter. Regenerate with /plan:handoff." |
| Circular deps | "Circular dependency: {task1} ↔ {task2}" |
| Agent failure | Log error, mark failed, show resume instructions |

---

## Constraints

- Only modify task file YAML frontmatter (status field) - never content
- Commit after each successful task (atomic units)
- Tag after each batch for easy rollback
- Complete entire batch before stopping on failure
- Log everything to progress.md
- Always lock workflow-state.json before access
