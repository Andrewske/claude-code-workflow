<!-- dual-review-protocol section file. Loaded lazily per the routing table in ../SKILL.md (the index). Original section numbers (§N) preserved for citation stability. Content is verbatim from the pre-split SKILL.md. -->

## 12. Tier Selection (Phase 1.6 cost policy)

All tiers run `gpt-5.4`. The cost lever is `model_reasoning_effort`.
Commands invoking this protocol classify each review as `lite`, `normal`, or
`high` before Phase 2 and emit `MODEL_FLAGS` accordingly. Higher effort →
more reasoning tokens (billed as output) → higher cost on the same diff.

### Resolution order

1. **`--lite` flag** from the calling command → `TIER=lite`.
2. **`--high` flag** from the calling command → `TIER=high`.
3. **Auto-classify** (no flag):
   - `lines_changed` = sum of `+`/`-` from `git diff --shortstat <range>`
   - `files_changed` = files count from same `--shortstat`
   - `paths` = `git diff --name-only <range>`
   - **Sensitive-path regex** (any match → `high`):
     ```
     migrations/|auth/|billing/|payments/|infrastructure/|\.github/workflows/|webhooks/|scheduledEvents/|src/utils/crypto/|court-api/
     ```
   - **UI-file regex** (any match → `high`):
     ```
     \.(tsx|jsx|scss)$
     ```
   - **Large diff** (any match → `high`): `lines_changed ≥ 1500` OR `files_changed ≥ 20`.
   - **Lite tier** iff: `lines_changed < 200` AND `files_changed ≤ 5` AND no sensitive/UI/large match.
   - Else → `TIER=normal`.

   Rationale: pricing is uniform across reasoning levels at the per-token
   rate, but high effort consumes meaningfully more reasoning-output tokens.
   Reserve `high` for diffs that need deeper exploration (sensitive paths,
   UI surface, or sheer size). Default `normal` (medium effort) handles the
   bulk of code review with strong fidelity. `lite` is the cost floor for
   trivial diffs.

### MODEL_FLAGS by tier

For Phase 2 code reviews, derive `MODEL_FLAGS` from `TIER` and use it in
place of the inline `-m gpt-5.4 -c model_reasoning_effort=medium`
example in §1. The rest of the `codex exec` invocation (sandbox, `--json`,
`--output-schema`, `-C <workdir>`) is unchanged.

| Tier | MODEL_FLAGS |
|---|---|
| `lite` | `-m gpt-5.4 -c model_reasoning_effort=low` |
| `normal` | `-m gpt-5.4 -c model_reasoning_effort=medium` |
| `high` | `-m gpt-5.4 -c model_reasoning_effort=medium` |

Phase 3 triage and Phase 4 debate stay on
`gpt-5.4 -c model_reasoning_effort=medium` regardless of tier.

### Print convention

After classification, the calling command prints one line:

```
Tier: {lite|normal|high} (reason: <reason-string>)
```

Reason strings (first matching reason in this order wins):

| Source | Reason string |
|---|---|
| `--lite` flag | `--lite override` |
| `--high` flag | `--high override` |
| sensitive-path match | `sensitive-path:<matched-token>` (e.g., `sensitive-path:webhooks/`) |
| UI-file match | `ui-files:<count>` |
| lines ≥ 1500 | `large-diff:<N>-lines` |
| files ≥ 20 | `large-diff:<N>-files` |
| all-clear lite | `small-diff` |
| else | `default-normal` |

### Scope

§12 applies to commands that invoke code-review GPT phases:
`/dual-code-review` and `/review-pr`. Plan-review commands (`/dual-plan-review`,
`/gpt-review`, `/ask-gpt`) default to `normal` (medium effort) and accept
`--high` for adversarial deep dives.
