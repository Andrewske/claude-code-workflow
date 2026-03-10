# Progressive Disclosure

How to structure skills so Claude loads information only when needed.

## The Three-Tier System

```
┌─────────────────────────────────────────────────────────┐
│ Tier 1: Metadata (~100 tokens)                          │
│ • name + description                                    │
│ • Always in context                                     │
│ • Used for skill discovery                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ (skill triggers)
┌─────────────────────────────────────────────────────────┐
│ Tier 2: SKILL.md Body (<5k tokens)                      │
│ • Overview and navigation                               │
│ • Quick start examples                                  │
│ • Workflow summaries                                    │
│ • Links to reference files                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ (as needed)
┌─────────────────────────────────────────────────────────┐
│ Tier 3: Reference Files (unlimited)                     │
│ • Detailed documentation                                │
│ • Extended examples                                     │
│ • Domain-specific content                               │
│ • Scripts (executed, not loaded)                        │
└─────────────────────────────────────────────────────────┘
```

## Why This Matters

**Without progressive disclosure:**
- 100 skills × 5k tokens = 500k tokens always loaded
- Exceeds context window
- Degrades performance

**With progressive disclosure:**
- 100 skills × 100 tokens = 10k tokens for metadata
- Only triggered skill's SKILL.md loads
- Reference files load only when navigated

## Design Patterns

### Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick Start
[10-line example]

## Features
- **Text extraction**: See [reference/extraction.md](reference/extraction.md)
- **Form filling**: See [reference/forms.md](reference/forms.md)
- **Merging**: See [reference/merging.md](reference/merging.md)
```

Claude loads extraction.md only if the task involves extraction.

### Pattern 2: Domain-Specific Organization

```
bigquery-skill/
├── SKILL.md              # Overview + navigation
└── reference/
    ├── finance.md        # Revenue, ARR, billing
    ├── sales.md          # Pipeline, opportunities
    ├── product.md        # Usage, features
    └── marketing.md      # Campaigns, attribution
```

SKILL.md:
```markdown
## Datasets

| Domain | Reference |
|--------|-----------|
| Finance | [reference/finance.md](reference/finance.md) |
| Sales | [reference/sales.md](reference/sales.md) |
| Product | [reference/product.md](reference/product.md) |
| Marketing | [reference/marketing.md](reference/marketing.md) |

## Quick Search
```bash
grep -i "revenue" reference/finance.md
grep -i "pipeline" reference/sales.md
```
```

Claude loads only the relevant domain file.

### Pattern 3: Conditional Details

```markdown
## Document Modification

**Creating new content?**
→ Use docx-js: [reference/creating.md](reference/creating.md)

**Editing existing?**
→ Modify XML: [reference/editing.md](reference/editing.md)

**Working with tracked changes?**
→ See: [reference/tracked-changes.md](reference/tracked-changes.md)
```

Only the relevant path loads.

### Pattern 4: Searchable Large Files

For reference files over 500 lines, provide grep patterns:

```markdown
## API Reference

Full documentation: [reference/api.md](reference/api.md) (800 lines)

### Quick Search
```bash
# Find authentication methods
grep -A 10 "## Authentication" reference/api.md

# Find specific endpoint
grep -A 20 "### /api/users" reference/api.md

# Find error codes
grep -B 2 -A 5 "Error:" reference/api.md
```
```

## Reference File Guidelines

### Keep References One Level Deep

```
# ❌ Bad - Too nested
SKILL.md → advanced.md → details.md → actual_info.md

# ✅ Good - One level
SKILL.md → advanced.md
SKILL.md → details.md
SKILL.md → actual_info.md
```

Claude may only partially read deeply nested files.

### Add Table of Contents for Long Files

```markdown
# API Reference

## Contents
- [Authentication](#authentication)
- [Users Endpoint](#users-endpoint)
- [Products Endpoint](#products-endpoint)
- [Error Codes](#error-codes)
- [Rate Limiting](#rate-limiting)

## Authentication
...
```

Ensures Claude sees full scope even when previewing.

### Organize by Use Case, Not File Type

```
# ❌ Bad - By type
reference/
├── schemas.md
├── examples.md
├── errors.md

# ✅ Good - By use case
reference/
├── user-management.md    # Schema + examples + errors for users
├── payments.md           # Schema + examples + errors for payments
├── reporting.md          # Schema + examples + errors for reports
```

## Scripts: The Ultimate Progressive Disclosure

Scripts are **token-free until output appears**:

```markdown
## Analyze Form Structure

```bash
python scripts/analyze_form.py input.pdf
```

Output:
```json
{"fields": [...], "pages": 3}
```
```

The script itself (maybe 100 lines) never enters context. Only its output does.

### When to Use Scripts vs. Reference Files

| Content Type | Use Script | Use Reference |
|--------------|------------|---------------|
| Deterministic operation | ✅ | |
| Complex validation | ✅ | |
| Data extraction | ✅ | |
| Conceptual explanation | | ✅ |
| Examples and patterns | | ✅ |
| Decision guidance | | ✅ |

## Measuring Token Efficiency

### Good Skill Structure
```
Metadata:        ~100 tokens (always loaded)
SKILL.md body:   ~2000 tokens (when triggered)
Reference files: ~10000 tokens (as needed, rarely all)
Scripts:         0 tokens (executed, not loaded)
─────────────────────────────────────────────
Typical usage:   ~2500 tokens
```

### Bad Skill Structure
```
Metadata:        ~100 tokens
SKILL.md body:   ~8000 tokens (everything inline)
Reference files: 0 (nothing split out)
Scripts:         0
─────────────────────────────────────────────
Every usage:     ~8100 tokens
```

## Anti-Patterns

### Everything in SKILL.md
Don't cram all content into the main file. Split by topic.

### Reference Files That Reference Each Other
Avoid `a.md → b.md → c.md` chains. Keep flat.

### Unused Reference Files
If a file is never navigated to, delete it.

### Scripts Loaded as Documentation
If showing script content for understanding (not execution), keep it short or summarize the algorithm instead.
