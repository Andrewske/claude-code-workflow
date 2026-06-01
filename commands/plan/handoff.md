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

Resolve the storage location via the `kg-plan.sh` helper (see `commands/plan/README.md`, Storage section).

1. Run `~/.claude/scripts/kg-plan.sh resolve`.
   - **On success:** read `REPO` and `SLUG` from the output. The `{slug}` is the implementation plan's identity (it ties to the Linear ticket), **not** the Claude plan-file name.
   - **On non-zero exit** (branch has no `<team>-<num>-` ticket, detached HEAD, or no origin): every plan must map to a Linear ticket. Try a Linear lookup for the current branch; if that fails, ask the user for the `{repo}` and the ticket `{slug}` (`<team>-<num>-<title>`). Do not invent a slug from the plan-file name.
2. Create the target via `~/.claude/scripts/kg-plan.sh create-todo {repo} {slug}`. It prints the path `{KG_ROOT}/plans/{repo}/todo/{slug}/`.
   - **If it exits non-zero with `EXISTS={status}`:** a plan for this slug already lives under `{status}/`. Ask: "Plan '{slug}' already exists under {status}/. Overwrite? (y/n)"
     - If yes and `{status}` is `todo`: remove the existing `todo/{slug}/` contents and recreate.
     - If yes and `{status}` is `doing`/`done`: warn this plan is already in progress; only proceed if the user confirms re-handoff (move it back to `todo` first via `kg-plan.sh move`).
     - If no: abort handoff.

Print the resolved target path.

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

3. Write file to `{PLAN_DIR}/{NN}-{task-name}.md` (where `{PLAN_DIR}` is the `create-todo` path from Phase 2, i.e. `{KG_ROOT}/plans/{repo}/todo/{slug}/`)

### Phase 5: Generate README.md
Create `{PLAN_DIR}/README.md`:

```markdown
---
slug: {slug}
linear: {LINEAR_ID}
repo: {repo}
initiative:            # optional link to a KB initiative (initiatives/<slug>); leave blank for now
---

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

### Phase 6: Commit the Plan to the kg Repo (REQUIRED — do not skip)

The plan folder's location under `todo/` is its status. Committing it records the handoff in `kg` git history (there is no `workflow-state.json`).

1. `git -C ~/dev/kg add plans/{repo}/todo/{slug}`
2. `git -C ~/dev/kg commit -m "plan: add {slug} (todo)"`
3. **Verify** the commit landed: `git -C ~/dev/kg log --oneline -1` shows the `plan: add {slug}` entry.

### Phase 7: Summary

1. List all created files with count
2. Verify numbering is sequential
3. **Verify the `plan: add {slug} (todo)` commit exists in `~/dev/kg`**
4. Output summary:
   ```
   ✓ Plan distributed to {PLAN_DIR}
   ✓ {N} task files + README.md created
   ✓ Committed to kg (plan: add {slug} (todo))

   Ready for implementation:
   → {PLAN_DIR}/README.md

   Next steps:
   1. Run /clear
   2. Run /plan:review
      (auto-detects plan from your branch, or shows a selector)
   ```

**If the kg commit did NOT land, stop and fix it before showing the summary.**

## ERROR HANDLING

- **No plan file:** "No active plan found. Create a plan first before distribution."
- **No ticket-bearing branch:** "Branch has no Linear ticket pattern. Provide the repo and ticket slug (`<team>-<num>-<title>`)."
- **Plan already exists** (`create-todo` reports `EXISTS={status}`): "Plan '{slug}' already exists under {status}/. Overwrite? (y/n)"
- **Empty plan sections:** Flag warning but continue with available content

## CONSTRAINTS

- Never modify the original plan file in `.claude/plans/`
- Preserve all technical details from original plan
- Maintain implementation order strictly
- Use absolute minimum of task files while keeping logical coherence
- Always include YAML frontmatter with depends array (even if empty)
