We disagree on a finding from the {{REVIEW_SUBJECT}} review. I need your genuine best-idea evaluation — not a shallow agreement or a restatement of your original position.

FINDING: {{FINDING_FULL}}
YOUR ORIGINAL POSITION: {{GPT_ORIGINAL}}
MY POSITION: {{CLAUDE_ORIGINAL}}

I ran the /plan:best-idea evaluation framework (Eliminate / Reuse / Standard / Minimal / Strategic) and my recommendation is:

RECOMMENDATION:
- Action: {{CLAUDE_ACTION}}
- Pick: {{CLAUDE_PICK}}
- Why: {{CLAUDE_WHY}}
- Trade-offs: {{CLAUDE_TRADEOFFS}}

Now you run the same evaluation. Do NOT simply agree with me to end the debate. Do NOT restate your original position without engaging with mine. Actually work through the framework below.

EVALUATION FRAMEWORK (from /plan:best-idea):
1. Frame the problem — restate the actual constraints from the {{EVIDENCE_SOURCE}} in 1-3 bullets (not abstract constraints)
2. Generate alternatives through these lenses:
   - Eliminate: Can we avoid/defer/simplify the problem itself?
   - Reuse: What does this codebase already do in similar situations? Read the repo to check (and use the `web_search` tool for upstream/library claims if available).
   - Standard: Is there a well-maintained library or pattern that solves this?
   - Minimal: What's the boring, safe, smallest-change solution?
   - Strategic: Is there a higher-effort option with 3x+ long-term payoff?
3. Compare your top 3 alternatives using this table:
   | Solution | Pros | Cons | Effort (S/M/L) | Risk (Low/Med/High) |
4. Pick the best one

The `Action` field is required. `fix` = code change warranted. `skip` = finding is real but not worth fixing now (micro-opt, low ROI, scope-out).

Output in this exact format:

FRAME:
[1-3 bullets]

ALTERNATIVES:
[comparison table]

RECOMMENDATION:
- Action: fix | skip
- Pick: [Your chosen solution — or "skip" if Action is skip]
- Why: [2-3 sentences — engage with my reasoning, don't just restate yours]
- Trade-offs: [What's given up]
VERDICT: AGREE | DISAGREE
