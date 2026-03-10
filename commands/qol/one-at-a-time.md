# One-at-a-Time Finding Resolution

You've just completed a review (plan or code) with findings. Now walk through each finding systematically with the user.

## Process

### Step 1: Categorize Findings

**CRITICAL: Use objective confidence thresholds, not subjective judgment.**

Separate findings into two categories based on confidence:

**Autosolve Findings (≥90% confidence):**
- **MUST include:** Any finding scoring 90% or higher
- There is ONE clearly superior fix
- Minimal trade-offs or debate needed
- Best practice is unambiguous
- Examples: typos, obvious bugs, clear standard violations, missing semicolons, unused imports

**Discussion Findings (<90% confidence):**
- **Only use for:** Findings scoring below 90%
- Multiple viable approaches exist
- Trade-offs need user input
- Context-dependent decisions
- Subjective preferences matter

**Confidence calibration examples:**
- Typo fix: 99%
- Unused import removal: 95%
- Missing null check (clear bug): 92%
- Architecture choice (2-3 valid options): 85%
- Naming preference (subjective): 75%
- Performance optimization (trade-offs): 80%

### Step 2: Process Discussion Findings First

For each discussion finding, follow this exact format:

**Finding:** [Brief description]

**Option 1:** [Approach name]
- Pro: [Benefit]
- Con: [Trade-off]

**Option 2:** [Approach name]
- Pro: [Benefit]
- Con: [Trade-off]

**Option 3:** [Approach name]
- Pro: [Benefit]
- Con: [Trade-off]

**Recommended:** Option [X] (XX% confidence) - [One sentence explaining why]

**Tip:** For complex findings with many trade-offs, invoke `/plan:best-idea` to explore alternatives more deeply.

Then **STOP and WAIT** for user confirmation. Do NOT continue to next finding.

**Grouping exception:** Only group discussion findings if they meet BOTH:
- **Small:** One-line fix, no discussion needed
- **Related:** Fixing one fixes the other

### Step 3: Handle User Response
- Questions? Answer them, re-present if needed
- Confirmation? Move to next finding
- Different choice? Acknowledge and move to next

### Step 4: Present Autosolve Findings (if any)

After all discussion findings are resolved, present autosolve findings as a single group.

**IMPORTANT:** ALL findings with ≥90% confidence MUST be in this group, not discussed individually earlier.

**Autosolve Findings - High Confidence Fixes**

I've identified [N] findings with clear, unambiguous fixes:

1. [Brief description] → [One-line fix summary] (XX%)
2. [Brief description] → [One-line fix summary] (XX%)
3. [Brief description] → [One-line fix summary] (XX%)
...

These are all >90% confidence - standard best practices with no meaningful trade-offs.

**Confirm to apply all, or say "review" to discuss individually.**

Then **STOP and WAIT** for confirmation.

If user says "review", process each autosolve finding individually using the discussion format from Step 2.

### Step 5: Complete
After all findings are resolved, briefly summarize decisions made.

## Rules

**DO:**
- Wait for explicit confirmation before proceeding
- Keep pros/cons to one line each
- Be concise but conversational
- Use the ≥90% threshold objectively - let the confidence score decide
- Present autosolve findings in scannable list format
- Show confidence percentage on ALL recommendations (required for transparency)
- Trust your confidence scores - if it's 90%+, it goes in autosolve

**DON'T:**
- Present multiple discussion findings at once
- Auto-proceed without confirmation
- Write lengthy explanations upfront
- Second-guess confidence scores - 90%+ = autosolve, no exceptions
- Mix autosolve and discussion findings in same step
- Artificially lower confidence to force discussion (be honest about confidence)
