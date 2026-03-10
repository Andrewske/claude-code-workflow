# Capture Error Pattern

Quickly capture a bug or error pattern we just encountered and add it to the project skill.

## Gather Information

Ask for (or extract from conversation context):

1. **Error message**: What exactly appeared?
2. **Symptom**: How did the user notice the problem?
3. **Root cause**: What was actually wrong?
4. **Investigation steps**: How did we diagnose it?
5. **Solution**: How was it fixed?

## Format Entry

Create entry in this format:

```markdown
---

## [Error Category]

### Error: [ErrorName/Type]

**Symptom**:
```
[User-visible behavior or error message]
```

**Root Cause**:
[Brief explanation of what causes this]

**Investigation**:
```bash
[Commands to diagnose - logs, queries, etc.]
```

**Solution**:
[How to fix it - code change, config, etc.]

**Prevention**:
- [How to avoid this in future]
```

## Add to Skill

Append the formatted entry to:
`.claude/skills/[project-skill]/reference/error-patterns.md`

If the file doesn't exist, create it with a header:
```markdown
# Error Patterns & Solutions

Common errors, their causes, and how to fix them.

[entries go here]
```

## Also Update Quick Diagnosis Table

Add a row to the quick diagnosis table in error-patterns.md (if one exists):

```markdown
| [keyword from error] | [Category] | [First check] | [Common fix] |
```

## Confirm

Tell the user:
- What was added
- Where it was added
- Suggest they commit the change

---

Error details from user: $ARGUMENTS
