#!/usr/bin/env python3
"""Find and optionally delete junk Claude Code sessions created by Stop hooks.

Two known sources:
  1. Scoring sessions — conscious_hook.py previously used `claude -p` for
     quality scoring, creating recursive sessions.
  2. Summarizer sessions — episodic-memory plugin uses `claude -p` (via
     claude-agent-sdk `query()`) to generate conversation summaries.

Both produce sessions where the only user message is an automated prompt,
triggering Stop hooks again and polluting the conversation tracker dashboard.

Usage:
    cleanup-scoring-sessions.py          # interactive: find + prompt to delete
    cleanup-scoring-sessions.py --dry-run  # just list, don't prompt
    cleanup-scoring-sessions.py --yes      # delete without prompting
"""

import argparse
import json
import sys
from pathlib import Path

JUNK_MARKERS = [
    "You are scoring a Claude Code session",
    "This summary will be shown in a list",
]


def find_junk_sessions(projects_dir):
    """Find session files that are junk-only (no real user messages)."""
    junk_files = []
    for jsonl_path in projects_dir.rglob("*.jsonl"):
        try:
            lines = jsonl_path.read_text().strip().split("\n")
            matched_marker = None
            has_real_user_messages = False
            for line in lines:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("type") == "user":
                    content = record.get("message", {}).get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            str(b.get("text", ""))
                            for b in content
                            if isinstance(b, dict)
                        )
                    content_str = str(content)
                    for marker in JUNK_MARKERS:
                        if marker in content_str:
                            matched_marker = marker
                            break
                    else:
                        if content_str.strip():
                            has_real_user_messages = True

            if matched_marker and not has_real_user_messages:
                junk_files.append((jsonl_path, matched_marker))
        except Exception:
            continue
    return junk_files


def main():
    parser = argparse.ArgumentParser(description="Clean up episodic-memory summarizer session logs")
    parser.add_argument("--dry-run", action="store_true", help="List files without deleting")
    parser.add_argument("--yes", "-y", action="store_true", help="Delete without prompting")
    args = parser.parse_args()

    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        print("No projects directory found at", projects_dir)
        sys.exit(1)

    print("Scanning for junk sessions (scoring + summarizer)...")
    results = find_junk_sessions(projects_dir)

    if not results:
        print("No junk sessions found.")
        sys.exit(0)

    paths = [f for f, _ in results]
    total_bytes = sum(f.stat().st_size for f in paths)
    total_mb = total_bytes / (1024 * 1024)
    total_chars = sum(len(f.read_text()) for f in paths)
    total_tokens = total_chars // 4

    # Count by type
    type_counts: dict[str, int] = {}
    for _, marker in results:
        label = "scoring" if "scoring" in marker.lower() else "summarizer"
        type_counts[label] = type_counts.get(label, 0) + 1
    breakdown = ", ".join(f"{v} {k}" for k, v in type_counts.items())
    print(f"Found {len(results)} junk sessions ({breakdown}) — {total_mb:.1f} MB, ~{total_tokens:,} tokens")

    if args.dry_run:
        for f, marker in results:
            label = "scoring" if "scoring" in marker.lower() else "summarizer"
            chars = len(f.read_text())
            print(f"  [{label}]  {f}  (~{chars // 4:,} tokens)")
        sys.exit(0)

    if not args.yes:
        answer = input("Delete all? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    deleted = 0
    for f in paths:
        try:
            f.unlink()
            deleted += 1
        except OSError as e:
            print(f"  Failed to delete {f}: {e}", file=sys.stderr)

    print(f"Deleted {deleted}/{len(results)} files ({total_mb:.1f} MB freed)")


if __name__ == "__main__":
    main()
