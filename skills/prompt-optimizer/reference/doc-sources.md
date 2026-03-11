# Prompt Engineering Doc Sources

Canonical documentation URLs for model-specific prompting best practices. Fetch these before optimizing for a specific model.

## Primary Sources (Official Docs)

| Provider | URL | What's There |
|----------|-----|-------------|
| **Anthropic** | `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` | Claude prompting overview |
| **Anthropic** | `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices` | Detailed best practices |
| **OpenAI** | `https://platform.openai.com/docs/guides/prompt-engineering` | General prompting guide |
| **OpenAI** | `https://platform.openai.com/docs/models` | Current model list + capabilities |
| **OpenAI Cookbook** | `https://developers.openai.com/cookbook` | Model-specific prompting guides (GPT-5, GPT-4.1, etc.) |
| **Google Gemini** | `https://ai.google.dev/gemini-api/docs/prompting-strategies` | Gemini prompting strategies |
| **Google Gemini** | `https://ai.google.dev/gemini-api/docs/changelog` | Latest model updates |
| **Mistral** | `https://docs.mistral.ai/guides/prompting-capabilities` | Mistral prompting guide |
| **Meta Llama** | `https://www.llama.com/docs/how-to-guides/prompting` | Llama prompting guide |

## Cookbook / Deep-Dive Sources

| Provider | URL | What's There |
|----------|-----|-------------|
| **OpenAI Cookbook** | `https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide` | GPT-5 specific guide |
| **OpenAI Cookbook** | `https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide` | GPT-4.1 patterns (still relevant for agentic work) |
| **Anthropic** | `https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking` | Extended thinking guide |
| **Anthropic** | `https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching` | Prompt caching |

## Search Strategies

When the primary docs don't cover a specific model or technique:

### For a specific model's prompting guide:
```
WebSearch: "[model name] prompting guide [current year]" site:platform.openai.com OR site:docs.anthropic.com OR site:ai.google.dev
```

### For a newly released model:
```
WebSearch: "[model name] prompt engineering best practices [current year]"
```
Then fetch the official announcement blog post - it usually contains prompting tips.

### For open-source models:
```
WebSearch: "[model name] prompting tips" site:huggingface.co OR site:github.com
```
Check the model card on HuggingFace - often has prompting examples and chat templates.

### For technique-specific guidance:
```
WebSearch: "[technique] [model name] best practices" (e.g., "chain of thought GPT-5")
```

## When to Fetch Docs

| Scenario | Action |
|----------|--------|
| User specifies a non-Claude model | Fetch primary doc for that provider |
| User mentions a model you don't recognize | WebSearch for it first |
| User is building a production system | Fetch docs even for Claude (check for updates) |
| BASIC mode / quick fix | Skip fetch, use baseline from model-specific.md |
| Model was released after your training data | Always fetch docs |

## Community Resources (Secondary)

These are useful for practical tips but may be opinionated:

- **LangChain Hub** - Community prompts and patterns
- **PromptHub** - Prompt testing and optimization
- **HuggingFace** - Model cards with prompting examples
- **GitHub model repos** - Official examples from model creators
