<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 4. Triage Protocol

Two-part prompt sent to GPT via resume. See `templates/triage.md` for the
full template with placeholders.

### Part 1: GPT self-evaluation

```
SELF-DISMISS: G[N]
REASON: [why context invalidates this finding]
```

If none invalidated: `SELF-DISMISS: NONE`.

### Part 2: GPT cross-evaluates Claude's findings

For each Claude finding, exactly one block:

```
FINDING: C[N]
VERDICT: AGREE | DISAGREE
PREVIEW: [N/A on AGREE; 2 sentences max on DISAGREE with code-evidence rebuttal]
```

After per-finding blocks, GPT notes overlaps:

```
OVERLAP: G2 <-> C3
```

### Self-dismiss handling

- Parse `SELF-DISMISS` entries.
- Claude evaluates each. If Claude agrees the finding is invalid given conversation context, move to "Dismissed (Context)" — skip autosolve and debate.
- If Claude disagrees, keep in normal triage flow.
- **Fast-exit:** if GPT self-dismisses ALL findings AND Claude agrees with all dismissals, skip debate entirely.

### Claude triage of remaining GPT findings

For each non-dismissed GPT finding, Claude assesses AGREE or DISAGREE based
on whether the issue is real and material. Read the cited file at the
cited lines using `Read` to verify. Claude-agreed GPT findings enter the
autosolve queue.

### Triage failure

If the resume call fails: present findings side-by-side without negotiation.
Claude triages all GPT findings alone (agree/disagree based on overlap and
merit + conversation context).

## 5. Deduplication

Match by: same file AND overlapping line range AND similar problem domain.
(For plans: same section AND overlapping problem domain.) Claude makes the
call and explains reasoning.

- Exact same issue → merge, tag `[both-found]`, auto-agree
- Partial overlap → keep separate with cross-references
- Overlapping findings with same fix → auto-agree

## 13. Low-Finding Triage Policy (Phase 3 short-circuit)

Commands invoking this protocol skip the Phase 3 codex resume call when
total findings (Claude + GPT) ≤ 3. Claude performs the dedup and routing
in-context with no cost change to fidelity for that small a finding list.
Typical savings: ~$2.74 per run when triggered.

### Trigger

After Phase 2 emits Claude findings and GPT findings (parsed via
`~/.claude/scripts/parse-codex-output.sh` then `jq -r '.findings | length'`
on the `=== RESPONSE ===` JSON):

```
total = claude_count + gpt_count
```

- If `total ≤ 3` → **skip codex resume triage call**. Apply §13 short-circuit (below).
- Else → existing Phase 3 codex flow (§4 Triage Protocol) unchanged.

### Short-circuit procedure

1. Print: `Triage: Claude-only (low-finding policy, total=N).`
2. Apply §5 (Deduplication): same file + overlapping line range + similar
   problem domain → merge. Tag `[both-found]`, auto-`agreed-fix`.
3. For each remaining (un-merged) GPT finding, Claude assigns
   `AGREE | DISAGREE` based on cited code. **Read each cited file/line first**
   to verify the issue is real before deciding.
4. Treat GPT-agree findings as triage-agreed (autosolve queue entry,
   default `agreed-fix`).
5. Treat GPT-disagree findings as `[unresolved]` and route to the debate
   queue. Note: with ≤3 total findings, debate-queue entries will usually be
   0–1; debate may run anyway per §6, or §6's cap-of-5 will fast-exit naturally.
6. Route per §7 (Routing).

### Distinction from §10 "Triage failure" fallback

§10 fires on **codex error** and presents findings side-by-side without
dedup. §13 is a **policy-driven** short-circuit on small finding counts.
§13 performs full §5 dedup and §7 routing — same fidelity as full triage
minus GPT's self-dismiss cross-eval, which adds little signal at ≤3 findings.

### Scope

§13 applies to the same commands as §12: `/dual-code-review` and
`/review-pr`. Plan-review commands keep full Phase 3 codex triage.
