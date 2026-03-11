# Prompt Optimization Techniques

## Foundation Techniques

### Role Assignment
```
You are a [specific role] with expertise in [domain].
```
**When:** Always for complex tasks. Specific > generic ("Senior database architect" > "helpful assistant").

### Context Layering
```
Background: [situation]
Current state: [what exists now]
Goal: [desired outcome]
Constraints: [limitations]
```
**When:** Task requires domain knowledge or has implicit assumptions.

### Output Specification
```
Format: [markdown table / bullet list / JSON / etc.]
Length: [word count / paragraph count / page count]
Structure: [sections, headers, ordering]
Audience: [who will read this]
```
**When:** Always. Even "respond in 2-3 sentences" helps.

### Task Decomposition
```
Complete these steps in order:
1. [First analysis/action]
2. [Second analysis/action]
3. [Synthesis/output]
```
**When:** Multi-part tasks, anything requiring >1 type of thinking.

## Advanced Techniques

### Chain-of-Thought (CoT)
```
Think through this step by step:
1. First, identify [X]
2. Then, evaluate [Y]
3. Finally, recommend [Z]
Show your reasoning for each step.
```
**When:** Analysis, decisions, math, logic.
**Note:** Redundant/harmful for reasoning models (o3, DeepSeek R1). Helpful for GPT-5, Claude, Gemini.

### Few-Shot Learning
```
Here are examples of the format I want:

Input: "quarterly sales report"
Output: "Q3 2024 Revenue Analysis: SaaS Growth Drives 23% YoY Increase"

Input: "bug fix for login"
Output: "Fix: Resolve OAuth Token Refresh Race Condition in Login Flow"

Now process: [actual input]
```
**When:** Formatting, classification, style matching. 2-3 examples optimal; 3-5 for open-source models.

### Constraint Optimization
```
Requirements (in priority order):
1. Must: [non-negotiable]
2. Should: [important but flexible]
3. Could: [nice to have]
```
**When:** Design decisions, trade-off analysis, creative tasks with boundaries.

### Evaluation Criteria
```
Evaluate your response against:
- Accuracy: Are all claims verifiable?
- Completeness: Are all aspects addressed?
- Actionability: Can the reader act on this immediately?
```
**When:** High-stakes output, reviews, analysis.

## Structural Patterns

### The Sandwich Pattern
```
[Context/Role]
[Task]
[Format/Constraints]
```
Works universally across all models.

### The Template Pattern
```
Fill in this template:

Title: ___
Summary: ___
Key Points:
1. ___
2. ___
3. ___
Recommendation: ___
```
**When:** Consistent structured output needed.

### The Gatekeeper Pattern
```
Before responding, verify:
- [ ] Do I have enough information?
- [ ] Am I staying within scope?
- [ ] Is my response actionable?

If any check fails, ask for clarification instead of guessing.
```
**When:** Reducing hallucination, improving accuracy.

### The Iterative Refinement Pattern
```
1. Generate initial response
2. Critique it for [specific weaknesses]
3. Revise based on critique
4. Present final version
```
**When:** Creative work, complex analysis where first-draft quality matters.
