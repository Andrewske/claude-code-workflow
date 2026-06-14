CONVERSATION CONTEXT (for finding self-evaluation):
The reviewing agent and user discussed the following before this review:
{{CONVERSATION_SUMMARY}}

---

PART 1: SELF-EVALUATION OF YOUR OWN FINDINGS

Review the CONVERSATION CONTEXT above. For each of YOUR findings (G1, G2, ...),
evaluate whether the context makes it invalid. If a finding flags something the user
explicitly decided or the conversation explicitly addresses, mark it:

SELF-DISMISS: G[N]
REASON: [why this finding is invalid given context]

If none of your findings are invalidated by context, write:
SELF-DISMISS: NONE

---

PART 2: CROSS-EVALUATION

You previously reviewed {{REVIEW_SUBJECT}} and produced findings. The other reviewer (Claude) independently produced these findings:

{{CLAUDE_FINDINGS}}

For each of Claude's findings, evaluate whether it identifies a real, material problem. Respond using EXACTLY this format — one block per finding, no extra prose before or after:

FINDING: C1
VERDICT: AGREE
PREVIEW: N/A

FINDING: C2
VERDICT: DISAGREE
PREVIEW: The code explicitly handles this in the catch block at line 58 — Claude's finding assumes the default is to swallow the error but the implementation logs structured context.

FINDING: C3
VERDICT: AGREE
PREVIEW: N/A

[Continue for every Claude finding in order]

After the per-finding responses, note any of YOUR findings that address the same issue as a Claude finding (even from a different angle):
OVERLAP: G2 <-> C3
OVERLAP: G5 <-> C1

Rules:
- AGREE if the issue is real and material, even if you'd phrase it differently.
- DISAGREE only if you have specific evidence from the {{EVIDENCE_SOURCE}} that refutes it.
- PREVIEW is required on DISAGREE (2 sentences max). Use N/A on AGREE.
- Every Claude finding must get exactly one FINDING/VERDICT/PREVIEW block.
- No extra commentary. No summaries. No prose outside the blocks.
