"""Shared JSONL session parser for Claude Code transcripts.

All telemetry consumers import from this module. When Claude Code changes
its JSONL format, fix it here once.
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1

CORRECTION_KEYWORDS = [
    "no,", "no.", "wrong", "that's not", "actually", "instead",
    "I said", "not what I", "stop", "don't do", "undo",
]

COMPOUND_BASH_PREFIXES = frozenset([
    "git", "npm", "npx", "yarn", "pnpm", "docker", "kubectl",
    "pip", "pip3", "python", "python3", "node", "cargo", "go",
    "make", "rtk", "bun", "gh", "aws", "gcloud", "terraform",
])

ERROR_CLASSIFIERS = [
    ("exit_code", "Exit code"),
    ("rejected", "user doesn't want"),
    ("rejected", "The user rejected"),
    ("file_too_large", "exceeds maximum"),
    ("file_too_large", "too large"),
    ("permission_denied", "Permission denied"),
    ("not_found", "No such file"),
    ("not_found", "not found"),
]

MAX_TRANSCRIPT_BYTES = 20 * 1024 * 1024  # 20MB safety limit


def parse_messages(jsonl_path):
    """Yield parsed message dicts from a JSONL transcript file.

    Skips malformed lines and non-message types (progress, file-history-snapshot).
    """
    try:
        with open(jsonl_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg_type = obj.get("type")
                if msg_type in ("user", "assistant", "system"):
                    yield obj
    except (OSError, IOError):
        return


def extract_metadata(messages):
    """Extract session metadata from the first user message.

    Returns dict with session_id, cwd, project, git_branch, version,
    timestamp_start, permission_mode.
    """
    meta = {
        "session_id": None,
        "cwd": None,
        "project": None,
        "git_branch": None,
        "version": None,
        "permission_mode": "default",
    }
    for msg in messages:
        if msg.get("type") == "user":
            meta["session_id"] = msg.get("sessionId")
            meta["cwd"] = msg.get("cwd", "")
            meta["project"] = os.path.basename(meta["cwd"]) if meta["cwd"] else None
            meta["git_branch"] = msg.get("gitBranch")
            meta["version"] = msg.get("version")
            break
    return meta


def extract_timestamps(messages):
    """Return (timestamp_start, timestamp_end) ISO strings from message list."""
    first_ts = None
    last_ts = None
    for msg in messages:
        ts = msg.get("timestamp")
        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts
    return first_ts, last_ts


def compute_duration(ts_start, ts_end):
    """Compute duration in seconds between two ISO timestamps."""
    if not ts_start or not ts_end:
        return 0
    try:
        fmt_options = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]
        t_start = t_end = None
        for fmt in fmt_options:
            try:
                t_start = datetime.strptime(ts_start, fmt)
                break
            except ValueError:
                continue
        for fmt in fmt_options:
            try:
                t_end = datetime.strptime(ts_end, fmt)
                break
            except ValueError:
                continue
        if t_start and t_end:
            return max(0, int((t_end - t_start).total_seconds()))
    except Exception:
        pass
    return 0


def count_turns(messages):
    """Count turns by message type."""
    counts = Counter()
    for msg in messages:
        counts[msg.get("type", "unknown")] += 1
    return dict(counts)


def accumulate_tokens(messages):
    """Sum token usage across all assistant messages."""
    totals = {
        "input_total": 0,
        "output_total": 0,
        "cache_creation_total": 0,
        "cache_read_total": 0,
    }
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        usage = msg.get("message", {}).get("usage", {})
        totals["input_total"] += usage.get("input_tokens", 0)
        totals["output_total"] += usage.get("output_tokens", 0)
        totals["cache_creation_total"] += usage.get("cache_creation_input_tokens", 0)
        totals["cache_read_total"] += usage.get("cache_read_input_tokens", 0)
    return totals


def count_tools(messages):
    """Count tool_use invocations by tool name."""
    counts = Counter()
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                counts[block.get("name", "unknown")] += 1
    return dict(counts)


def extract_bash_prefixes(messages):
    """Extract command prefixes from Bash tool_use blocks."""
    counts = Counter()
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use" or block.get("name") != "Bash":
                continue
            cmd = block.get("input", {}).get("command", "").strip()
            parts = cmd.split()
            if not parts:
                continue
            if len(parts) >= 2 and parts[0] in COMPOUND_BASH_PREFIXES:
                prefix = f"{parts[0]} {parts[1]}"
            else:
                prefix = parts[0]
            counts[prefix] += 1
    return dict(counts)


def detect_skills_and_mcp(messages):
    """Detect skill invocations and MCP tool usage."""
    skills = set()
    mcp_tools = set()
    for msg in messages:
        if msg.get("type") != "assistant":
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            if name == "Skill":
                skill_name = block.get("input", {}).get("skill", "")
                if skill_name:
                    skills.add(skill_name)
            elif name.startswith("mcp__"):
                mcp_tools.add(name)
    return sorted(skills), sorted(mcp_tools)


def count_errors(messages):
    """Count tool errors from tool_result blocks in user messages."""
    total = 0
    by_type = Counter()
    for msg in messages:
        if msg.get("type") != "user":
            continue
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_result" or not block.get("is_error"):
                continue
            total += 1
            error_content = str(block.get("content", ""))
            classified = False
            for err_type, prefix in ERROR_CLASSIFIERS:
                if prefix.lower() in error_content.lower():
                    by_type[err_type] += 1
                    classified = True
                    break
            if not classified:
                by_type["other"] += 1
    return {"total": total, "by_type": dict(by_type)}


def detect_corrections(messages):
    """Detect user correction patterns in user messages."""
    count = 0
    keywords_matched = []
    for msg in messages:
        if msg.get("type") != "user":
            continue
        content = msg.get("message", {}).get("content", "")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            content = " ".join(text_parts)
        if not isinstance(content, str):
            continue
        content_lower = content.lower().strip()
        for kw in CORRECTION_KEYWORDS:
            if content_lower.startswith(kw.lower()) or f" {kw.lower()}" in f" {content_lower}":
                count += 1
                if kw not in keywords_matched:
                    keywords_matched.append(kw)
                break
    return {"count": count, "keywords_matched": keywords_matched}


def extract_file_extension_errors(messages):
    """Map tool errors to the file extension being operated on.

    Cross-references Edit/Write/Read tool_use blocks with their
    subsequent tool_result is_error=True responses.
    Returns: {".ts": 3, ".py": 1}
    """
    errors_by_ext = Counter()
    tool_id_to_ext = {}

    for msg in messages:
        if msg.get("type") == "assistant":
            content = msg.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                if block.get("name") not in ("Edit", "Write", "Read"):
                    continue
                fp = block.get("input", {}).get("file_path", "")
                if fp:
                    ext = Path(fp).suffix.lower()
                    if ext:
                        tool_id_to_ext[block.get("id", "")] = ext

        elif msg.get("type") == "user":
            content = msg.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_result" or not block.get("is_error"):
                    continue
                ext = tool_id_to_ext.get(block.get("tool_use_id", ""))
                if ext:
                    errors_by_ext[ext] += 1

    return dict(errors_by_ext)


def detect_retries(messages):
    """Detect consecutive same-tool sequences (retry patterns)."""
    total = 0
    sequences = []
    prev_tool = None
    consecutive = 0

    for msg in messages:
        if msg.get("type") != "assistant":
            if prev_tool and consecutive >= 3:
                sequences.append({"tool": prev_tool, "consecutive": consecutive})
                total += consecutive - 1
            prev_tool = None
            consecutive = 0
            continue

        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue

        tools_in_msg = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools_in_msg.append(block.get("name", ""))

        for tool in tools_in_msg:
            if tool == prev_tool:
                consecutive += 1
            else:
                if prev_tool and consecutive >= 3:
                    sequences.append({"tool": prev_tool, "consecutive": consecutive})
                    total += consecutive - 1
                prev_tool = tool
                consecutive = 1

    if prev_tool and consecutive >= 3:
        sequences.append({"tool": prev_tool, "consecutive": consecutive})
        total += consecutive - 1

    return {"total": total, "sequences": sequences}


def build_telemetry_record(jsonl_path, source_path=None):
    """Build a complete telemetry record from a JSONL transcript file.

    Returns None if the file is too large, empty, or unparseable.
    """
    file_size = 0
    try:
        file_size = os.path.getsize(jsonl_path)
    except OSError:
        return None

    if file_size > MAX_TRANSCRIPT_BYTES:
        return None

    messages = list(parse_messages(jsonl_path))
    if not messages:
        return None

    meta = extract_metadata(messages)
    if not meta["session_id"]:
        return None

    ts_start, ts_end = extract_timestamps(messages)
    turns = count_turns(messages)
    tokens = accumulate_tokens(messages)
    tools = count_tools(messages)
    bash_prefixes = extract_bash_prefixes(messages)
    skills, mcp_tools = detect_skills_and_mcp(messages)
    errors = count_errors(messages)
    corrections = detect_corrections(messages)
    retries = detect_retries(messages)
    file_ext_errors = extract_file_extension_errors(messages)

    record = {
        "schema_version": SCHEMA_VERSION,
        "session_id": meta["session_id"],
        "source_path": source_path or str(jsonl_path),
        "timestamp_start": ts_start,
        "timestamp_end": ts_end,
        "duration_seconds": compute_duration(ts_start, ts_end),
        "cwd": meta["cwd"],
        "project": meta["project"],
        "git_branch": meta["git_branch"],
        "version": meta["version"],
        "permission_mode": meta["permission_mode"],
        "turns": turns,
        "tokens": tokens,
        "tools": tools,
        "tool_errors": errors,
        "retries": retries,
        "corrections": corrections,
        "skills_invoked": skills,
        "mcp_tools_used": mcp_tools,
        "bash_command_prefixes": bash_prefixes,
        "file_extension_errors": file_ext_errors,
    }

    return record
