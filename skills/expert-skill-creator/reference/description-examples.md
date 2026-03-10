# Description Examples

The description is the most critical part of your skill. Claude uses it to choose from potentially 100+ available skills.

## Requirements

1. **Third person voice** - The description injects into system prompt
2. **Specific capabilities** - What the skill does
3. **Trigger contexts** - When to use it
4. **Key terms** - File types, action words users would say
5. **Under 1024 characters**

## Formula

```
[What it does - specific capabilities]. [Additional capabilities]. 
Use when [trigger context 1], [trigger context 2], or [trigger context 3]. 
Triggers on [file types], [action phrases], [key terms].
```

## Good Examples

### Simple Utility Skill
```yaml
description: Convert images between formats (PNG, JPEG, WebP, GIF). Resize, 
  compress, and optimize images for web or print. Use when working with image 
  files, converting formats, resizing images, or optimizing file sizes. 
  Triggers on .png, .jpg, .jpeg, .webp, .gif files or "convert image", 
  "resize image", "compress image", "optimize image".
```

**Why it works:**
- Lists specific formats
- Lists specific actions
- Includes file extensions
- Includes trigger phrases

### Domain Knowledge Skill
```yaml
description: Query company BigQuery data warehouse for sales, finance, product, 
  and marketing metrics. Includes table schemas, common query patterns, and 
  data filtering rules. Use when analyzing company data, writing SQL queries, 
  generating reports, or answering questions about business metrics. Triggers 
  on "BigQuery", "sales data", "revenue", "pipeline", "metrics", "dashboard".
```

**Why it works:**
- Names the specific system
- Lists domains covered
- Mentions what's included
- Lists trigger keywords

### Project Knowledge Skill
```yaml
description: Deep knowledge of ProductPix architecture, data flows, debugging 
  patterns, and codebase navigation. Covers Next.js frontend, API routes, 
  Convex database, and Imagen integration. Use when investigating bugs, 
  understanding features, tracing issues, or debugging errors. Triggers on 
  "how does X work", "why is Y broken", "trace the flow", "debug this", 
  "ProductPix architecture".
```

**Why it works:**
- Names the project
- Lists key technologies
- Lists use cases
- Includes debug trigger phrases

### Complex Workflow Skill
```yaml
description: Comprehensive PDF manipulation toolkit for extracting text and 
  tables, filling forms, merging/splitting documents, and handling scanned 
  PDFs with OCR. Includes validation scripts and error recovery. Use when 
  working with PDF files, forms, document extraction, or PDF modification. 
  Triggers on .pdf files, "extract text", "fill form", "merge PDF", "split PDF".
```

**Why it works:**
- Lists all capabilities
- Mentions included tools
- File extension trigger
- Action phrase triggers

## Bad Examples

### Too Vague
```yaml
# ❌ Bad
description: Helps with documents
```
- No specific capabilities
- No trigger context
- Won't match user intent

### Missing Triggers
```yaml
# ❌ Bad
description: Converts images between different formats using Python libraries
```
- No file types listed
- No action phrases
- No "use when" context

### Wrong Voice
```yaml
# ❌ Bad
description: I can help you process Excel files and create reports
```
- Uses "I" (first person)
- Uses "you" (second person)
- Causes discovery problems

### Too Generic
```yaml
# ❌ Bad
description: Processes data and generates outputs
```
- Could match anything
- No specific domain
- No useful triggers

### Too Long (Over 1024 chars)
```yaml
# ❌ Bad
description: This skill provides comprehensive functionality for working with 
  various document formats including but not limited to Microsoft Word documents, 
  Excel spreadsheets, PowerPoint presentations, and PDF files. It can extract 
  text, modify content, convert between formats, apply formatting, handle tracked 
  changes, manage comments, process images embedded in documents, handle headers 
  and footers, work with tables, manage styles, process bibliographies, handle 
  cross-references, and much more. Use this skill whenever you need to work with 
  any kind of office document or when you need to process multiple documents at 
  once or when you need to convert documents between different formats or when...
  [continues for another 500 characters]
```
- Way over limit
- Tries to cover too much
- Should be multiple skills

## Trigger Phrase Patterns

### Action-Based Triggers
- "convert X", "transform X"
- "extract from", "parse"
- "create a", "generate a"
- "analyze", "debug", "trace"
- "fix", "repair", "resolve"

### File-Based Triggers
- Include extensions: `.pdf`, `.docx`, `.xlsx`
- Include format names: "PDF", "Word document", "Excel"
- Include mime types if relevant

### Question-Based Triggers
- "how does X work"
- "why is X broken"
- "where is X defined"
- "what does X do"

### Context-Based Triggers
- "for my project"
- "in our codebase"
- "company data"
- "internal API"
