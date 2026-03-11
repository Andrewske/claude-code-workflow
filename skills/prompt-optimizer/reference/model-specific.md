# Model-Specific Optimization Guide

Baseline tips for each model family. For current docs, use the live lookup in SKILL.md.

## Model Selection Guide

| Need | Best Choice | Why |
|------|------------|-----|
| Deep reasoning, nuanced writing | Claude Opus | Adaptive thinking, long context |
| Balanced speed/quality, coding | Claude Sonnet, GPT-5 | Strong instruction following |
| Speed, classification, high-volume | Claude Haiku, GPT-5-mini, Gemini Flash | Cost-efficient |
| Hard math, logic, proofs | OpenAI o3, DeepSeek R1 | Built-in reasoning |
| Multimodal (images, video, audio) | Gemini 2.5 Pro | Native multimodal |
| Massive context (1M+ tokens) | Gemini 2.5, Llama 4 Scout (10M) | Large context windows |
| Privacy, local deployment | Llama 4, Mistral, Qwen 3 | Open-source, self-hosted |
| Cost optimization | Open-source (Q5+ quant) | Free inference |

## Reasoning vs Non-Reasoning Models

This is the most important distinction for prompt optimization:

| Aspect | Reasoning (o3, DeepSeek R1) | Non-Reasoning (GPT-5, Claude, Gemini) |
|--------|---------------------------|---------------------------------------|
| CoT prompting | Redundant/harmful | Helpful for complex tasks |
| System prompt | Minimal, direct | Detailed rules welcome |
| Temperature | Fixed/ignored | Tune per task |
| Prompt style | Senior coworker (give goals) | Junior coworker (explicit steps) |
| Best for | Hard problems, math, logic | General purpose, creative, agentic |

## Claude (Anthropic) - Baseline

Key patterns (our default since we're in Claude Code):
- **XML tags** for structure: `<context>`, `<task>`, `<format>`, `<examples>`
- **Adaptive thinking** with `effort` parameter: `low` / `medium` / `high` / `max`
- **Be direct** - Claude generalizes from explanations, not rigid rules
- **Explain the "why"** behind constraints (not just "NEVER do X")
- **Long documents first** - Place context at top, queries below
- **Positive framing** - "Respond in plain prose" > "Don't use markdown"
- **Prefill technique** (API) - Start assistant response to guide format

## OpenAI GPT-5 - Baseline

Key patterns:
- **`reasoning_effort`** parameter controls thinking depth
- **Structure for caching** - Static content first, variable last (50-90% savings)
- **Contradictions waste tokens** - GPT-5 follows with "surgical precision"; conflicting instructions hurt
- **Don't over-prompt thoroughness** - Counterproductive; GPT-5 is naturally introspective
- **Tool preambles** - Have model rephrase goals and outline plans before tool calls
- **Markdown off by default** - Enable explicitly

## Gemini 2.5 - Baseline

Key patterns:
- **Always include few-shot examples** - Official docs say prompts without them are "likely less effective"
- **Temperature 1.0 for Gemini 3** - Changing it "may lead to unexpected behavior"
- **Context first, instructions last** - "Based on the information above..."
- **Multimodal is native** - Images/video/audio are integral, not attachments
- **Safety filters aggressive** - Adjust `safety_settings` per category
- **Google Search grounding** - Request explicitly when current info needed

## Open Source Models - Baseline

Key patterns:
- **System prompts ~75-85% reliable** - Layer critical instructions into user message too
- **Context degrades at 70-80%** of window - Keep critical info in first 30%
- **Q5 quantization minimum** for reliable instruction following
- **Temperature 0.6-0.7** (default 1.0 is too creative for most tasks)
- **Shorter prompts** - Open-source handles 200-word prompts better than 1000-word
- **Verify chat template** - `ollama show modelname`
- **DeepSeek R1** - "Think step-by-step" actually works (unlike o3); budget 2-3x tokens

### Quantization Impact

| Quant Level | Instruction Adherence | Recommendation |
|-------------|----------------------|----------------|
| Q8 (8-bit) | ~95% | Full quality |
| Q6 (6-bit) | ~85-90% | Good balance |
| Q5 (5-bit) | ~75-80% | Minimum for reliable use |
| Q4 (4-bit) | ~60-70% | Needs simpler prompts |
| Q3 and below | Not recommended | Instruction following breaks |

## Cross-Model Best Practices

### The "Context Engineering" Mindset
The LLM is a CPU, the context window is RAM, your job is the operating system loading exactly the right data for each task. Treat context as a budget.

**Prompt length sweet spot:** 150-300 words. Reasoning degrades around 3,000 tokens.

### Universal Techniques

1. **Clear role definition** - Always set expertise context
2. **Explicit output format** - Never assume the model will guess
3. **Direct imperative language** - "Analyze" not "Could you analyze"
4. **Provide examples** when format matters (3-5 is the sweet spot)
5. **Scope limiting** - "Only use information from the provided context"
6. **Priority ordering** - Order instructions by importance
7. **One primary task** - If combining tasks, clearly separate and label them
8. **Positive framing** - "Respond in plain prose" beats "Don't use markdown"
9. **Structure for caching** - Static content first, variable content last
10. **Test across model tiers** - What works on Opus/GPT-5 may overwhelm Haiku/Mini
