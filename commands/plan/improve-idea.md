---
description: Brainstorm improvements, simplifications, and "wouldn't it be cool" features before implementing an idea
argument-hint: <path-to-plan>
---

# Improve Idea

## Phase 1: Plan Selection

$argument provided? Use that path.

Otherwise: Follow **Plan Selection Pattern** (README.md) with status filter: `ready`

After selection: Read the plan's README.md and all task files.

---

## Phase 2: Four-Lens Analysis

Review the design through four lenses. **Number suggestions sequentially across ALL sections** (1, 2, 3... not restarting).

### Simplify (0-4 suggestions)
What can be removed, merged, or eliminated? Minimum viable version?
*(If lens doesn't apply, say so in one line and move on.)*

### High-Leverage (0-4 suggestions)
80/20 opportunities: small changes with disproportionate impact.

### Strengthen (0-4 suggestions)
What's fragile, unclear, or will cause implementation friction?

### Stretch (2-5 suggestions)
Be generous here — more ideas are better even if some feel unnecessary. Think expansively:
- "Wouldn't it be cool if..." — delightful features users didn't know they wanted
- Future-proofing — cheap hooks now, expensive retrofits later
- Wild cards — might be genius or terrible, include them anyway
- Adjacent possibilities — what does this unlock if we push it further?
- "What could go wrong?" — surface blind spots and risks

### Suggestion Format
Each suggestion, exactly:
```
**{N}. {Title}** [{Low|Med|High}]
{What changes} → {Why it matters}
```

Example:
```
**3. Remove auth middleware** [Low]
Consolidate three auth checks into single entry point → Reduces 40 lines to 12
```

### Summary
After all suggestions:
1. **Top 3 by value-to-effort**, ranked
2. **If only one:** Which and why?

Then prompt:
> Ready to resolve. Say **go** to walk through, or pick numbers to discuss.

---

## Phase 3: Resolution (on "go")

Walk through **every** suggestion one at a time. Do NOT skip or batch suggestions — each one gets user input.

### For each suggestion:

Present it with options:
```
**{N}. {Title}**
{What} → {Why}

- A: Apply as described
- B: Apply with modification: {variation}
- C: Skip

Recommended: {X} — {reason}
```

**STOP. Present ONE suggestion, then end your response. Do not continue until user replies.**

### After all suggestions resolved:

Apply approved changes to plan documents.
> ✅ Applied. Ready for /plan:start-implementation.
