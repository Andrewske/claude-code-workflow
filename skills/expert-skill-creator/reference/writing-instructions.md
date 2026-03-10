# Writing Instructions for SKILL.md

Guidelines for writing effective skill instructions.

## Core Philosophy

**Claude is already smart.** Your job is to provide:
- What Claude doesn't know (your specific context)
- What Claude should do (procedures)
- Where to find things (navigation)

NOT:
- Generic explanations
- How programming works
- What libraries do

## Structure Template

```markdown
# [Skill Name]

## Quick Start
[Minimal working example - 5-10 lines max]

## Workflows
### [Common Task 1]
[Steps with script references]

### [Common Task 2]
[Steps with script references]

## Quick Reference
[Tables, commands, key lookups]

## Deep Dives
- **[Topic A]**: See [reference/topic-a.md](reference/topic-a.md)
- **[Topic B]**: See [reference/topic-b.md](reference/topic-b.md)

## Dependencies
[Required packages and install commands]
```

## Line Budget

| Section | Target | Maximum |
|---------|--------|---------|
| Quick Start | 10 lines | 20 lines |
| Each Workflow | 20 lines | 50 lines |
| Quick Reference | 20 lines | 40 lines |
| Deep Dives | 10 lines | 20 lines |
| **Total SKILL.md** | **300 lines** | **500 lines** |

## Writing Style

### Use Imperative Voice
```markdown
# ✅ Good
Extract text from the PDF using pdfplumber.
Run the validation script before proceeding.

# ❌ Bad
You should extract text from the PDF.
The user will want to run validation.
```

### Be Concise
```markdown
# ✅ Good (50 tokens)
## Extract PDF Text
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

# ❌ Bad (150 tokens)
## Extract PDF Text
PDF files are a common format that contains text and images. To extract 
text from a PDF file, you'll need to use a library. There are many 
libraries available, but we recommend pdfplumber because it's easy to 
use and handles most cases well. First, install it with pip, then...
```

### Tables Over Prose
```markdown
# ✅ Good
| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server |
| `npm run test` | Run tests |
| `npm run build` | Production build |

# ❌ Bad
To start the development server, run `npm run dev`. If you want to run 
the tests, use `npm run test`. For a production build, the command is 
`npm run build`.
```

### Code Over Description
```markdown
# ✅ Good
Rotate PDF 90 degrees:
```bash
python scripts/rotate.py input.pdf 90 output.pdf
```

# ❌ Bad
To rotate a PDF, you need to specify the input file, the rotation angle 
in degrees (90, 180, or 270), and the output file path. The script will 
read the input, apply the rotation transformation to each page, and 
write the result to the output file.
```

## Workflow Patterns

### Simple Linear Workflow
```markdown
## Convert Image Format

1. Run conversion:
   ```bash
   python scripts/convert.py input.png output.jpg
   ```

2. Verify output exists and check file size.
```

### Workflow with Validation Loop
```markdown
## Fill PDF Form

```
Progress:
- [ ] 1. Analyze form
- [ ] 2. Create mapping
- [ ] 3. Validate (REQUIRED)
- [ ] 4. Fill form
- [ ] 5. Verify output
```

**Step 1: Analyze**
```bash
python scripts/analyze_form.py input.pdf > fields.json
```

**Step 2: Map fields**
Edit `fields.json` to add values for each field.

**Step 3: Validate**
```bash
python scripts/validate.py fields.json
# Must pass before continuing!
```

**Step 4: Fill**
```bash
python scripts/fill_form.py input.pdf fields.json output.pdf
```

**Step 5: Verify**
```bash
python scripts/verify.py output.pdf
```

If verification fails, return to Step 2.
```

### Conditional Workflow
```markdown
## Modify Document

Determine modification type:

**Creating new content?**
→ Use docx-js library
→ See [reference/creating-docs.md](reference/creating-docs.md)

**Editing existing content?**
→ Modify XML directly
→ See [reference/editing-docs.md](reference/editing-docs.md)
```

## Reference Linking

### When to Link vs. Include

**Include in SKILL.md:**
- Quick start examples
- Command summaries
- Navigation tables
- Critical warnings

**Link to reference files:**
- Detailed API docs
- Extended examples
- Edge case handling
- Historical context

### Link Format
```markdown
# ✅ Good - Descriptive with context
For form field specifications, see [reference/form-fields.md](reference/form-fields.md)

# ❌ Bad - No context
See [reference/form-fields.md](reference/form-fields.md)
```

## Common Sections

### Dependencies Section
```markdown
## Dependencies

Required packages:
- **pdfplumber**: `pip install pdfplumber`
- **Pillow**: `pip install Pillow`

System requirements:
- **Tesseract** (for OCR): `sudo apt install tesseract-ocr`
```

### Quick Reference Section
```markdown
## Quick Reference

### File Locations
| Component | Path |
|-----------|------|
| API routes | `src/app/api/` |
| Components | `src/components/` |
| Database schema | `prisma/schema.prisma` |

### Common Commands
| Task | Command |
|------|---------|
| Start dev | `npm run dev` |
| Run tests | `npm run test` |
| Type check | `npm run typecheck` |
```

### Troubleshooting Section
```markdown
## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFound` | Missing input | Check file path |
| `PermissionError` | File locked | Close other programs |
| `TimeoutError` | Large file | Increase timeout in config |
```
