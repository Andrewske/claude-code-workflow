#!/usr/bin/env python3
"""Claude Conscious — Stop hook for session telemetry and quality scoring.

Registered as a Stop hook in Claude Code settings. Runs after every Claude
response but rate-limits itself: only extracts telemetry once per session
per calendar day (UTC). Multi-day sessions get daily checkpoints.

Uses `claude -p --model haiku` for quality scoring (no API key management).

Input (stdin): JSON with session_id, transcript_path, cwd, etc.
Output (stdout): JSON with optional systemMessage for display.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve src/ directory for parse_session import
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from parse_session import build_telemetry_record

TELEMETRY_DIR = Path.home() / ".claude" / "conscious" / "telemetry"
QUALITY_SCORE_PROMPT = """\
You are scoring a Claude Code session. Return ONLY valid JSON, no other text.

Session summary:
- Project: {project}
- Duration: {duration_minutes:.0f} minutes
- Turns: {user_turns} user, {assistant_turns} assistant
- Tools used: {tools_summary}
- Tool errors: {error_count}
- User corrections: {correction_count}
- Retries (consecutive same-tool): {retry_count}

Scoring rubric:
- Task completion (0-3): Did Claude finish what was asked?
- Efficiency (0-2): Reasonable turns/tokens for the task?
- Friction (0-3): Corrections, retries, permission prompts?
- Correctness (0-2): Tool errors, user rejections?

Return JSON: {{"quality_score": <1-10>, "task_completion": <0-3>, "efficiency": <0-2>, "friction": <0-3>, "correctness": <0-2>, "session_topic": "<debugging|feature|review|planning|infrastructure|learning|other>", "topic_confidence": <0.0-1.0>}}"""


def already_checkpointed(session_id):
    """Check if this session has already been recorded today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    telemetry_file = TELEMETRY_DIR / f"{today}.jsonl"
    if not telemetry_file.exists():
        return False
    try:
        with open(telemetry_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("session_id") == session_id:
                        return True
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return False


def call_haiku_for_scoring(record):
    """Call claude CLI with haiku model for quality scoring.

    Returns dict with quality_score, session_topic, topic_confidence
    or None on failure.
    """
    tools = record.get("tools", {})
    tools_summary = ", ".join(f"{k}:{v}" for k, v in sorted(tools.items(), key=lambda x: -x[1])[:8])
    if not tools_summary:
        tools_summary = "(none)"

    prompt = QUALITY_SCORE_PROMPT.format(
        project=record.get("project", "unknown"),
        duration_minutes=record.get("duration_seconds", 0) / 60,
        user_turns=record.get("turns", {}).get("user", 0),
        assistant_turns=record.get("turns", {}).get("assistant", 0),
        tools_summary=tools_summary,
        error_count=record.get("tool_errors", {}).get("total", 0),
        correction_count=record.get("corrections", {}).get("count", 0),
        retry_count=record.get("retries", {}).get("total", 0),
    )

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        output = result.stdout.strip()
        if not output:
            return None

        # claude --output-format json wraps the response; extract the text
        try:
            wrapper = json.loads(output)
            # The CLI JSON output has a "result" field with the text
            text = wrapper.get("result", output)
            if isinstance(text, str):
                return json.loads(text)
            return text
        except (json.JSONDecodeError, TypeError):
            # Try parsing the raw output as JSON directly
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def write_telemetry(record):
    """Append telemetry record to today's JSONL file."""
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    telemetry_file = TELEMETRY_DIR / f"{today}.jsonl"
    with open(telemetry_file, "a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = data.get("session_id")
    transcript_path = data.get("transcript_path")

    if not session_id or not transcript_path:
        sys.exit(0)

    if not os.path.exists(transcript_path):
        sys.exit(0)

    # Rate-limit: one checkpoint per session per day
    if already_checkpointed(session_id):
        sys.exit(0)

    # Build telemetry from transcript
    record = build_telemetry_record(transcript_path, source_path=transcript_path)
    if not record:
        sys.exit(0)

    # Quality scoring via Claude CLI (haiku)
    scoring = call_haiku_for_scoring(record)
    if scoring:
        record["quality_score"] = scoring.get("quality_score")
        record["quality_breakdown"] = {
            "task_completion": scoring.get("task_completion"),
            "efficiency": scoring.get("efficiency"),
            "friction": scoring.get("friction"),
            "correctness": scoring.get("correctness"),
        }
        record["session_topic"] = scoring.get("session_topic")
        record["topic_confidence"] = scoring.get("topic_confidence")

    write_telemetry(record)


try:
    main()
except Exception:
    # Never crash the hook
    pass
