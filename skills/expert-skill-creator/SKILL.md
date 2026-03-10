---
name: creating-skills
description: "Expert guidance for creating high-quality Claude Code skills. Covers generic skills (utilities, domain knowledge, workflows) and project-specific skills (architecture docs, debugging playbooks, codebase navigation). Use when creating a new skill, improving an existing skill, or learning skill best practices. Triggers on 'create a skill', 'build a skill', 'make a skill', 'skill for my project', 'document my architecture as a skill', 'improve this skill', or 'skill best practices'."
---

# Expert Skill Creator

Create high-quality Claude Code skills that follow community best practices.

## Core Principles

1. **Claude is smart** - Only include what Claude doesn't already know
2. **Context is precious** - Every token competes for attention
3. **Progressive disclosure** - Load details only when needed
4. **Description is discovery** - The description determines when skills trigger

## Skill Creation Workflow

### Step 1: Determine Skill Type

Ask the user what kind of skill they want to create:

| Type | Use Case | Template |
|------|----------|----------|
| **Simple Utility** | Single-purpose tools, converters | [templates/simple-utility/](templates/simple-utility/) |
| **Domain Knowledge** | Company data, schemas, APIs | [templates/domain-knowledge/](templates/domain-knowledge/) |
| **Project Knowledge** | Architecture, debugging, codebase | [templates/project-knowledge/](templates/project-knowledge/) |
| **Complex Workflow** | Multi-step processes, validation | [templates/complex-workflow/](templates/complex-workflow/) |

### Step 2: Gather Requirements

**For Generic Skills**, ask:
1. What specific task does this skill help with?
2. What trigger phrases should activate it?
3. Are there scripts needed for reliability?
4. What reference material should be included?

**For Project-Specific Skills**, ask:
1. What is the project's tech stack?
2. What are the main components/services?
3. What are common bugs or issues?
4. What debugging workflows exist?

See [reference/gathering-requirements.md](reference/gathering-requirements.md) for detailed questions.

### Step 3: Initialize the Skill

Run the initialization script:

```bash
python scripts/init_skill.py <skill-name> --type <type> --path <output-dir>
```

Types: `simple`, `domain`, `project`, `workflow`

### Step 4: Write the Description

**This is the most critical step.** The description determines skill discovery.

Requirements:
- Third person voice (not "I" or "you")
- Include specific capabilities
- Include trigger phrases/contexts
- List relevant file types or keywords
- Under 1024 characters

See [reference/description-examples.md](reference/description-examples.md) for patterns.

### Step 5: Write SKILL.md Body

Keep under 500 lines. Structure:

```markdown
# [Skill Name]

## Quick Start
[Minimal working example - 5-10 lines]

## Workflows
[Main procedures with script references]

## Quick Reference
[Tables, commands, key info]

## Deep Dives
[Links to reference files]

## Dependencies
[Required packages]
```

See [reference/writing-instructions.md](reference/writing-instructions.md) for guidelines.

### Step 6: Create Reference Files

For content that:
- Is only needed sometimes
- Exceeds 100 lines
- Covers specific sub-topics

Organize by domain, not by file type. See [reference/progressive-disclosure.md](reference/progressive-disclosure.md).

### Step 7: Add Scripts (If Needed)

Include scripts when:
- Same code is written repeatedly
- Deterministic reliability needed
- Complex validation required

Scripts should handle errors explicitly, not punt to Claude.

### Step 8: Validate and Test

```bash
python scripts/validate_skill.py <skill-directory>
```

Then test with fresh Claude session:
1. Does it trigger on expected phrases?
2. Does Claude find the right information?
3. Are reference files discovered when needed?

### Step 9: Package for Distribution

```bash
python scripts/package_skill.py <skill-directory> [output-dir]
```

Creates `.skill` file (zip with proper structure).

## Reference Documentation

- [Description Examples](reference/description-examples.md) - Good and bad descriptions
- [Writing Instructions](reference/writing-instructions.md) - How to write SKILL.md
- [Progressive Disclosure](reference/progressive-disclosure.md) - Structuring large skills
- [Anti-Patterns](reference/anti-patterns.md) - Common mistakes to avoid
- [Gathering Requirements](reference/gathering-requirements.md) - Questions to ask
- [Project Knowledge Patterns](reference/project-knowledge-patterns.md) - For project-specific skills

## Maintaining Skills

Skills need updates as projects evolve. Use these commands:

### Update Skill (Git-Aware)
```
/project:update-skill                     # Check last 10 commits
/project:update-skill auth system changed # Focus on specific area
/project:update-skill full audit          # Comprehensive review
```

### Capture Error Pattern
```
/project:capture-error                    # Add error we just debugged
```

### Audit Script
```bash
python scripts/audit_skill.py --commits 10   # Check recent changes
python scripts/audit_skill.py --full         # Full audit
```

### Best Practices for Maintenance
- **Capture as you go**: When Claude solves a tricky bug, immediately add it to the skill
- **Review on architecture changes**: Major refactors warrant skill updates
- **Avoid volatile info**: Don't include version numbers, dates, team members
- **Commit skill changes**: Include in PRs when relevant code changes

---

## Quick Validation Checklist

Before finalizing any skill:

- [ ] Description is specific with trigger phrases
- [ ] Description is in third person
- [ ] SKILL.md under 500 lines
- [ ] Reference files one level deep from SKILL.md
- [ ] All internal links work
- [ ] Scripts tested and executable
- [ ] Forward slashes in all paths
- [ ] No generic info Claude already knows
- [ ] No time-sensitive information
