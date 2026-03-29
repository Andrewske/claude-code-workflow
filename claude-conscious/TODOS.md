# TODOS

## Claude Conscious v1

### ~~GOAL.md — Full vision document~~ DONE
Created GOAL.md with full v1/v2/v3 vision, all 7 categories, action types, security model, and architecture.

### Security documentation
**What:** Document what data the hook sends to the Claude CLI (summary text + stats), what stays on disk, and how to disable telemetry collection. Add a `--no-telemetry` flag to install.sh.
**Why:** Codex review flagged hook-to-API as an exfiltration path. Document explicitly for transparency.
**Depends on:** Phase 1 implementation.

### Migrate bullet-summary.py to CLI calls
**What:** Replace direct Anthropic SDK call in bullet-summary.py with `claude -p` CLI call. Remove anthropic/python-dotenv dependencies and manual API key reading.
**Why:** conscious-hook.py will use CLI calls. Migrating the older hook removes SDK dependency entirely.
**Depends on:** conscious-hook.py working with CLI calls first (proves the pattern).

### Settings precedence for apply path
**What:** /review-suggestions should detect whether a permission is global vs project-specific and edit the appropriate settings file.
**Why:** Claude Code has user/project/local/managed precedence. analyze_permissions.py already has per-project detection (>80% in one project = project-specific).
**Depends on:** v1 shipping with global-only default.

## Deferred categories (v2+)

- **profile_updates** — auto-update interaction-profile.json (no approval needed)
- **feature_ideas** — surface unused CC features from auto-generated catalog
- **skill_improvements** — suggest modifications to existing skills
- **self_improvements** — meta-loop: pipeline improves itself (Goodhart risk, defer until v1 proves value)

## Deferred features (v2+)

- Weekly digest (Sunday markdown summary)
- Deferred suggestion revisit-date handling
- Feature catalog auto-generation from introspection (replace manual curation)
- Shareable improvement report (--report flag) — the "cool factor" deliverable
- Cross-session topic tracking (data captured via quality scoring, analysis deferred)
