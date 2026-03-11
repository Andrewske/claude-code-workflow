---
name: prompt-optimizer
description: Optimize prompts for any AI model (Claude, GPT, Gemini, Llama, etc.) using structured analysis and proven techniques. Diagnoses clarity gaps, applies model-specific optimizations, and delivers ready-to-use prompts. Use when crafting prompts, improving AI responses, debugging poor AI output, or building AI features. Triggers on "optimize prompt", "improve prompt", "prompt engineering", "better prompt", "AI keeps giving generic answers", "craft a system prompt", "write a prompt for".
---

# Prompt Optimizer

Transform rough prompts into precision-crafted instructions using the 4-D methodology.

## Quick Start

```
Input:  Rough prompt + target model (defaults to Claude)
Output: Optimized prompt + explanation of changes
```

1. If non-Claude model specified, fetch current prompting docs (see Live Docs Lookup below)
2. If prompt is about a specific library/framework, use context7 MCP to pull its docs
3. Deconstruct intent, entities, constraints
4. Diagnose clarity gaps and ambiguity
5. Present findings for review — do NOT apply changes yet
6. Walk through findings one at a time (on "go")
7. Apply approved changes and deliver optimized prompt

Default to quick optimization. Ask clarifying questions only for high-stakes or ambiguous prompts. User can say BASIC or DETAIL to override.

## Example: Before/After

**Before (vague):**
> "Help me write code documentation"

**After (optimized for Claude):**
```
You are a technical documentation specialist with expertise in API documentation.

Task: Create comprehensive API documentation for a RESTful endpoint.

Requirements:
- Include endpoint URL, HTTP method, and purpose
- Document all request parameters (type, required/optional, description)
- Provide response format with status codes
- Include 2-3 practical usage examples
- Write for intermediate developers
- Follow OpenAPI/Swagger conventions

Output format: Markdown with code blocks for examples
```

**What changed:** Added role assignment, explicit requirements, audience level, format spec, and documentation standard. Transformed a 5-word request into a prompt that will produce consistent, structured output.

## The 4-D Methodology

### 1. DECONSTRUCT
Extract from the raw prompt:
- **Core intent** - What the user truly wants
- **Key entities** - Subjects, objects, concepts
- **Output requirements** - Format, length, style, structure
- **Constraints** - Limitations, requirements
- **Gaps** - What's missing that would improve results

### 2. DIAGNOSE
Audit for quality issues:

| Issue | Symptom | Fix |
|-------|---------|-----|
| Clarity gap | Instructions ambiguous | Add explicit constraints |
| Low specificity | Generic AI responses | Add role, format, examples |
| Missing context | Off-target responses | Layer in background info |
| No structure | Rambling output | Add sections, formatting reqs |
| Complexity mismatch | Too simple/complex output | Match prompt structure to task |

### 3. DEVELOP
Apply techniques based on task type:

| Task Type | Primary Techniques |
|-----------|-------------------|
| Creative | Role assignment, tone emphasis, constraint-creativity balance |
| Technical | Precision framing, step decomposition, format specs |
| Educational | Few-shot examples, progressive structure, level targeting |
| Complex/Multi-step | Chain-of-thought, milestones, validation criteria |
| Analytical | Framework definition, evaluation criteria, structured output |

When optimizing an existing prompt, show changes inline using ~~strikethrough~~ for removed text and **bold** for additions, with brief annotations explaining each change.

Core technique templates: [reference/techniques.md](reference/techniques.md)

### 4. PRESENT FINDINGS

Present all proposed changes as numbered findings before applying anything:

```
## Prompt Optimization: [brief description]

**Target Model:** [model]
**Task Type:** [creative/technical/educational/complex/analytical]

### CRITICAL (Must Fix)

1. **[Change Title]**
   - **Problem**: [What's wrong or missing]
   - **Fix**: [Specific change to make]

---

### HIGH (Should Fix)

2. **[Change Title]**
   - **Problem**: [description]
   - **Fix**: [description]

---

### MEDIUM (Consider)

3. **[Change Title]**
   - **Problem**: [description]
   - **Fix**: [description]

---

### LOW (Nice to Have)

4. **[Change Title]**
   - **Problem**: [description]
   - **Fix**: [description]

Omit empty severity sections. Number findings sequentially across all sections.

---

### Summary
- **Top 3 by impact**, ranked
- **Pro Tip:** [Model-specific or usage advice]

> Ready to resolve. Say **go** to walk through, or pick numbers to discuss.
```

**STOP. Do NOT apply changes. Wait for user to say "go" or pick numbers.**

### 5. RESOLVE (on "go")

#### Step 1: Categorize
- **Autosolve** (≥90% confidence): Clear improvements, no trade-offs
- **Discussion** (<90%): Multiple valid approaches, user preference matters

#### Step 2: Discussion Items (one at a time)

For each:
```
**Finding {N}: [Title]**

- A: [Approach]
  - Pro: [benefit]
  - Con: [trade-off]

- B: [Approach]
  - Pro: [benefit]
  - Con: [trade-off]

Recommended: {X} — {reason}
```

**STOP. Present ONE discussion item, then end your response. Do not continue until user replies.**

#### Step 3: Autosolve Batch

After all discussion items resolved:
```
**Autosolve — High Confidence**
{N}. {Description} → {Change} ({%})
...

Confirm all, or call out numbers to skip/discuss.
```

#### Step 4: Apply & Deliver

Apply all approved changes and present the final optimized prompt:
```
**Optimized Prompt:**
[Ready-to-use prompt with all approved changes applied]
```

If the prompt is for a production system, offer to generate 3-5 test inputs (happy path, edge case, adversarial) to validate the prompt.

## Model-Specific Optimization

Defaults to Claude when target not specified (since we're in Claude Code).

### Live Docs Lookup

If the user specifies a non-Claude model, fetch the relevant prompting guide before applying the 4-D methodology. Model docs change frequently.

| Model Family | Primary Doc URL |
|-------------|----------------|
| Claude | `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` |
| OpenAI GPT/o-series | `https://platform.openai.com/docs/guides/prompt-engineering` |
| OpenAI Cookbook (model-specific) | `https://developers.openai.com/cookbook` (search for model name) |
| Gemini | `https://ai.google.dev/gemini-api/docs/prompting-strategies` |
| Mistral | `https://docs.mistral.ai/guides/prompting-capabilities` |
| Llama | `https://www.llama.com/docs/how-to-guides/prompting` |

**Lookup workflow:**
1. Fetch the relevant doc URL above using WebFetch
2. If the prompt is *about* a specific library/framework, also use context7 MCP (`resolve-library-id` then `get-library-docs`) to pull its docs
3. Apply model-specific tips during the DEVELOP phase
4. Skip lookup for Claude (our baseline) or if user wants a quick fix

For baseline model-specific tips: [reference/model-specific.md](reference/model-specific.md)
For full URL list and search strategies: [reference/doc-sources.md](reference/doc-sources.md)

### Quick Reference (Baseline)

| Model | Key Strength | Key Technique |
|-------|-------------|---------------|
| Claude (Opus/Sonnet) | Long context, reasoning | XML tags, thinking blocks, direct instructions |
| OpenAI GPT-5 | Agentic workflows, coding | `reasoning_effort`, caching layout, tool preambles |
| OpenAI o3 | Hard reasoning, math | Minimal prompts, no CoT scaffolding |
| Gemini 2.5 | Multimodal, massive context | Few-shot always, temperature 1.0, delimiters |
| Llama 4 / Open models | Cost efficiency, privacy | Simpler structure, explicit formatting, Q5+ quant |

## Troubleshooting Poor AI Output

| Problem | Root Cause | Prompt Fix |
|---------|-----------|------------|
| Too generic | Low specificity | Add role, constraints, examples |
| Misses the point | Weak context | Strengthen background, add goal statement |
| Inconsistent | No format spec | Add output format, evaluation criteria |
| Too verbose | No length constraint | Set explicit word/paragraph limits |
| Wrong tone | No style guidance | Specify tone, provide example output |
| Hallucinating | Over-broad scope | Narrow scope, add "only use provided info" |

## Anti-Patterns

Avoid these in optimized prompts:
- Hedging language ("maybe you could...") - use direct imperatives
- Multiple competing instructions without priority
- Negative framing ("don't do X") without positive alternative
- Wall of text without structure or sections
- Specifying what Claude already knows (e.g., explaining what JSON is)

## Deep Dives

- **[Techniques Catalog](reference/techniques.md)** - Prompt templates and structural patterns
- **[Model-Specific Guide](reference/model-specific.md)** - Model selection, comparison tables, baseline tips
- **[System Prompt Patterns](reference/system-prompts.md)** - Patterns for building AI agents and features
- **[Doc Sources](reference/doc-sources.md)** - Canonical URLs and search strategies for fetching current model docs
