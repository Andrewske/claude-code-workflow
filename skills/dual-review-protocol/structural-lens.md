# Structural Maintainability Lens

Canonical content for the structural / maintainability review axis. Single source of truth
consumed by `/dual-code-review` and `/plan:code-review` (the self-review surfaces). **NOT used by
`/review-pr`** — maintainability opinions don't belong on a teammate's incoming PR.

This axis is orthogonal to the correctness/security/Glade-pattern lenses in `SKILL.md §3`. It asks
one question those lenses don't: *is this the simplest possible implementation, or did the diff
leave the codebase messier than it found it?*

Consumers pull the blocks they need:
- **Block A** — always-on for self-review commands.
- **Blocks B + C** — opt-in via `--thermo`.
- **Block D** — the GPT-prompt addendum `/dual-code-review` appends to the rendered GPT prompt.

---

## Block A — Mechanical checks (always-on)

Cheap, high-signal, low-variance. Apply on every self-review run. Each finding cites `file:line`
with evidence, same discipline as §3.

- **File-size budget.** Flag any file the diff pushes from under 1000 lines to over 1000 lines.
  Treat as a strong smell by default — prefer extracting helpers/subcomponents/modules first. Only
  waive with a compelling structural reason and a still-clearly-organized result.
  → *"this pushes the file past 1k lines. can we decompose this first?"*
- **Spaghetti-growth.** A new ad-hoc conditional, special case, or one-off branch inserted into an
  existing busy flow is a **design finding, not a nit**. Push the logic behind a dedicated helper,
  policy object, or dispatcher instead of tangling the existing path.
  → *"this adds another special-case branch into an already busy flow. can we move this behind its own abstraction?"*
- **Refactor-didn't-reduce.** A `refactor`-labeled change that moves complexity around without
  deleting concepts. The reader still holds the same number of moving pieces in their head.
  → *"this refactor moves complexity around, but doesn't really delete it. is there a way to make the model itself simpler?"*
- **Thin-wrapper / identity abstraction.** A pass-through helper, wrapper, or layer that adds
  indirection without buying clarity. Prefer the direct flow.
  → *"this abstraction seems unnecessary. can we just keep the direct flow?"*

---

## Block B — Ambition / code-judo lens (`--thermo` only)

Be **ambitious** about structure. Do not stop at "this could be a bit cleaner." Actively hunt for
restructurings that preserve behavior while making the implementation dramatically simpler.

- Look for the reframing that makes whole branches, helpers, modes, conditionals, or layers
  disappear entirely — not just get centralized.
- Assume a "code-judo" move is often available: a re-organization that uses the existing
  architecture more effectively and makes the change feel inevitable in hindsight.
- Prefer **deleting** complexity over rearranging it. If there's a path to remove moving pieces
  rather than relocate them, push hard for it.
- Reframe state models so conditionals vanish; change ownership boundaries so the feature becomes a
  natural extension of an existing abstraction; turn special-case logic into a simpler default with
  fewer exceptions.
  → *"i think there's a code-judo move here that makes this much simpler. can we reframe this so these branches disappear?"*

---

## Block C — Approval bar / presumptive blockers (`--thermo` only)

Do not pass a change merely because behavior is correct. Under thermo, these are **presumptive
blockers** unless the author justifies them clearly:

- A lot of incidental complexity preserved when a plausible code-judo move would delete it.
- A file pushed from under 1000 to over 1000 lines without a compelling reason.
- Ad-hoc branching that makes an existing flow more tangled.
- A local problem solved by scattering feature checks across shared code.
- An unnecessary abstraction, wrapper, or cast-heavy contract that makes the design more indirect.
- A duplicated helper or logic in the wrong layer when a clear canonical home exists.

Be direct and demanding about quality, never rude. If the implementation missed an opportunity for
a dramatic simplification, say so clearly. Prefer a small number of high-conviction structural
comments over a long list of cosmetic notes — do not flood the review with nits.

---

## Block D — GPT prompt addendum

Append this to the rendered GPT reviewer prompt (after placeholder substitution). Include the
Block A section always; include the Block B section only under `--thermo`.

```
ADDITIONAL LENS — Structural maintainability (pick each issue through exactly one of these,
same ≤8-findings discipline; cite file:line):
- File-size budget: flag any file the diff pushes from <1000 to >1000 lines; prefer decomposition first.
- Spaghetti-growth: a new ad-hoc conditional/special-case bolted into an existing busy flow is a design finding, not a nit — push it behind a dedicated helper/dispatcher.
- Refactor-didn't-reduce: a refactor that rearranges complexity without deleting concepts.
- Thin-wrapper: pass-through indirection that adds a layer without buying clarity.
```

Under `--thermo`, also append:

```
THERMO — Be ambitious about structure. Hunt for "code-judo" moves: behavior-preserving
restructurings that make whole branches/modes/layers disappear entirely. Prefer deleting
complexity over rearranging it. Do not pass a change merely because it is correct — a preserved
pile of incidental complexity, a file crossing 1k lines, ad-hoc branch-tangling, or an obvious
missed simplification are presumptive blockers. High-conviction structural comments only.
```
