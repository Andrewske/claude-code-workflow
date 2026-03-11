---
description: Capture ideas quickly with minimal friction. Append to docs/ideas.md with date and brief context.
---

# Idea Capture

Capture ideas the user shares with minimal friction.

## Behavior

1. **Listen**: Let the user share ideas freely
2. **Document**: Append each idea to `docs/ideas.md` (create if missing)
3. **Format**:
   ```markdown
   ## [Brief title] - YYYY-MM-DD

   [Idea description in 1-3 sentences]

   **Context**: [Which part of codebase this touches, if obvious]
   ```
4. **Research**: Only quick grep/glob if it helps identify affected area - no deep dives
5. **Respond**: Short confirmation (e.g., "Added: auth token refresh idea") unless you need clarification

## Guidelines

- Don't expand or plan - just capture
- Don't over-research - note obvious connections only
- Ask clarifying questions only if the idea is ambiguous
- Multiple ideas in one message = multiple entries
