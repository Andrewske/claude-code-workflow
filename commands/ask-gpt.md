---
description: Send a prompt to GPT via Codex CLI for a second opinion or alternative perspective
argument-hint: [--model <model>] <prompt>
---

<!-- Pricing config (verify periodically at https://platform.openai.com/docs/pricing):
  gpt-5.2-codex: $1.75/1M input, $14.00/1M output
  o3: $2.00/1M input, $8.00/1M output
  gpt-4o: $2.50/1M input, $10.00/1M output
-->

Send a task or question to an OpenAI model via the `codex exec` CLI. Codex does its own codebase research — do NOT pre-gather context.

## Argument Parsing

Parse the argument string for an optional `--model` flag:
- `--model <model>` — override the model (e.g., `--model o3`). Default: `gpt-5.2-codex`
- Everything after the flag (or the entire argument if no flag) is the prompt

Examples:
- `/ask-gpt How does the payment flow work?` → model: `gpt-5.2-codex`, prompt: "How does the payment flow work?"
- `/ask-gpt --model o3 Review this migration for issues` → model: `o3`, prompt: "Review this migration for issues"

## Behavior

1. **Capture the prompt.** If no argument was provided, ask the user what they'd like to ask.

2. **Determine the working directory.**
   - If the question targets a specific repo, use that repo's directory
   - Otherwise, use the current working directory

3. **Build the context prefix.** Check which of these files exist in the working directory: `AGENTS.md`, `CLAUDE.md`, `README.md`. If any exist, prepend this to the user's prompt:

   ```
   This project has the following context files in the repo root: [list files that exist]. Read them first if you need project context.
   ```

   If none exist, skip the prefix.

4. **Run codex exec.** Use the Bash tool with `run_in_background: true` and a 300000ms timeout (5 minutes):

   ```
   printf '%s' '<full_prompt>' | codex exec -m <model> --full-auto --search --json --ephemeral -C <working_directory> - 2>/dev/null
   ```

   Where `<full_prompt>` is the context prefix + user's question with any single quotes escaped.

   Tell the user that GPT is working on it and they can continue with other tasks.

   If the command times out, tell the user and suggest they run codex interactively for longer tasks.

5. **Parse the JSONL output.** Use the dedicated parser script on the task output file (get the path from `TaskOutput`):

   ```
   ~/.claude/scripts/parse-codex-output.sh <output_file>
   ```

   This outputs two sections:
   - `=== USAGE ===` — JSON object with `input`, `output`, `cached` token counts
   - `=== RESPONSE ===` — concatenated agent message text

6. **Present the result.** Show the GPT response, then append a cost report using the pricing from the config block at the top of this file for the selected model:

   ```
   ---
   **<Model> Usage Report**
   - Input tokens: X,XXX (cached: X,XXX)
   - Output tokens: X,XXX
   - Estimated cost: $X.XX
     - Input: X,XXX × $X.XX/1M = $X.XXXX
     - Output: X,XXX × $XX.XX/1M = $X.XXXX
   ```

## Good Use Cases

- **Second opinion on an approach**: "I'm thinking of splitting the auth service into two modules — what are the tradeoffs?"
- **Code review**: "Review the changes on this branch for bugs, security issues, and missed edge cases"
- **Alternative design**: "How would you implement rate limiting for this API? Look at the current middleware first."
- **Codebase questions**: "How does the payment flow work end-to-end? Trace it from the frontend."

## Notes

- Codex has its own file system access — it will read files, search code, and explore the repo independently
- If codex returns an error (e.g., auth issues), surface the raw error so the user can debug
- `--full-auto` uses sandboxed execution with workspace write access — reads are unrestricted, writes are sandboxed
- If the user wants codex to make changes (not just answer), warn them that changes are sandboxed and they'll need to run `codex apply` to accept them
