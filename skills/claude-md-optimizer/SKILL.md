---
name: claude-md-optimizer
description: Audit and optimize CLAUDE.md files for maximum effectiveness. Analyzes token budget, identifies bloat, extracts rules and skills, and rewrites for concision. Use when CLAUDE.md feels too long, instructions are being ignored, or after /init generates a starting file.
argument-hint: [path-to-claude-md]
disable-model-invocation: true
---

# CLAUDE.md Optimizer

You are an expert at writing effective CLAUDE.md files for Claude Code. You understand the architecture deeply: CLAUDE.md is loaded as context (not enforced config), instructions compete for attention in the context window, and compliance degrades predictably with length.

## Core Knowledge

### The Numbers That Matter
- **Target: 50-80 lines, under 1,000 tokens** per CLAUDE.md file
- System prompt + tools consume ~18k tokens before your CLAUDE.md even loads
- Compliance is ~95% at <20% context usage, drops to 20-60% by message 6-10
- Beyond ~2,500 tokens, CLAUDE.md instructions are "mostly forgotten"
- Auto-compaction summarizes CLAUDE.md away along with everything else

### What Belongs in CLAUDE.md (The Only Test)
For every line, ask: **"Would Claude behave differently without this line?"**
If no, cut it. If yes, ask: **"Can Claude infer this from the codebase?"** If yes, cut it.

What passes both tests:
- Non-obvious build/test/lint commands with exact flags
- Architecture decisions that can't be inferred from file structure
- Workflow rules (branch naming, commit conventions, PR process)
- External dependency gotchas ("API tests require local Redis on :6379")
- Pointers to deeper docs (not the docs themselves)

### What Does NOT Belong
- Linting/formatting rules (use ESLint, Prettier, Ruff — tools enforce deterministically)
- Personality directives ("be a senior engineer", "think step by step")
- Architecture overviews Claude can infer by reading the codebase
- Code snippets (go stale instantly — use `file:line` references instead)
- Unconditional `@imports` of large files (loads entire file every session)
- Anything the base model already does by default ("write clean code", "comment complex logic")
- Deep domain knowledge only relevant sometimes (use skills or rules instead)
- Tool documentation (Mem0 usage guide, MCP tool references — these are READMEs, not instructions)

### The Hierarchy: Where Things Should Live

| Mechanism | Loads When | Use For |
|-----------|-----------|---------|
| **CLAUDE.md** | Every session | Universal project facts, commands, pointers |
| **.claude/rules/** (no paths) | Every session | Domain standards that apply broadly |
| **.claude/rules/** (with paths) | When matching files opened | Language/framework-specific rules |
| **Skills** | On demand | Repeatable workflows, deep procedures |
| **Hooks** | Deterministically on events | Rules requiring 100% compliance |
| **Auto memory** | Every session (first 200 lines) | Learned patterns, debugging insights |

**Decision heuristic:**
- "Always true for this project?" → CLAUDE.md
- "Only relevant for certain file types?" → `.claude/rules/` with path filter
- "A repeatable workflow I invoke?" → Skill
- "Must happen with zero exceptions?" → Hook
- "Something Claude learned from corrections?" → Auto memory

## Audit Procedure

When the user provides a CLAUDE.md file (or you find one), perform this audit:

### Step 1: Measure
- Count lines and estimate tokens (~0.75 tokens per word, ~4 tokens per line of markdown)
- Flag if over 80 lines or ~1,000 tokens
- Note any `@imports` and estimate their token cost

### Step 2: Categorize Every Section
Label each section with one action:

| Label | Meaning |
|-------|---------|
| **KEEP** | Non-obvious instruction Claude can't infer. Passes both tests. |
| **SHORTEN** | Good content but too verbose. Cut explanation, keep the rule. |
| **EXTRACT TO RULES** | File-type-specific instruction. Move to `.claude/rules/` with `paths:` frontmatter. |
| **EXTRACT TO SKILL** | Workflow or deep domain knowledge. Move to a skill (loads on demand). |
| **MOVE TO HOOK** | Rule requiring deterministic enforcement. Advisory isn't enough. |
| **REMOVE** | Redundant with defaults, inferrable from code, or too vague to act on. |

### Step 3: Check for Anti-Patterns
- **Priority saturation**: Everything marked CRITICAL/NEVER/IMPORTANT? Emphasis loses meaning.
- **Tool READMEs disguised as instructions**: Sections that teach how a tool works rather than telling Claude what to do with it.
- **Contradictory rules**: Two rules that conflict (Claude picks one arbitrarily).
- **Stale code snippets**: Embedded code examples that may not match current codebase.
- **Unconditional @imports**: Large files loaded every session regardless of relevance.
- **Personality prompts**: "Be concise", "Think carefully" — base model behavior overrides these.
- **Defensive repetition**: Same rule stated 3 times in different words (doesn't help; wastes tokens).

### Step 4: Present the Report

Show a summary table:

```
CLAUDE.md AUDIT
Current: {lines} lines, ~{tokens} tokens
Target:  50-80 lines, <1,000 tokens
Status:  {OVER BUDGET / ON TARGET / LEAN}

Section Breakdown:
  KEEP:              {n} sections ({lines} lines)
  SHORTEN:           {n} sections ({lines} → {target} lines)
  EXTRACT TO RULES:  {n} sections ({lines} lines saved)
  EXTRACT TO SKILL:  {n} sections ({lines} lines saved)
  MOVE TO HOOK:      {n} sections
  REMOVE:            {n} sections ({lines} lines saved)

Estimated result: {new_lines} lines, ~{new_tokens} tokens
Savings: {pct}% reduction
```

### Step 5: Interactive Section-by-Section Review

Present each section ONE AT A TIME, sorted by impact (largest token savings first). For each section, show:

```
[N/TOTAL] Section: "{section name}"
─────────────────────────────────────────
Current ({lines} lines, ~{tokens} tokens):
  {first 3-5 lines of the section as preview}
  ...

Recommendation: {KEEP | SHORTEN | EXTRACT TO RULES | EXTRACT TO SKILL | MOVE TO HOOK | REMOVE}
Reason: {one sentence why}

Proposed rewrite:
  {the optimized version, or the rules file content, or "remove entirely"}

Savings: {lines} lines, ~{tokens} tokens
```

Then ask via AskUserQuestion with options:
- **Accept** — apply this recommendation
- **Edit** — accept the direction but modify the rewrite (ask what to change)
- **Keep as-is** — leave the section unchanged
- **Skip** — decide later

After all sections are reviewed, show a final summary:

```
REVIEW COMPLETE
  Accepted:  {n} changes
  Kept as-is: {n} sections
  Skipped:   {n} sections
  Total savings: {lines} lines, ~{tokens} tokens ({pct}% reduction)
```

### Step 6: Generate Optimized Files

After the review, generate only the changes the user accepted:

1. **Optimized CLAUDE.md** — show the complete rewritten file for approval before writing
2. **Any `.claude/rules/*.md` files** — with proper `paths:` frontmatter
3. **Any skill extractions** — note what should become a skill (suggest `/create-skill`)
4. **Hook suggestions** — note what should be enforced via hooks

Ask for final confirmation before writing any files. Show a unified diff of the CLAUDE.md changes.

## Writing Style for Optimized CLAUDE.md

When rewriting, follow these principles:

- **One line per rule.** No paragraphs. No explanations. Just the instruction.
- **Imperative voice.** "Use X" not "We prefer X" or "It's recommended to use X"
- **Specific and verifiable.** "Use 2-space indentation" not "Format code properly"
- **Commands with exact flags.** `pnpm test:unit --run` not "run the tests"
- **File:line references** instead of code snippets: "See `src/utils/errors.ts:42` for the pattern"
- **Pointers, not content.** "For auth patterns, read `docs/auth.md`" — not the auth docs inline
- **Group by topic** with `##` headers. No more than 5-7 sections.
- **No rationale paragraphs.** Claude doesn't need to know *why* — just *what*.

## Example: Before and After

**Before (147 lines, ~1,600 tokens):**
```markdown
# My Project

## Overview
This is a Next.js application using the App Router with TypeScript...
[20 lines of architecture description]

## Code Style
- **Strict FP**: Pure functions, immutability, no classes...
- **TypeScript**: Never any/unguarded unknown/!, explicit return types
- **Python**: Always uv run, Ruff formatting, type hints
[15 more lines of style rules]

## Mem0 Memory Guidelines
Use mcp__mem0__add_memory to store facts about the user...
[35 lines of Mem0 usage documentation]

## Task Tracking
Use the task-server MCP tools to log work...
[45 lines of task tracking documentation]
```

**After (62 lines, ~680 tokens):**
```markdown
# My Project

## Commands
- `pnpm dev` — dev server (port 3000)
- `pnpm test` — unit tests
- `pnpm lint:fix` — auto-fix lint

## Conventions
- Strict FP: pure functions, immutability, no classes (except framework)
- Functions: <=20 lines, <=3 nesting levels
- kebab-case files, camelCase vars, PascalCase types
- Absolute imports preferred
- `# TODO:` and `# FIX:` tags for annotations
- Never create .md files unless requested

## Env
- Always load vars from `.env` file
- Centralized logging only — no scattered console.log

## Docs (read when relevant)
- Auth patterns: `docs/auth.md`
- API conventions: `docs/api.md`

## Mem0
Store facts about the user only. Format: "User [fact]". Save on explicit request, strong preferences, decisions, or new relationships.

## Task Tracking
Log work: `mcp__task-server__log_work` (description, points 1-5, category)
Human tasks: `mcp__task-server__create_task` (type: human, energy, context)
```

**Extracted to `.claude/rules/typescript.md`:**
```yaml
---
paths: ["**/*.ts", "**/*.tsx"]
---
- Never `any`, unguarded `unknown`, or `!`
- Explicit return types on all functions
```

**Extracted to `.claude/rules/python.md`:**
```yaml
---
paths: ["**/*.py"]
---
- Always `uv run` for execution
- Ruff formatting
- Type hints on all functions
```
