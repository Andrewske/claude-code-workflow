<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 3. Review Lenses

### Code-review lenses

**GPT (production resilience):** Error handling. Defensive coding. Failure modes.
Performance. Security. Race conditions. Resource management. DRY (>20 line
duplications). Architecture layers (logic in wrong layer). See
`templates/gpt-prompt-code.md` for the full reviewer prompt.

**Claude (correctness & architecture):** Logic errors. Defensive coding.
Edge cases. Type safety. Architecture layers. DRY violations. Design system
compliance (frontend). Simplicity. Dependency ordering. CI/CD safety.

**Structural maintainability:** orthogonal maintainability/simplification axis —
see `structural-lens.md`. Applied by `/dual-code-review` and `/plan:code-review`
(self-review surfaces); **NOT** `/review-pr`. Mechanical checks (Block A)
always-on for those commands; the ambition lens + approval bar (Blocks B/C)
gate behind `--thermo`. See §14.

**High-frequency Glade patterns** (mined from accepted PR feedback — bots catch
these on ~91% of diffs that ship them; hunt them explicitly, grep can't):

- **Comment / error-message vs code drift** — every comment, doc line, error
  string, and hard-coded `file:line` ref must still match what the code does.
- **Empty is not absent** — guards on missing/`null` that a present-but-empty or
  whitespace-only string slips past (`!v?.trim()`, not just `v == null`).
- **Side-effect before validation** — anything persisted/uploaded/emitted before
  its PII/`sha256`/auth guard runs.
- **Incomplete flag plumbing** — a new flag/param declared in one layer but not
  threaded end-to-end, so a selector requires a value nothing ever sets.
- **Inverted clamp / unit mismatch** — `Math.max` where `min` was meant (a cap
  that allows oversize); `.length` (UTF-16 units) used where bytes are intended.
- **Behavior change under a `refactor` label** — an empty-return that now throws,
  an auth path silently narrowed. See `~/.claude/rules/glade-backend.md`.

### Plan-review lenses

**GPT (implementation feasibility):** Unstated prerequisites. Dependency
ordering. Simplification. Integration risks. Missing error handling. Code
verification (use `--search`). See `templates/gpt-prompt-plan.md` for the
full reviewer prompt.

**Claude (adversarial):** Assumption stress test. Failure mode exploration.
Simplicity audit. Architecture check. Dependency ordering.

### Universal rules for both reviewers

- Technical only. Skip docs style, formatting, naming opinions.
- Specific or silent — every finding cites file+line (or section).
- Every criticism gets a concrete fix — not "consider X" but "in file.ts line 42, change Y to Z".
- Quality over quantity. Aim for ≤8 findings unless systemic issues.
- Use `--search` to verify assumptions before citing them.

After all findings, output:
```
WHAT WORKS:
[2-5 specific strengths the author got right]
```

## 14. Structural Maintainability & `--thermo`

Canonical content lives in `structural-lens.md` (sibling file). This section
defines *when* each block applies and the orchestration mechanics. Scope:
`/dual-code-review` and `/plan:code-review` only — **`/review-pr` does not
apply this axis** (no maintainability opinions on a teammate's incoming PR).

### Block application

| Block | Content | When |
|---|---|---|
| A | Mechanical checks (file-size budget, spaghetti-growth, refactor-didn't-reduce, thin-wrapper) | Always-on for self-review commands |
| B | Ambition / code-judo lens | `--thermo` only |
| C | Approval bar / presumptive blockers | `--thermo` only |
| D | GPT-prompt addendum (A always; A+B under `--thermo`) | `/dual-code-review` GPT side |

Claude `Read`s `structural-lens.md` and applies the in-scope blocks as extra
lenses alongside §3. Findings use the same FINDING schema (§2) and the same
universal rules (§3): cite file:line, concrete fix, ≤8 findings, high-conviction
over nit-flood.

### GPT side (`/dual-code-review` only)

After rendering `templates/gpt-prompt-code.md` and substituting placeholders,
**append** Block D to the prompt file (Block A always; Block A+B under
`--thermo`). This reaches the GPT reviewer without editing the shared template
(which `/review-pr` also renders). Mirrors the existing large-PR "FOCUS FILES"
append mechanic.

### `--thermo` → tier

`--thermo` is orthogonal to the §12 reasoning-effort tier but implies deep
exploration. Resolution: when `--thermo` is set and `--lite` is **not** present,
force `TIER=high` (reason string `thermo`). An explicit `--lite` wins — tier
stays `lite`, but the ambition lens still applies (the lens is independent of
reasoning effort). `--high` and `--thermo` together are redundant but harmless.

### Effect on routing / verdict

`/dual-code-review` has no GitHub verdict. Under `--thermo`, elevate
structural-regression findings to HIGH so they route to the individual-review
queue (§7) rather than silent autosolve-skip, and surface the Block C approval
bar in the Phase 5 presentation. `/plan:code-review` (which does emit a verdict)
may return `REQUEST CHANGES` on a structural regression under `--thermo` even
when behavior is correct.
