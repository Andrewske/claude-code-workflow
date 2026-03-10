---
name: processing-[resource]
description: "Comprehensive [resource] manipulation toolkit for [capability 1], [capability 2], [capability 3], and [capability 4]. Includes validation scripts and error recovery. Use when working with [resource] files, [use case 1], [use case 2], or [use case 3]. Triggers on [file extensions], '[action phrase 1]', '[action phrase 2]', '[action phrase 3]'."
---

# [Resource] Processing

## Quick Start

[Simplest operation]:
```bash
python scripts/[simple_script].py input.ext output.ext
```

## Workflows

### [Workflow 1]: [Simple Operation]

```bash
python scripts/[script].py input output [options]
```

### [Workflow 2]: [Complex Operation with Validation]

**Follow this checklist:**

```
Progress:
- [ ] 1. Analyze input
- [ ] 2. Create plan
- [ ] 3. Validate plan (REQUIRED)
- [ ] 4. Execute
- [ ] 5. Verify output
```

**Step 1: Analyze**
```bash
python scripts/analyze.py input.ext > analysis.json
```

**Step 2: Create Plan**
Edit `analysis.json` to specify desired changes.

**Step 3: Validate**
```bash
python scripts/validate.py analysis.json
# Must pass before continuing!
```

**Step 4: Execute**
```bash
python scripts/execute.py input.ext analysis.json output.ext
```

**Step 5: Verify**
```bash
python scripts/verify.py output.ext
```

If verification fails, return to Step 2.

### [Workflow 3]: [Conditional Operation]

Determine operation type:

**[Condition A]?**
→ Use [approach A]
→ See [reference/approach-a.md](reference/approach-a.md)

**[Condition B]?**
→ Use [approach B]
→ See [reference/approach-b.md](reference/approach-b.md)

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze.py` | Extract structure | `analyze.py <input>` |
| `validate.py` | Check plan validity | `validate.py <plan.json>` |
| `execute.py` | Apply changes | `execute.py <input> <plan> <output>` |
| `verify.py` | Confirm output | `verify.py <output>` |

## Common Options

| Option | Purpose | Default |
|--------|---------|---------|
| `--verbose` | Detailed output | false |
| `--dry-run` | Preview changes | false |
| `--force` | Overwrite existing | false |

## Error Recovery

| Error | Cause | Recovery |
|-------|-------|----------|
| `ValidationError` | Invalid plan | Fix plan, re-validate |
| `InputError` | Corrupt input | Check input file |
| `OutputError` | Write failed | Check permissions |

## Advanced Features

- **[Feature A]**: See [reference/feature-a.md](reference/feature-a.md)
- **[Feature B]**: See [reference/feature-b.md](reference/feature-b.md)
- **[Feature C]**: See [reference/feature-c.md](reference/feature-c.md)

## Dependencies

Required packages:
- **[package1]**: `pip install [package1]`
- **[package2]**: `pip install [package2]`

System requirements:
- **[tool]**: `sudo apt install [tool]`
