#!/usr/bin/env python3
"""Find and optionally delete recursive scoring-only Claude Code sessions.

The conscious_hook.py Stop hook previously used `claude -p` for quality
scoring, which created new sessions that triggered the hook again — a
recursive loop producing thousands of junk conversation logs.

This script identifies those sessions (where the only user message is
the scoring prompt) and prompts before deleting.

Usage:
    cleanup-scoring-sessions.py          # interactive: find + prompt to delete
    cleanup-scoring-sessions.py --dry-run  # just list, don't prompt
    cleanup-scoring-sessions.py --yes      # delete without prompting
"""

import argparse
import json
import sys
from pathlib import Path

SCORING_MARKER = "You are scoring a Claude Code session"


def find_scoring_sessions(projects_dir):
    """Find session files that are scoring-only (no real user messages)."""
    scoring_files = []
    for jsonl_path in projects_dir.rglob("*.jsonl"):
        try:
            lines = jsonl_path.read_text().strip().split("\n")
            has_scoring_prompt_as_user = False
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
                    if SCORING_MARKER in str(content):
                        has_scoring_prompt_as_user = True
                    elif isinstance(content, str) and len(content.strip()) > 0:
                        has_real_user_messages = True

            if has_scoring_prompt_as_user and not has_real_user_messages:
                scoring_files.append(jsonl_path)
        except Exception:
            continue
    return scoring_files


def main():
    parser = argparse.ArgumentParser(description="Clean up recursive scoring session logs")
    parser.add_argument("--dry-run", action="store_true", help="List files without deleting")
    parser.add_argument("--yes", "-y", action="store_true", help="Delete without prompting")
    args = parser.parse_args()

    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        print("No projects directory found at", projects_dir)
        sys.exit(1)

    print("Scanning for scoring-only sessions...")
    files = find_scoring_sessions(projects_dir)

    if not files:
        print("No scoring-only sessions found.")
        sys.exit(0)

    total_bytes = sum(f.stat().st_size for f in files)
    total_mb = total_bytes / (1024 * 1024)
    print(f"Found {len(files)} scoring-only sessions ({total_mb:.1f} MB)")

    if args.dry_run:
        for f in files:
            print(f"  {f}")
        sys.exit(0)

    if not args.yes:
        answer = input("Delete all? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    deleted = 0
    for f in files:
        try:
            f.unlink()
            deleted += 1
        except OSError as e:
            print(f"  Failed to delete {f}: {e}", file=sys.stderr)

    print(f"Deleted {deleted}/{len(files)} files ({total_mb:.1f} MB freed)")


if __name__ == "__main__":
    main()
