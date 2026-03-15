#!/usr/bin/env python3
"""Analyze Claude Code session JSONL files to find tool calls that required manual permission approval.

Compares tool_use blocks against current settings.json allow list to identify
which tools/commands are most frequently approved manually. Outputs results
as JSON for easy consumption by the skill.

Usage:
    python3 analyze_permissions.py [--project <project-dir-name>] [--top N]
"""

import json
import os
import re
import sys
import fnmatch
from collections import Counter, defaultdict
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"


def load_allow_list():
    """Load auto-allowed patterns from settings.json and settings.local.json."""
    patterns = []
    for fname in ["settings.json", "settings.local.json"]:
        fpath = CLAUDE_DIR / fname
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text())
                patterns.extend(data.get("permissions", {}).get("allow", []))
            except (json.JSONDecodeError, KeyError):
                pass
    return patterns


ALWAYS_ALLOWED_TOOLS = {
    "Grep", "Glob", "Read", "ToolSearch", "TodoRead", "TodoWrite",
    "Skill", "ListMcpResourcesTool", "ReadMcpResourceTool",
    "NotebookRead",
}


def is_auto_allowed(tool_name, tool_input, allow_patterns):
    """Check if a tool call matches any auto-allowed pattern."""
    # Built-in tools that never require permission
    if tool_name in ALWAYS_ALLOWED_TOOLS:
        return True

    for pattern in allow_patterns:
        # Simple tool name match: "Edit", "Write", "Agent", etc.
        if pattern == tool_name:
            return True

        # Bash command pattern: "Bash(git log *)"
        if pattern.startswith("Bash(") and pattern.endswith(")") and tool_name == "Bash":
            cmd = tool_input.get("command", "")
            inner = pattern[5:-1]  # e.g., "git log *"
            if fnmatch.fnmatch(cmd, inner):
                return True

        # Read/Edit/Write with path pattern: "Read(//tmp/**)"
        for t in ["Read", "Edit", "Write"]:
            if pattern.startswith(f"{t}(") and pattern.endswith(")") and tool_name == t:
                path_pattern = pattern[len(t) + 1:-1]
                file_path = tool_input.get("file_path", "")
                # Convert // prefix to / for matching
                if path_pattern.startswith("//"):
                    path_pattern = path_pattern[1:]
                if fnmatch.fnmatch(file_path, path_pattern):
                    return True

        # MCP tool exact match
        if pattern == tool_name and tool_name.startswith("mcp__"):
            return True

    return False


def extract_tool_uses(jsonl_path):
    """Extract all tool_use blocks from a JSONL session file."""
    tool_uses = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_uses.append({
                                "name": block.get("name", ""),
                                "input": block.get("input", {}),
                            })
                except (json.JSONDecodeError, AttributeError):
                    pass
    except (OSError, IOError):
        pass
    return tool_uses


def analyze_project(project_dir, allow_patterns):
    """Analyze all sessions in a project directory."""
    results = {
        "auto_allowed": Counter(),
        "manual_approved": Counter(),
        "manual_details": defaultdict(list),
    }

    jsonl_files = list(project_dir.glob("*.jsonl"))
    for jsonl_path in jsonl_files:
        tool_uses = extract_tool_uses(jsonl_path)
        for tu in tool_uses:
            name = tu["name"]
            inp = tu["input"]

            if is_auto_allowed(name, inp, allow_patterns):
                results["auto_allowed"][name] += 1
            else:
                if name == "Bash":
                    cmd = inp.get("command", "")
                    # Extract command prefix (first word or first two words for git/npm/etc.)
                    parts = cmd.strip().split()
                    if len(parts) >= 2 and parts[0] in ("git", "npm", "npx", "yarn", "pnpm", "docker", "kubectl", "pip", "pip3", "python", "python3", "node", "cargo", "go", "make", "rtk"):
                        key = f"Bash({parts[0]} {parts[1]})"
                    elif parts:
                        key = f"Bash({parts[0]})"
                    else:
                        key = "Bash(<empty>)"
                    results["manual_approved"][key] += 1
                    results["manual_details"][key].append(cmd[:120])
                elif name in ("Read", "Edit", "Write"):
                    file_path = inp.get("file_path", "")
                    # Group by directory
                    dirname = os.path.dirname(file_path)
                    key = f"{name}({dirname}/)"
                    results["manual_approved"][key] += 1
                else:
                    results["manual_approved"][name] += 1

    return results, len(jsonl_files)


def suggest_rules(manual_approved, threshold=3):
    """Suggest permission rules based on frequency."""
    suggestions = []
    for key, count in manual_approved.most_common():
        if count < threshold:
            continue

        if key.startswith("Bash("):
            inner = key[5:-1]
            parts = inner.split()
            if len(parts) == 2 and parts[0] in ("git", "npm", "npx", "docker", "kubectl", "pip", "pip3", "python", "python3", "node", "cargo", "go", "make", "rtk"):
                rule = f'Bash({parts[0]} {parts[1]} *)'
            else:
                rule = f'Bash({parts[0]} *)'
            suggestions.append({"rule": rule, "count": count, "source": key})
        elif key.startswith(("Read(", "Edit(", "Write(")):
            tool = key.split("(")[0]
            path = key[len(tool) + 1:-1]
            rule = f'{tool}({path}**)'
            suggestions.append({"rule": rule, "count": count, "source": key})
        else:
            suggestions.append({"rule": key, "count": count, "source": key})

    return suggestions


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze Claude Code permission usage")
    parser.add_argument("--project", help="Specific project directory name to analyze")
    parser.add_argument("--top", type=int, default=30, help="Number of top results to show")
    parser.add_argument("--threshold", type=int, default=3, help="Minimum occurrences to suggest a rule")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")
    args = parser.parse_args()

    allow_patterns = load_allow_list()

    if args.project:
        project_dirs = [d for d in PROJECTS_DIR.iterdir() if d.is_dir() and args.project in d.name]
    else:
        project_dirs = [d for d in PROJECTS_DIR.iterdir() if d.is_dir()]

    global_manual = Counter()
    global_auto = Counter()
    per_project = {}
    total_sessions = 0

    for pdir in sorted(project_dirs):
        results, session_count = analyze_project(pdir, allow_patterns)
        total_sessions += session_count
        global_manual += results["manual_approved"]
        global_auto += results["auto_allowed"]

        if results["manual_approved"]:
            per_project[pdir.name] = {
                "sessions": session_count,
                "manual_count": sum(results["manual_approved"].values()),
                "top_manual": results["manual_approved"].most_common(10),
            }

    global_suggestions = suggest_rules(global_manual, args.threshold)

    # Per-project suggestions (tools only used in that project)
    project_suggestions = {}
    for pname, pdata in per_project.items():
        proj_counter = Counter(dict(pdata["top_manual"]))
        proj_only = Counter()
        for key, count in proj_counter.items():
            # If >80% of this tool's usage is in this project, it's project-specific
            if global_manual[key] > 0 and count / global_manual[key] > 0.8:
                proj_only[key] = count
        if proj_only:
            project_suggestions[pname] = suggest_rules(proj_only, args.threshold)

    if args.json:
        output = {
            "total_sessions": total_sessions,
            "total_auto_allowed": sum(global_auto.values()),
            "total_manual_approved": sum(global_manual.values()),
            "global_suggestions": global_suggestions[:args.top],
            "project_suggestions": project_suggestions,
            "top_manual_by_frequency": global_manual.most_common(args.top),
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"# Permission Analysis Report")
        print(f"")
        print(f"- **Sessions analyzed**: {total_sessions}")
        print(f"- **Auto-allowed calls**: {sum(global_auto.values()):,}")
        print(f"- **Manually approved calls**: {sum(global_manual.values()):,}")
        print(f"")
        print(f"## Top Manually Approved (Global)")
        print(f"")
        print(f"| Count | Tool/Command | Suggested Rule |")
        print(f"|------:|-------------|---------------|")
        for s in global_suggestions[:args.top]:
            print(f"| {s['count']:,} | `{s['source']}` | `{s['rule']}` |")

        if project_suggestions:
            print(f"")
            print(f"## Project-Specific Suggestions")
            print(f"")
            for pname, suggestions in project_suggestions.items():
                if suggestions:
                    print(f"### {pname}")
                    print(f"")
                    print(f"| Count | Tool/Command | Suggested Rule |")
                    print(f"|------:|-------------|---------------|")
                    for s in suggestions:
                        print(f"| {s['count']:,} | `{s['source']}` | `{s['rule']}` |")
                    print(f"")

        # Show current allow list for reference
        print(f"")
        print(f"## Current Allow List ({len(allow_patterns)} rules)")
        print(f"")
        for p in allow_patterns:
            print(f"- `{p}`")


if __name__ == "__main__":
    main()
