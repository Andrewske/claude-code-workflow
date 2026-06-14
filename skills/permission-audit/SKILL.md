---
name: permission-audit
description: "Analyze Claude Code session logs to find frequently manually-approved tool calls and suggest permission rule changes. Scans JSONL session files across all projects, compares tool usage against the current allow list, and recommends global and per-project settings changes to reduce permission prompts. Use when asked to audit permissions, reduce permission prompts, optimize settings, or review which tools need approval. Triggers on: 'audit permissions', 'reduce prompts', 'permission analysis', 'optimize permissions', 'what am I approving', 'settings audit'."
---

# Permission Audit

Analyze Claude Code session history to reduce manual permission approvals.

## Workflow

### Step 1: Run the analysis script

```bash
python3 ~/.claude/skills/permission-audit/scripts/analyze_permissions.py --top 20
```

Options:
- `--project <name>` — filter to a specific project directory name (substring match)
- `--top N` — show top N results (default 30)
- `--threshold N` — minimum occurrences to suggest a rule (default 3)
- `--json` — output raw JSON for programmatic use

### Step 2: Interpret results

The script compares every `tool_use` block in session JSONL files against the current `~/.claude/settings.json` and `~/.claude/settings.local.json` allow lists.

- **Auto-allowed**: matched an existing allow rule or is a built-in tool (Read, Grep, Glob, etc.)
- **Manually approved**: required user confirmation — these are candidates for new allow rules

### Step 3: Suggest changes

Based on the report, suggest concrete edits to:

1. **Global settings** (`~/.claude/settings.json`) — for tools used across many projects
2. **Per-project settings** (`<project-dir>/.claude/settings.json`) — for tools only used in one project

#### Rule format reference

| Pattern | Matches |
|---------|---------|
| `"Edit"` | All Edit calls |
| `"Bash(npm test *)"` | Bash commands starting with `npm test` |
| `"Read(//tmp/**)"` | Read calls for paths under `/tmp/` |
| `"mcp__server__tool"` | Specific MCP tool call |

#### Safety rules

**HARD RULE — push must always ask.** Never suggest any allow pattern that could shadow these ask rules:
- `Bash(git push *)`, `Bash(git push)`
- `Bash(gh pr create *)`, `Bash(gh pr merge *)`, `Bash(gh pr close *)`, `Bash(gh pr edit *)`, `Bash(gh pr ready *)`

This means **never suggest umbrella patterns**:
- ❌ `Bash(gh *)` — shadows `gh pr create`, `gh pr merge`, etc.
- ❌ `Bash(git *)` — shadows `git push`
- ❌ `Bash(/usr/bin/git *)`, `Bash(git -C * push *)` — backdoor paths to push
- ✅ `Bash(gh pr view *)`, `Bash(gh pr list *)`, `Bash(gh issue list *)` — specific read subcommands only

**Shell-execution wrappers are backdoors.** `Bash(bash *)`, `Bash(eval *)`, `Bash(source *)`, `Bash(sh -c *)`, `Bash(codex *)`, `Bash(claude *)` can run `git push` indirectly. Flag this when suggesting; do not suggest umbrella shell wrappers without explicit acknowledgment.

**Other destructive operations to keep in `"ask"`:**
- `Bash(rm *)`, `Bash(rm -*)`
- `Bash(git reset *)`, `Bash(git clean *)`
- `Bash(git push --force*)`, `Bash(git push -f*)`
- MCP write operations that affect shared state (Slack messages, public issue creation, dashboard mutations)

**Before suggesting any new rule, check:** does it match a forbidden pattern listed above? If yes, drop it from suggestions and tell the user why.

### Step 4: Apply changes

Present the suggested settings changes as a diff. Ask the user to confirm before applying. Edit `~/.claude/settings.json` for global rules or create/edit per-project `settings.local.json` files.

## How it works

Session data lives in `~/.claude/projects/<project-name>/<session-id>.jsonl`. Each line is a JSON object. The script:

1. Walks all JSONL files across all project directories
2. Extracts `tool_use` blocks (tool name + input)
3. Checks each against the current allow list using fnmatch
4. Groups unapproved calls by tool/command prefix
5. Identifies project-specific vs global patterns (>80% usage in one project = project-specific)

No session content enters the context window — Python processes everything on disk.
