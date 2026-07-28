<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 6. Debate Protocol

Only Phase 3 disagreements enter debate. **Cap: 5 findings** (priority by
severity: CRITICAL → HIGH → MEDIUM → LOW). Beyond cap: tag
`[unresolved-no-debate]`, present both positions in Phase 5.

Debate delegates to `/plan:best-idea` (Debate Mode). See
`templates/debate.md` for the wrapper prompt that calls best-idea with
debate context.

### Round 1

Claude runs `/plan:best-idea` internally with debate context (the disagreed
finding + its own original position). Output is a RECOMMENDATION block:

```
RECOMMENDATION:
- Action: fix | skip
- Pick: <solution name, or "skip" if Action is skip>
- Why: <2-3 sentences>
- Trade-offs: <what's given up>
```

`Action: fix` = code change warranted. `Action: skip` = finding is real but
not worth fixing now (micro-opt, low ROI, scope-out).

The wrapper prompt is sent to GPT via `codex exec resume`. GPT runs the
same evaluation through `/plan:best-idea` lenses (Eliminate / Reuse /
Standard / Minimal / Strategic) and emits its own RECOMMENDATION + a
final `VERDICT: AGREE | DISAGREE`.

**If GPT AGREE:** finding moves to autosolve, tag `[debate-agreed]`,
action verdict from Claude's `Action:` field.

### Round 2 (only if GPT DISAGREE)

Claude considers GPT's Round 1 recommendation, re-runs `/plan:best-idea`
debate-mode, emits a fresh RECOMMENDATION:

- Concede → autosolve using GPT's rec, tag `[debate-agreed]`, action verdict from GPT's `Action:`
- Hold → tag `[unresolved]`, both RECOMMENDATION blocks preserved for Phase 6 best-idea tiebreaker

### Resume failure during debate

Mark the finding `[unresolved]` with both original positions. Continue.
