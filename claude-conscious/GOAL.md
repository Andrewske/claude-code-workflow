# Claude Conscious — Full Vision

The complete picture of what this system becomes. v1 ships with a subset; this
doc captures everything so future sessions don't lose context.

## What it does (one sentence)

Observes how Claude Code sessions actually go, generates data-driven improvement
suggestions, and applies them with manual approval — so the environment gets
measurably better every week.

## v1 (shipped)

- **Telemetry**: Rate-limited Stop hook extracts session stats + Haiku quality
  score. Writes compact JSONL records (~1KB per session from ~500KB raw).
- **Analysis**: Daily cron computes aggregates and generates rule-based suggestions.
- **Review**: `/review-suggestions` presents suggestions one at a time with
  Apply/Dismiss/Defer. Two action types: settings_edit, edit_file.
- **Metrics**: Baseline capture + before/after comparison table.
- **Categories**: permissions, claude_md_updates, skill_ideas.

## v2: Complete suggestion categories

| Category | What it generates | Action type |
|----------|------------------|-------------|
| permissions | Allow rules for frequently-approved commands | settings_edit |
| claude_md_updates | Interaction profile section in CLAUDE.md | edit_file |
| skill_ideas | Unused installed skills worth trying | edit_file |
| profile_updates | Interaction profile JSON (auto, no approval) | update_profile |
| feature_ideas | CC features you have but haven't used | documentation_note |
| skill_improvements | Modifications to existing skills | edit_skill |
| self_improvements | Changes to the conscious pipeline itself | edit_conscious |

## v2: All action types

| Action type | What it does |
|-------------|-------------|
| settings_edit | Modify permissions.allow in settings.json |
| edit_file | Edit any file (CLAUDE.md, etc.) via Claude |
| create_skill | Scaffold new skill under ~/.claude/skills/ |
| edit_skill | Modify existing SKILL.md files |
| update_profile | Write to interaction-profile.json (automatic) |
| documentation_note | Append to a "features to try" list |
| edit_conscious | Modify files under ~/.claude/conscious/ |

## v2: Self-improvement meta-loop

The analysis engine generates `self_improvements` suggestions when:
- New JSONL fields appear that the extractor doesn't capture
- A suggestion category has >70% dismiss rate (adjust thresholds)
- The user consistently reviews one category first (reorder)
- Bullet summary output misses info that raw JSONL contains
- Interaction profile is stale (>30 days with no updates)

Deferred because of Goodhart risk (Codex review): a pipeline optimizing its own
proxy metrics will optimize for score movement, not actual improvement. Ship v1,
prove the core loop works, then add the meta-loop with human-in-the-loop validation.

## v2: Feature catalog auto-generation

Replace the manual feature-catalog.md with programmatic introspection:
- List installed skills from ~/.claude/skills/*/SKILL.md
- List available tools from Claude Code's tool manifest
- List registered MCP servers from .mcp.json files
- List hook types from settings.json
- Cross-reference with actual usage from telemetry

## v3: Weekly digest

Every Sunday, the scheduled agent writes `digests/week-{date}.md`:
- Suggestions generated this week
- Improvements applied
- Metric deltas (before/after)
- Highlight of the week
- Optional Slack posting (configurable)

## v3: Shareable improvement report

`python3 analyze_sessions.py --report` generates polished markdown:
- Before/after metrics with ASCII sparklines
- Narrative summary of what changed and why
- Designed for GitHub README, blog post, or tweet thread
- This is the "cool factor" — hard numbers proving your environment improved

## v3: Settings precedence

/review-suggestions detects whether a permission is global vs project-specific:
- If >80% of a command's usage is in one project, suggest project-level rule
- Otherwise suggest global rule
- analyze_permissions.py already has per-project detection logic to reuse

## v3: Cross-session topic tracking

Quality scoring already captures session_topic and topic_confidence. The analysis
to use it is deferred:
- Topic-aware suggestions ("debugging sessions have 2x retries — consider...")
- Topic distribution over time (what you spend your time on)
- Topic-specific efficiency metrics

## Security model

What leaves disk:
- Haiku receives: project name, duration, turn counts, tool counts, error count,
  correction count, retry count (~500 tokens). NOT raw user messages or code.

What stays local:
- All telemetry records at ~/.claude/conscious/telemetry/
- All suggestion history at ~/.claude/conscious/suggestions/
- All metrics at ~/.claude/conscious/metrics/

Disable: `install.sh --uninstall` removes the hook and cron. Telemetry data
is preserved for manual deletion.

## Architecture (final, per eng review)

```
Stop hook (conscious_hook.py) — rate-limited, once per session per day
    |-- Dedup check: session_id in today's telemetry?
    |-- Parse via parse_session.py (shared module)
    |-- Claude CLI haiku call: quality_score + topic
    |-- Write compact telemetry record (with source_path for replay)

Daily cron (launchd, 6:37 AM)
    |-- analyze_sessions.py reads compact records
    |-- Generates suggestions to pending.jsonl

/review-suggestions (on demand)
    |-- AI enrichment at review time
    |-- Apply/Dismiss/Defer flow
    |-- Modifies settings.json or CLAUDE.md
```
