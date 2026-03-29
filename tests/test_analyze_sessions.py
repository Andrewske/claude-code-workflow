"""Tests for analyze_sessions.py — batch analysis engine."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analyze_sessions import (
    compute_aggregates,
    generate_suggestions,
    is_bash_prefix_allowed,
    read_telemetry,
)


def make_record(**overrides):
    """Build a minimal telemetry record with sensible defaults."""
    base = {
        "schema_version": 1,
        "session_id": "test-001",
        "source_path": "/tmp/test.jsonl",
        "timestamp_start": "2026-03-26T10:00:00.000Z",
        "timestamp_end": "2026-03-26T10:30:00.000Z",
        "duration_seconds": 1800,
        "cwd": "/Users/test/dev/proj",
        "project": "proj",
        "git_branch": "main",
        "version": "2.1.85",
        "permission_mode": "default",
        "turns": {"user": 10, "assistant": 12},
        "tokens": {
            "input_total": 5000,
            "output_total": 1000,
            "cache_creation_total": 2000,
            "cache_read_total": 3000,
        },
        "tools": {"Bash": 5, "Read": 3, "Edit": 2},
        "tool_errors": {"total": 1, "by_type": {"exit_code": 1}},
        "retries": {"total": 0, "sequences": []},
        "corrections": {"count": 0, "keywords_matched": []},
        "skills_invoked": [],
        "mcp_tools_used": [],
        "bash_command_prefixes": {"git status": 3, "npm test": 2},
    }
    base.update(overrides)
    return base


# ── is_bash_prefix_allowed ──


def test_bash_prefix_allowed_exact():
    patterns = ["Bash(git status *)"]
    assert is_bash_prefix_allowed("git status", patterns) is True


def test_bash_prefix_allowed_wildcard():
    patterns = ["Bash(npm *)"]
    assert is_bash_prefix_allowed("npm test", patterns) is True


def test_bash_prefix_not_allowed():
    patterns = ["Bash(git status *)"]
    assert is_bash_prefix_allowed("docker build", patterns) is False


def test_bash_prefix_empty_patterns():
    assert is_bash_prefix_allowed("git log", []) is False


# ── compute_aggregates ──


def test_aggregates_basic():
    records = [make_record(), make_record(session_id="test-002", project="other")]
    agg = compute_aggregates(records)
    assert agg["sessions"] == 2
    assert agg["total_user_turns"] == 20
    assert agg["tool_frequency"]["Bash"] == 10
    assert agg["error_rate"] == 2 / 20  # 2 errors / 20 total tool calls
    assert agg["avg_corrections"] == 0


def test_aggregates_empty():
    agg = compute_aggregates([])
    assert agg["sessions"] == 0
    assert agg["total_user_turns"] == 0
    assert agg["error_rate"] == 0


def test_aggregates_cache_hit_rate():
    records = [make_record()]
    agg = compute_aggregates(records)
    # cache_read=3000, cache_creation=2000, total=5000
    assert agg["cache_hit_rate"] == 3000 / 5000


def test_aggregates_corrections():
    records = [
        make_record(corrections={"count": 3, "keywords_matched": ["no,"]}),
        make_record(session_id="test-002", corrections={"count": 1, "keywords_matched": ["actually"]}),
    ]
    agg = compute_aggregates(records)
    assert agg["avg_corrections"] == 2.0


def test_aggregates_skills_used():
    records = [
        make_record(skills_invoked=["browse", "qa"]),
        make_record(session_id="test-002", skills_invoked=["browse", "ship"]),
    ]
    agg = compute_aggregates(records)
    assert agg["skills_used"] == {"browse", "qa", "ship"}


# ── generate_suggestions ──


def test_permission_gap_suggestion():
    agg = {
        "sessions": 20,
        "total_user_turns": 200,
        "avg_duration_minutes": 30,
        "tool_frequency": {"Bash": 100},
        "bash_prefix_frequency": {"docker build": 15, "git status": 3},
        "error_rate": 0.02,
        "retry_rate": 0.01,
        "avg_corrections": 0.5,
        "cache_hit_rate": 0.7,
        "skills_used": set(),
        "projects": {},
    }
    # No allow patterns → docker build should trigger a suggestion
    suggestions = generate_suggestions(agg, [])
    perm_suggestions = [s for s in suggestions if s["category"] == "permissions"]
    assert any("docker build" in s["title"] for s in perm_suggestions)
    # git status has count=3, below threshold of 5
    assert not any("git status" in s["title"] for s in perm_suggestions)


def test_permission_gap_already_allowed():
    agg = {
        "sessions": 20,
        "total_user_turns": 200,
        "avg_duration_minutes": 30,
        "tool_frequency": {"Bash": 100},
        "bash_prefix_frequency": {"git status": 10},
        "error_rate": 0.02,
        "retry_rate": 0.01,
        "avg_corrections": 0.5,
        "cache_hit_rate": 0.7,
        "skills_used": set(),
        "projects": {},
    }
    suggestions = generate_suggestions(agg, ["Bash(git status *)"])
    perm_suggestions = [s for s in suggestions if s["category"] == "permissions"]
    assert not any("git status" in s["title"] for s in perm_suggestions)


def test_no_suggestions_when_healthy():
    agg = {
        "sessions": 5,
        "total_user_turns": 50,
        "avg_duration_minutes": 20,
        "tool_frequency": {"Read": 10},
        "bash_prefix_frequency": {},
        "error_rate": 0.01,
        "retry_rate": 0.0,
        "avg_corrections": 0.2,
        "cache_hit_rate": 0.8,
        "skills_used": set(),
        "projects": {},
    }
    suggestions = generate_suggestions(agg, [])
    # No permission gaps (no bash prefixes), too few sessions for profile
    perm_suggestions = [s for s in suggestions if s["category"] == "permissions"]
    assert len(perm_suggestions) == 0


def test_claude_md_suggestion_requires_10_sessions():
    agg = {
        "sessions": 5,
        "total_user_turns": 50,
        "avg_duration_minutes": 30,
        "tool_frequency": {"Bash": 20},
        "bash_prefix_frequency": {},
        "error_rate": 0.02,
        "retry_rate": 0.01,
        "avg_corrections": 0.5,
        "cache_hit_rate": 0.7,
        "skills_used": set(),
        "projects": {"myproj": 5},
    }
    suggestions = generate_suggestions(agg, [])
    claude_md = [s for s in suggestions if s["category"] == "claude_md_updates"]
    assert len(claude_md) == 0  # Not enough sessions

    agg["sessions"] = 15
    suggestions = generate_suggestions(agg, [])
    claude_md = [s for s in suggestions if s["category"] == "claude_md_updates"]
    assert len(claude_md) == 1


def test_suggestion_priority_high_above_20():
    agg = {
        "sessions": 20,
        "total_user_turns": 200,
        "avg_duration_minutes": 30,
        "tool_frequency": {"Bash": 100},
        "bash_prefix_frequency": {"kubectl apply": 25},
        "error_rate": 0.02,
        "retry_rate": 0.01,
        "avg_corrections": 0.5,
        "cache_hit_rate": 0.7,
        "skills_used": set(),
        "projects": {},
    }
    suggestions = generate_suggestions(agg, [])
    perm = [s for s in suggestions if "kubectl" in s["title"]]
    assert perm[0]["priority"] == "high"
