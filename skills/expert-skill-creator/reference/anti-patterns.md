# Anti-Patterns to Avoid

Common mistakes that reduce skill effectiveness.

## Description Anti-Patterns

### Vague Description
```yaml
# ❌ Bad
description: Helps with documents

# ✅ Fix
description: Create, edit, and analyze Word documents (.docx) with support 
  for tracked changes, comments, and formatting. Use when working with 
  professional documents, resumes, reports, or any .docx files.
```

**Why it fails:** Won't trigger for specific requests.

### Wrong Voice
```yaml
# ❌ Bad
description: I can help you process Excel files

# ✅ Fix
description: Process Excel files (.xlsx) for data extraction, formula 
  evaluation, and report generation. Use when working with spreadsheets.
```

**Why it fails:** First/second person causes discovery issues.

### Missing Triggers
```yaml
# ❌ Bad
description: Converts images between formats using Python

# ✅ Fix
description: Convert images between formats (PNG, JPEG, WebP, GIF). Use 
  when converting, resizing, or compressing images. Triggers on .png, 
  .jpg, .webp, .gif or "convert image", "resize image".
```

**Why it fails:** No actionable phrases for Claude to match.

---

## Content Anti-Patterns

### Kitchen Sink SKILL.md
```markdown
# ❌ Bad - 800 lines, everything included
## Complete API Reference
[300 lines]
## All Error Codes
[200 lines]
## Extended Examples
[200 lines]
## Edge Cases
[100 lines]
```

```markdown
# ✅ Fix - Split into reference files
## Quick Start
[10 lines]

## Reference
- API: [reference/api.md](reference/api.md)
- Errors: [reference/errors.md](reference/errors.md)
- Examples: [reference/examples.md](reference/examples.md)
```

**Why it fails:** Wastes tokens on every invocation.

### Explaining What Claude Knows
```markdown
# ❌ Bad
## What is JSON?
JSON (JavaScript Object Notation) is a lightweight data interchange 
format that is easy for humans to read and write...

# ✅ Fix
[Just don't include it. Claude knows what JSON is.]
```

**Why it fails:** Wastes tokens on common knowledge.

### Deeply Nested References
```markdown
# ❌ Bad
SKILL.md → overview.md → details.md → specifics.md → actual_content.md

# ✅ Fix
SKILL.md → overview.md
SKILL.md → details.md  
SKILL.md → specifics.md
```

**Why it fails:** Claude may partially read nested files.

---

## Script Anti-Patterns

### Scripts That Punt Errors
```python
# ❌ Bad
def process_file(path):
    return open(path).read()  # Just crashes on error

# ✅ Fix
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating empty")
        Path(path).touch()
        return ""
    except PermissionError:
        print(f"Cannot access {path}, check permissions")
        return None
```

**Why it fails:** Claude can't recover from cryptic errors.

### Magic Numbers
```python
# ❌ Bad
TIMEOUT = 47
RETRIES = 5
CHUNK_SIZE = 8192

# ✅ Fix
# HTTP requests typically complete within 30 seconds
REQUEST_TIMEOUT = 30

# Most intermittent failures resolve by second retry
MAX_RETRIES = 3

# 8KB chunks balance memory usage and I/O efficiency
CHUNK_SIZE = 8 * 1024
```

**Why it fails:** Claude can't adjust values intelligently.

### Windows Paths
```markdown
# ❌ Bad
See scripts\helper.py for details
Load reference\guide.md

# ✅ Fix
See scripts/helper.py for details
Load reference/guide.md
```

**Why it fails:** Breaks on Unix systems (most Claude environments).

---

## Workflow Anti-Patterns

### No Validation Steps
```markdown
# ❌ Bad
1. Create mapping
2. Apply changes
3. Done!

# ✅ Fix
1. Create mapping
2. **Validate mapping** (REQUIRED)
3. Apply changes
4. **Verify output**
5. Done only if verification passes
```

**Why it fails:** Errors discovered too late.

### Too Many Options
```markdown
# ❌ Bad
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or 
pdfminer, or camelot, or tabula...

# ✅ Fix
Use pdfplumber for text extraction:
```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image + pytesseract instead.
```

**Why it fails:** Decision paralysis, inconsistent approaches.

### Assuming Tools Are Installed
```markdown
# ❌ Bad
Use the pdf library to process files.

# ✅ Fix
Install required package:
```bash
pip install pdfplumber
```

Then use:
```python
from pdfplumber import open as open_pdf
```
```

**Why it fails:** Silent failures when dependency missing.

---

## Structural Anti-Patterns

### Auxiliary Files
```
# ❌ Bad
my-skill/
├── SKILL.md
├── README.md           # Unnecessary
├── CHANGELOG.md        # Unnecessary
├── INSTALLATION.md     # Unnecessary
├── CONTRIBUTING.md     # Unnecessary
└── reference/

# ✅ Fix
my-skill/
├── SKILL.md
└── reference/
```

**Why it fails:** Skills are for Claude, not human onboarding.

### Time-Sensitive Information
```markdown
# ❌ Bad
If you're doing this before August 2025, use API v1.
After August 2025, use API v2.

# ✅ Fix
## Current Method
Use API v2: `api.example.com/v2/`

<details>
<summary>Legacy v1 (deprecated)</summary>
Previously: `api.example.com/v1/`
</details>
```

**Why it fails:** Becomes incorrect without updates.

### Inconsistent Terminology
```markdown
# ❌ Bad
Use the API endpoint... connect to the URL... call the route... 
access the path...

# ✅ Fix
Use the API endpoint... call the endpoint... access the endpoint...
```

**Why it fails:** Confuses Claude about what's being referenced.

---

## Testing Anti-Patterns

### Never Testing with Real Tasks
```markdown
# ❌ Bad
Created skill, looks good, ship it!

# ✅ Fix
1. Fresh Claude session with skill
2. Ask realistic questions
3. Watch what Claude reads/does
4. Fix based on observations
```

**Why it fails:** Discovery and navigation issues go unnoticed.

### Only Testing with One Model
```markdown
# ❌ Bad
Works with Opus, good enough!

# ✅ Fix
Test with:
- Haiku (needs more guidance)
- Sonnet (balanced)
- Opus (might be over-explained)
```

**Why it fails:** Different models need different detail levels.

---

## Quick Reference: Red Flags

| Red Flag | Likely Problem |
|----------|----------------|
| SKILL.md over 500 lines | Not using progressive disclosure |
| Description under 50 chars | Missing triggers |
| "I can help you..." | Wrong voice |
| Multiple library options | Too many choices |
| Scripts with bare `open()` | Missing error handling |
| Backslashes in paths | Windows-only |
| No validation step | Error-prone workflow |
| README.md in skill | Unnecessary files |
| "Before/after date X" | Time-sensitive |
