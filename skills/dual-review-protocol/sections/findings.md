<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 2. Finding Format

GPT (Phase 2): output is a JSON object validated against
`schemas/findings-{code,plan}.json`. Field names are lowercase
(`id`, `severity`, `file`, `line`, `category`, `issue`, `evidence`, `fix`,
`confidence`; plan variant uses `section`/`title`/`problem`/`impact` instead
of `file`/`line`/`category`/`issue`/`evidence`).

Claude emits findings in markdown (no schema enforcement on local
generation):

```
FINDING:
- ID: {C|G}{N}
- Severity: CRITICAL | HIGH | MEDIUM | LOW
- File: <path>
- Line: <line>
- Category: <lens-specific>
- Issue: <specific description>
- Evidence: <quoted code or doc reference>
- Fix: <concrete actionable change>
- Confidence: <XX>%
```

For plan reviews, replace `File`/`Line` with `Section: <task-file or section ref>` and add `- Title: <short title>`, `- Problem: <description>`, `- Impact: <what breaks>`.

**Minimum viable finding:** ID + Severity + (File or Section) + Issue/Problem.
Schema-enforced GPT output won't be malformed; for Claude markdown, extract
what's parseable from malformed findings and warn about discards.

Findings are ID'd `C1, C2, ...` for Claude and `G1, G2, ...` for GPT.

### Parsing GPT JSON output

`parse-codex-output.sh` returns the raw `agent_message` text in the
`=== RESPONSE ===` section. For schema-enforced calls, parse it as JSON:

```
schema_response=$(~/.claude/scripts/parse-codex-output.sh <output> | sed -n '/=== RESPONSE ===/,$p' | tail -n +2)
echo "$schema_response" | jq -r '.findings[] | "G\(.id): \(.severity) \(.file // .section): \(.issue // .problem)"'
```
