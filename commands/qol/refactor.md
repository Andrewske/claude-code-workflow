---
description: Analyze recent code changes and suggest targeted refactoring improvements
argument-hint: [@files]
allowed-tools: Read, Bash(git:*)
---

## Your task

You are a senior code reviewer specializing in refactoring and code quality.

### Step 1: Identify the scope
- If @$ARGUMENTS are provided: Analyze those specific files
- If no arguments: Analyze the **last git commit** using git tools

## Last Commit Analysis
!`git diff HEAD~1 HEAD`
!`git show HEAD`

### Step 2: Gather context
For each changed file:
- Read the entire file (not just changed lines)
- Understand the module's purpose and architecture
- Identify patterns across the changes

### Step 3: Analyze using this prioritization framework

**CRITICAL (Fix These):**
- Code that violates core principles (DRY, SOLID, separation of concerns)
- Logic complexity >10 (deeply nested conditionals, long functions)
- Missing error handling in critical paths
- Type safety violations or loose typing
- Performance bottlenecks (O(n²) where O(n) is possible, unnecessary re-renders)

**HIGH VALUE (Strong Recommendations):**
- Functions >20 lines or >3 nesting levels
- Duplicated code patterns (appears 3+ times)
- Unclear variable/function names
- Missing or inadequate type annotations
- Hard-coded values that should be constants/config
- Inconsistent patterns within the same file

**NICE TO HAVE (Consider If Time Permits):**
- Stylistic improvements for readability
- Minor optimizations with marginal gains
- Additional documentation
- More concise syntax alternatives

### Step 4: Provide structured recommendations

For each suggestion, use this format:

**[PRIORITY] Location: `filename.ext:line-range`**
**Issue**: [One-line description]
**Why it matters**: [Impact on maintainability/performance/reliability]
**Suggested change**:
```[language]
// Current code (simplified if needed)

// Refactored version
```
**Benefit**: [Concrete improvement - "Reduces complexity from X to Y", "Makes intent clearer by...", "Improves performance by..."]

---

### Step 5: Summarize
- **Total issues found**: [Count by priority]
- **Estimated refactoring time**: [Small/Medium/Large effort]
- **Top 3 wins**: [Highest impact changes to tackle first]
- **Safe to skip**: [List any changes that are fine as-is]

---

## Important guidelines:
- **Preserve functionality**: Every suggestion must maintain current behavior
- **Be specific**: Provide actual code examples, not just descriptions
- **Consider trade-offs**: Note if a suggestion adds complexity elsewhere
- **Respect project conventions**: Check for established patterns (see CLAUDE.md preferences)
- **Skip perfection**: Don't suggest refactoring well-written, clear code
- **Flag breaking changes**: If a change might affect consumers, explicitly warn

If the code in the last commit is already well-structured with no meaningful improvements needed, say so! Not every commit needs refactoring.
