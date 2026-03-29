---
name: rules-manager
description: Create, audit, and manage .claude/rules/ files with path-scoped frontmatter. Use when creating new rules, organizing existing rules, or migrating content from CLAUDE.md to rules. Triggers on "create rule", "add rule", "rules", "path-scoped".
argument-hint: [action] [path-or-topic]
---

# Rules Manager

Create and manage `.claude/rules/` files — path-scoped instructions that load only when Claude works with matching files.

## When to Create a Rule

Rules are better than CLAUDE.md for instructions that:
- Apply only to specific file types (`.ts`, `.py`, `.tsx`, etc.)
- Are domain-specific (API design, testing, security) rather than universal
- Would waste context tokens if loaded in every session

Rules are better than skills when:
- The content is standards/conventions (recognition), not procedures (execution)
- You want it loaded automatically when matching files are opened, not on-demand

## Rule File Structure

Every rule lives at `~/.claude/rules/<name>.md` (user-global) or `<project>/.claude/rules/<name>.md` (project-scoped).

```yaml
---
paths: ["**/*.ts", "**/*.tsx"]
---
- Rule one: imperative, specific, verifiable
- Rule two: one line per rule
```

### CRITICAL: paths: syntax bug

YAML block array syntax is **broken** in user-level rules (GitHub #21858). Always use inline JSON array:

```yaml
# CORRECT — always use this
paths: ["**/*.ts", "**/*.tsx"]

# ALSO WORKS — comma-separated string
paths: "**/*.ts,**/*.tsx"

# BROKEN — do NOT use multi-line YAML arrays
paths:
  - "**/*.ts"
  - "**/*.tsx"
```

### Path Pattern Reference

| Pattern | Matches |
|---------|---------|
| `**/*.ts` | All TypeScript files |
| `src/**/*` | All files under src/ |
| `*.md` | Markdown in project root only |
| `**/*.{ts,tsx}` | Brace expansion for multiple extensions |
| `src/api/**/*.ts` | API files specifically |
| `**/*.test.{ts,tsx}` | All test files |

Rules **without** a `paths:` field load every session (same as CLAUDE.md content).

### Known Limitations
- Rules only trigger on **Read**, not Write — new file creation won't load matching rules
- Instruction budget: ~150 items total across all loaded files (system prompt takes ~50)
- Debug which rules loaded: run `/memory` or check `InstructionsLoaded` hook

## Creating a Rule

When the user asks to create a rule:

1. **Determine scope**: User-global (`~/.claude/rules/`) or project-specific (`.claude/rules/`)
2. **Choose path patterns**: What file types should trigger this rule?
3. **Write concise content**: One line per rule, imperative voice, specific and verifiable
4. **Check for conflicts**: Read existing rules to avoid contradictions
5. **Present for approval**: Show the complete file before writing

### Content Guidelines

- **One line per rule.** No paragraphs, no explanations.
- **Imperative voice.** "Use X" not "Consider using X"
- **Specific and verifiable.** "Use 2-space indentation" not "Format properly"
- **5-10 rules max per file.** More than that loses attention.
- **No rationale.** Claude doesn't need to know why — just what.

## Actions

### `create <topic>` — Create a new rule file
Ask what file types it applies to, write the rule, present for approval.

### `audit` — Audit existing rules
Read all `.claude/rules/*.md` files (both user and project), report:
- Total rules count and estimated token cost
- Rules without path patterns (always-load — are they necessary?)
- Overlapping path patterns between files
- Rules that duplicate CLAUDE.md content
- Rules that are too long or too vague

### `migrate <section>` — Move CLAUDE.md content to a rule
Read CLAUDE.md, identify the specified section, extract it to a path-scoped rule file, and remove it from CLAUDE.md.

### `suggest` — Suggest rules based on project structure
Scan the current project's file types and directory structure. Suggest rules that would be valuable based on:
- Dominant file types (suggest language-specific rules)
- Framework detection (Next.js → server/client component rules)
- Test file presence (suggest testing conventions rule)
- API directory presence (suggest API design rule)

## Common Rule Templates

When creating rules for common topics, start from these templates and customize:

### React/Next.js
```yaml
---
paths: ["**/*.tsx", "**/app/**"]
---
- Default to Server Components; add "use client" only for browser APIs or interactivity
- Never fetch data in Client Components — lift to Server Component or server action
- Use loading.tsx and error.tsx at route segment level
- cn() for conditional classes, never string concatenation
```

### Testing
```yaml
---
paths: ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"]
---
- Test file lives next to source file, not in __tests__/
- One describe per module; test names read as sentences
- Mock at module boundary, never internal implementation
- Assert behavior and output, not internal state
```

### Security
```yaml
---
paths: ["**/*.ts", "**/*.tsx", "**/*.py"]
---
- All secrets from environment variables, never hardcoded
- Validate all user input at API boundary
- Parameterized queries only, never string interpolation into SQL
- Server-only secrets must never appear in Client Component imports
```

### API Design
```yaml
---
paths: ["**/api/**", "**/routes/**"]
---
- Validate input with Zod schema at handler entry
- Return consistent {data, error} response shape
- Include request ID in error responses for debuggability
- Rate-limit all public endpoints
```
