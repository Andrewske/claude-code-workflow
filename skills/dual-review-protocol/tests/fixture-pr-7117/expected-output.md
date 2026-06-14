# Expected Output: dual-code-review fixture for PR #7117

**PR:** [glade-ai/noodle-api#7117](https://github.com/glade-ai/noodle-api/pull/7117) — `[CAS-673] feat(workflowCompiledDocument): add attorneyEmail + attorneyPhone to debtor data`

**Captured:** 2026-04-30 from rewritten `/dual-code-review` (post-refactor baseline; no pre-refactor parity available).

**Repo state:** local `main` behind origin/main by 12 commits at capture time. PR branch `kevin/cas-673-noodle-api-add-attorneyemail-attorneyphone-to-case` exists on origin. GPT noted that `origin/main...HEAD` is empty locally and reviewed via `/tmp/.../diff.txt` — this matches the dual-code-review.md Phase 1 PR path, which writes the `gh pr diff` output to a temp file.

**Codex session ID:** `019ddf47-66fb-72b1-a315-2750584d99b7`. Persistent across `codex exec` initial → `codex exec resume` triage.

## Phase 1: scope

```
Reviewing: PR #7117 — [CAS-673] feat(workflowCompiledDocument): add attorneyEmail + attorneyPhone to debtor data
Commits: 2 (38a7ab8, d5daeeb)
Files changed: 3 (+113 -0)
```

Diff written to `/tmp/dual-code-review-1777567405-diff.txt` (134 lines).

## Phase 2: parallel reviews

### Claude (correctness & architecture lens)

```
FINDING:
- ID: C1
- Severity: MEDIUM
- File: src/services/workflowCompiledDocument/buildDebtorDataFromQuestionnaire.ts
- Line: 1037
- Category: defensive-coding
- Issue: personAttorney.email is assigned without trim() and without whitespace-only guard, breaking parity with the phone fallback in the same block which trims both candidates. A persisted email like '  attorney@example.com  ' or '   ' is accepted (whitespace is truthy), surfacing tainted values to downstream PDF/form generators.
- Evidence: `if (personAttorney.email) { debtorData.attorneyEmail = personAttorney.email; }` vs. `const attorneyPhone = personAttorney.daytimePhoneNumber?.trim() || personAttorney.mobilePhoneNumber?.trim();` two lines below.
- Fix: const attorneyEmail = personAttorney.email?.trim(); if (attorneyEmail) { debtorData.attorneyEmail = attorneyEmail; }
- Confidence: 75%
```

### GPT (production resilience lens)

Usage: input 594,728 tokens, output 4,310, cached 0. Estimated cost ≈ $3.10 (input $2.97 + output $0.13).

```
FINDING:
- ID: G1
- Severity: HIGH
- File: src/services/workflowCompiledDocument/buildDebtorDataFromQuestionnaire.ts
- Line: 1038
- Category: security
- Issue: Adding attorneyEmail and attorneyPhone to DebtorData causes attorney contact PII to be written to response logs for GET /webhooks/noodle-questionnaires/questionnaire/:questionnaireId/debtor-data. logResponseBody logs all response bodies, deepSanitize only redacts password, client_secret, and socialsecuritynumber, and this route returns { debtorData } directly.
- Evidence: `debtorData.attorneyEmail = personAttorney.email;` and `debtorData.attorneyPhone = attorneyPhone;`; global response logging calls deepSanitize(bodyToLog) then logger.info({ body: sanitizedBody }, 'response-body').
- Fix: Before shipping these new PII fields, add this route to src/middleware/logResponseBody/shouldLogRequest.ts ignoreRoutes as { method: 'GET', path: '/webhooks/noodle-questionnaires/questionnaire/:questionnaireId/debtor-data' }, or extend deepSanitize to redact email, attorneyEmail, phoneNumber, attorneyPhone, d2email, d2phoneNumber.
- Confidence: 94%
```

## Phase 3: triage

GPT self-evaluation + cross-evaluation (codex exec resume). Usage: input 750,317 (cumulative), output 5,206.

```
SELF-DISMISS: G1
REASON: The PR context explicitly identifies this as a known, pre-existing response logging PII leak that the new fields only extend, and the author has explicitly scoped the systemic redaction fix to a separate ticket.

FINDING: C1
VERDICT: DISAGREE
PREVIEW: Production create/update paths normalize personAttorney.email before persistence, so the cited whitespace-only value is not accepted through the service path this field reads from. A defensive trim at emission would be harmless, but this is not a material SRE/security finding without evidence of bypassing writers or dirty production data.

OVERLAP: NONE
```

Claude triage of GPT self-dismiss: AGREE — PR body explicitly scopes this out as pre-existing.

Routing:
- G1 → Dismissed (Context)
- C1 → debate queue (1 disagreement; would invoke Phase 4 best-idea debate)

## Issues encountered

1. **`codex exec resume -C` fails.** The codex CLI accepts `-C, --cd <DIR>` on `codex exec` but **NOT** on `codex exec resume` (`error: unexpected argument '-C' found`). SKILL.md Section 1 was wrong; fixed in this same session. Resumes use the session's recorded cwd.

2. **Local repo behind origin.** GPT correctly reported that `origin/main...HEAD` was empty locally but used the supplied `/tmp/.../diff.txt`. Phase 1 PR path is robust to this.

## Parity check guidance

For future refactors:

1. **Byte-identical comparison on rendered prompt** (`gpt-prompt.txt`) — should match modulo `{TIMESTAMP}` substitution and PR metadata (commit hashes, body if PR description was edited). The file is non-deterministic in `CHANGE SUMMARY` if the model re-derives it; keep CHANGE SUMMARY mechanical (commit log + diff stat) so it's stable.

2. **Structural comparison on findings** (`expected-output.md`):
   - Both reviewers should produce ≥1 finding for the email/phone code block.
   - GPT should flag the PII logging concern (HIGH/security).
   - Claude should flag the missing email trim (MEDIUM/defensive-coding).
   - Triage should self-dismiss G1 given the PR body context.
   - C1 should hit DISAGREE → debate queue.

3. **What divergence means investigate:**
   - Different number of findings (count drift).
   - Different routing of G1 (failure of self-dismiss path).
   - Triage that doesn't preserve the FINDING/VERDICT/PREVIEW format.
   - Resume failure (likely codex CLI flag drift — re-check `codex exec resume --help`).

## Files in this fixture

| File | Source |
|------|--------|
| `gpt-prompt.txt` | Rendered Phase 2 prompt |
| `codex-output.jsonl` | Raw GPT review JSONL |
| `triage-prompt.txt` | Phase 3 triage prompt sent via resume |
| `triage-output.jsonl` | Raw triage JSONL |
| `diff.txt` | PR diff (gh pr diff 7117) |
| `expected-output.md` | This file |

Phases 4–7 not captured (debate, present, resolve, cleanup) — the fixture stops at routing because applying fixes would mutate the working tree.
