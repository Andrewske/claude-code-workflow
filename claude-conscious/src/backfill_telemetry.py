#!/usr/bin/env python3
"""One-time backfill of telemetry from historical Claude Code session JSONL files.

Scans all ~/.claude/projects/*/*.jsonl files, extracts telemetry records,
and writes them to ~/.claude/conscious/telemetry/backfill-{date}.jsonl.

No Haiku calls — quality scores are only generated for new sessions.
Historical sessions get telemetry (tool counts, errors, retries, etc.) but
no quality_score, session_topic, or topic_confidence.

Usage:
    python3 backfill_telemetry.py [--limit N] [--project SUBSTRING] [--dry-run]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from parse_session import build_telemetry_record

PROJECTS_DIR = Path.home() / ".claude" / "projects"
TELEMETRY_DIR = Path.home() / ".claude" / "conscious" / "telemetry"


def find_session_files(project_filter=None):
    """Find all JSONL session files, optionally filtered by project name."""
    if not PROJECTS_DIR.exists():
        return []

    files = []
    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        if project_filter and project_filter not in project_dir.name:
            continue
        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            files.append(jsonl_file)
    return files


def load_existing_session_ids():
    """Load session IDs already in telemetry to avoid duplicates."""
    existing = set()
    if not TELEMETRY_DIR.exists():
        return existing
    for telemetry_file in TELEMETRY_DIR.glob("*.jsonl"):
        try:
            with open(telemetry_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        sid = record.get("session_id")
                        if sid:
                            existing.add(sid)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    return existing


def main():
    parser = argparse.ArgumentParser(description="Backfill telemetry from historical sessions")
    parser.add_argument("--limit", type=int, default=0, help="Max sessions to process (0=all)")
    parser.add_argument("--project", type=str, default=None, help="Filter by project name substring")
    parser.add_argument("--dry-run", action="store_true", help="Count files without processing")
    args = parser.parse_args()

    session_files = find_session_files(args.project)
    print(f"Found {len(session_files)} session files")

    if args.dry_run:
        total_size = sum(f.stat().st_size for f in session_files)
        print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
        return

    existing_ids = load_existing_session_ids()
    print(f"Already have {len(existing_ids)} sessions in telemetry")

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = TELEMETRY_DIR / f"backfill-{today}.jsonl"

    processed = 0
    skipped_existing = 0
    skipped_error = 0
    limit = args.limit if args.limit > 0 else len(session_files)

    with open(output_file, "a") as out:
        for i, jsonl_path in enumerate(session_files):
            if processed >= limit:
                break

            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(session_files)} files, {processed} records written")

            record = build_telemetry_record(jsonl_path, source_path=str(jsonl_path))
            if not record:
                skipped_error += 1
                continue

            if record["session_id"] in existing_ids:
                skipped_existing += 1
                continue

            existing_ids.add(record["session_id"])
            out.write(json.dumps(record, separators=(",", ":")) + "\n")
            processed += 1

    print(f"\nBackfill complete:")
    print(f"  Written: {processed} records to {output_file}")
    print(f"  Skipped (already exists): {skipped_existing}")
    print(f"  Skipped (parse error/too large): {skipped_error}")


if __name__ == "__main__":
    main()
