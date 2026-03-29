"""Tests for parse_session.py — shared JSONL parser."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parse_session import (
    accumulate_tokens,
    build_telemetry_record,
    compute_duration,
    count_errors,
    count_tools,
    count_turns,
    detect_corrections,
    detect_retries,
    detect_skills_and_mcp,
    extract_bash_prefixes,
    extract_metadata,
    extract_timestamps,
    parse_messages,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


# --- parse_messages ---


def test_parse_messages_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    types = [m["type"] for m in msgs]
    assert "user" in types
    assert "assistant" in types
    assert "file-history-snapshot" not in types


def test_parse_messages_skips_malformed():
    msgs = list(parse_messages(os.path.join(FIXTURES, "malformed-session.jsonl")))
    assert len(msgs) >= 2  # should get the valid user + assistant messages
    for m in msgs:
        assert m["type"] in ("user", "assistant", "system")


def test_parse_messages_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("")
        path = f.name
    try:
        msgs = list(parse_messages(path))
        assert msgs == []
    finally:
        os.unlink(path)


def test_parse_messages_nonexistent_file():
    msgs = list(parse_messages("/nonexistent/path/file.jsonl"))
    assert msgs == []


def test_parse_messages_skips_progress_and_snapshots():
    msgs = list(parse_messages(os.path.join(FIXTURES, "malformed-session.jsonl")))
    for m in msgs:
        assert m["type"] != "progress"
        assert m["type"] != "file-history-snapshot"


# --- extract_metadata ---


def test_extract_metadata_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    meta = extract_metadata(msgs)
    assert meta["session_id"] == "test-session-001"
    assert meta["project"] == "myproject"
    assert meta["git_branch"] == "main"
    assert meta["version"] == "2.1.85"
    assert meta["cwd"] == "/Users/test/dev/myproject"


# --- extract_timestamps ---


def test_extract_timestamps_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    ts_start, ts_end = extract_timestamps(msgs)
    assert ts_start == "2026-03-25T10:00:00.000Z"
    assert ts_end == "2026-03-25T10:00:15.000Z"


def test_extract_timestamps_single_message():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({
            "type": "user", "message": {"role": "user", "content": "hi"},
            "timestamp": "2026-01-01T00:00:00.000Z", "sessionId": "x",
        }) + "\n")
        path = f.name
    try:
        msgs = list(parse_messages(path))
        ts_start, ts_end = extract_timestamps(msgs)
        assert ts_start == ts_end
    finally:
        os.unlink(path)


# --- compute_duration ---


def test_compute_duration():
    assert compute_duration("2026-03-25T10:00:00.000Z", "2026-03-25T10:00:15.000Z") == 15


def test_compute_duration_missing():
    assert compute_duration(None, "2026-03-25T10:00:15.000Z") == 0
    assert compute_duration("2026-03-25T10:00:00.000Z", None) == 0


# --- count_turns ---


def test_count_turns_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    turns = count_turns(msgs)
    assert turns["user"] == 3
    assert turns["assistant"] == 3


# --- accumulate_tokens ---


def test_accumulate_tokens_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    tokens = accumulate_tokens(msgs)
    assert tokens["input_total"] == 500 + 600 + 700
    assert tokens["output_total"] == 50 + 40 + 30
    assert tokens["cache_creation_total"] == 1000
    assert tokens["cache_read_total"] == 200 + 1200 + 1400


# --- count_tools ---


def test_count_tools_small_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    tools = count_tools(msgs)
    assert tools.get("Read") == 1
    assert tools.get("Edit") == 1


def test_count_tools_no_tools():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "hi"}],
                        "usage": {"input_tokens": 0, "output_tokens": 0}},
            "timestamp": "2026-01-01T00:00:00Z",
        }) + "\n")
        path = f.name
    try:
        msgs = list(parse_messages(path))
        tools = count_tools(msgs)
        assert tools == {}
    finally:
        os.unlink(path)


# --- extract_bash_prefixes ---


def test_extract_bash_prefixes():
    msgs = list(parse_messages(os.path.join(FIXTURES, "retries-session.jsonl")))
    prefixes = extract_bash_prefixes(msgs)
    assert prefixes.get("npm test") >= 2
    assert prefixes.get("git status") >= 1


# --- detect_skills_and_mcp ---


def test_detect_skills():
    msgs = list(parse_messages(os.path.join(FIXTURES, "retries-session.jsonl")))
    skills, mcp = detect_skills_and_mcp(msgs)
    assert "investigate" in skills
    assert mcp == []


# --- count_errors ---


def test_count_errors_corrections_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "corrections-session.jsonl")))
    errors = count_errors(msgs)
    assert errors["total"] == 1
    assert errors["by_type"].get("exit_code", 0) == 1


def test_count_errors_retries_session():
    msgs = list(parse_messages(os.path.join(FIXTURES, "retries-session.jsonl")))
    errors = count_errors(msgs)
    assert errors["total"] == 3  # three failed npm test results


def test_count_errors_no_errors():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    errors = count_errors(msgs)
    assert errors["total"] == 0


# --- detect_corrections ---


def test_detect_corrections_present():
    msgs = list(parse_messages(os.path.join(FIXTURES, "corrections-session.jsonl")))
    corrections = detect_corrections(msgs)
    assert corrections["count"] >= 2
    matched = corrections["keywords_matched"]
    assert any(kw in matched for kw in ["no,", "stop", "that's not", "actually"])


def test_detect_corrections_none():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    corrections = detect_corrections(msgs)
    assert corrections["count"] == 0


# --- detect_retries ---


def test_detect_retries_present():
    msgs = list(parse_messages(os.path.join(FIXTURES, "retries-session.jsonl")))
    retries = detect_retries(msgs)
    assert retries["total"] >= 1
    assert any(s["tool"] == "Bash" for s in retries["sequences"])


def test_detect_retries_none():
    msgs = list(parse_messages(os.path.join(FIXTURES, "small-session.jsonl")))
    retries = detect_retries(msgs)
    assert retries["total"] == 0
    assert retries["sequences"] == []


# --- build_telemetry_record ---


def test_build_telemetry_record_small():
    record = build_telemetry_record(os.path.join(FIXTURES, "small-session.jsonl"))
    assert record is not None
    assert record["schema_version"] == 1
    assert record["session_id"] == "test-session-001"
    assert record["project"] == "myproject"
    assert record["duration_seconds"] == 15
    assert record["tools"]["Read"] == 1
    assert record["tools"]["Edit"] == 1
    assert record["corrections"]["count"] == 0
    assert record["retries"]["total"] == 0


def test_build_telemetry_record_corrections():
    record = build_telemetry_record(os.path.join(FIXTURES, "corrections-session.jsonl"))
    assert record is not None
    assert record["session_id"] == "test-session-corrections"
    assert record["corrections"]["count"] >= 2
    assert record["tool_errors"]["total"] == 1


def test_build_telemetry_record_has_source_path():
    path = os.path.join(FIXTURES, "small-session.jsonl")
    record = build_telemetry_record(path, source_path="/original/path.jsonl")
    assert record["source_path"] == "/original/path.jsonl"


def test_build_telemetry_record_nonexistent():
    record = build_telemetry_record("/nonexistent/file.jsonl")
    assert record is None


def test_build_telemetry_record_too_large():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        # Write just enough metadata to be valid, but make file huge via padding
        f.write(json.dumps({
            "type": "user", "message": {"role": "user", "content": "x" * 100},
            "sessionId": "big", "timestamp": "2026-01-01T00:00:00Z",
        }) + "\n")
        # Pad to exceed 20MB
        padding = "x" * (1024 * 1024)  # 1MB per line
        for _ in range(21):
            f.write(padding + "\n")
        path = f.name
    try:
        record = build_telemetry_record(path)
        assert record is None
    finally:
        os.unlink(path)


def test_build_telemetry_record_malformed():
    record = build_telemetry_record(os.path.join(FIXTURES, "malformed-session.jsonl"))
    assert record is not None
    assert record["session_id"] == "test-session-malformed"
