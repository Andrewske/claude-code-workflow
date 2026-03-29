#!/usr/bin/env python3
"""Claude Conscious — Session analysis engine.

Reads compact telemetry records, computes aggregates, and generates
rule-based improvement suggestions.

Usage:
    python3 analyze_sessions.py [--days N] [--baseline] [--metrics]
"""

import argparse
import fnmatch
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
CONSCIOUS_DIR = CLAUDE_DIR / "conscious"
TELEMETRY_DIR = CONSCIOUS_DIR / "telemetry"
SUGGESTIONS_DIR = CONSCIOUS_DIR / "suggestions"
METRICS_DIR = CONSCIOUS_DIR / "metrics"

ALWAYS_ALLOWED_TOOLS = frozenset([
    "Grep", "Glob", "Read", "ToolSearch", "TodoRead", "TodoWrite",
    "Skill", "ListMcpResourcesTool", "ReadMcpResourceTool",
    "NotebookRead",
])

COMPOUND_BASH_PREFIXES = frozenset([
    "git", "npm", "npx", "yarn", "pnpm", "docker", "kubectl",
    "pip", "pip3", "python", "python3", "node", "cargo", "go",
    "make", "rtk", "bun", "gh", "aws", "gcloud", "terraform",
])


# ── Permission matching (adapted from analyze_permissions.py) ──


def load_allow_list():
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


def is_bash_prefix_allowed(prefix, allow_patterns):
    """Check if a bash command prefix is covered by any allow pattern.

    Handles both space-style patterns (Bash(git *)) and colon-style
    patterns (Bash(git:*)) used by Claude Code's permission system.
    """
    parts = prefix.split()
    for pattern in allow_patterns:
        if not (pattern.startswith("Bash(") and pattern.endswith(")")):
            continue
        inner = pattern[5:-1]
        # Handle colon-style patterns: Bash(git:*) means "git" followed by anything
        # The colon acts as a command-name separator in Claude Code permissions
        if ":" in inner:
            colon_cmd = inner.split(":")[0]
            colon_rest = inner[len(colon_cmd) + 1:]
            # "git:*" covers any command starting with "git"
            if colon_rest == "*" and parts and parts[0] == colon_cmd:
                return True
            # Also check fnmatch with the colon replaced by space
            space_inner = colon_cmd + " " + colon_rest
            if fnmatch.fnmatch(prefix, space_inner):
                return True
            if fnmatch.fnmatch(prefix + " anything", space_inner):
                return True
        else:
            # Space-style patterns: Bash(git *)
            if fnmatch.fnmatch(prefix, inner):
                return True
            if fnmatch.fnmatch(prefix + " anything", inner):
                return True
            # Check first word match for compound commands
            if len(parts) >= 2:
                if fnmatch.fnmatch(f"{parts[0]} {parts[1]} anything", inner):
                    return True
    return False


# ── Skill detection ──


def list_installed_skills():
    """List skill names from ~/.claude/skills/*/SKILL.md."""
    skills_dir = CLAUDE_DIR / "skills"
    if not skills_dir.exists():
        return []
    skills = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skills.append(skill_dir.name)
    return skills


# ── Telemetry reading ──


def read_telemetry(days=7):
    """Read all telemetry records from the last N days."""
    records = []
    if not TELEMETRY_DIR.exists():
        return records

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for telemetry_file in sorted(TELEMETRY_DIR.glob("*.jsonl")):
        try:
            with open(telemetry_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        # Filter by timestamp if available
                        ts = record.get("timestamp_start")
                        if ts:
                            try:
                                record_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if record_time < cutoff:
                                    continue
                            except (ValueError, TypeError):
                                pass
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue

    return records


# ── Aggregate computation ──


def compute_aggregates(records):
    """Compute aggregate statistics from telemetry records."""
    if not records:
        return {
            "sessions": 0,
            "total_user_turns": 0,
            "avg_duration_minutes": 0,
            "tool_frequency": {},
            "bash_prefix_frequency": {},
            "error_rate": 0,
            "retry_rate": 0,
            "avg_corrections": 0,
            "cache_hit_rate": 0,
            "skills_used": set(),
            "projects": Counter(),
        }

    total_user_turns = 0
    total_assistant_turns = 0
    total_tool_calls = 0
    total_errors = 0
    total_retries = 0
    total_corrections = 0
    total_cache_creation = 0
    total_cache_read = 0
    total_duration = 0

    tool_freq = Counter()
    bash_prefix_freq = Counter()
    skills_used = set()
    projects = Counter()

    for r in records:
        turns = r.get("turns", {})
        total_user_turns += turns.get("user", 0)
        total_assistant_turns += turns.get("assistant", 0)

        tools = r.get("tools", {})
        for tool, count in tools.items():
            tool_freq[tool] += count
            total_tool_calls += count

        for prefix, count in r.get("bash_command_prefixes", {}).items():
            bash_prefix_freq[prefix] += count

        total_errors += r.get("tool_errors", {}).get("total", 0)
        total_retries += r.get("retries", {}).get("total", 0)
        total_corrections += r.get("corrections", {}).get("count", 0)

        tokens = r.get("tokens", {})
        total_cache_creation += tokens.get("cache_creation_total", 0)
        total_cache_read += tokens.get("cache_read_total", 0)

        total_duration += r.get("duration_seconds", 0)

        for skill in r.get("skills_invoked", []):
            skills_used.add(skill)

        proj = r.get("project")
        if proj:
            projects[proj] += 1

    n = len(records)
    cache_total = total_cache_creation + total_cache_read

    return {
        "sessions": n,
        "total_user_turns": total_user_turns,
        "avg_duration_minutes": (total_duration / n / 60) if n else 0,
        "tool_frequency": dict(tool_freq.most_common()),
        "bash_prefix_frequency": dict(bash_prefix_freq.most_common()),
        "error_rate": (total_errors / total_tool_calls) if total_tool_calls else 0,
        "retry_rate": (total_retries / total_tool_calls) if total_tool_calls else 0,
        "avg_corrections": total_corrections / n if n else 0,
        "cache_hit_rate": (total_cache_read / cache_total) if cache_total else 0,
        "skills_used": skills_used,
        "projects": projects,
    }


# ── Rule suggestion heuristics ──


LANGUAGE_PATTERNS = {
    "tsx": (["**/*.tsx"], ["react", "jsx", "component", "hook", "use client", "use server"]),
    "sql": (["**/*.sql"], ["sql", "postgres", "query", "migration", "schema"]),
    "sh": (["**/*.sh"], ["bash", "shell", "set -e", "#!/bin"]),
    "css": (["**/*.css", "**/*.scss"], ["css", "tailwind", "scss", "styled"]),
    "go": (["**/*.go"], ["golang", "go ", "goroutine", "go run"]),
    "rs": (["**/*.rs"], ["rust", "cargo", "ownership", "borrow"]),
}


def list_existing_rules():
    """List rule file stems from ~/.claude/rules/."""
    rules_dir = CLAUDE_DIR / "rules"
    if not rules_dir.exists():
        return set()
    return {p.stem.lower() for p in rules_dir.glob("*.md")}


def detect_claude_md_rule_candidates():
    """Find language-specific content in CLAUDE.md that should be path-scoped rules."""
    claude_md = CLAUDE_DIR / "CLAUDE.md"
    if not claude_md.exists():
        return []

    content = claude_md.read_text().lower()
    existing = list_existing_rules()
    candidates = []

    for lang, (globs, keywords) in LANGUAGE_PATTERNS.items():
        if lang in existing:
            continue
        hits = sum(1 for kw in keywords if kw in content)
        if hits >= 2:
            candidates.append({
                "lang": lang,
                "hits": hits,
                "globs": globs,
            })
    return candidates


def detect_skill_project_correlations(records, min_cooccurrences=3):
    """Find skills consistently invoked in specific project types."""
    skill_project = defaultdict(Counter)
    for r in records:
        project = (r.get("project") or "").lower()
        for skill in r.get("skills_invoked", []):
            skill_project[skill][project] += 1

    correlations = []
    for skill, proj_counts in skill_project.items():
        for project, count in proj_counts.items():
            if count >= min_cooccurrences:
                correlations.append({
                    "skill": skill,
                    "project": project,
                    "count": count,
                })
    return correlations


def detect_file_extension_errors(records, min_sessions=3, min_errors=5):
    """Find file extensions with clustered errors across sessions."""
    ext_errors = Counter()
    ext_sessions = Counter()
    for r in records:
        for ext, count in r.get("file_extension_errors", {}).items():
            ext_errors[ext] += count
            if count > 0:
                ext_sessions[ext] += 1

    results = []
    existing = list_existing_rules()
    for ext, total in ext_errors.items():
        lang = ext.lstrip(".")
        if lang in existing:
            continue
        if total >= min_errors and ext_sessions[ext] >= min_sessions:
            results.append({"ext": ext, "errors": total, "sessions": ext_sessions[ext]})
    return results


def generate_rule_suggestions(records, make_id, now):
    """Generate rule-category suggestions from telemetry and CLAUDE.md analysis."""
    suggestions = []

    # Heuristic 1: CLAUDE.md content with language-specific instructions lacking rules
    for candidate in detect_claude_md_rule_candidates():
        lang = candidate["lang"]
        globs = candidate["globs"]
        suggestions.append({
            "id": make_id(),
            "created": now,
            "category": "rules",
            "priority": "medium",
            "title": f"Create path-scoped rule for {lang.upper()} files",
            "description": (
                f"CLAUDE.md contains {candidate['hits']} {lang}-related instructions "
                f"that could be scoped to {globs[0]} instead of loading every session."
            ),
            "evidence_count": candidate["hits"],
            "action_type": "create_rule",
            "action_target": str(CLAUDE_DIR / "rules" / f"{lang}.md"),
            "action_value": json.dumps({"paths": globs}),
            "status": "pending",
        })

    # Heuristic 2: Skills consistently invoked in specific projects
    for corr in detect_skill_project_correlations(records):
        suggestions.append({
            "id": make_id(),
            "created": now,
            "category": "rules",
            "priority": "low",
            "title": f"Add /{corr['skill']} to {corr['project']} rules",
            "description": (
                f"Skill '{corr['skill']}' invoked {corr['count']}x in project "
                f"'{corr['project']}'. Consider adding a reminder to project rules."
            ),
            "evidence_count": corr["count"],
            "action_type": "edit_rule",
            "action_target": corr["project"],
            "action_value": f"Use /{corr['skill']} after changes",
            "status": "pending",
        })

    # Heuristic 3: File extension error clustering (needs schema extension)
    for result in detect_file_extension_errors(records):
        ext = result["ext"]
        lang = ext.lstrip(".")
        suggestions.append({
            "id": make_id(),
            "created": now,
            "category": "rules",
            "priority": "high" if result["errors"] >= 10 else "medium",
            "title": f"Recurring errors on {ext} files ({result['errors']} errors)",
            "description": (
                f"{result['errors']} edit/write errors on {ext} files across "
                f"{result['sessions']} sessions. A path-scoped rule may help."
            ),
            "evidence_count": result["errors"],
            "action_type": "create_rule",
            "action_target": str(CLAUDE_DIR / "rules" / f"{lang}.md"),
            "action_value": json.dumps({"paths": [f"**/*{ext}"]}),
            "status": "pending",
        })

    return suggestions


# ── Suggestion generation ──


def generate_suggestions(aggregates, allow_patterns, records=None):
    """Generate rule-based suggestions from aggregates."""
    suggestions = []
    now = datetime.now(timezone.utc).isoformat()
    seq = 0

    def make_id():
        nonlocal seq
        seq += 1
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"sug_{date_str}_{seq:03d}"

    # 1. Permission gaps: bash prefixes >5 times not covered by allow rules
    for prefix, count in aggregates.get("bash_prefix_frequency", {}).items():
        if count < 5:
            continue
        if is_bash_prefix_allowed(prefix, allow_patterns):
            continue
        parts = prefix.split()
        if len(parts) >= 2 and parts[0] in COMPOUND_BASH_PREFIXES:
            rule = f"Bash({parts[0]} {parts[1]} *)"
        else:
            rule = f"Bash({parts[0]} *)"
        suggestions.append({
            "id": make_id(),
            "created": now,
            "category": "permissions",
            "priority": "high" if count >= 20 else "medium",
            "title": f"Add allow rule for '{prefix}'",
            "description": f"Manually approved ~{count} times across recent sessions.",
            "evidence_count": count,
            "action_type": "settings_edit",
            "action_target": str(CLAUDE_DIR / "settings.json"),
            "action_value": rule,
            "status": "pending",
        })

    # 2. Unused skills detection
    installed = set(list_installed_skills())
    used = aggregates.get("skills_used", set())
    unused = sorted(installed - used)
    # Filter out infrastructure/framework skills that aren't directly invoked
    infra_skills = {"gstack", "gstack-upgrade", "connect-chrome", "setup-browser-cookies",
                    "setup-deploy", "guard", "freeze", "unfreeze", "careful", "loop",
                    "schedule", "update-config", "keybindings-help"}
    unused_actionable = [s for s in unused if s not in infra_skills]

    if unused_actionable:
        top_unused = unused_actionable[:5]
        suggestions.append({
            "id": make_id(),
            "created": now,
            "category": "skill_ideas",
            "priority": "low",
            "title": f"{len(unused_actionable)} installed skills never used",
            "description": f"Skills you have but haven't invoked: {', '.join(top_unused)}"
                           + (f" (+{len(unused_actionable) - 5} more)" if len(unused_actionable) > 5 else ""),
            "evidence_count": len(unused_actionable),
            "action_type": "edit_file",
            "action_target": str(CLAUDE_DIR / "CLAUDE.md"),
            "action_value": f"Consider trying: {', '.join(top_unused)}",
            "status": "pending",
        })

    # 3. CLAUDE.md interaction profile update
    if aggregates["sessions"] >= 10:
        top_tools = list(aggregates.get("tool_frequency", {}).items())[:5]
        projects = aggregates.get("projects", {})
        if isinstance(projects, Counter):
            top_projects = projects.most_common(3)
        else:
            top_projects = sorted(projects.items(), key=lambda x: -x[1])[:3]
        avg_corrections = aggregates.get("avg_corrections", 0)
        avg_duration = aggregates.get("avg_duration_minutes", 0)

        profile_lines = []
        if top_projects:
            profile_lines.append(f"Primary projects: {', '.join(p for p, _ in top_projects)}")
        if top_tools:
            profile_lines.append(f"Most-used tools: {', '.join(f'{t} ({c})' for t, c in top_tools)}")
        if avg_duration:
            profile_lines.append(f"Average session: {avg_duration:.0f} minutes")
        if avg_corrections > 1:
            profile_lines.append(f"Correction rate: {avg_corrections:.1f}/session (consider adjusting prompting style)")

        if profile_lines:
            suggestions.append({
                "id": make_id(),
                "created": now,
                "category": "claude_md_updates",
                "priority": "medium",
                "title": "Update interaction profile in CLAUDE.md",
                "description": "Suggested profile based on session analysis:\n" + "\n".join(f"- {l}" for l in profile_lines),
                "evidence_count": aggregates["sessions"],
                "action_type": "edit_file",
                "action_target": str(CLAUDE_DIR / "CLAUDE.md"),
                "action_value": "\n".join(profile_lines),
                "status": "pending",
            })

    # 4. Rule suggestions from telemetry and CLAUDE.md analysis
    if records is not None:
        suggestions.extend(generate_rule_suggestions(records, make_id, now))

    return suggestions


# ── Baseline / Metrics ──


def capture_baseline(aggregates, allow_patterns):
    """Capture a baseline snapshot for future comparison."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = METRICS_DIR / "baseline.json"

    baseline = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sessions_analyzed": aggregates["sessions"],
        "permissions": {
            "allow_rules": len(allow_patterns),
        },
        "efficiency": {
            "avg_tool_error_rate": round(aggregates["error_rate"], 4),
            "avg_retry_rate": round(aggregates["retry_rate"], 4),
            "avg_corrections_per_session": round(aggregates["avg_corrections"], 2),
            "cache_hit_rate": round(aggregates["cache_hit_rate"], 4),
        },
        "coverage": {
            "skills_installed": len(list_installed_skills()),
            "skills_used": len(aggregates["skills_used"]),
            "skills_used_pct": round(
                len(aggregates["skills_used"]) / max(len(list_installed_skills()), 1) * 100, 1
            ),
        },
    }

    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")

    return baseline


def show_metrics(aggregates, allow_patterns):
    """Show comparison table: baseline vs current."""
    baseline_path = METRICS_DIR / "baseline.json"
    if not baseline_path.exists():
        print("No baseline found. Run with --baseline first.")
        return

    with open(baseline_path) as f:
        baseline = json.load(f)

    current_skills_installed = len(list_installed_skills())
    current_skills_used = len(aggregates["skills_used"])

    rows = [
        ("Tool error rate",
         baseline["efficiency"]["avg_tool_error_rate"],
         round(aggregates["error_rate"], 4),
         "lower"),
        ("Retry rate",
         baseline["efficiency"]["avg_retry_rate"],
         round(aggregates["retry_rate"], 4),
         "lower"),
        ("Corrections/session",
         baseline["efficiency"]["avg_corrections_per_session"],
         round(aggregates["avg_corrections"], 2),
         "lower"),
        ("Cache hit rate",
         baseline["efficiency"]["cache_hit_rate"],
         round(aggregates["cache_hit_rate"], 4),
         "higher"),
        ("Allow rules",
         baseline["permissions"]["allow_rules"],
         len(allow_patterns),
         "info"),
        ("Skills used %",
         baseline["coverage"]["skills_used_pct"],
         round(current_skills_used / max(current_skills_installed, 1) * 100, 1),
         "higher"),
    ]

    print(f"\n{'Metric':<25} {'Baseline':>10} {'Current':>10} {'Delta':>10} {'Status':>8}")
    print("-" * 70)

    for name, base_val, curr_val, direction in rows:
        delta = curr_val - base_val
        if direction == "info":
            status = ""
            delta_str = f"{delta:+.0f}" if delta != 0 else "—"
        else:
            if isinstance(base_val, float):
                delta_str = f"{delta:+.4f}"
            else:
                delta_str = f"{delta:+.1f}"

            if direction == "lower":
                status = "better" if delta < 0 else ("worse" if delta > 0 else "same")
            else:
                status = "better" if delta > 0 else ("worse" if delta < 0 else "same")

        if isinstance(base_val, float):
            print(f"{name:<25} {base_val:>10.4f} {curr_val:>10.4f} {delta_str:>10} {status:>8}")
        else:
            print(f"{name:<25} {base_val:>10} {curr_val:>10} {delta_str:>10} {status:>8}")

    print()
    print(f"Baseline captured: {baseline['captured_at'][:10]}")
    print(f"Sessions analyzed: {baseline['sessions_analyzed']} (baseline) / {aggregates['sessions']} (current)")

    # Append to history
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    history_path = METRICS_DIR / "history.jsonl"
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessions": aggregates["sessions"],
        "error_rate": round(aggregates["error_rate"], 4),
        "retry_rate": round(aggregates["retry_rate"], 4),
        "corrections": round(aggregates["avg_corrections"], 2),
        "cache_hit_rate": round(aggregates["cache_hit_rate"], 4),
        "allow_rules": len(allow_patterns),
        "skills_used_pct": round(current_skills_used / max(current_skills_installed, 1) * 100, 1),
    }
    with open(history_path, "a") as f:
        f.write(json.dumps(snapshot, separators=(",", ":")) + "\n")


# ── Main ──


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude Code session telemetry")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    parser.add_argument("--baseline", action="store_true", help="Capture baseline metrics snapshot")
    parser.add_argument("--metrics", action="store_true", help="Show baseline vs current comparison")
    parser.add_argument("--json", action="store_true", help="Output suggestions as JSON")
    args = parser.parse_args()

    # Read all telemetry (use large window for baseline, --days for suggestions)
    if args.baseline:
        records = read_telemetry(days=365)
        print(f"Reading all available telemetry for baseline...")
    else:
        records = read_telemetry(days=args.days)

    if not records:
        print(f"No telemetry records found for the last {args.days} days.")
        print("Run the backfill first: python3 src/backfill_telemetry.py")
        return

    aggregates = compute_aggregates(records)
    allow_patterns = load_allow_list()

    print(f"Analyzed {aggregates['sessions']} sessions")
    print(f"  Avg duration: {aggregates['avg_duration_minutes']:.0f} min")
    print(f"  Error rate: {aggregates['error_rate']:.2%}")
    print(f"  Retry rate: {aggregates['retry_rate']:.2%}")
    print(f"  Avg corrections/session: {aggregates['avg_corrections']:.1f}")
    print(f"  Cache hit rate: {aggregates['cache_hit_rate']:.2%}")

    if args.baseline:
        baseline = capture_baseline(aggregates, allow_patterns)
        print(f"\nBaseline captured to {METRICS_DIR / 'baseline.json'}")
        print(f"  Allow rules: {baseline['permissions']['allow_rules']}")
        print(f"  Skills used: {baseline['coverage']['skills_used']}/{baseline['coverage']['skills_installed']}"
              f" ({baseline['coverage']['skills_used_pct']}%)")
        return

    if args.metrics:
        show_metrics(aggregates, allow_patterns)
        return

    # Generate suggestions
    suggestions = generate_suggestions(aggregates, allow_patterns, records)

    if not suggestions:
        print("\nNo suggestions generated. Everything looks good!")
        return

    # Write to pending.jsonl
    SUGGESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    pending_path = SUGGESTIONS_DIR / "pending.jsonl"

    # Load existing pending suggestions to avoid duplicates
    existing_titles = set()
    if pending_path.exists():
        with open(pending_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing_titles.add(json.loads(line).get("title", ""))
                    except json.JSONDecodeError:
                        pass

    new_count = 0
    with open(pending_path, "a") as f:
        for s in suggestions:
            if s["title"] in existing_titles:
                continue
            f.write(json.dumps(s, separators=(",", ":")) + "\n")
            new_count += 1

    if args.json:
        print(json.dumps(suggestions, indent=2))
    else:
        print(f"\n{new_count} new suggestions generated ({len(suggestions) - new_count} duplicates skipped)")
        for s in suggestions:
            marker = "NEW" if s["title"] not in existing_titles else "DUP"
            print(f"  [{marker}] [{s['priority']}] {s['title']}")
        print(f"\nSuggestions written to {pending_path}")
        print("Review with: /review-suggestions")


if __name__ == "__main__":
    main()
