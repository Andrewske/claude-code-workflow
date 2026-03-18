---
description: Generate implementation-ready task files from a Claude Code plan
---

## When to Use

Use this command when:
- You have a plan in `.claude/plans/` ready for implementation
- You want to hand off to another AI instance (Sonnet, OpenCode, etc.)
- You want a historical record of what was planned

**Workflow:** Plan → `/plan:handoff` → `/clear` → `/plan:review` → `/clear` → `/plan:start-implementation`

---

You are a plan distribution orchestrator. Transform the current plan file into an implementation-ready task sequence.

## EXECUTION SEQUENCE

### Phase 1: Locate & Validate Plan
1. Identify current plan file in `.claude/plans/` (extract from context or system state)
2. Read plan content in full
3. Extract plan file name without extension (e.g., `buzzing-wibbling-wirth` from `buzzing-wibbling-wirth.md`)
4. Verify plan is non-empty and properly formatted

**Abort if:** No active plan found or plan file is empty

### Phase 2: Prepare Target Directory

Compute `STORAGE_ROOT` per `commands/plan/README.md`, Storage Root section. Print the resolved path.

1. Set target directory to `{STORAGE_ROOT}/tasks/{plan-name}/`
2. Check if `{STORAGE_ROOT}/tasks/{plan-name}/` already exists on filesystem:
   - If exists: Ask "Task files already exist at {STORAGE_ROOT}/tasks/{plan-name}/. Overwrite? (y/n)"
     - If yes: Remove existing directory and proceed
     - If no: Abort handoff
   - If new: Create the target directory structure

### Phase 3: Semantic Task Parsing
Parse the plan using **semantic grouping logic**:

**Grouping Criteria:**
- Group tasks that modify the same file(s) together
- Group tasks with shared domain context (e.g., "authentication flow" tasks stay together even if touching different files)
- Respect natural implementation order (foundational tasks before dependent tasks)
- Each group = one numbered markdown file

**Detection Method:**
- Analyze file paths mentioned in task descriptions
- Identify conceptual clusters (authentication, UI components, API endpoints, testing, etc.)
- Maintain dependency order from original plan

**Task Boundary Signals:**
- Shift to different file set
- Change in functional domain
- Explicit phase markers in original plan

### Phase 4: Generate Numbered Task Files
For each semantic task group:

1. **Generate filename:**
   - Format: `{NN}-{task-name}.md`
   - NN = zero-padded sequence (01, 02, 03...)
   - task-name = kebab-case extracted from task title/description
   - Example: `01-implement-auth-middleware.md`

2. **File content structure (with YAML frontmatter):**
   ```markdown
   ---
   task: {NN}-{task-name}
   status: pending
   depends: [{list of task IDs this depends on, e.g., 01-setup-auth}]
   files:
     - path: path/to/file1.ts
       action: modify
     - path: path/to/file2.ts
       action: create
   ---

   # {Task Title}

   ## Context
   {1-2 sentences: what problem this solves, where it fits in the bigger picture}

   ## Files to Modify/Create
   - path/to/file1.ts (modify)
   - path/to/file2.ts (new)

   ## Implementation Details
   {Extracted task description and requirements}

   ## Verification
   {How to test THIS task specifically - commands to run, expected output}
   ```

   **YAML frontmatter fields:**
   - `task`: The task identifier (matches filename without .md)
   - `status`: Always `pending` initially (orchestrator updates to `running`/`done`/`failed`)
   - `depends`: Array of task IDs that must complete before this one (empty array `[]` if no deps)
   - `files`: List of files with path and action (create/modify/delete)

3. Write file to `{STORAGE_ROOT}/tasks/{plan-name}/{NN}-{task-name}.md`

### Phase 5: Generate README.md
Create `{STORAGE_ROOT}/tasks/{plan-name}/README.md`:

```markdown
# {Plan Name}

## Overview
{What is being built and why - extracted from original plan}

## Task Sequence
1. [01-{task-name}.md](./01-{task-name}.md) - {Brief description}
2. [02-{task-name}.md](./02-{task-name}.md) - {Brief description}
...

## Success Criteria
{End-to-end verification: how to confirm the entire implementation worked}

## Dependencies
{External dependencies, prerequisites, or setup requirements}
```

### Phase 6: Update Workflow State (REQUIRED — do not skip)

**This step is critical.** Downstream commands (`/plan:review`, `/plan:start-implementation`) depend on this file to find the plan.

1. Read existing `{STORAGE_ROOT}/workflow-state.json` (or create new file if missing)
2. If a plan with this name already exists in state:
   - Warn: "Plan '{plan-name}' already exists in workflow state with status '{status}'. Overwrite? (y/n)"
   - If yes: Update the entry, reset status to "ready"
   - If no: Abort handoff
3. Add/update entry for this plan:

```json
{
  "plans": {
    "{plan-name}": {
      "path": "tasks/{plan-name}/",
      "status": "ready",
      "handoffAt": "{ISO timestamp}"
    }
  }
}
```

4. **Write the file** to `{STORAGE_ROOT}/workflow-state.json` using the Write tool
5. **Verify** the file exists and contains the plan entry by reading it back

**Important:** Preserve existing plans in the state file. Only add/update the entry for the current plan.

### Phase 7: Summary

1. List all created files with count
2. Verify numbering is sequential
3. **Verify `{STORAGE_ROOT}/workflow-state.json` exists and contains the plan entry**
4. Output summary:
   ```
   ✓ Plan distributed to {STORAGE_ROOT}/tasks/{plan-name}/
   ✓ {N} task files + README.md created
   ✓ Workflow state updated ({STORAGE_ROOT}/workflow-state.json)

   Ready for implementation:
   → {STORAGE_ROOT}/tasks/{plan-name}/README.md

   Next steps:
   1. Run /clear
   2. Run /plan:review
      (auto-detects plan, or shows selector if multiple ready plans)
   ```

**If workflow-state.json was NOT created, stop and fix it before showing the summary.**

## ERROR HANDLING

- **No plan file:** "No active plan found. Create a plan first before distribution."
- **Target directory exists:** "Task files already exist at {STORAGE_ROOT}/tasks/{plan-name}/. Overwrite? (y/n)"
- **Plan exists in workflow state:** "Plan '{plan-name}' already exists in workflow state with status '{status}'. Overwrite? (y/n)"
- **Empty plan sections:** Flag warning but continue with available content

## CONSTRAINTS

- Never modify the original plan file in `.claude/plans/`
- Preserve all technical details from original plan
- Maintain implementation order strictly
- Use absolute minimum of task files while keeping logical coherence
- Always include YAML frontmatter with depends array (even if empty)
