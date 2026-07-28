---
name: dual-review-protocol
description: Shared protocol for dual-agent reviews (Claude + GPT) — finding format, triage, debate, codex execution, result presentation. Used by /dual-code-review, /dual-plan-review, /ask-gpt, /gpt-review. Invoke via `Read` from a command and follow the relevant section.
---

# Dual Review Protocol — Index

Shared knowledge for any command that runs Claude + GPT as parallel reviewers,
negotiates findings, and presents results. The substance lives in
`sections/*.md`; this file is a thin **routing index**. Templates live in
`templates/`, schemas in `schemas/`, the structural lens in `structural-lens.md`.

## How commands consume this (lazy load — read this carefully)

**Do NOT read this whole skill, and do NOT read every section file up front.**
At each phase, `Read` *only* the one section file that phase needs, per the
routing table below. Commands cite sections as `SKILL.md §N` (or `§N`) inline —
each `§N` lives in exactly one section file; resolve it via the table and read
that file when you reach that phase. Section numbers are preserved verbatim
across the split, so every existing `§N` citation in a command still resolves.

Commands keep their own workflow logic (argument parsing, human gates, queue
routing, file I/O); this skill keeps the *content* (prompts, formats, rules).

## Routing table — `§N` → file → when to read

| Sections | File | Read at |
|---|---|---|
| §1 Codex execution (invoke, model select, retry/fallback, pricing) · §10 Error-handling table | `sections/codex.md` | Phase 2 (before first codex call); §10 only on a codex failure |
| §2 Finding format & parsing | `sections/findings.md` | Phase 2 (before emitting/parsing findings) |
| §3 Review lenses (+ Glade patterns) · §14 Structural maintainability & `--thermo` | `sections/lenses.md` | Phase 2 (Claude review); §14 when `--thermo`/structural axis applies |
| §4 Triage · §5 Dedup · §13 Low-finding short-circuit | `sections/triage.md` | Phase 3 |
| §6 Debate protocol | `sections/debate.md` | Phase 4 — **only if triage produced ≥1 disagreement**; skip the read on a fully-agreed run |
| §7 Routing · §8 Result presentation (+ leverage summary) · §9 Phase-6 tiebreaker · §11 Fairness | `sections/routing-present.md` | Phase 5–6 |
| §12 Tier selection (cost policy) | `sections/tier.md` | Phase 1.6 (tier classification) |
| `/dual-code-review` Phase 6 resolution flow (Steps 1–5, input grammar) | `sections/resolution-code.md` | Phase 6, only after the user says **go** |
| `/review-pr` Phase 6 resolution + GitHub POST flow (irreversibility contract, Steps 0–6) | `sections/resolution-pr.md` | Phase 6, only after the user says **go**; read fully before any POST |

Typical early-phase footprint: `codex.md` + `findings.md` + `lenses.md` + `tier.md`.
`triage.md`/`debate.md` and `routing-present.md` load only when those phases run
(`debate.md` only when triage finds a disagreement);
a clean APPROVE / low-finding short-circuit skips most of them.

## 0. Voice setup — always run first

`Read` `~/.claude/skills/outbound-prose-setup/SKILL.md` and follow it as the first action of the calling command, before any codex invocation, finding generation, triage, debate, presentation, or POST step. Applies to every invocation, including resumed runs and Phase 5/6 re-renders.

Internal prose (findings produced by codex, triage/debate verdicts) is NOT outbound — it stays in-line. Only review bodies and inline comments posted to GitHub go through `voice-writer`.

## Contract (applies to all consumers)

- Consumers: `/dual-code-review`, `/dual-plan-review`, `/gpt-review`, `/ask-gpt` (and `/review-pr`).
- Section numbering is stable — do not renumber. To add content, extend the
  relevant section file and, if it's a new section, add a row above.
- §12 (tier) and §13 (low-finding) scope to `/dual-code-review` and `/review-pr`
  only; plan-review commands default to `normal` tier and full triage.
- §14 (structural/thermo) scopes to `/dual-code-review` and `/plan:code-review`;
  `/review-pr` does not apply that axis.
