<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 1. Codex Execution

### Invocation

Background, parallel, with session persisted for resume:

```
cat /tmp/{prefix}-{TIMESTAMP}-gpt-prompt.txt | codex exec -m gpt-5.4 -c model_reasoning_effort=medium --sandbox workspace-write --json --output-schema <schema-path> -C <working_directory> - 2>/dev/null
```

**`-c model_reasoning_effort=medium`** is the default for all Phase 2/3/4
calls. Override via tier (§12): `--high` bumps Phase 2 to `high`, `--lite`
drops it to `low`. Triage and debate phases stay on `medium` regardless of
tier — the extra reasoning cost isn't justified for structured cross-eval.

**`--output-schema` is required for Phase 2** initial reviews. Use:
- `~/.claude/skills/dual-review-protocol/schemas/findings-code.json` — code reviews
- `~/.claude/skills/dual-review-protocol/schemas/findings-plan.json` — plan reviews

The model's final `agent_message` will be a single JSON object matching the
schema (see §2). Triage/debate phases (resume calls) do NOT use a schema —
they emit prose verdicts/recommendations.

For plan reviews add `--search` **before `exec`** (top-level flag, not on `exec`):
`codex --search exec -m ...`. For code reviews omit `--search` unless the lens
requires verifying assumptions in the diff context.

Run via `Bash` with `run_in_background: true` and `timeout: 300000`.

### Model selection

All phases use `gpt-5.4`. The cost lever is `model_reasoning_effort`,
set per tier (§12):

| Phase | Reasoning effort | Why |
|-------|------------------|-----|
| Initial review (Phase 2) | `medium` (default) / `medium` (--high) / `low` (--lite) | Tier-driven; see §12. |
| Triage (Phase 3) | `medium` | Structured cross-eval; deeper thinking adds little. |
| Debate (Phase 4) | `medium` | Best-idea framework eval; same rationale. |

`gpt-5.4` accepts verbosity values `low|medium|high` — no `-c
model_verbosity=medium` flag needed. Verbosity defaults from
`~/.codex/config.toml`.

> **Model note:** We run `gpt-5.4`. The `-codex` variants (`gpt-5.3-codex`,
> `gpt-5.2-codex`) were retired from ChatGPT-account access on 2026-06-02 and
> now require API-key billing. `gpt-5.4` is the entitled flagship on a ChatGPT
> Business sub. Do not revert to a `-codex` model without switching codex auth
> to an API key.

### Resume

Subsequent turns (triage, debate) reuse the same session. **`codex exec resume`
does NOT accept `-C`** — the cwd is the session's recorded cwd. To run from a
different directory, `cd` in the same shell command:

```
cat /tmp/{prefix}-{TIMESTAMP}-{phase}.txt | codex exec resume <SESSION_ID> --json - 2>/dev/null
```

`timeout: 120000` is enough for resumes.

### JSONL parsing

Use the dedicated parser:

```
~/.claude/scripts/parse-codex-output.sh <output_file>
```

Output format:
- `=== USAGE ===` — `{"input": N, "output": N, "cached": N}` (token totals)
- `=== RESPONSE ===` — concatenated `agent_message` text

To extract the `thread_id` (session ID) for resumes: read the first
`thread.started` event from the JSONL. The parser doesn't surface it; grep
for `"thread.started"` and pull `.thread_id`.

### Background retry + fallback model protocol

After every `codex exec` (initial or resume), parse the JSONL for `error`
events. Classify by error message:

| Error substring | Class | Action |
|---|---|---|
| `Selected model is at capacity` | **capacity** | Drop GPT lens for this run; continue Claude-only. No alt-model fallback. |
| `429` / `rate_limit_exceeded` | **rate** | Retry once with `run_in_background: true`. |
| `5xx` / network / timeout | **transient** | Retry once with `run_in_background: true`. |
| anything else | **unknown** | Surface raw error; continue Claude-only. |

**Fallback chain** (per phase):

| Phase | Primary | Fallback |
|-------|---------|----------|
| Phase 2 review | `gpt-5.4` | Claude-only |
| Phase 3 triage | `gpt-5.4` | Claude-only triage |
| Phase 4 debate | `gpt-5.4` | mark `[unresolved]` |

**Retry sequence on capacity:**

1. Print: "gpt-5.4 at capacity. Continuing Claude-only."
2. Skip GPT lens for the remainder of the run.

**Transient retry (rate / 5xx / timeout):**

1. Print: "GPT review timed out. Retrying in background..."
2. Start a SECOND `codex exec` with the SAME payload + same model, `run_in_background: true`, `timeout: 300000`
3. Continue immediately to Claude's review and subsequent phases as Claude-only
4. If the background retry completes BEFORE Phase 5 presentation: merge GPT findings (run context-aware triage on them first)
5. If retry completes DURING Phase 6 resolution: print "GPT results arrived late — [N] findings. Review after current findings?"
6. If retry also fails: silently continue Claude-only

**Error detection from JSONL:**

```
jq -r 'select(.type == "error") | .message' <output.jsonl>
jq -r 'select(.type == "turn.failed") | .error.message' <output.jsonl>
```

Both event types carry the OpenAI error JSON. Capacity error structure:
```json
{"type":"error","code":"...","message":"Selected model is at capacity. Please try a different model."}
```

### Pricing (verified 2026-05-19)

- gpt-5.4: $5.00/1M input, $0.50/1M cached input, $30.00/1M output (API rate; flat on ChatGPT-sub auth)

Reasoning tokens bill as output. Higher `model_reasoning_effort` → more
reasoning tokens → higher run cost (same per-token rate). Verify periodically
at https://developers.openai.com/codex/pricing.

## 10. Error Handling Table

| Error | Handling |
|-------|----------|
| Codex initial review timeout/fail (transient) | Background retry (same payload, same model). Claude proceeds immediately. |
| Codex returns "at capacity" | Drop GPT lens for the run; continue Claude-only. No alt-model fallback. |
| Background retry fails | Silent — Claude-only already in progress. |
| GPT response unparseable (Phase 2) | Schema enforces JSON shape — if `jq` parse fails, retry once with same payload; if still failing, fall back to Claude-only. |
| GPT response unparseable (triage/debate) | Extract what's usable from prose; fall back to Claude-only for rest. |
| `invalid_json_schema` 400 from API | Schema file diverged from OpenAI strict-mode rules (`additionalProperties:false` + every key in `required` + null-union for optional). Fix schema and retry. |
| Resume fails (triage) | Claude triages all GPT findings alone (with conversation context). |
| Resume fails (debate round) | Mark finding `[unresolved]` with both positions; continue. |
| Session ID not found | Claude triages all GPT findings alone. |
| No findings from either agent | Clean APPROVE with summary. |
| All GPT findings dismissed by context | Skip debate, Claude-only with dismissed section. |
| More than 5 disagreements | Debate top 5 by severity; remaining marked `[unresolved-no-debate]`. |
