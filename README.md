# claude-code-workflow

Claude Code commands and skills for structured planning and implementation workflows.

## Installation

Symlink to your Claude commands directory:

```bash
ln -s $(pwd)/commands/* ~/.claude/commands/
```

## Structure

```
commands/
  plan/               # Full planning pipeline (see plan/README.md)
                      #   includes discuss.md for requirements discovery
  qol/                # Quality-of-life utilities
skills/
  expert-skill-creator/  # Skill creation guidance
```

## Quick Start

```
/plan:discuss          # Start requirements conversation
# (enter plan mode)   # Claude builds the plan
/plan:handoff         # Convert to task files
/clear
/plan:review          # Technical review
/plan:start-implementation  # Parallel sub-agents
/plan:code-review     # Review commits
```

See `commands/plan/README.md` for full workflow details.
